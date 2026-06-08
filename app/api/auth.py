from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Tenant, User
from app.schemas.auth import TenantCreate, TenantRead, UserCreate, UserRead, LoginRequest, TokenResponse
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/tenants", response_model=TenantRead)
def create_tenant(body: TenantCreate, db: Session = Depends(get_db)):
    t = Tenant(name=body.name)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.post("/users", response_model=UserRead)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).first()
    if not tenant:
        raise HTTPException(400, "Create tenant first")
    u = User(tenant_id=tenant.id, email=body.email, hashed_password=hash_password(body.password), role=body.role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == body.email).first()
    if not u or not verify_password(body.password, u.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return TokenResponse(access_token=create_access_token(u))


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user
