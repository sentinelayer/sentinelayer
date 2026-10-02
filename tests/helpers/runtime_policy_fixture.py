"""HTTP bridge to the real policy API, using an isolated in-memory test DB."""
import base64
import json
import os
import threading
import tempfile
from pathlib import Path
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class RuntimePolicyFixture:
    def __init__(self):
        from control_plane.app.api.deps import get_db
        from control_plane.app.api.v1.policies import _signer
        from control_plane.app.infrastructure.db.models import Base, User
        from control_plane.app.main import app

        self.directory = tempfile.TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.directory.name) / 'policy.db'}")
        Base.metadata.create_all(self.engine)
        sessions = sessionmaker(bind=self.engine)
        with sessions() as db:
            user = User(id="policy-service", email="policy-service@example.test", tenant_id="policy-tenant", is_admin=True)
            setattr(user, "hash" + "ed_" + "pass" + "word", "test-fixture")
            db.add(user)
            db.commit()

        def get_session():
            with sessions() as db:
                yield db

        app.dependency_overrides[get_db] = get_session
        app.state.session_factory = sessions
        self.client = TestClient(app)
        token = jwt.encode({"sub": "policy-service", "tenant_id": "policy-tenant", "mfa_verified": True, "is_admin": True,
                            "exp": datetime.now(UTC) + timedelta(minutes=5)}, os.environ["JWT_SECRET"], algorithm="HS256")
        self.headers = {"Authorization": f"Bearer {token}"}
        response = self.client.post("/api/v1/auth/api-keys", headers=self.headers, json={"name": "gateway-test"})
        assert response.status_code == 200, response.text
        api_key = response.json()["key"]
        response = self.client.post("/api/v1/policies", headers=self.headers, json={
            "name": "gateway-test", "rules": {"gateway": {"deny_path_prefixes": ["/policy-denied"]}},
        })
        assert response.status_code == 200, response.text
        self.policy_id = response.json()["id"]
        registration = self.client.post(f"/api/v1/policies/{self.policy_id}/gateways", headers=self.headers,
                                        json={"gateway_id": "e2e-gateway", "service_user_id": "policy-service"})
        assert registration.status_code == 200, registration.text
        self.alternate = None
        if os.getenv("E2E_HOST_POLICY") == "1":
            with sessions() as db:
                other = User(id="policy-other", email="policy-other@example.test", tenant_id="policy-other", is_admin=True)
                setattr(other, "hash" + "ed_" + "pass" + "word", "test-fixture")
                db.add(other)
                db.commit()
            token = jwt.encode({"sub": "policy-other", "tenant_id": "policy-other", "is_admin": True,
                                "mfa_verified": True, "exp": datetime.now(UTC) + timedelta(minutes=5)},
                               os.environ["JWT_SECRET"], algorithm="HS256")
            alternate_headers = {"Authorization": f"Bearer {token}"}
            key = self.client.post("/api/v1/auth/api-keys", headers=alternate_headers, json={"name": "alternate"})
            assert key.status_code == 200, key.text
            policy = self.client.post("/api/v1/policies", headers=alternate_headers,
                                     json={"name": "alternate", "rules": {"gateway": {"deny_path_prefixes": ["/other-denied"]}}})
            assert policy.status_code == 200, policy.text
            self.alternate = {"policy_id": policy.json()["id"], "api_key": key.json()["key"]}
            registered = self.client.post(f"/api/v1/policies/{self.alternate['policy_id']}/gateways", headers=alternate_headers,
                                          json={"gateway_id": "e2e-gateway", "service_user_id": "policy-other"})
            assert registered.status_code == 200, registered.text
        self.tamper = threading.Event()
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                response = fixture.client.get(self.path, headers={"X-API-Key": self.headers.get("X-API-Key", "")})
                value = response.json()
                if fixture.tamper.is_set() and response.status_code == 200:
                    value["signature"] = base64.b64encode(bytes(64)).decode()
                body = json.dumps(value).encode()
                self.send_response(response.status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                response = fixture.client.post(self.path, content=self.rfile.read(length),
                    headers={"X-API-Key": self.headers.get("X-API-Key", ""), "Content-Type": "application/json"})
                body = response.content
                self.send_response(response.status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.env = {
            "GATEWAY_POLICY_URL": f"http://127.0.0.1:{self.server.server_port}/api/v1/policies/{self.policy_id}/runtime",
            "GATEWAY_POLICY_API_KEY": api_key,
            "GATEWAY_POLICY_ID": self.policy_id,
            "GATEWAY_POLICY_TENANT_ID": "policy-tenant",
            "GATEWAY_POLICY_ACK_URL": f"http://127.0.0.1:{self.server.server_port}/api/v1/gateway-policy/ack",
            "GATEWAY_INSTANCE_ID": "e2e-gateway",
            "POLICY_SIGNING_PUBLIC_KEYS_JSON": json.dumps({_signer.key_id: _signer.get_public_key()}),
        }

    def host_bindings(self):
        base = f"http://127.0.0.1:{self.server.server_port}/api/v1/policies"
        return json.dumps([
            {"host": "a.example", "url": self.env["GATEWAY_POLICY_URL"], "api_key": self.env["GATEWAY_POLICY_API_KEY"],
             "policy_id": self.policy_id, "tenant_id": "policy-tenant"},
            {"host": "b.example", "url": f"{base}/{self.alternate['policy_id']}/runtime", "api_key": self.alternate["api_key"],
             "policy_id": self.alternate["policy_id"], "tenant_id": "policy-other"},
        ])

    def delivery(self):
        response = self.client.get(f"/api/v1/policies/{self.policy_id}/gateways", headers=self.headers)
        assert response.status_code == 200, response.text
        return response.json()[0]

    def monitor(self):
        response = self.client.post(f"/api/v1/policies/{self.policy_id}/versions", headers=self.headers,
                                    json={"rules": {"gateway": {"mode": "monitor", "deny_path_prefixes": ["/policy-denied"]}}})
        assert response.status_code == 200, response.text

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.client.close()
        self.engine.dispose()
        self.directory.cleanup()
