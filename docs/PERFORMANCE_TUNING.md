# Performance Tuning

## Concurrent Request Tuning

- vLLM scheduler handles dynamic batching; concurrency increases throughput.
- Watch p95 latency under realistic request mixes.
- Increase client concurrency gradually while tracking token throughput.

## Max Model Length

- Higher `*_MAX_MODEL_LEN` increases KV cache memory usage.
- Set only as high as your workload needs.
- Lowering max length often prevents OOM and improves stability.

## GPU Memory Utilization

- `*_GPU_MEMORY_UTILIZATION` controls memory reservation pressure.
- Start around `0.85-0.90` for LLMs, lower for embeddings.
- If OOM/restarts happen, reduce utilization and/or max length.

## Batching Behavior

- Throughput improves with more concurrent short requests.
- Extremely long prompts can dominate scheduler time.
- Separate long-running jobs from latency-sensitive traffic where possible.

## Streaming Tradeoffs

- Streaming improves time-to-first-token.
- Full non-streaming may improve aggregate throughput in some workloads.
- Use streaming for user-facing chat UX, non-streaming for backend batch jobs.

## Throughput vs Latency

- More batching usually improves throughput and can increase latency variance.
- Keep separate SLO targets per product path (CogniOPS vs CogniScribe workflows).
- Scale horizontally by adding more model replicas when needed.

## Embedding Optimization

- Keep `bge-large` isolated from heavy long-context chat spikes when possible.
- Use batched embedding inputs for throughput.
- Monitor embedding request queue depth and latency separately.
