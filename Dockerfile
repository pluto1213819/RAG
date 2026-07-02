FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///rag.db
ENV CHROMA_DIR=/app/chroma_data
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV EMBED_MODEL=bge-m3
ENV LLM_MODEL=qwen2.5:7b

EXPOSE 8000

CMD ["python", "run_server.py"]
