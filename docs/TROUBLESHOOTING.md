# Troubleshooting

## CUDA Out Of Memory

- Reduce `*_MAX_MODEL_LEN`
- Lower `*_GPU_MEMORY_UTILIZATION`
- Increase tensor parallelism (`*_TP`)
- Move large model to dedicated GPUs

## ROCm Device Not Found

- Verify `/dev/kfd` and `/dev/dri` exist
- Confirm user membership in `video` and `render`
- Check ROCm driver installation on host

## Hugging Face Gated Model Access

- Ensure `HF_TOKEN` is set in `.env`
- Confirm token has accepted model licenses
- Restart stack after updating token

## Model Name Mismatch

- Request body `model` must be alias:
  - `qwen-main`, `coder`, `deepseek`, `bge-large`
- Use `GET /v1/models` to confirm available aliases

## Slow Startup

- First launch downloads large model weights
- Ensure `./hf_cache` is persistent and on fast storage
- Watch logs:
  - `docker compose -f docker-compose.cuda.yml logs -f qwen-main-vllm`

## Container Restart Loop

- Inspect service logs for OOM, auth, or startup command errors
- Validate env variable values in `.env`
- Check GPU visibility from host and container runtime

## 404 Route Errors

- Use `http://localhost:8101/v1/...` path prefix
- Verify endpoint spelling:
  - `/v1/chat/completions`
  - `/v1/completions`
  - `/v1/embeddings`
  - `/v1/models`

## Streaming Errors

- Check client supports SSE stream parsing
- Increase `GATEWAY_TIMEOUT_SECONDS` for long generations
- Validate upstream model health and gateway logs
