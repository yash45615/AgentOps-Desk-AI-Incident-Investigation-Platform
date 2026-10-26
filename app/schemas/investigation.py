from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InvestigationFinding(BaseModel):
    rule_id: str
    title: str
    description: str
    evidence_id: str
    evidence_title: str
    evidence_type: str
    source: str
    excerpt: str


class InvestigationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    status: str
    summary: str | None
    findings: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float | None
    engine_version: str
    created_at: datetime
    completed_at: datetime | None


class InvestigationList(BaseModel):
    items: list[InvestigationRead]
    total: int
