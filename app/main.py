from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.db import Base, engine
from app.api.documents import router as docs_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG Agent Platform", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(docs_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def admin_page():
    return Path("templates/admin.html").read_text(encoding="utf-8")
