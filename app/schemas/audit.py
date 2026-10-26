from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str | None = None
    actor: str
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AuditEventList(BaseModel):
    items: list[AuditEventRead]
    total: int
    limit: int
    offset: int
