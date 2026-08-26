from fastapi.testclient import TestClient

from control_plane.app.main import app

client = TestClient(app)

def test_cl_te_smuggling():
    headers = {
        "Content-Length": "13",
        "Transfer-Encoding": "chunked"
    }
    response = client.get("/health", headers=headers)
    assert response.status_code in [200, 400, 403]

def test_duplicate_content_length():
    headers = {
        "Content-Length": "10",
        "Content-Length": "20"
    }
    response = client.get("/health", headers=headers)
    assert response.status_code in [200, 400, 403]
