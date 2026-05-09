import json
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse

from .config import Settings, get_settings
from .metrics import REQUESTS_BY_MODEL, STREAM_REQUESTS, UPSTREAM_ERRORS
from .models import ModelCard, ModelsResponse, OpenAIErrorBody, OpenAIErrorResponse

LOGGER = logging.getLogger("gateway.router")
router = APIRouter(prefix="/v1", tags=["v1"])
SAFE_PASSTHROUGH_HEADERS = {
    "authorization",
    "openai-organization",
    "openai-project",
    "x-request-id",
    "x-correlation-id",
}
RESPONSE_PASSTHROUGH_HEADERS = {
    "content-type",
    "cache-control",
    "x-request-id",
}


def _error(message: str, status_code: int, param: Optional[str] = None) -> JSONResponse:
    payload = OpenAIErrorResponse(error=OpenAIErrorBody(message=message, param=param))
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _extract_model(payload: Dict[str, Any]) -> Optional[str]:
    model = payload.get("model")
    return str(model) if isinstance(model, str) and model.strip() else None


def _validate_api_key(request: Request, settings: Settings) -> None:
    configured = settings.gateway_api_key.strip()
    if not configured:
        return
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer API key",
        )
    supplied = auth_header.replace("Bearer ", "", 1).strip()
    if supplied != configured:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


def _filtered_headers(request: Request) -> Dict[str, str]:
    outgoing: Dict[str, str] = {}
    for key, value in request.headers.items():
        if key.lower() in SAFE_PASSTHROUGH_HEADERS:
            outgoing[key] = value
    return outgoing


def _response_headers(headers: httpx.Headers) -> Dict[str, str]:
    outgoing: Dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in RESPONSE_PASSTHROUGH_HEADERS:
            outgoing[key] = value
    return outgoing


def _resolve_target_for_chat_or_completion(payload: Dict[str, Any], settings: Settings) -> str:
    alias = _extract_model(payload)
    if not alias:
        raise HTTPException(status_code=400, detail="Field 'model' is required")
    if alias == settings.bge_alias:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{alias}' is embedding-only and cannot be used for text generation",
        )
    if alias not in settings.llm_aliases:
        raise HTTPException(status_code=404, detail=f"Unknown model alias '{alias}'")
    return settings.alias_to_backend[alias]


def _resolve_target_for_embeddings(payload: Dict[str, Any], settings: Settings) -> str:
    alias = _extract_model(payload)
    if not alias:
        raise HTTPException(status_code=400, detail="Field 'model' is required")
    if alias != settings.bge_alias:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{alias}' does not support embeddings; use '{settings.bge_alias}'",
        )
    return settings.alias_to_backend[alias]


async def _proxy_openai_request(
    request: Request,
    backend_base_url: str,
    endpoint: str,
    payload: Dict[str, Any],
    settings: Settings,
) -> Response:
    timeout = httpx.Timeout(settings.gateway_timeout_seconds)
    headers = _filtered_headers(request)
    url = f"{backend_base_url}{endpoint}"
    is_stream = bool(payload.get("stream"))
    model_alias = _extract_model(payload) or "unknown"
    REQUESTS_BY_MODEL.labels(endpoint, model_alias).inc()
    if is_stream:
        STREAM_REQUESTS.labels(endpoint, model_alias).inc()
    LOGGER.info(
        "proxy_request",
        extra={"extra": {"endpoint": endpoint, "backend": backend_base_url, "stream": is_stream}},
    )

    if is_stream:
        try:
            client = httpx.AsyncClient(timeout=timeout)
            upstream = await client.send(
                client.build_request("POST", url, headers=headers, json=payload),
                stream=True,
            )
            if upstream.status_code >= 400:
                body = await upstream.aread()
                await upstream.aclose()
                await client.aclose()
                return Response(
                    content=body,
                    status_code=upstream.status_code,
                    headers=_response_headers(upstream.headers),
                    media_type=upstream.headers.get("content-type", "application/json"),
                )

            async def body_stream():
                try:
                    async for chunk in upstream.aiter_bytes():
                        yield chunk
                finally:
                    await upstream.aclose()
                    await client.aclose()

            return StreamingResponse(
                body_stream(),
                status_code=upstream.status_code,
                media_type=upstream.headers.get("content-type", "text/event-stream"),
                headers={**_response_headers(upstream.headers), "X-Accel-Buffering": "no"},
            )
        except httpx.TimeoutException:
            UPSTREAM_ERRORS.labels(endpoint, "timeout").inc()
            return _error(f"Gateway timeout after {settings.gateway_timeout_seconds}s", 504)
        except httpx.RequestError as exc:
            UPSTREAM_ERRORS.labels(endpoint, "request_error").inc()
            LOGGER.exception("stream_proxy_error", extra={"extra": {"error": str(exc)}})
            return _error("Upstream model service unavailable", 502)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream = await client.post(url, headers=headers, json=payload)
            return Response(
                content=upstream.content,
                status_code=upstream.status_code,
                headers=_response_headers(upstream.headers),
                media_type=upstream.headers.get("content-type", "application/json"),
            )
    except httpx.TimeoutException:
        UPSTREAM_ERRORS.labels(endpoint, "timeout").inc()
        return _error(f"Gateway timeout after {settings.gateway_timeout_seconds}s", 504)
    except httpx.RequestError as exc:
        UPSTREAM_ERRORS.labels(endpoint, "request_error").inc()
        LOGGER.exception("proxy_error", extra={"extra": {"error": str(exc)}})
        return _error("Upstream model service unavailable", 502)


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Response:
    _validate_api_key(request, settings)
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return _error("Invalid JSON body", 400)
    if not isinstance(payload, dict):
        return _error("JSON body must be an object", 400)
    try:
        backend = _resolve_target_for_chat_or_completion(payload, settings)
    except HTTPException as exc:
        return _error(str(exc.detail), exc.status_code, param="model")
    return await _proxy_openai_request(request, backend, "/v1/chat/completions", payload, settings)


@router.post("/completions")
async def completions(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Response:
    _validate_api_key(request, settings)
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return _error("Invalid JSON body", 400)
    if not isinstance(payload, dict):
        return _error("JSON body must be an object", 400)
    try:
        backend = _resolve_target_for_chat_or_completion(payload, settings)
    except HTTPException as exc:
        return _error(str(exc.detail), exc.status_code, param="model")
    return await _proxy_openai_request(request, backend, "/v1/completions", payload, settings)


@router.post("/embeddings")
async def embeddings(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Response:
    _validate_api_key(request, settings)
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return _error("Invalid JSON body", 400)
    if not isinstance(payload, dict):
        return _error("JSON body must be an object", 400)
    try:
        backend = _resolve_target_for_embeddings(payload, settings)
    except HTTPException as exc:
        return _error(str(exc.detail), exc.status_code, param="model")
    return await _proxy_openai_request(request, backend, "/v1/embeddings", payload, settings)


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> ModelsResponse:
    _validate_api_key(request, settings)
    data = [
        ModelCard(id=alias, root=real_model)
        for alias, real_model in settings.alias_to_model_id.items()
    ]
    return ModelsResponse(data=data)
