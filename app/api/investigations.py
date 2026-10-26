from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.investigation import InvestigationList, InvestigationRead
from app.services.audit_service import AuditService
from app.services.investigation_service import InvestigationService

router = APIRouter(tags=["Investigations"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/incidents/{incident_id}/investigations",
    response_model=InvestigationRead,
    status_code=status.HTTP_201_CREATED,
)
def run_investigation(
    incident_id: str,
    db: DatabaseSession,
) -> InvestigationRead:
    try:
        investigation = InvestigationService(db).run(incident_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    AuditService(db).record(
        action="investigation.run",
        resource_type="investigation",
        resource_id=investigation.id,
        incident_id=incident_id,
        details={"success": True},
    )
    return investigation


@router.get(
    "/incidents/{incident_id}/investigations",
    response_model=InvestigationList,
)
def list_investigations(
    incident_id: str,
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> InvestigationList:
    try:
        items, total = InvestigationService(db).list_for_incident(
            incident_id,
            limit=limit,
            offset=offset,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return InvestigationList(items=items, total=total)


@router.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationRead,
)
def get_investigation(
    investigation_id: str,
    db: DatabaseSession,
) -> InvestigationRead:
    try:
        return InvestigationService(db).get(investigation_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
