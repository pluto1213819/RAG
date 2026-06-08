import os
from openai import OpenAI


def get_llm_client() -> OpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return OpenAI(api_key=api_key, base_url=base_url)


def get_llm_model() -> str:
    return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
