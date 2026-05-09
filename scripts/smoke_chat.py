#!/usr/bin/env python3
import os
from typing import Iterable

from openai import OpenAI


def stream_and_print(client: OpenAI, base_url: str, model: str) -> None:
    print(f"\n=== Streaming chat test for {model} ===")
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with exactly: CogniCore online"}],
        temperature=0,
        stream=True,
    )
    chunks: Iterable = stream
    for chunk in chunks:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            print(delta, end="", flush=True)
    print("\n[stream complete]")


def non_stream_test(client: OpenAI, model: str) -> None:
    print(f"\n=== Non-streaming chat test for {model} ===")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say hello from CogniCore."}],
        temperature=0,
    )
    print(response.choices[0].message.content)


def main() -> None:
    base_url = os.getenv("BASE_URL", os.getenv("OPENAI_BASE_URL", "http://localhost:8101/v1"))
    api_key = os.getenv("API_KEY", os.getenv("OPENAI_API_KEY", "test-key"))
    client = OpenAI(base_url=base_url, api_key=api_key)

    for model in ("qwen-main", "coder", "deepseek"):
        non_stream_test(client, model)
        stream_and_print(client, base_url, model)


if __name__ == "__main__":
    main()
