# CogniCore vLLM Server

CogniCore vLLM Server is a production-ready, unified inference platform for CogniOPS and CogniScribe.  
It exposes one OpenAI-compatible API endpoint on `http://localhost:8101/v1` and routes model traffic to dedicated vLLM backends.

**Default deployment is AMD ROCm** (`docker-compose.yml`). NVIDIA CUDA is supported via `docker-compose.cuda.yml`.

## AMD Development Hackathon reminder

The CogniCore stack is split across **three codebases** on GitHub:

| Repo | URL |
|------|-----|
| **Cogni_vLLM** (this repo) | [github.com/CogniCore-gg/Cogni_vLLM](https://github.com/CogniCore-gg/Cogni_vLLM) |
| **cogniOPS** | [github.com/CogniCore-gg/cogniOPS](https://github.com/CogniCore-gg/cogniOPS) |
| **cogniScribe** | [github.com/CogniCore-gg/cogniScribe](https://github.com/CogniCore-gg/cogniScribe) |

- **Cogni_vLLM** — OpenAI-compatible inference gateway and vLLM backends (ROCm default, CUDA optional).
- **cogniOPS** — Governed AI engineering platform (orchestration, agents, governance, integrations).
- **cogniScribe** — Meeting intelligence (uploads, transcription, extraction via the same vLLM-style API).

## Architecture Overview

- One gateway service (`FastAPI`) on port `8101`
- One vLLM container per model
- Internal model routing by alias
- Streaming proxy support for chat/completions
- Health checks for gateway and each vLLM service
- Prometheus monitoring hooks (`/metrics`)
- Shared persistent Hugging Face cache volume (`./hf_cache`)

## Model Aliases

- `qwen-main` -> `Qwen/Qwen3.6-35B-A3B`
- `coder` -> `Qwen/Qwen3-Coder-Next`
- `deepseek` -> `deepseek-ai/DeepSeek-V3.2`
- `bge-large` -> `BAAI/bge-large-en-v1.5`

## Quick Start (ROCm — default)

1. Copy environment file and set your token:
   - `cp .env.example .env`
   - set `HF_TOKEN` in `.env`
2. Start stack (either command):
   - `./scripts/start.sh` or `./scripts/start_rocm.sh`
   - or `docker compose --env-file .env up -d --build`
3. Verify:
   - `./scripts/healthcheck.sh`
4. Install smoke-test deps:
   - `pip install -r scripts/requirements.txt`
5. Test API:
   - `python3 scripts/list_models.py`
   - `python3 scripts/smoke_chat.py`
   - `python3 scripts/smoke_embedding.py`

## Quick Start (CUDA — optional)

1. Copy environment file and set your token:
   - `cp .env.example .env`
   - set `HF_TOKEN` in `.env`
2. Start stack:
   - `./scripts/start_cuda.sh`
3. Verify:
   - `./scripts/healthcheck.sh`
4. Install smoke-test deps:
   - `pip install -r scripts/requirements.txt`
5. Test API:
   - `python3 scripts/list_models.py`
   - `python3 scripts/smoke_chat.py`
   - `python3 scripts/smoke_embedding.py`

## Environment Variables

Main variables are defined in `.env.example`:

- Gateway: `GATEWAY_TIMEOUT_SECONDS`, `GATEWAY_API_KEY` (API is always served on **host port 8101** → container 8101; see `docker-compose.yml` / `docker-compose.cuda.yml`)
- Gateway security: `GATEWAY_RATE_LIMIT_RPM`, `GATEWAY_CORS_ALLOWED_ORIGINS`, `GATEWAY_TRUST_X_FORWARDED_FOR`
- HF cache/token: `HF_TOKEN`, `HF_HOME`
- Global GPU visibility: `CUDA_VISIBLE_DEVICES`, `HIP_VISIBLE_DEVICES`
- Per-model controls:
  - `*_TP`
  - `*_MAX_MODEL_LEN`
  - `*_GPU_MEMORY_UTILIZATION`
  - `*_DTYPE`

## API Usage

- Base URL: `http://localhost:8101/v1`
- Endpoints:
  - `POST /v1/chat/completions`
  - `POST /v1/completions`
  - `POST /v1/embeddings`
  - `GET /v1/models`

See detailed examples in `docs/API_USAGE.md`.

## Hardware Planning

- Use `docs/MODEL_PLANNING.md` for VRAM sizing and tensor-parallel strategy.
- For larger models, start with one major model per multi-GPU node.
- Embeddings are lightweight and can typically co-reside with one LLM.
- Do not assume all listed models can run together on one consumer GPU.

## Common Errors

- CUDA OOM -> lower `*_MAX_MODEL_LEN`, reduce `*_GPU_MEMORY_UTILIZATION`, increase TP.
- ROCm device missing -> check `/dev/kfd`, `/dev/dri`, user group permissions.
- 404 model errors -> verify alias in request body matches `/v1/models`.
- 502 **Upstream model service unavailable** -> gateway cannot reach the vLLM container (crashed, still starting, or wrong Docker network). Check `docker logs <backend>-vllm`; common ROCm cause: `HIP_VISIBLE_DEVICES` lists GPUs that do not exist → **No HIP GPUs** in logs — fix `QWEN_MAIN_HIP_VISIBLE_DEVICES` etc. in `.env` (default compose runs **qwen-main only**; use `--profile full-stack` for all four backends).
- Gated model failures -> confirm `HF_TOKEN` has access for each model.

## Production Deployment Notes

- Put TLS in front of gateway (example Nginx config in `configs/nginx.conf`).
- Set `GATEWAY_API_KEY` and enforce private network ACLs.
- Set `GATEWAY_RATE_LIMIT_RPM` to a conservative value before exposing externally.
- Keep `hf_cache` on fast local NVMe.
- Route logs to a centralized stack (Loki/ELK/Datadog).
- Monitor `vllm:*` and gateway metrics through Prometheus.

## Known Limitations

- In-memory rate limiting is per-gateway instance (not globally shared across replicas).
- `/health` checks service availability, not full warm-token readiness.
- Large model startup can take many minutes due to weight downloads and graph warmup.
- DeepSeek-V3.2 deployment shape depends on actual checkpoint and context requirements.

## First Deployment Checklist

- Set `HF_TOKEN` with access to all gated models.
- Set `GATEWAY_API_KEY` (non-empty) for production.
- Set `GATEWAY_CORS_ALLOWED_ORIGINS` explicitly; keep empty for server-to-server only.
- Confirm TLS termination at NGINX/Traefik/Envoy.
- Validate GPU visibility (ROCm: `/dev/kfd`, `/dev/dri`; CUDA: `nvidia-smi`).
- Run `docker compose config` (default ROCm) and/or `docker compose -f docker-compose.cuda.yml config` before first `up`.
- Run `./scripts/healthcheck.sh` and smoke tests.
- Verify Prometheus scrape targets are healthy.

## Minimum Viable Hardware Setups

- `bge-large` only: 1x consumer GPU is usually sufficient.
- Single LLM (`qwen-main` or `coder`): often needs high-memory GPU or quantization.
- DeepSeek-V3.2: typically requires multi-GPU or specialized high-memory deployment.

## Recommended Enterprise Hardware Setups

- NVIDIA: A100/H100 multi-GPU nodes for heavy LLM workloads.
- AMD: MI300X 192GB nodes for high-memory inference and larger context windows.
- Split `deepseek` to dedicated GPUs/node when targeting strict latency SLOs.

## Critical Warning

Do not run all giant models on one consumer GPU.  
Use model separation, tensor parallelism, and hardware planning before production traffic.

## Stopping Services

- `./scripts/stop.sh`

## Monitoring Stack

- Start Prometheus:
  - `docker compose -f docker-compose.monitoring.yml up -d`
- Open Prometheus:
  - [http://localhost:9090](http://localhost:9090)
