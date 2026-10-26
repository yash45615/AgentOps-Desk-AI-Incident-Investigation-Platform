from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import (
    agent_router,
    audit_router,
    evidence_router,
    incidents_router,
    investigations_router,
)
from app.core.config import get_settings
from app.db.init_db import initialize_database
from app.db.session import get_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "An evidence-based incident investigation workspace for developers and AI agents."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Content-Type"],
)
app.include_router(incidents_router, prefix=settings.api_prefix)
app.include_router(evidence_router, prefix=settings.api_prefix)
app.include_router(investigations_router, prefix=settings.api_prefix)
app.include_router(agent_router, prefix=settings.api_prefix)
app.include_router(audit_router, prefix=settings.api_prefix)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request data is invalid.",
                    "details": exc.errors(),
                    "path": request.url.path,
                }
            }
        ),
    )


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "agentops-desk",
    }


@app.get(f"{settings.api_prefix}/health", tags=["System"])
def api_health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": settings.app_version,
    }


@app.get(f"{settings.api_prefix}/health/database", tags=["System"])
def database_health(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
    }
