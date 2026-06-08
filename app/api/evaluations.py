from fastapi import APIRouter, Depends
from app.models import User
from app.auth import require_role

router = APIRouter(prefix="/api/eval", tags=["eval"])


@router.post("/run")
def run_eval(user: User = Depends(require_role("owner"))):
    return {
        "status": "ok",
        "message": "评测任务已触发（可对接 RAGAS worker）",
        "artifacts": ["faithfulness", "answer_relevancy"]
    }
