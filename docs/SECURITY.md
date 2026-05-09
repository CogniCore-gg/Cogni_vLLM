# Security

## API Key at Gateway

- Set `GATEWAY_API_KEY` in `.env` to enforce bearer auth.
- Clients must send:
  - `Authorization: Bearer <key>`

## Network Isolation

- Publish only gateway port `8101`.
- Keep vLLM services on internal Docker network.
- Restrict host/network ACLs to trusted CIDRs.

## Hugging Face Token Handling

- Store `HF_TOKEN` in environment or secret manager.
- Never hardcode token in repo.
- Rotate token and use least privilege where possible.

## Rate Limiting

The gateway enforces an in-memory per-client rate limit (`GATEWAY_RATE_LIMIT_RPM`) on `/v1/*` routes.
For enterprise deployments, still add an external API gateway for:

- per-key request limits
- burst control
- WAF policies

Set `GATEWAY_TRUST_X_FORWARDED_FOR=true` only when the gateway sits behind a trusted reverse proxy.

## CORS Policy

- CORS is disabled by default (safe server-to-server posture).
- To enable browser clients, set `GATEWAY_CORS_ALLOWED_ORIGINS` to explicit origins.
- Do not use wildcard origins for production inference APIs.

## TLS Reverse Proxy

Use Nginx/Traefik/Envoy in front of gateway for TLS termination.  
An Nginx example is provided in `configs/nginx.conf`.

Traefik/Envoy alternatives are valid if they enforce TLS, auth, and request size/time limits.

## Enterprise Hardening Checklist

- Enforce API key and TLS everywhere
- Centralize logs with retention policy
- Add admission policies/image scanning
- Pin container image tags and sign images
- Apply runtime seccomp/apparmor where feasible
- Run regular dependency and CVE scans
