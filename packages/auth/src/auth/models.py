from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: str
    password: str
    name: str | None = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: UUID
    email: str
    name: str | None = None
    role: str = "member"
    ai_enabled: bool = False
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyRead(BaseModel):
    id: UUID
    name: str
    last4: str
    created_at: str
    revoked_at: str | None = None
    last_used_at: str | None = None


class UserUpdate(BaseModel):
    ai_enabled: bool | None = None
    role: str | None = None
