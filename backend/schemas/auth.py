"""Pydantic schemas for authentication and user access control (Phase 10)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend.auth.rbac import UserRole


class LoginRequest(BaseModel):
    """User credentials for authentication."""

    username: str = Field(description="Username or email address")
    password: str = Field(description="Account password")


class TokenResponse(BaseModel):
    """JWT bearer token envelope."""

    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    role: UserRole
    username: str


class UserProfileResponse(BaseModel):
    """Authenticated user profile metadata."""

    username: str
    email: str
    role: UserRole
    full_name: Optional[str] = None
    is_active: bool = True
