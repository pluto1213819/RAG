import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val if val else default


def main():
    print("=== 一键生成 .env ===")
    db = ask("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/rag")
    redis_url = ask("REDIS_URL", "redis://localhost:6379/0")
    jwt_secret = ask("JWT_SECRET", "change-me")
    ds_key = ask("DEEPSEEK_API_KEY", "")
    ds_base = ask("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    ds_model = ask("DEEPSEEK_MODEL", "deepseek-chat")
    chroma_dir = ask("CHROMA_DIR", "chroma_data")

    content = f"""DATABASE_URL={db}
REDIS_URL={redis_url}
JWT_SECRET={jwt_secret}

DEEPSEEK_API_KEY={ds_key}
DEEPSEEK_BASE_URL={ds_base}
DEEPSEEK_MODEL={ds_model}

CHROMA_DIR={chroma_dir}
"""
    if ENV_PATH.exists():
        overwrite = input(".env 已存在，是否覆盖？(y/N): ").strip().lower()
        if overwrite != "y":
            print("已取消，不覆盖 .env")
            return

    ENV_PATH.write_text(content, encoding="utf-8")
    print(f"已生成: {ENV_PATH}")


if __name__ == "__main__":
    main()
