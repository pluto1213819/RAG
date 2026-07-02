"""本地 LLM 服务：通过 Ollama 调用 qwen2.5:7b"""
import os
import requests
import json


def get_ollama_url() -> str:
    return os.getenv("OLLAMA_URL", "http://localhost:11434")


def get_llm_model() -> str:
    return os.getenv("LLM_MODEL", "qwen2.5:7b")


def generate(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.3,
    max_tokens: int = 1000,
) -> str:
    """调用本地 qwen2.5:7b 生成回答"""
    url = f"{get_ollama_url()}/api/generate"
    payload = {
        "model": get_llm_model(),
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["response"]
