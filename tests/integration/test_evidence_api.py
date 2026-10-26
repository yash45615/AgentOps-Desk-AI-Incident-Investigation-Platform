from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_incident() -> str:
    response = client.post(
        "/api/v1/incidents",
        json={
            "title": "Evidence API test incident",
            "description": "Incident created for evidence API tests.",
            "severity": "high",
            "service_name": "payments",
            "environment": "test",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def evidence_payload() -> dict:
    return {
        "evidence_type": "log",
        "title": "Payment service error",
        "content": "Connection timeout while contacting payment provider.",
        "source": "test-runner",
        "metadata": {
            "request_id": "req-test-001",
            "region": "ap-south-1",
        },
    }


def test_create_and_get_evidence() -> None:
    incident_id = create_incident()

    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        json=evidence_payload(),
    )

    assert response.status_code == 201, response.text
    created = response.json()
    assert created["incident_id"] == incident_id
    assert created["evidence_type"] == "log"
    assert created["metadata"]["request_id"] == "req-test-001"
    assert "metadata_json" not in created

    get_response = client.get(f"/api/v1/evidence/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


def test_list_evidence_for_incident() -> None:
    incident_id = create_incident()

    for title in ("First log", "Second log"):
        payload = evidence_payload()
        payload["title"] = title
        response = client.post(
            f"/api/v1/incidents/{incident_id}/evidence",
            json=payload,
        )
        assert response.status_code == 201, response.text

    response = client.get(
        f"/api/v1/incidents/{incident_id}/evidence",
        params={"limit": 1, "offset": 0},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 1


def test_create_evidence_for_missing_incident_returns_404() -> None:
    response = client.post(
        "/api/v1/incidents/incident-does-not-exist/evidence",
        json=evidence_payload(),
    )

    assert response.status_code == 404


def test_invalid_evidence_type_returns_422() -> None:
    incident_id = create_incident()
    payload = evidence_payload()
    payload["evidence_type"] = "random_text"

    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_blank_evidence_title_returns_422() -> None:
    incident_id = create_incident()
    payload = evidence_payload()
    payload["title"] = "   "

    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        json=payload,
    )

    assert response.status_code == 422


def test_delete_evidence() -> None:
    incident_id = create_incident()
    create_response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        json=evidence_payload(),
    )
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/evidence/{evidence_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/evidence/{evidence_id}")
    assert get_response.status_code == 404


def test_list_evidence_for_missing_incident_returns_404() -> None:
    response = client.get("/api/v1/incidents/incident-does-not-exist/evidence")

    assert response.status_code == 404
