#!/usr/bin/env python3
import os

from openai import OpenAI


def main() -> None:
    base_url = os.getenv("BASE_URL", os.getenv("OPENAI_BASE_URL", "http://localhost:8101/v1"))
    api_key = os.getenv("API_KEY", os.getenv("OPENAI_API_KEY", "test-key"))
    client = OpenAI(base_url=base_url, api_key=api_key)

    response = client.embeddings.create(
        model="bge-large",
        input=["CogniCore powers CogniOPS and CogniScribe."],
    )
    vector = response.data[0].embedding
    print(f"Embedding dimension: {len(vector)}")
    print(f"First 8 values: {vector[:8]}")


if __name__ == "__main__":
    main()
