from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends

from .config import Settings, get_settings
from .models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    status = "ok"
    details: Dict[str, Any] = {}
    timeout = httpx.Timeout(5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for alias, backend in settings.alias_to_backend.items():
            try:
                response = await client.get(f"{backend}/health")
                details[alias] = {"status": "ok", "code": response.status_code}
                if response.status_code >= 500:
                    status = "degraded"
            except Exception as exc:  # noqa: BLE001
                details[alias] = {"status": "down", "error": str(exc)}
                status = "degraded"
    return HealthResponse(status=status, services=details)
