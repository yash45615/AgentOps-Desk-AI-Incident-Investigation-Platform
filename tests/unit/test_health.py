from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_application_information() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["name"] == "AgentOps Desk"
    assert response.json()["status"] == "running"


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "agentops-desk",
    }


def test_versioned_health_endpoint_returns_version() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.1.0"


def test_unknown_endpoint_returns_404() -> None:
    response = client.get("/does-not-exist")

    assert response.status_code == 404
