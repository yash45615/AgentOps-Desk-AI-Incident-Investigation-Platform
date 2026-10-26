from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

EvidenceType = Literal["log", "stack_trace", "metric", "event"]


class EvidenceCreate(BaseModel):
    evidence_type: EvidenceType
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100_000)
    source: str = Field(default="manual", min_length=1, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime | None = None

    @field_validator("title", "content", "source")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    evidence_type: str
    title: str
    content: str
    source: str
    metadata: dict[str, Any] = Field(
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    observed_at: datetime | None
    created_at: datetime


class EvidenceList(BaseModel):
    items: list[EvidenceRead]
    total: int
