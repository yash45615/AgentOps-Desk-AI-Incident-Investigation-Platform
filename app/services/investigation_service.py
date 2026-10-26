from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.investigation_engine import EvidenceInput, analyze_evidence
from app.models.evidence import Evidence
from app.models.incident import Incident
from app.models.investigation import Investigation


class InvestigationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, incident_id: str) -> Investigation:
        incident = self.db.get(Incident, incident_id)
        if incident is None:
            raise LookupError("Incident not found.")

        statement = (
            select(Evidence)
            .where(Evidence.incident_id == incident_id)
            .order_by(Evidence.created_at.asc(), Evidence.id.asc())
        )
        evidence_rows = list(self.db.scalars(statement).all())

        evidence_inputs = [
            EvidenceInput(
                id=item.id,
                evidence_type=item.evidence_type,
                title=item.title,
                content=item.content,
                source=item.source,
            )
            for item in evidence_rows
        ]

        result = analyze_evidence(evidence_inputs)
        investigation = Investigation(
            incident_id=incident_id,
            status="completed",
            summary=result.summary,
            findings=result.findings,
            confidence=result.confidence,
            engine_version=result.engine_version,
            completed_at=datetime.now(UTC),
        )

        self.db.add(investigation)
        self.db.commit()
        self.db.refresh(investigation)
        return investigation

    def get(self, investigation_id: str) -> Investigation:
        investigation = self.db.get(Investigation, investigation_id)
        if investigation is None:
            raise LookupError("Investigation not found.")
        return investigation

    def list_for_incident(
        self,
        incident_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Investigation], int]:
        incident = self.db.get(Incident, incident_id)
        if incident is None:
            raise LookupError("Incident not found.")

        statement = select(Investigation).where(Investigation.incident_id == incident_id)
        items = list(
            self.db.scalars(
                statement.order_by(
                    Investigation.created_at.desc(),
                    Investigation.id.desc(),
                )
                .limit(limit)
                .offset(offset)
            ).all()
        )

        count_statement = select(Investigation.id).where(Investigation.incident_id == incident_id)
        total = len(self.db.scalars(count_statement).all())
        return items, total
