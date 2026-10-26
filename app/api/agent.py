from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import require_agent_api_key
from app.db.session import get_db
from app.schemas.agent import AgentEvidenceSummary, AgentIncidentContext
from app.schemas.evidence import EvidenceList
from app.schemas.investigation import InvestigationRead
from app.services.audit_service import AuditService
from app.services.evidence_service import EvidenceService
from app.services.incident_service import IncidentService
from app.services.investigation_service import InvestigationService

router = APIRouter(
    prefix="/agent",
    tags=["Agent API"],
    dependencies=[Depends(require_agent_api_key)],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/incidents/{incident_id}/context",
    response_model=AgentIncidentContext,
)
def get_incident_context(
    incident_id: str,
    db: DatabaseSession,
) -> AgentIncidentContext:
    incident = IncidentService(db).get(incident_id)

    evidence_items, evidence_total = EvidenceService(db).list_for_incident(
        incident_id,
        limit=10,
        offset=0,
    )

    return AgentIncidentContext(
        incident=incident,
        evidence_count=evidence_total,
        evidence=[AgentEvidenceSummary.model_validate(item) for item in evidence_items],
    )


@router.get(
    "/incidents/{incident_id}/evidence",
    response_model=EvidenceList,
)
def get_incident_evidence(
    incident_id: str,
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
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


@router.post(
    "/incidents/{incident_id}/investigate",
    response_model=InvestigationRead,
    status_code=status.HTTP_201_CREATED,
)
def investigate_incident(
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
        actor="agent_api",
        action="agent.investigation.run",
        resource_type="investigation",
        resource_id=investigation.id,
        incident_id=incident_id,
        details={"outcome": "success"},
    )

    return investigation


@router.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationRead,
)
def get_agent_investigation(
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
