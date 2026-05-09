# Deployment on ROCm

## Requirements

- Linux host with AMD GPU(s) and ROCm-compatible drivers
- Docker Engine 24+
- Access to `/dev/kfd` and `/dev/dri`
- User in `video` and `render` groups

## MI300X Notes

MI300X with 192GB HBM is a strong platform for large context windows and multi-model co-location.  
Use conservative `GPU_MEMORY_UTILIZATION` initially, then tune upward.
Even with MI300X, do not assume all giant models can run concurrently at high context lengths without careful TP and memory planning.

## Start Steps

1. `cp .env.example .env`
2. set `HF_TOKEN` and ROCm-specific env vars
3. optionally set `HIP_VISIBLE_DEVICES` and `HSA_OVERRIDE_GFX_VERSION`
4. `./scripts/start.sh` or `./scripts/start_rocm.sh` or `docker compose --env-file .env up -d --build`
5. `./scripts/healthcheck.sh`

## Docker Permission Considerations

- Ensure device mappings:
  - `/dev/kfd:/dev/kfd`
  - `/dev/dri:/dev/dri`
- Ensure groups:
  - `video`
  - `render`
- `ipc: host` and larger shared memory can reduce runtime issues for heavy models.

## ROCm Visibility Debugging

- `ls -l /dev/kfd /dev/dri`
- `docker compose logs -f deepseek-vllm` (from repo root; uses `docker-compose.yml`)
- Check health endpoint:
  - `curl http://localhost:8101/health`
