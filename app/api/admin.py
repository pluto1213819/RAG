from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog, User
from app.auth import require_role

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/audit-logs", response_model=List[dict])
def list_logs(user: User = Depends(require_role("owner")), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()
    return [{"id": r.id, "tenant_id": r.tenant_id, "user_id": r.user_id, "action": r.action, "payload": r.payload, "created_at": str(r.created_at)} for r in rows]


@router.post("/eval/run")
def run_eval(user: User = Depends(require_role("owner"))):
    return {"status": "queued", "message": "触发评测流水线（可接 RAGAS job worker）"}
