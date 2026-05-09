# Deployment on CUDA

## Requirements

- Linux host with NVIDIA GPU(s)
- NVIDIA driver compatible with your CUDA stack
- Docker Engine 24+
- NVIDIA Container Toolkit configured (`nvidia-container-runtime`)

## Validate Host GPU

Run:

- `nvidia-smi`
- `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi`

If the second command fails, fix NVIDIA container runtime before deploying.

## Start Steps

1. `cp .env.example .env`
2. set `HF_TOKEN` and model tuning variables
3. optionally set `CUDA_VISIBLE_DEVICES`
4. `./scripts/start_cuda.sh`
5. `./scripts/healthcheck.sh`

## GPU Visibility Debugging

- Check Docker runtime:
  - `docker info | rg -i nvidia`
- Check container logs:
  - `docker compose -f docker-compose.cuda.yml logs -f qwen-main-vllm`
- Verify gateway:
  - `curl http://localhost:8101/health`

## Hardware Recommendations

- H100 80GB: strong throughput and long-context performance
- A100 80GB: excellent stable production baseline
- RTX 4090 24GB: development/testing or smaller quantized setups; not suitable for running all large listed models together

For very large models, use tensor parallelism and spread across multiple GPUs.
DeepSeek-V3.2 usually needs dedicated multi-GPU planning in production.
