from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from src.apps.users.api_errors import ApiErrorCode
from src.apps.users.auth import decode_token, ensure_auth_configured
from src.apps.users.models import User, UserStatus
from src.utils.api_errors import raise_api_error
from src.utils.deps import get_db_session

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session | None = Depends(get_db_session),
) -> User:
    if session is None:
        raise_api_error(
            ApiErrorCode.database_not_configured,
            "database not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    ensure_auth_configured()
    if creds is None or creds.scheme.lower() != "bearer":
        raise_api_error(
            ApiErrorCode.not_authenticated,
            "Not authenticated",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise_api_error(
            ApiErrorCode.invalid_or_expired_token,
            "Invalid or expired token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError):
        raise_api_error(
            ApiErrorCode.invalid_token,
            "Invalid token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user = session.get(User, user_id)
    if user is None:
        raise_api_error(
            ApiErrorCode.user_not_found,
            "User not found",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if user.status != UserStatus.active:
        raise_api_error(
            ApiErrorCode.account_not_active,
            "Account is not active",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return user
