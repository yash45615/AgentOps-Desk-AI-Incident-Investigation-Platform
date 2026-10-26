import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.audit_event import AuditEvent
    from app.models.evidence import Evidence
    from app.models.investigation import Investigation


def utc_now() -> datetime:
    return datetime.now(UTC)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
        index=True,
    )
    service_name: Mapped[str] = mapped_column(
        String(120),
        default="unknown",
        nullable=False,
        index=True,
    )
    environment: Mapped[str] = mapped_column(
        String(50),
        default="development",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    evidence_items: Mapped[list["Evidence"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    investigations: Mapped[list["Investigation"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
    )
