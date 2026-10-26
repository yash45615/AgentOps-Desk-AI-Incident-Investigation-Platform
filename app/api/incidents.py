from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.incident import (
    IncidentCreate,
    IncidentList,
    IncidentRead,
    IncidentStatus,
    IncidentUpdate,
    Severity,
)
from app.services.audit_service import AuditService
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["Incidents"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_incident(
    payload: IncidentCreate,
    db: DatabaseSession,
) -> IncidentRead:
    incident = IncidentService(db).create(payload)

    AuditService(db).record(
        action="incident.created",
        resource_type="incident",
        resource_id=incident.id,
        incident_id=incident.id,
        details={
            "severity": str(incident.severity),
            "service_name": incident.service_name,
        },
    )
    return incident


@router.get("", response_model=IncidentList)
def list_incidents(
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    severity: Severity | None = None,
    status_filter: Annotated[
        IncidentStatus | None,
        Query(alias="status"),
    ] = None,
    service_name: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
) -> IncidentList:
    items, total = IncidentService(db).list(
        limit=limit,
        offset=offset,
        severity=severity,
        status=status_filter,
        service_name=service_name,
        search=search.strip() if search else None,
    )
    return IncidentList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: str,
    db: DatabaseSession,
) -> IncidentRead:
    return IncidentService(db).get(incident_id)


@router.patch("/{incident_id}", response_model=IncidentRead)
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    db: DatabaseSession,
) -> IncidentRead:
    changed_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    incident = IncidentService(db).update(incident_id, payload)

    AuditService(db).record(
        action="incident.updated",
        resource_type="incident",
        resource_id=incident.id,
        incident_id=incident.id,
        details={"changed_fields": changed_fields},
    )
    return incident


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_incident(
    incident_id: str,
    db: DatabaseSession,
) -> Response:
    IncidentService(db).delete(incident_id)

    # Do not set incident_id here: the incident has already been deleted.
    # resource_id preserves its identifier for the audit record.
    AuditService(db).record(
        action="incident.deleted",
        resource_type="incident",
        resource_id=incident_id,
        details={"deleted": True},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
