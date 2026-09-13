from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.exceptions.handlers import (
    AccountAccessForbiddenException,
    AuthenticationException,
    InvalidCredentialsException,
    PermissionDeniedException,
)

ALGORITHM = "HS256"

# What each role is allowed to *do*, regardless of which account it's done on.
# LITE_CUSTOMER is read-only - it can look up a balance but never move money.
ROLE_PERMISSIONS = {
    "LITE_CUSTOMER": {"account:read"},
    "STD_CUSTOMER": {"account:read", "transfer:create"},
    "ADMIN": {"account:read", "transfer:create"},
}

# Roles that skip the "is this your own account?" ownership check below -
# an admin/support role legitimately needs to act on other people's accounts.
ADMIN_ROLES = {"ADMIN"}

# Hardcoded "user directory" - stands in for a real user store (DB, IdP, ...).
# Only used to look up who a username belongs to at login time; every request
# after that is authenticated off the signed JWT itself, not this dict.
USERS = {
    "asha": {"user_id": "u-asha", "account_id": "acc-1001", "role": "LITE_CUSTOMER"},
    "ravi": {"user_id": "u-ravi", "account_id": "acc-1002", "role": "STD_CUSTOMER"},
    "admin": {"user_id": "u-admin", "account_id": None, "role": "ADMIN"},
}

bearer_scheme = HTTPBearer(auto_error=False)


def authenticate_user(username: str) -> dict:
    user = USERS.get(username)
    if user is None:
        raise InvalidCredentialsException()
    return user


def create_access_token(user: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.AUTH_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user["user_id"],
        "account_id": user["account_id"],
        "role": user["role"],
        "exp": expire,
    }
    return jwt.encode(payload, settings.AUTH_TOKEN_SECRET, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> dict:
    if credentials is None:
        raise AuthenticationException()
    try:
        payload = jwt.decode(credentials.credentials, settings.AUTH_TOKEN_SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise AuthenticationException()
    return {
        "user_id": payload["sub"],
        "account_id": payload["account_id"],
        "role": payload["role"],
    }


def require_permission(permission: str):
    """Dependency factory: only lets the request through if the caller's role has `permission`."""

    def checker(user: dict = Depends(get_current_user)) -> dict:
        if permission not in ROLE_PERMISSIONS.get(user["role"], set()):
            raise PermissionDeniedException(user["role"], permission)
        return user

    return checker


def ensure_account_access(user: dict, account_id: str) -> None:
    """Restrict a customer role to its own account_id; admin roles bypass this."""

    if user["role"] in ADMIN_ROLES:
        return
    if user["account_id"] != account_id:
        raise AccountAccessForbiddenException(account_id)
