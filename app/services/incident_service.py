from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident import IncidentCreate, IncidentUpdate


class IncidentService:
    def __init__(self, db: Session) -> None:
        self.repository = IncidentRepository(db)

    def create(self, data: IncidentCreate) -> Incident:
        return self.repository.create(data)

    def get(self, incident_id: str) -> Incident:
        incident = self.repository.get_by_id(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found.",
            )
        return incident

    def list(
        self,
        *,
        limit: int,
        offset: int,
        severity: str | None = None,
        status: str | None = None,
        service_name: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Incident], int]:
        return self.repository.list(
            limit=limit,
            offset=offset,
            severity=severity,
            status=status,
            service_name=service_name,
            search=search,
        )

    def update(self, incident_id: str, data: IncidentUpdate) -> Incident:
        incident = self.get(incident_id)
        changes = data.model_dump(exclude_unset=True)

        if not changes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide at least one field to update.",
            )

        if any(value is None for value in changes.values()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Updated fields cannot be null.",
            )

        return self.repository.update(incident, data)

    def delete(self, incident_id: str) -> None:
        incident = self.get(incident_id)
        self.repository.delete(incident)
