from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .repository import AuthRepository
from .security import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)

_auth_repo: AuthRepository | None = None


def _get_auth_repo() -> AuthRepository:
    global _auth_repo
    if _auth_repo is None:
        _auth_repo = AuthRepository()
    return _auth_repo


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    repo = _get_auth_repo()

    api_key = request.headers.get("x-api-key")
    if api_key:
        user = repo.get_user_by_api_key(api_key)
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            user_id = UUID(payload["sub"])
            user = repo.get_user_by_id(user_id)
            if user:
                return user
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide a valid Bearer token or x-api-key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_ai_access(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") == "admin":
        return current_user
    if not current_user.get("ai_enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI access has not been enabled for your account. Contact an administrator.",
        )
    return current_user
