from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        incident_id: str | None = None,
        actor: str = "system",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            incident_id=incident_id,
            details=details or {},
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        incident_id: str | None = None,
        action: str | None = None,
    ) -> tuple[list[AuditEvent], int]:
        statement = select(AuditEvent)
        count_statement = select(func.count()).select_from(AuditEvent)

        if incident_id is not None:
            statement = statement.where(AuditEvent.incident_id == incident_id)
            count_statement = count_statement.where(AuditEvent.incident_id == incident_id)

        if action is not None:
            statement = statement.where(AuditEvent.action == action)
            count_statement = count_statement.where(AuditEvent.action == action)

        total = self.db.scalar(count_statement) or 0

        items = list(
            self.db.scalars(
                statement.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )

        return items, total
