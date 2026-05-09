# API Usage

Base URL:

- `http://localhost:8101/v1`

## Curl Chat Example

```bash
curl -s http://localhost:8101/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-main",
    "messages": [{"role": "user", "content": "Say hello from CogniCore."}],
    "temperature": 0.2
  }'
```

## Curl Streaming Example

```bash
curl -N http://localhost:8101/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "coder",
    "messages": [{"role": "user", "content": "Write a Python hello world function."}],
    "stream": true
  }'
```

## Python OpenAI SDK Example

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8101/v1", api_key="test-key")
response = client.chat.completions.create(
    model="deepseek",
    messages=[{"role": "user", "content": "Summarize CogniCore routing in one line."}],
)
print(response.choices[0].message.content)
```

## Embeddings Example

```bash
curl -s http://localhost:8101/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bge-large",
    "input": ["CogniCore embedding smoke test"]
  }'
```

## CogniOPS Integration Example

- Configure CogniOPS LLM connector:
  - Base URL: `http://<cognicore-host>:8101/v1`
  - Model alias: `qwen-main` (or `deepseek` for complex tasks)
- Use streaming for interactive operator workflows.
- Keep retries enabled for transient network failures.

## CogniScribe Integration Example

- Configure CogniScribe:
  - Base URL: `http://<cognicore-host>:8101/v1`
  - Generation model: `coder` or `qwen-main`
  - Embeddings model: `bge-large`
- Route search/indexing to embeddings endpoint only.
