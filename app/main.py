from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.db import Base, engine
from app.api.auth import router as auth_router
from app.api.documents import router as docs_router
from app.api.admin import router as admin_router
from app.api.evaluations import router as eval_router
from app.services.rate_limit import RedisRateLimitMiddleware
from app.services.logger import AuditLogMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Production RAG Platform", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RedisRateLimitMiddleware, max_requests=120, window_seconds=60)
app.add_middleware(AuditLogMiddleware)

app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(admin_router)
app.include_router(eval_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return Path("templates/admin.html").read_text(encoding="utf-8")
