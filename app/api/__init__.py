from app.api.agent import router as agent_router
from app.api.audit import router as audit_router
from app.api.evidence import router as evidence_router
from app.api.incidents import router as incidents_router
from app.api.investigations import router as investigations_router

__all__ = [
    "agent_router",
    "audit_router",
    "evidence_router",
    "incidents_router",
    "investigations_router",
]
