# CogniCore vLLM Operator Handover

## 1) System purpose

This repository is the unified vLLM inference server for CogniCore. It serves both:

- CogniOPS
- CogniScribe

Public API (OpenAI-compatible):

- `http://<host>:8101/v1`

## 2) Architecture

- Gateway service on port `8101`
- One vLLM container per model
- Internal routing by model alias
- Persistent Hugging Face cache in `./hf_cache`
- **Primary stack (ROCm):** `docker-compose.yml` — `vllm/vllm-openai:latest-rocm`, AMD device mappings
- **Optional NVIDIA stack:** `docker-compose.cuda.yml`
- Monitoring with Prometheus: `docker-compose.monitoring.yml`

## 3) Service inventory

| Service | Purpose | Internal port | Public exposure | Healthcheck behavior |
|---|---|---:|---|---|
| `gateway` | OpenAI-compatible API gateway, auth, rate limit, routing, metrics | `8101` | `8101` published | GET `http://127.0.0.1:8101/health` |
| `qwen-main-vllm` | LLM inference for `qwen-main` alias | `8000` | none | GET `http://127.0.0.1:8000/health` with long startup window |
| `coder-vllm` | LLM inference for `coder` alias | `8000` | none | GET `http://127.0.0.1:8000/health` with long startup window |
| `deepseek-vllm` | LLM inference for `deepseek` alias | `8000` | none | GET `http://127.0.0.1:8000/health` with long startup window |
| `bge-large-vllm` | Embedding inference for `bge-large` alias | `8000` | none | GET `http://127.0.0.1:8000/health` with long startup window |
| `prometheus` | Metrics collection for gateway + vLLM services | `9090` | `9090` published only if monitoring stack started | Process-level health (Prometheus running) |

## 4) Model aliases

- `qwen-main` -> `Qwen/Qwen3.6-35B-A3B`
- `coder` -> `Qwen/Qwen3-Coder-Next`
- `deepseek` -> `deepseek-ai/DeepSeek-V3.2`
- `bge-large` -> `BAAI/bge-large-en-v1.5`

Usage rules:

- `qwen-main`, `coder`, `deepseek` are for chat/completions
- `bge-large` is for embeddings only

## 5) Ports

- `8101`: gateway public API
- `9090`: Prometheus (if monitoring compose is running)
- `8000` internal per vLLM service (not published publicly)

## 6) First deployment checklist

1. Confirm GPU drivers are installed and working.
2. Confirm Docker daemon is running.
3. Confirm GPU runtime:
   - NVIDIA Container Toolkit for CUDA
   - ROCm device access (`/dev/kfd`, `/dev/dri`) for AMD
4. Set `HF_TOKEN` in `.env`.
5. Review `.env` values.
6. **Default:** deploy ROCm (`docker-compose.yml`). Use CUDA only if on NVIDIA.
7. Check available VRAM.
8. Do not start all huge models blindly.
9. Run compose validation: `docker compose config` (ROCm) and, if using NVIDIA, `docker compose -f docker-compose.cuda.yml config`.
10. Start stack.
11. Run health check.
12. Run smoke tests.

## 7) ROCm startup (default)

```bash
./scripts/start.sh
# or: ./scripts/start_rocm.sh
# or: docker compose --env-file .env up -d --build
./scripts/healthcheck.sh
pip install -r scripts/requirements.txt
python3 scripts/list_models.py
python3 scripts/smoke_chat.py
python3 scripts/smoke_embedding.py
```

## 8) CUDA startup (optional)

```bash
./scripts/start_cuda.sh
./scripts/healthcheck.sh
pip install -r scripts/requirements.txt
python3 scripts/list_models.py
python3 scripts/smoke_chat.py
python3 scripts/smoke_embedding.py
```

## 9) Stop stack

```bash
./scripts/stop.sh
```

## 10) Authenticated usage

If `GATEWAY_API_KEY` is set, all `/v1/*` calls require:

- `Authorization: Bearer <key>`

Examples:

```bash
API_KEY=<key> ./scripts/healthcheck.sh
API_KEY=<key> python3 scripts/smoke_chat.py
```

```bash
curl -s http://localhost:8101/v1/models \
  -H "Authorization: Bearer <key>"
```

## 11) CogniOPS integration

- Base URL: `http://<host>:8101/v1`
- Use `coder` for coding agents
- Use `deepseek` or `qwen-main` for reasoning/planning based on available hardware
- Use `bge-large` for retrieval embeddings

Python OpenAI SDK example:

```python
from openai import OpenAI

client = OpenAI(base_url="http://<host>:8101/v1", api_key="<key>")

resp = client.chat.completions.create(
    model="deepseek",
    messages=[{"role": "user", "content": "Create an incident response plan for a failed deploy."}],
    temperature=0.2,
)
print(resp.choices[0].message.content)
```

## 12) CogniScribe integration

- Base URL: `http://<host>:8101/v1`
- Use `qwen-main` for summarization/action extraction
- Use `bge-large` for meeting/document embeddings
- Use `coder` only for technical implementation-plan generation

Python OpenAI SDK example:

```python
from openai import OpenAI

client = OpenAI(base_url="http://<host>:8101/v1", api_key="<key>")

summary = client.chat.completions.create(
    model="qwen-main",
    messages=[{"role": "user", "content": "Summarize this meeting and extract action items."}],
    temperature=0.1,
)
print(summary.choices[0].message.content)
```

## 13) Logs

```bash
# Default (ROCm) stack — from repo root
docker compose logs -f gateway
docker compose logs -f qwen-main-vllm
# Optional NVIDIA stack
docker compose -f docker-compose.cuda.yml logs -f gateway
docker compose -f docker-compose.cuda.yml logs -f qwen-main-vllm
```

