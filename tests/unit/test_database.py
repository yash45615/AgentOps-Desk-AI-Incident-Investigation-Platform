from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.init_db import initialize_database
from app.models import AuditEvent, Evidence, Incident, Investigation


def make_test_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_initialization_creates_all_expected_tables() -> None:
    test_engine = make_test_engine()

    try:
        initialize_database(test_engine)

        tables = set(inspect(test_engine).get_table_names())

        assert {
            "incidents",
            "evidence",
            "investigations",
            "audit_events",
        }.issubset(tables)
    finally:
        test_engine.dispose()


def test_incident_and_related_records_persist() -> None:
    test_engine = make_test_engine()
    Base.metadata.create_all(bind=test_engine)

    try:
        with Session(test_engine) as session:
            incident = Incident(
                title="Checkout latency spike",
                description="Checkout requests became slow.",
                severity="high",
                service_name="checkout-api",
            )
            session.add(incident)
            session.flush()

            evidence = Evidence(
                incident_id=incident.id,
                evidence_type="log",
                title="Gateway timeout",
                content="Upstream request timed out after 3000ms.",
                source="test-fixture",
                metadata_json={"request_id": "req-001"},
            )
            investigation = Investigation(
                incident_id=incident.id,
                status="completed",
                summary="The logs show an upstream timeout.",
                findings=[
                    {
                        "claim": "An upstream request timed out.",
                        "evidence_ids": [evidence.id],
                    }
                ],
                confidence=0.85,
            )
            audit_event = AuditEvent(
                incident_id=incident.id,
                actor="test-user",
                action="incident.created",
                resource_type="incident",
                resource_id=incident.id,
                details={"source": "unit-test"},
            )

            session.add_all([evidence, investigation, audit_event])
            session.commit()
            incident_id = incident.id

        with Session(test_engine) as session:
            saved_incident = session.get(Incident, incident_id)

            assert saved_incident is not None
            assert saved_incident.title == "Checkout latency spike"
            assert len(saved_incident.evidence_items) == 1
            assert len(saved_incident.investigations) == 1
            assert len(saved_incident.audit_events) == 1

            saved_evidence = session.scalar(select(Evidence))
            assert saved_evidence is not None
            assert saved_evidence.metadata_json == {"request_id": "req-001"}

    finally:
        test_engine.dispose()


def test_incident_delete_removes_dependent_records() -> None:
    test_engine = make_test_engine()
    Base.metadata.create_all(bind=test_engine)

    try:
        with Session(test_engine) as session:
            incident = Incident(
                title="Temporary test incident",
                service_name="test-service",
            )
            incident.evidence_items.append(
                Evidence(
                    evidence_type="log",
                    title="Test log",
                    content="Test content",
                )
            )
            session.add(incident)
            session.commit()
            incident_id = incident.id

            session.delete(incident)
            session.commit()

            assert session.get(Incident, incident_id) is None
            assert session.scalar(select(Evidence)) is None
    finally:
        test_engine.dispose()
