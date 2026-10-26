from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_agent_api_key
from app.db.session import get_db
from app.schemas.audit import AuditEventList
from app.services.audit_service import AuditService

router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
    dependencies=[Depends(require_agent_api_key)],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/events", response_model=AuditEventList)
def list_audit_events(
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    incident_id: Annotated[str | None, Query(min_length=1, max_length=36)] = None,
    action: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
) -> AuditEventList:
    items, total = AuditService(db).list_events(
        limit=limit,
        offset=offset,
        incident_id=incident_id,
        action=action,
    )

    return AuditEventList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
