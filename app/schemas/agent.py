from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentEvidenceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    evidence_type: str
    title: str
    source: str | None = None
    created_at: datetime | None = None


class AgentIncidentContext(BaseModel):
    incident: dict[str, Any]
    evidence_count: int = Field(ge=0)
    evidence: list[AgentEvidenceSummary] = Field(default_factory=list)
    available_actions: list[Literal["list_evidence", "run_investigation"]] = Field(
        default_factory=lambda: ["list_evidence", "run_investigation"]
    )
