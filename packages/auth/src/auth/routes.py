from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from .dependencies import get_current_user
from .models import ApiKeyCreate, ApiKeyRead, TokenResponse, UserCreate, UserLogin, UserRead
from .repository import AuthRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])

_auth_repo: AuthRepository | None = None


def _get_repo() -> AuthRepository:
    global _auth_repo
    if _auth_repo is None:
        _auth_repo = AuthRepository()
    return _auth_repo


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: UserCreate):
    repo = _get_repo()
    try:
        result = repo.create_user(data.email, data.password, data.name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    return TokenResponse(
        access_token=result["access_token"],
        user=UserRead(**result["user"]),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    repo = _get_repo()
    try:
        result = repo.authenticate_user(data.email, data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e

    return TokenResponse(
        access_token=result["access_token"],
        user=UserRead(**result["user"]),
    )


@router.get("/me", response_model=UserRead)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserRead(**current_user)


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: ApiKeyCreate,
    current_user: dict = Depends(get_current_user),
):
    repo = _get_repo()
    result = repo.create_api_key(current_user["id"], data.name)
    return {
        "id": result["id"],
        "name": result["name"],
        "key": result["key"],
        "last4": result["last4"],
        "created_at": result["created_at"],
        "message": "Save this key now. You won't be able to see it again.",
    }


@router.get("/api-keys", response_model=list[ApiKeyRead])
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    repo = _get_repo()
    keys = repo.list_api_keys(current_user["id"])
    return [ApiKeyRead(**k) for k in keys]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    key_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    repo = _get_repo()
    revoked = repo.revoke_api_key(key_id, current_user["id"])
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or already revoked",
        )
    return {"message": "API key revoked successfully"}
