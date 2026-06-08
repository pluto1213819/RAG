from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str


class TenantRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "member"


class UserRead(BaseModel):
    id: int
    tenant_id: int
    email: str
    role: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str
