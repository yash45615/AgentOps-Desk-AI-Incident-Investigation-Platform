import hmac
from typing import Annotated

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_agent_api_key(
    supplied_key: Annotated[
        str | None,
        Header(alias="X-Agent-API-Key"),
    ] = None,
) -> None:
    settings = get_settings()
    expected_key = settings.agent_api_key

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent API authentication is not configured.",
        )

    if supplied_key is None or not hmac.compare_digest(
        supplied_key,
        expected_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid agent API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
