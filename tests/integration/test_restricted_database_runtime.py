"""Production API smoke tests with actual non-owner, non-bypass service roles."""
import os
import json
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
import uuid

from cryptography.fernet import Fernet
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import pytest

from control_plane.app.infrastructure.db.privileges import validate_database_roles
from control_plane.app.infrastructure.db.session import set_tenant_context
from scripts.configure_database_roles import configure_roles, ROLES

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_production_api_with_restricted_database_roles(tmp_path):
    if os.getenv("TEST_RESTRICTED_DATABASE") != "1":
        pytest.skip("requires a disposable PostgreSQL database")
    admin_url = os.environ["DATABASE_URL"]
    admin_engine = create_engine(admin_url)
    passwords = {profile: secrets.token_urlsafe(32) for profile in ROLES}
    with psycopg2.connect(admin_url) as connection:
        configure_roles(connection, passwords)
    urls = {profile: admin_engine.url.set(username=name, password=passwords[profile]).render_as_string(hide_password=False)
            for profile, name in ROLES.items()}
    engines = {profile: create_engine(url) for profile, url in urls.items()}
    api = None
    second_api = None
    try:
        validate_database_roles(engines["runtime"], engines["authentication"], engines["worker"])
        with pytest.raises(RuntimeError, match="elevated privileges"):
            validate_database_roles(admin_engine, engines["authentication"], engines["worker"])
        # Service credentials cannot impersonate another profile or run DDL.
        for profile, statement in (("runtime", "SET ROLE sentinel_auth"),
                                   ("runtime", "CREATE TABLE forbidden_ddl (id integer)"),
                                   ("authentication", "SELECT * FROM applications"),
                                   ("worker", "SELECT * FROM users")):
            with psycopg2.connect(urls[profile]) as db:
                with db.cursor() as cursor:
                    with pytest.raises(psycopg2.errors.InsufficientPrivilege):
                        cursor.execute(statement)
        tenant_a, tenant_b = "restricted-a-" + uuid.uuid4().hex, "restricted-b-" + uuid.uuid4().hex
        ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        with admin_engine.begin() as db:
            db.execute(text("INSERT INTO tenants (id,name) VALUES (:a,'A'),(:b,'B')"), {"a": tenant_a,"b":tenant_b})
            db.execute(text("INSERT INTO applications (id,name,tenant_id) VALUES (:a,'A',:ta),(:b,'B',:tb)"),
                       {"a":ids[0],"b":ids[1],"ta":tenant_a,"tb":tenant_b})
        with Session(engines["runtime"]) as db:
            assert db.execute(text("SELECT id FROM applications")).all() == []
            assert db.execute(text("SELECT id FROM tenants")).all() == []
            set_tenant_context(db, tenant_a)
            assert db.execute(text("SELECT id FROM applications")).all() == [(ids[0],)]
            db.commit()
            assert db.execute(text("SELECT id FROM applications")).all() == [(ids[0],)]
            assert db.execute(text("SELECT id FROM tenants")).all() == [(tenant_a,)]
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = {**os.environ, "SL_ENV":"production", "ENVIRONMENT":"production", "SL_AUTO_CREATE_SCHEMA":"0",
               "DATABASE_URL":urls["runtime"], "AUTH_DATABASE_URL":urls["authentication"],
               "WORKER_DATABASE_URL":urls["worker"], "KMS_KEY":Fernet.generate_key().decode(),
               "JWT_SECRET":secrets.token_urlsafe(48), "SL_ENFORCE_PROVENANCE":"0", "PYTHONPATH":str(ROOT),
               "CONTROL_PLANE_URL":f"http://127.0.0.1:{port}"}
        # No runtime connection uses the owner/admin URL.
        env.pop("MIGRATION_DATABASE_URL", None)
        log_path = tmp_path / "restricted-api.log"
        with log_path.open("w+") as log:
            api = subprocess.Popen([sys.executable,"-m","uvicorn","control_plane.app.main:app",
                                    "--host","127.0.0.1","--port",str(port)],cwd=ROOT,env=env,stdout=log,stderr=log)
            for _ in range(100):
                if api.poll() is not None:
                    pytest.fail("Restricted API startup failed; inspect disposable runner log")
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/health/readiness",timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(.1)
            else:
                pytest.fail("Restricted API readiness timed out")
            tests = subprocess.run([sys.executable,"-m","pytest","tests/test_bola_real.py","tests/test_tenant_matrix.py",
                                    "tests/integration/test_full_pipeline.py","-q","--tb=short"],cwd=ROOT,env=env,
                                   capture_output=True,text=True,timeout=60)
            assert tests.returncode == 0, tests.stdout
            maintenance = subprocess.run([sys.executable,"-m","control_plane.app.workers.runner","--once"],
                                         cwd=ROOT,env=env,capture_output=True,text=True,timeout=30)
            assert maintenance.returncode == 0, "Maintenance must succeed with its narrow worker role"
            # Two actual API processes share only PostgreSQL, not a socket manager.
            from websockets.sync.client import connect
            import requests
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                second_port = sock.getsockname()[1]
            second_api = subprocess.Popen([sys.executable, "-m", "uvicorn", "control_plane.app.main:app",
                                           "--host", "127.0.0.1", "--port", str(second_port)],
                                          cwd=ROOT, env=env, stdout=log, stderr=log)
            for _ in range(100):
                try:
                    if requests.get(f"http://127.0.0.1:{second_port}/health", timeout=1).status_code == 200:
                        break
                except requests.RequestException:
                    time.sleep(.1)
            else:
                pytest.fail("Second restricted API did not start")
            suffix = uuid.uuid4().hex
            base = f"http://127.0.0.1:{port}"
            account = {"email": f"stream-{suffix}@example.com", "password": "DurableStreamTest123!",
                       "full_name": "Stream fixture", "tenant_id": f"stream-{suffix}"}
            assert requests.post(base + "/api/v1/auth/register", json=account, timeout=5).status_code == 200
            login = requests.post(base + "/api/v1/auth/login", json=account, timeout=5)
            assert login.status_code == 200
            headers = {"Authorization": "Bearer " + login.json()["access_token"]}
            ws_url = f"ws://127.0.0.1:{second_port}/api/v1/events-ws/stream?after=0"
            with connect(ws_url, additional_headers=headers, proxy=None) as subscriber:
                assert json.loads(subscriber.recv(timeout=5))["type"] == "stream.ready"
                created = requests.post(base + "/api/v1/events", headers=headers,
                                        json={"event_type": "test.multiworker", "data": {"durable": True}}, timeout=5)
                assert created.status_code == 200, created.text
                event_id = created.json()["id"]
                delivered = json.loads(subscriber.recv(timeout=5))
                assert delivered["event"]["id"] == event_id
                assert delivered["cursor"] == 1
            second_api.terminate()
            second_api.wait(timeout=10)
            second_api = None
            # Reconnect to the remaining process and replay from durable cursor 0.
            with connect(f"ws://127.0.0.1:{port}/api/v1/events-ws/stream?after=0",
                         additional_headers=headers, proxy=None) as subscriber:
                subscriber.recv(timeout=5)
                assert json.loads(subscriber.recv(timeout=5))["event"]["id"] == event_id
                assert requests.post(base + "/api/v1/auth/logout", headers=headers, timeout=5).status_code == 200
                from websockets.exceptions import ConnectionClosed
                with pytest.raises(ConnectionClosed):
                    subscriber.recv(timeout=5)
    finally:
        if second_api is not None:
            second_api.terminate()
            second_api.wait(timeout=10)
        if api is not None:
            api.terminate()
            api.wait(timeout=10)
        for engine in engines.values():
            engine.dispose()
        admin_engine.dispose()
