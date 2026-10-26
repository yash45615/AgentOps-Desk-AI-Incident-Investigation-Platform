from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate


class IncidentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: IncidentCreate) -> Incident:
        incident = Incident(**data.model_dump())
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get_by_id(self, incident_id: str) -> Incident | None:
        return self.db.get(Incident, incident_id)

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
        statement = select(Incident)
        count_statement = select(func.count()).select_from(Incident)

        if severity is not None:
            statement = statement.where(Incident.severity == severity)
            count_statement = count_statement.where(Incident.severity == severity)

        if status is not None:
            statement = statement.where(Incident.status == status)
            count_statement = count_statement.where(Incident.status == status)

        if service_name is not None:
            statement = statement.where(Incident.service_name == service_name)
            count_statement = count_statement.where(Incident.service_name == service_name)

        if search is not None:
            pattern = f"%{search}%"
            search_filter = Incident.title.ilike(pattern)
            statement = statement.where(search_filter)
            count_statement = count_statement.where(search_filter)

        statement = (
            statement.order_by(Incident.created_at.desc(), Incident.id.desc())
            .limit(limit)
            .offset(offset)
        )

        items = list(self.db.scalars(statement).all())
        total = self.db.scalar(count_statement) or 0
        return items, total

    def update(
        self,
        incident: Incident,
        data: IncidentUpdate,
    ) -> Incident:
        changes = data.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(incident, field, value)

        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def delete(self, incident: Incident) -> None:
        self.db.delete(incident)
        self.db.commit()
