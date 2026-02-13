"""
DEPRECATED: Authentication Module for YuKyuDATA

⚠️  WARNING: This module is deprecated and will be removed in v2.0.
    Use services.auth_service.AuthService instead.

This file is kept for backwards compatibility only.
New code should import from services.auth_service.
"""

import warnings
warnings.warn(
    "services.auth is deprecated, use services.auth_service.AuthService instead",
    DeprecationWarning,
    stacklevel=2
)

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import os
import logging
from config.security import settings

# Try to import bcrypt for production, fall back to PBKDF2 if not available
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


# ============================================
# MODELS
# ============================================

class UserLogin(BaseModel):
    """Login request model"""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=255)


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class CurrentUser(BaseModel):
    """Current authenticated user"""
    username: str
    role: str
    name: str
    exp: float


# ============================================
# PASSWORD HASHING UTILITIES
# ============================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt (preferred) or PBKDF2 (fallback).

    Args:
        password: Plain text password

    Returns:
        Hashed password string with algorithm prefix
    """
    if BCRYPT_AVAILABLE:
        # Use bcrypt with work factor 12
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return f"bcrypt:{hashed.decode('utf-8')}"
    else:
        # Fallback to PBKDF2-SHA256 with 600,000 iterations (OWASP recommendation)
        salt = secrets.token_hex(16)
        iterations = 600000
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        ).hex()
        return f"pbkdf2:{salt}:{iterations}:{hashed}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        password: Plain text password to verify
        hashed_password: Stored hash (with algorithm prefix)

    Returns:
        True if password matches, False otherwise
    """
    # Handle legacy plain text passwords (migration support)
    if not hashed_password.startswith(('bcrypt:', 'pbkdf2:')):
        # Plain text comparison for legacy accounts - log warning
        logger.warning("Legacy plain-text password detected - migration recommended")
        return secrets.compare_digest(password, hashed_password)

    if hashed_password.startswith('bcrypt:'):
        if not BCRYPT_AVAILABLE:
            logger.error("bcrypt hash found but bcrypt not installed")
            return False
        stored_hash = hashed_password[7:].encode('utf-8')  # Remove 'bcrypt:' prefix
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

    elif hashed_password.startswith('pbkdf2:'):
        parts = hashed_password.split(':')
        if len(parts) != 4:
            logger.error("Invalid PBKDF2 hash format")
            return False
        _, salt, iterations, stored_hash = parts
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            int(iterations)
        ).hex()
        return secrets.compare_digest(computed_hash, stored_hash)

    return False


# ============================================
# USER STORE (Load from environment in production)
# ============================================

def _load_users_from_env() -> Dict[str, Dict[str, Any]]:
    """
    Load users from environment variables.
    Format: USERS_JSON='{"username": {"password": "hash", "role": "admin", "name": "Full Name"}}'

    In production, use a database or secrets manager!
    """
    import json

    users_json = os.getenv("USERS_JSON")
    if users_json:
        try:
            return json.loads(users_json)
        except json.JSONDecodeError:
            logger.error("Failed to parse USERS_JSON from environment")

    # Default: Only allow if explicitly configured
    if settings.debug:
        # Development fallback (INSECURE - never in production!)
        logger.warning("Using development user store. Configure USERS_JSON in production!")
        return {
            "demo": {
                "password": "demo123456",  # Min 8 chars
                "role": "user",
                "name": "Demo User"
            },
            "admin": {
                "password": "admin123456",  # Min 8 chars - DEV ONLY!
                "role": "admin",
                "name": "Admin (Dev)"
            }
        }

    return {}


USERS_DB = _load_users_from_env()


# ============================================
# JWT TOKEN MANAGEMENT
# ============================================

def create_access_token(
    username: str,
    role: str,
    name: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        username: Username
        role: User role (admin, user, etc.)
        name: Full name
        expires_delta: Custom expiration time

    Returns:
        JWT token string
    """
    if not expires_delta:
        # Prefer minute-based expiry (aligned con configuración actual y guías de seguridad)
        expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": username,
        "role": role,
        "name": name,
        "iat": now.timestamp(),
        "exp": expire.timestamp(),
        "token_type": "access"
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    logger.info(f"Access token created for user: {username}, role: {role}")

    return token


def verify_token(token: str) -> Optional[CurrentUser]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        CurrentUser object if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        # Check expiration
        exp = payload.get("exp")
        if exp and exp < datetime.now(timezone.utc).timestamp():
            logger.warning(f"Token expired for user: {payload.get('sub')}")
            return None

        return CurrentUser(
            username=payload.get("sub"),
            role=payload.get("role", "user"),
            name=payload.get("name", "Unknown"),
            exp=exp
        )

    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None


# ============================================
# AUTHENTICATION DEPENDENCIES
# ============================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> CurrentUser:
    """
    Dependency to get the current authenticated user.
    Raises 401 if not authenticated.

    Usage:
        @app.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_user)):
            return {"user": user.username}
    """
    if not credentials:
        logger.warning("Missing credentials")
        raise HTTPException(
            status_code=401,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = verify_token(credentials.credentials)
    if not user:
        logger.warning(f"Invalid token attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_admin_user(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Dependency to ensure the user has admin role.
    Raises 403 if not admin.

    Usage:
        @app.delete("/admin/users")
        async def admin_route(user: CurrentUser = Depends(get_admin_user)):
            return {"message": "Admin action completed"}
    """
    if user.role != "admin":
        logger.warning(f"Unauthorized admin access attempt by: {user.username}")
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    return user


# ============================================
# LOGIN HANDLER
# ============================================

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with username and password.

    Args:
        username: Username
        password: Password (plain text input, verified against hash)

    Returns:
        User object if valid, None otherwise
    """
    user = USERS_DB.get(username)

    if not user:
        logger.warning(f"Login attempt with non-existent username: {username}")
        return None

    stored_password = user.get("password", "")

    # Use secure password verification (supports bcrypt, PBKDF2, and legacy plain text)
    if not verify_password(password, stored_password):
        logger.warning(f"Login attempt with wrong password for user: {username}")
        return None

    logger.info(f"User authenticated: {username}")
    return user


# ============================================
# RATE LIMIT DEPENDENCY
# ============================================

async def check_rate_limit(request: Request) -> None:
    """
    Dependency to check rate limiting.

    Usage:
        @app.post("/login", dependencies=[Depends(check_rate_limit)])
        async def login(credentials: UserLogin):
            ...
    """
    from main import rate_limiter  # Import here to avoid circular imports

    client_ip = request.client.host

    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(settings.rate_limit_window_seconds)}
        )


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: Authorization header value (e.g., "Bearer token_value")

    Returns:
        Token string or None
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def log_auth_event(event: str, username: str, ip: str, success: bool):
    """
    Log authentication events for auditing.

    Args:
        event: Event type (login, logout, access_denied, etc.)
        username: Username (or "unknown" if not authenticated)
        ip: Client IP address
        success: Whether the event was successful
    """
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"AUTH_EVENT [{status}] event={event} user={username} ip={ip}")
