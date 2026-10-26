from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Severity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["open", "investigating", "resolved", "closed"]


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=10_000)
    severity: Severity = "medium"
    status: IncidentStatus = "open"
    service_name: str = Field(default="unknown", min_length=1, max_length=120)
    environment: str = Field(default="development", min_length=1, max_length=50)

    @field_validator("title", "service_name", "environment")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)
    severity: Severity | None = None
    status: IncidentStatus | None = None
    service_name: str | None = Field(default=None, min_length=1, max_length=120)
    environment: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("title", "service_name", "environment")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    severity: Severity
    status: IncidentStatus
    service_name: str
    environment: str
    created_at: datetime
    updated_at: datetime


class IncidentList(BaseModel):
    items: list[IncidentRead]
    total: int
    limit: int
    offset: int
