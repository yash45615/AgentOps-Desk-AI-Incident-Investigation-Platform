from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence import Evidence


class EvidenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **values: object) -> Evidence:
        evidence = Evidence(**values)
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def get_by_id(self, evidence_id: str) -> Evidence | None:
        statement = select(Evidence).where(Evidence.id == evidence_id)
        return self.db.scalar(statement)

    def list_for_incident(
        self,
        incident_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Evidence], int]:
        statement = select(Evidence).where(Evidence.incident_id == incident_id)
        total_statement = select(Evidence.id).where(Evidence.incident_id == incident_id)

        total = len(self.db.scalars(total_statement).all())
        items = list(
            self.db.scalars(
                statement.order_by(Evidence.created_at.desc(), Evidence.id.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )
        return items, total

    def delete(self, evidence: Evidence) -> None:
        self.db.delete(evidence)
        self.db.commit()
