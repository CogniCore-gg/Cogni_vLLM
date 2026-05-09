import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import get_settings
from .health import router as health_router
from .logging_config import configure_logging
from .metrics import REQUEST_COUNTER, REQUEST_LATENCY
from .ratelimit import SlidingWindowRateLimiter
from .router import router as v1_router

settings = get_settings()
configure_logging(settings.gateway_log_level)
rate_limiter = SlidingWindowRateLimiter(settings.gateway_rate_limit_rpm)

app = FastAPI(
    title="CogniCore vLLM Gateway",
    description="Unified OpenAI-compatible API gateway for CogniOPS and CogniScribe",
    version="1.0.0",
)

if settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "OpenAI-Organization", "OpenAI-Project"],
    )


def _client_identifier(request: Request) -> str:
    if settings.gateway_trust_x_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    path = request.url.path
    if path.startswith("/v1/"):
        rate = await rate_limiter.check(_client_identifier(request))
        if not rate.allowed:
            REQUEST_COUNTER.labels(request.method, path, "429").inc()
            REQUEST_LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "message": "Rate limit exceeded",
                        "type": "rate_limit_exceeded",
                        "param": None,
                        "code": "rate_limit_exceeded",
                    }
                },
            )
    response = await call_next(request)
    latency = time.perf_counter() - start
    REQUEST_COUNTER.labels(request.method, path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(latency)
    return response


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(v1_router)
