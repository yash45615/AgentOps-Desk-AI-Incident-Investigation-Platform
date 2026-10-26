import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def create_incident(client: TestClient, **overrides: object) -> dict:
    payload = {
        "title": "Checkout latency spike",
        "description": "Checkout requests are slower than usual.",
        "severity": "high",
        "service_name": "checkout-api",
        "environment": "staging",
    }
    payload.update(overrides)

    response = client.post("/api/v1/incidents", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_incident(client: TestClient) -> None:
    incident = create_incident(client)

    assert incident["title"] == "Checkout latency spike"
    assert incident["severity"] == "high"
    assert incident["status"] == "open"
    assert incident["service_name"] == "checkout-api"
    assert incident["id"]


def test_reject_invalid_severity(client: TestClient) -> None:
    response = client.post(
        "/api/v1/incidents",
        json={"title": "Invalid severity test", "severity": "urgent"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_reject_blank_title(client: TestClient) -> None:
    response = client.post(
        "/api/v1/incidents",
        json={"title": "   "},
    )

    assert response.status_code == 422


def test_get_incident(client: TestClient) -> None:
    created = create_incident(client)

    response = client.get(f"/api/v1/incidents/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_missing_incident_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/incidents/does-not-exist")

    assert response.status_code == 404


def test_update_incident(client: TestClient) -> None:
    created = create_incident(client)

    response = client.patch(
        f"/api/v1/incidents/{created['id']}",
        json={"status": "investigating", "severity": "critical"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "investigating"
    assert response.json()["severity"] == "critical"


def test_reject_empty_update(client: TestClient) -> None:
    created = create_incident(client)

    response = client.patch(
        f"/api/v1/incidents/{created['id']}",
        json={},
    )

    assert response.status_code == 400


def test_list_incidents_and_filter_by_severity(client: TestClient) -> None:
    create_incident(client, title="High priority issue", severity="high")
    create_incident(client, title="Low priority issue", severity="low")

    response = client.get("/api/v1/incidents", params={"severity": "high"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all(item["severity"] == "high" for item in body["items"])


def test_search_incidents(client: TestClient) -> None:
    create_incident(client, title="Payments service timeout")

    response = client.get(
        "/api/v1/incidents",
        params={"search": "Payments service timeout"},
    )

    assert response.status_code == 200
    assert any(item["title"] == "Payments service timeout" for item in response.json()["items"])


def test_delete_incident(client: TestClient) -> None:
    created = create_incident(client)

    response = client.delete(f"/api/v1/incidents/{created['id']}")

    assert response.status_code == 204

    follow_up = client.get(f"/api/v1/incidents/{created['id']}")
    assert follow_up.status_code == 404