What to look for:

- model download progress
- CUDA/ROCm detection
- OOM errors
- gated model/token errors
- vLLM startup completion
- gateway request routing logs

## 14) Health checks

- `GET /health`
- `GET /v1/models`
- Docker service healthchecks

Notes:

- model startup may take a long time
- health != first-token latency SLO guarantee

## 15) Metrics and monitoring

- Gateway metrics at `GET /metrics`
- Prometheus at `9090` when monitoring compose is started

Track:

- request count
- latency
- upstream errors
- streaming request counts
- requests by model
- vLLM native metrics

Recommended alerts:

- high gateway 5xx/upstream errors
- p95/p99 latency breach
- container restart spikes
- OOM occurrences
- scrape target down

## 16) GPU allocation

Controls:

- `*_TP` tensor parallel variables
- `CUDA_VISIBLE_DEVICES` / `HIP_VISIBLE_DEVICES`
- per-model memory/context variables in `.env`

Guidance:

- assign GPUs intentionally per model
- dedicate GPUs for DeepSeek on heavy workloads
- avoid co-locating many heavy models on limited GPU memory
- MI300X: strong capacity, still requires careful planning
- H100/A100: preferred for enterprise large-model throughput
- RTX 4090 warning: do not assume all giant models can run together

## 17) Changing tensor parallel size

1. Edit `.env`.
2. Update:
   - `QWEN_MAIN_TP`
   - `CODER_TP`
   - `DEEPSEEK_TP`
   - `BGE_TP`
3. Ensure matching GPUs are visible.
4. Restart stack.
5. Validate logs show expected TP configuration.

## 18) Adding a new model

1. Add model env vars in `.env.example` and `.env`.
2. Add model service to `docker-compose.yml` (ROCm) and, if you support NVIDIA, to `docker-compose.cuda.yml`.
3. Add alias/backend/model mapping in gateway config/routing.
4. Ensure `/v1/models` includes new alias.
5. Update docs.
6. Add/extend smoke tests.
7. Validate compose config.
8. Run health + smoke tests.

## 19) Removing a model

1. Remove/disable model service in compose.
2. Remove alias mapping in gateway.
3. Update docs.
4. Update smoke tests.
5. Validate no stale route remains in `/v1/models`.

## 20) Troubleshooting startup failure

- Docker not running
- missing GPU runtime support
- bad image tag
- `HF_TOKEN` missing
- model gated/private access denied
- no disk space
- insufficient shared memory
- port conflict
- container restart loop

## 21) Troubleshooting OOM

- lower `*_MAX_MODEL_LEN`
- lower `*_GPU_MEMORY_UTILIZATION`
- increase `*_TP`
- use smaller model
- use quantization if supported
- run fewer models simultaneously
- dedicate GPU/node to DeepSeek
- clear orphan containers and stale workloads

## 22) Troubleshooting HuggingFace errors

- accept model license on Hugging Face
- set `HF_TOKEN`
- verify token inside container environment
- check cache permissions
- remove corrupt cache subdirectory and redownload

## 23) Troubleshooting routing/API errors

- unknown model alias
- `bge-large` sent to chat endpoint
- LLM alias sent to embeddings endpoint
- missing Authorization header when API key enabled
- upstream service unhealthy
- streaming client timeout

## 24) Security checklist

- set `GATEWAY_API_KEY`
- run behind TLS proxy
- restrict CORS
- do not expose internal vLLM ports
- protect `.env`
- pin image tags
- enforce rate limits at gateway/proxy
- rotate `HF_TOKEN`
- maintain log hygiene

## 25) Monitoring checklist

- gateway metrics scraped
- vLLM metrics scraped
- GPU telemetry monitored
- disk usage monitored
- restart counts monitored
- request error alerts configured
- latency alerts configured
- OOM alerts configured

## 26) Backup/cache notes

- `hf_cache` contains model downloads
- cache size can be large
- backup is often optional
- preserving cache improves restart speed

Safe cleanup:

1. Stop stack.
2. Remove only targeted stale/corrupt cache paths.
3. Restart and revalidate.

## 27) Upgrade procedure

1. Backup `.env`.
2. Pin current image tags.
3. Pull new images.
4. Validate compose config.
5. Start one model first.
6. Run smoke tests.
7. Roll out remaining models.

## 28) Rollback procedure

1. Revert image tags.
2. Restore previous configs.
3. Restart stack.
4. Verify `/v1/models`.
5. Run smoke tests.
6. Inspect logs for stability.

## 29) Known limitations

- gateway rate limiter is in-memory per instance
- live inference must be validated by operator runtime tests
- very large models may require multi-GPU/multi-node
- `latest` tags can change over time
- health does not equal production readiness
- hardware fit depends on checkpoint, dtype, context, quantization, and workload

## 30) Final quick reference

```bash
# start default (ROCm)
./scripts/start.sh

# start ROCm (same as start.sh)
./scripts/start_rocm.sh

# start CUDA (optional)
./scripts/start_cuda.sh

# stop
./scripts/stop.sh

# logs (ROCm default)
docker compose logs -f gateway
docker compose logs -f qwen-main-vllm
# logs (CUDA)
docker compose -f docker-compose.cuda.yml logs -f gateway
docker compose -f docker-compose.cuda.yml logs -f qwen-main-vllm

# list models
python3 scripts/list_models.py

# smoke chat
python3 scripts/smoke_chat.py

# smoke embeddings
python3 scripts/smoke_embedding.py

# authenticated examples
API_KEY=<key> ./scripts/healthcheck.sh
API_KEY=<key> python3 scripts/smoke_chat.py
curl -s http://localhost:8101/v1/models -H "Authorization: Bearer <key>"
```
