"""Cryptographic security, password hashing, and JWT token management (Phase 10)."""

from datetime import datetime, timedelta
import hashlib
import hmac
import logging
import os
from typing import Any, Dict, Optional
import bcrypt
import jwt

from backend.config.settings import settings

logger = logging.getLogger("payroll_guardian.auth.security")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored hashed password string."""
    if not plain_password or not hashed_password:
        return False
    try:
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        elif hashed_password.startswith("pbkdf2:"):
            # PBKDF2 format: pbkdf2:salt:hex_hash
            parts = hashed_password.split(":")
            if len(parts) == 3:
                salt = bytes.fromhex(parts[1])
                target_hash = parts[2]
                computed = hashlib.pbkdf2_hmac(
                    "sha256", plain_password.encode("utf-8"), salt, 100_000
                ).hex()
                return hmac.compare_digest(computed, target_hash)
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False
    return False


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token with payload and expiration."""
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
    })

    secret = settings.secret_key
    algorithm = settings.jwt_algorithm
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate signature and expiration of a JWT access token."""
    try:
        secret = settings.secret_key
        algorithm = settings.jwt_algorithm
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token has expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid JWT token: {e}")
        return None
