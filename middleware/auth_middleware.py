"""
Authentication Middleware
Handles JWT token verification and user authentication
"""

import os
from typing import Optional
from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from exceptions.custom_exceptions import AuthenticationException, AuthorizationException


# Configuration from environment variables
def _get_secret_key():
    """Get JWT secret key from environment, raising error in production if not set."""
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        is_debug = os.getenv("DEBUG", "false").lower() == "true"
        if is_debug:
            import warnings
            import secrets
            warnings.warn(
                "JWT_SECRET_KEY not configured. Using temporary key for development only.",
                RuntimeWarning
            )
            return secrets.token_urlsafe(32)
        raise ValueError(
            "JWT_SECRET_KEY environment variable is required in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    return secret

SECRET_KEY = _get_secret_key()
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
# Default 15 minutes (0.25 hours) for production security
ACCESS_TOKEN_EXPIRE_HOURS = float(os.getenv("JWT_EXPIRATION_HOURS", "0.25"))

# HTTPBearer scheme for JWT tokens
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data"""
    username: str
    user_id: str
    role: str
    exp: datetime


class CurrentUser(BaseModel):
    """Current authenticated user"""
    user_id: str
    username: str
    role: str
    is_admin: bool


def create_access_token(user_id: str, username: str, role: str) -> str:
    """
    Create a new JWT access token
    
    Args:
        user_id: User ID
        username: Username
        role: User role (admin, user, etc.)
    
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token: str) -> TokenData:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        TokenData with user information
    
    Raises:
        AuthenticationException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        token_data = TokenData(
            username=payload.get("username"),
            user_id=payload.get("user_id"),
            role=payload.get("role"),
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
        
        return token_data
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Token has expired")
    except jwt.JWTError as e:
        raise AuthenticationException(f"Invalid token: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials
    
    Returns:
        CurrentUser object
    
    Raises:
        HTTPException: 401 if authentication fails
    """
    try:
        token = credentials.credentials
        token_data = decode_token(token)
        
        user = CurrentUser(
            user_id=token_data.user_id,
            username=token_data.username,
            role=token_data.role,
            is_admin=(token_data.role == "admin")
        )
        
        return user
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Dependency to require admin role
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        CurrentUser if admin
    
    Raises:
        HTTPException: 403 if user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[CurrentUser]:
    """
    Dependency to get current user if authenticated, None otherwise
    Useful for endpoints that work both with and without authentication
    
    Args:
        credentials: Optional HTTP Authorization credentials
    
    Returns:
        CurrentUser if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        token_data = decode_token(token)
        
        user = CurrentUser(
            user_id=token_data.user_id,
            username=token_data.username,
            role=token_data.role,
            is_admin=(token_data.role == "admin")
        )
        
        return user
        
    except (AuthenticationException, Exception):
        # If token is invalid, just return None instead of raising
        return None
