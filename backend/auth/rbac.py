"""Role-Based Access Control (RBAC) permissions matrix and route dependencies (Phase 10)."""

from enum import Enum
import logging
import os
from typing import Callable, List, Optional
from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from backend.auth.security import decode_access_token
from backend.config.settings import settings

logger = logging.getLogger("payroll_guardian.auth.rbac")


class UserRole(str, Enum):
    """Supported user roles in AI Payroll Guardian."""

    ADMIN = "ADMIN"
    PAYROLL_ADMIN = "PAYROLL_ADMIN"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"


# Permissions hierarchy
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "payroll:upload",
        "payroll:analyze",
        "payroll:view",
        "anomalies:view",
        "anomalies:resolve",
        "compliance:view",
        "assistant:query",
        "monitoring:view",
        "audit:view",
        "users:manage",
    },
    UserRole.PAYROLL_ADMIN: {
        "payroll:upload",
        "payroll:analyze",
        "payroll:view",
        "anomalies:view",
        "anomalies:resolve",
        "compliance:view",
        "assistant:query",
        "monitoring:view",
        "audit:view",
    },
    UserRole.AUDITOR: {
        "payroll:view",
        "anomalies:view",
        "anomalies:resolve",
        "compliance:view",
        "assistant:query",
        "monitoring:view",
        "audit:view",
    },
    UserRole.VIEWER: {
        "payroll:view",
        "anomalies:view",
        "compliance:view",
        "audit:view",
    },
}


class AuthenticatedUser(BaseModel):
    """Payload representing an authenticated caller."""

    username: str
    email: str
    role: UserRole
    full_name: Optional[str] = None
    is_active: bool = True


DEFAULT_DEV_USER = AuthenticatedUser(
    username="payroll_admin_dev",
    email="payroll_admin@payrollguardian.internal",
    role=UserRole.PAYROLL_ADMIN,
    full_name="Payroll Admin (Dev)",
    is_active=True,
)


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
) -> Optional[AuthenticatedUser]:
    """Extract and validate user if Authorization header is provided, or return None."""
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header scheme. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:].strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, corrupted, or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    email = payload.get("email", f"{username}@payrollguardian.internal")
    role_str = payload.get("role", "VIEWER").upper()

    try:
        role = UserRole(role_str)
    except ValueError:
        role = UserRole.VIEWER

    return AuthenticatedUser(
        username=username,
        email=email,
        role=role,
        full_name=payload.get("full_name"),
        is_active=payload.get("is_active", True),
    )


def get_current_user(
    authorization: Optional[str] = Header(None),
) -> AuthenticatedUser:
    """Strictly authenticate caller via JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_flexible(
    authorization: Optional[str] = Header(None),
) -> AuthenticatedUser:
    """Validate token when present; fallback to dev user when unauthenticated in non-strict mode."""
    # If strict auth is requested via env or production
    strict_auth = os.getenv("AUTH_STRICT", "false").lower() in ("true", "1") or settings.app_env == "production"

    if authorization:
        return get_current_user(authorization)
    elif strict_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        return DEFAULT_DEV_USER


def require_roles(*allowed_roles: UserRole) -> Callable:
    """FastAPI route dependency factory ensuring the authenticated user possesses an authorized role."""

    def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user_flexible),
    ) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Forbidden access: User '{current_user.username}' with role '{current_user.role}' "
                f"attempted to access endpoint requiring {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {[r.value for r in allowed_roles]}, "
                f"current role: {current_user.role.value}.",
            )
        return current_user

    return role_checker
