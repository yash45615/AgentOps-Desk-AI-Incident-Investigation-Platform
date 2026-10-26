from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.incident import Incident
from app.repositories.evidence_repository import EvidenceRepository
from app.schemas.evidence import EvidenceCreate


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = EvidenceRepository(db)

    def create(
        self,
        incident_id: str,
        payload: EvidenceCreate,
    ) -> Evidence:
        incident = self.db.get(Incident, incident_id)
        if incident is None:
            raise LookupError("Incident not found.")

        values = payload.model_dump()
        values["metadata_json"] = values.pop("metadata")
        values["incident_id"] = incident_id

        return self.repository.create(**values)

    def list_for_incident(
        self,
        incident_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Evidence], int]:
        incident = self.db.get(Incident, incident_id)
        if incident is None:
            raise LookupError("Incident not found.")

        return self.repository.list_for_incident(
            incident_id,
            limit=limit,
            offset=offset,
        )

    def get(self, evidence_id: str) -> Evidence:
        evidence = self.repository.get_by_id(evidence_id)
        if evidence is None:
            raise LookupError("Evidence not found.")
        return evidence

    def delete(self, evidence_id: str) -> None:
        evidence = self.get(evidence_id)
        self.repository.delete(evidence)
