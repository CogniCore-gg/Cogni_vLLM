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

## No HIP GPUs / gateway 502 upstream

- vLLM logs `RuntimeError: No HIP GPUs are available` when `HIP_VISIBLE_DEVICES` (set per backend as `QWEN_MAIN_HIP_VISIBLE_DEVICES`, etc.) references **indices that do not exist** on the host (e.g. `0,1,2,3` when only GPU 0 exists).
- Fix: set each backend’s variable to a valid index (`rocm-smi -L`). Single-GPU hosts should use `0` for **qwen-main** at minimum.
- Default `docker-compose.yml` starts **only qwen-main**; optional backends need `--profile full-stack`.
- After switching profiles, run `docker compose down --remove-orphans` so old vLLM containers stop fighting for the GPU.
- If `rocminfo` inside the container reports **`HSA_STATUS_ERROR_OUT_OF_RESOURCES`**, first check you did **not** set **`HSA_OVERRIDE_GFX_VERSION=`** (empty) in `.env`. An empty override breaks HSA initialization; remove the variable entirely unless you set a real value (see `.env.example`). If the variable is unset and the error persists, the host ROCm runtime may be exhausted (too many GPU processes, driver glitch): stop other GPU workloads / containers, then retry; reboot the host if it persists.
- Gateway **502** / `ConnectError` to `qwen-main-vllm:8000` means the vLLM process is **not listening** (usually crash-loop). Check `docker logs cognicore-vllm-qwen-main-vllm-1`. `compose.yml` sets **`privileged: true`** on qwen-main as a common ROCm workaround; remove only if your security policy forbids it.

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
