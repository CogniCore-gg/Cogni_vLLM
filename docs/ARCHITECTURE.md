# Architecture

## Gateway Design

The gateway is a FastAPI service that exposes a single OpenAI-compatible entry point on port `8101` and forwards requests to internal vLLM services.

- Public API surface:
  - `/v1/chat/completions`
  - `/v1/completions`
  - `/v1/embeddings`
  - `/v1/models`
- Internal services:
  - `qwen-main-vllm:8000`
  - `coder-vllm:8000`
  - `deepseek-vllm:8000`
  - `bge-large-vllm:8000`

## Why One Model Per vLLM Process

vLLM usually serves one primary model process because:

- KV cache and scheduler are tightly optimized around a loaded model
- GPU memory fragmentation and contention increase with multi-model loading
- Independent autoscaling, restarts, and tuning become easier
- Fault isolation is stronger (a single model failure does not drop all routes)

## Deployment layout

The default production compose file is `docker-compose.yml` (AMD ROCm + `vllm/vllm-openai:latest-rocm`).  
NVIDIA hosts use `docker-compose.cuda.yml` instead.

## Single Public API Endpoint

CogniOPS and CogniScribe only integrate with:

- `http://<host>:8101/v1`

This allows a stable client contract even when backend models or infrastructure change.

## Routing Behavior

- Chat/completions:
  - `qwen-main`, `coder`, `deepseek` are accepted
  - `bge-large` is rejected with OpenAI-style error JSON
- Embeddings:
  - only `bge-large` is accepted
  - LLM aliases are rejected
- `/v1/models` returns all alias cards and root model ids

## Request Flow

1. Client sends OpenAI-compatible request to gateway.
2. Gateway validates API key (if configured) and model alias.
3. Gateway selects target vLLM backend by alias.
4. Gateway forwards request with safe headers and timeout.
5. Gateway returns upstream response or OpenAI-style error.

## Streaming Proxy Behavior

For `stream=true` requests:

- gateway opens an upstream streaming connection
- bytes are relayed as they arrive (SSE-compatible flow)
- connection closes cleanly on upstream close/error
- timeout and upstream failures are converted to structured errors
