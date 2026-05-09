from prometheus_client import Counter, Histogram

REQUEST_COUNTER = Counter(
    "gateway_requests_total",
    "Total requests handled by gateway",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "gateway_request_duration_seconds",
    "Request duration in seconds",
    ["method", "path"],
)
UPSTREAM_ERRORS = Counter(
    "gateway_upstream_errors_total",
    "Upstream request failures grouped by endpoint and reason",
    ["endpoint", "reason"],
)
STREAM_REQUESTS = Counter(
    "gateway_stream_requests_total",
    "Streaming requests processed by gateway",
    ["endpoint", "model"],
)
REQUESTS_BY_MODEL = Counter(
    "gateway_model_requests_total",
    "Total model requests by endpoint and model alias",
    ["endpoint", "model"],
)
