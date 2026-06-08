import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.db import SessionLocal
from app.models import AuditLog
from app.auth import get_current_user


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        try:
            if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "DELETE"}:
                db = SessionLocal()
                try:
                    user = None
                    auth = request.headers.get("authorization", "")
                    if auth.startswith("Bearer "):
                        try:
                            user = get_current_user.__wrapped__(auth.split(" ")[1], db)
                        except Exception:
                            user = None
                    db.add(AuditLog(
                        tenant_id=getattr(user, "tenant_id", 0),
                        user_id=getattr(user, "id", 0),
                        action=f"{request.method} {request.url.path}",
                        payload={
                            "status_code": response.status_code,
                            "duration_ms": int((time.time() - start) * 1000),
                        },
                    ))
                    db.commit()
                finally:
                    db.close()
        except Exception:
            pass
        return response
