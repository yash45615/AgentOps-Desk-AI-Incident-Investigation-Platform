from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evidence import EvidenceCreate, EvidenceList, EvidenceRead
from app.services.audit_service import AuditService
from app.services.evidence_service import EvidenceService

router = APIRouter(tags=["Evidence"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/incidents/{incident_id}/evidence",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence(
    incident_id: str,
    payload: EvidenceCreate,
    db: DatabaseSession,
) -> EvidenceRead:
    try:
        evidence = EvidenceService(db).create(incident_id, payload)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    AuditService(db).record(
        action="evidence.created",
        resource_type="evidence",
        resource_id=evidence.id,
        incident_id=incident_id,
        details={"evidence_type": str(evidence.evidence_type)},
    )
    return evidence


@router.get(
    "/incidents/{incident_id}/evidence",
    response_model=EvidenceList,
)
def list_evidence(
    incident_id: str,
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EvidenceList:
    try:
        items, total = EvidenceService(db).list_for_incident(
            incident_id,
            limit=limit,
            offset=offset,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return EvidenceList(items=items, total=total)


@router.get("/evidence/{evidence_id}", response_model=EvidenceRead)
def get_evidence(
    evidence_id: str,
    db: DatabaseSession,
) -> EvidenceRead:
    try:
        return EvidenceService(db).get(evidence_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/evidence/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_evidence(
    evidence_id: str,
    db: DatabaseSession,
) -> Response:
    try:
        # Fetch first so we retain the parent incident ID.
        evidence = EvidenceService(db).get(evidence_id)
        incident_id = evidence.incident_id
        EvidenceService(db).delete(evidence_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    AuditService(db).record(
        action="evidence.deleted",
        resource_type="evidence",
        resource_id=evidence_id,
        incident_id=incident_id,
        details={"deleted": True},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
