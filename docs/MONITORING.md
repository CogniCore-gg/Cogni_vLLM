# Monitoring

## vLLM Metrics

vLLM exposes Prometheus-compatible metrics at `/metrics`.  
This stack includes a Prometheus config scraping all model services and the gateway.

## Prometheus

- Config file: `configs/prometheus.yml`
- Compose file: `docker-compose.monitoring.yml`
- Start:
  - `docker compose -f docker-compose.monitoring.yml up -d`
- UI:
  - [http://localhost:9090](http://localhost:9090)

## Grafana Recommendation

Use Grafana dashboards for:

- token throughput
- request latency distributions
- queue pressure
- GPU memory saturation
- error rates

Pair Prometheus with Grafana and alerting rules for SLO tracking.

## Logs

- Gateway uses structured JSON logs.
- vLLM logs are available via docker compose logs.
- Forward both to centralized observability (ELK/Loki/Datadog) in production.

## Key Metrics To Watch

- Gateway:
  - `gateway_requests_total`
  - `gateway_request_duration_seconds`
  - `gateway_upstream_errors_total`
  - `gateway_stream_requests_total`
  - `gateway_model_requests_total`
- vLLM:
  - request latency
  - queue depth
  - token generation rates
  - cache utilization
  - model health/restarts

## vLLM Native Metrics

Each vLLM container exposes `/metrics`; include per-model dashboards for:

- prefill/decode throughput
- pending/running request counts
- KV cache pressure
- token latency trends
- error and restart rates
