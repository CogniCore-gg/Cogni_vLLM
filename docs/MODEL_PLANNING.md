# Model Planning

## VRAM Estimates (Rule of Thumb)

Exact VRAM depends on dtype, KV cache, batch, and context length. Start conservative:

- `Qwen/Qwen3.6-35B-A3B`: multi-GPU strongly recommended
- `Qwen/Qwen3-Coder-Next`: high VRAM, often multi-GPU for production contexts
- `deepseek-ai/DeepSeek-V3.2`: very high VRAM, often dedicated node/GPU set
- `BAAI/bge-large-en-v1.5`: relatively lightweight

Do not plan as if all models will fit simultaneously on one consumer GPU.

## Tensor Parallel Suggestions

- Start `*_TP=1` for functional bring-up.
- Increase TP for larger models when single GPU memory is insufficient.
- Keep TP aligned with available GPU count and interconnect quality.

## Quantization Considerations

- Quantization reduces memory and may increase throughput.
- Accuracy trade-offs vary by task and model.
- Validate critical CogniOPS/CogniScribe prompts before production rollout.

## MI300X 192GB Strategy

- Co-locate one heavy LLM + embeddings on a single node when practical.
- Reserve headroom for KV cache growth and burst traffic.
- Prefer dedicated DeepSeek instance when sustained long-context load is expected.
- DeepSeek-V3.2 viability on a single MI300X depends on checkpoint precision and target context.

## Running DeepSeek Alone

Use a dedicated DeepSeek deployment when:

- latency SLOs are strict
- context windows are long
- concurrent enterprise load is high
- GPU memory pressure causes restart/OOM events

DeepSeek-V3.2 often requires multi-GPU tensor parallelism or specialized hardware, depending on actual checkpoint size and context profile.

## Splitting Models Across GPUs

- Place `deepseek` on dedicated GPUs first.
- Place `qwen-main` and `coder` on separate pools when both are heavily used.
- Keep `bge-large` colocated with a less loaded LLM service if capacity allows.
