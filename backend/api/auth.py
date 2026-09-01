"""Authentication and session management API endpoints (Phase 10)."""

from datetime import timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.auth.rbac import AuthenticatedUser, UserRole, get_current_user
from backend.auth.security import create_access_token, verify_password
from backend.config.settings import settings
from backend.database.repository import DatabaseAuditRepository, DatabaseUserRepository
from backend.schemas.auth import LoginRequest, TokenResponse, UserProfileResponse

logger = logging.getLogger("payroll_guardian.api.auth")

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, request: Request):
    """Authenticate user with username/password and issue a signed JWT access token."""
    req_id = getattr(request.state, "request_id", None) if hasattr(request, "state") else None
    audit_repo = DatabaseAuditRepository()
    user_repo = DatabaseUserRepository()

    user = user_repo.get_by_username(payload.username)
    if not user:
        # Check email fallback
        user = user_repo.get_by_email(payload.username)

    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username='{payload.username}'")
        audit_repo.log_event(
            event_type="USER_LOGIN_FAILED",
            actor_id=payload.username[:64] if payload.username else "anonymous",
            metadata={"reason": "Invalid credentials", "status": "REJECTED"},
            request_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        audit_repo.log_event(
            event_type="USER_LOGIN_FAILED",
            actor_id=user.username,
            metadata={"reason": "Inactive account", "status": "FORBIDDEN"},
            request_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact your system administrator.",
        )

    try:
        user_role = UserRole(user.role)
    except ValueError:
        user_role = UserRole.VIEWER

    token_data = {
        "sub": user.username,
        "email": user.email,
        "role": user_role.value,
        "full_name": user.full_name,
        "is_active": user.is_active,
    }

    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(token_data, expires_delta=expires_delta)

    # Log successful login to audit trail
    audit_repo.log_event(
        event_type="USER_LOGIN_SUCCESS",
        actor_id=user.username,
        metadata={"role": user_role.value},
        request_id=req_id,
    )

    logger.info(f"User '{user.username}' successfully authenticated with role '{user_role.value}'.")
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=settings.access_token_expire_minutes * 60,
        role=user_role,
        username=user.username,
    )


@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieve profile and role information of currently authenticated user."""
    return UserProfileResponse(
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh_access_token(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Issue a refreshed access token for the active session."""
    token_data = {
        "sub": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
    }
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(token_data, expires_delta=expires_delta)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=settings.access_token_expire_minutes * 60,
        role=current_user.role,
        username=current_user.username,
    )
