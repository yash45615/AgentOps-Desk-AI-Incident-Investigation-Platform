from sqlalchemy.engine import Engine

from app.db.base import Base
from app.db.session import engine
from app.models import AuditEvent, Evidence, Incident, Investigation


def initialize_database(target_engine: Engine = engine) -> None:
    """Create all registered database tables if they do not exist."""
    # Keep explicit references so the model imports are intentional.
    _ = (AuditEvent, Evidence, Incident, Investigation)
    Base.metadata.create_all(bind=target_engine)
