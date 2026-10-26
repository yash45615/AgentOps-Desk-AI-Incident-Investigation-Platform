from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_incident() -> str:
    response = client.post(
        "/api/v1/incidents",
        json={
            "title": "Investigation test incident",
            "description": "An incident used to test investigations.",
            "severity": "high",
            "service_name": "checkout",
            "environment": "test",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def add_evidence(incident_id: str, content: str) -> str:
    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        json={
            "evidence_type": "log",
            "title": "Checkout service log",
            "content": content,
            "source": "integration-test",
            "metadata": {"test": True},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_run_investigation_and_get_result() -> None:
    incident_id = create_incident()
    evidence_id = add_evidence(
        incident_id,
        "Payment provider returned HTTP 503 service unavailable.",
    )

    response = client.post(f"/api/v1/incidents/{incident_id}/investigations")

    assert response.status_code == 201, response.text
    result = response.json()
    assert result["incident_id"] == incident_id
    assert result["status"] == "completed"
    assert result["engine_version"] == "rules-v1"
    assert result["confidence"] > 0
    assert any(finding["evidence_id"] == evidence_id for finding in result["findings"])

    get_response = client.get(f"/api/v1/investigations/{result['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == result["id"]


def test_investigation_with_no_evidence() -> None:
    incident_id = create_incident()

    response = client.post(f"/api/v1/incidents/{incident_id}/investigations")

    assert response.status_code == 201, response.text
    result = response.json()
    assert result["findings"] == []
    assert result["confidence"] == 0.0


def test_missing_incident_returns_404() -> None:
    response = client.post("/api/v1/incidents/missing-incident/investigations")

    assert response.status_code == 404


def test_list_investigations_for_incident() -> None:
    incident_id = create_incident()

    for _ in range(2):
        response = client.post(f"/api/v1/incidents/{incident_id}/investigations")
        assert response.status_code == 201, response.text

    response = client.get(f"/api/v1/incidents/{incident_id}/investigations")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2


def test_missing_investigation_returns_404() -> None:
    response = client.get("/api/v1/investigations/missing-investigation")

    assert response.status_code == 404
