#!/usr/bin/env python3
import os

import requests


def main() -> None:
    base_url = os.getenv("BASE_URL", os.getenv("OPENAI_BASE_URL", "http://localhost:8101/v1"))
    api_key = os.getenv("API_KEY", os.getenv("OPENAI_API_KEY", ""))
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    response = requests.get(f"{base_url}/models", headers=headers, timeout=15)
    response.raise_for_status()
    payload = response.json()
    for model in payload.get("data", []):
        print(f"{model['id']} -> {model.get('root')}")


if __name__ == "__main__":
    main()
