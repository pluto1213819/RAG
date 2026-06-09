FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///rag.db
ENV CHROMA_DIR=/app/chroma_data

EXPOSE 8000

CMD ["python", "run_server.py"]
