"""
User Models - Schemas de usuarios y autenticacion
Modelos Pydantic para el sistema de auth
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


# ============================================
# ENUMS
# ============================================

class UserRole(str, Enum):
    """Roles de usuario."""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    READONLY = "readonly"


# ============================================
# AUTH REQUEST MODELS
# ============================================

class UserLogin(BaseModel):
    """Modelo para login de usuario."""
    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre de usuario"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Contrasena (minimo 8 caracteres)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "********"
            }
        }
    )


class LoginRequest(UserLogin):
    """Alias para compatibilidad con routes/auth.py"""
    pass


class RefreshRequest(BaseModel):
    """Request para refresh token."""
    refresh_token: str = Field(..., description="Refresh token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        }
    )


class RevokeRequest(BaseModel):
    """Request para revocar un refresh token especifico."""
    refresh_token: str = Field(..., description="Refresh token a revocar")


# ============================================
# USER CRUD MODELS
# ============================================

class UserBase(BaseModel):
    """Campos base de usuario."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nombre de usuario (3-50 caracteres)"
    )
    email: str = Field(
        ...,
        description="Email valido"
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre completo"
    )

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, v):
            raise ValueError('Email invalido')
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class UserCreate(UserBase):
    """Modelo para crear usuario."""
    password: str = Field(
        ...,
        min_length=8,
        description="Contrasena (minimo 8 caracteres)"
    )
    role: UserRole = Field(
        UserRole.USER,
        description="Rol del usuario"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contrasena debe tener al menos 8 caracteres')
        # Opcional: agregar mas validaciones de complejidad
        return v

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "username": "newuser",
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "SecurePass123",
                "role": "user"
            }
        }
    )


class RegisterRequest(UserCreate):
    """Alias para compatibilidad con routes/auth.py"""
    pass


class UserUpdate(BaseModel):
    """Modelo para actualizar usuario."""
    email: Optional[str] = Field(None, description="Nuevo email")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = Field(None, description="Nuevo rol")
    is_active: Optional[bool] = Field(None, description="Estado activo")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(pattern, v):
                raise ValueError('Email invalido')
        return v

    model_config = ConfigDict(
        use_enum_values=True
    )


class UserResponse(BaseModel):
    """Modelo de respuesta para usuario."""
    username: str = Field(..., description="Nombre de usuario")
    email: str = Field(..., description="Email")
    full_name: str = Field(..., description="Nombre completo")
    role: str = Field(..., description="Rol")
    is_active: bool = Field(True, description="Estado activo")
    created_at: Optional[datetime] = Field(None, description="Fecha de creacion")
    last_login: Optional[datetime] = Field(None, description="Ultimo login")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "Administrator",
                "role": "admin",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00"
            }
        }
    )


# ============================================
# PASSWORD MODELS
# ============================================

class ChangePasswordRequest(BaseModel):
    """Request para cambio de contrasena."""
    current_password: str = Field(
        ...,
        min_length=1,
        description="Contrasena actual"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="Nueva contrasena (minimo 8 caracteres)"
    )

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v, info):
        if info.data.get('current_password') and v == info.data['current_password']:
            raise ValueError('La nueva contrasena debe ser diferente a la actual')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newSecurePass456"
            }
        }
    )


class ResetPasswordRequest(BaseModel):
    """Request para reset de contrasena."""
    email: str = Field(..., description="Email del usuario")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class SetPasswordRequest(BaseModel):
    """Request para establecer nueva contrasena con token."""
    token: str = Field(..., description="Token de reset")
    new_password: str = Field(..., min_length=8, description="Nueva contrasena")


# ============================================
# TOKEN MODELS
# ============================================

class TokenResponse(BaseModel):
    """Respuesta con token de acceso."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Segundos hasta expiracion")
    user: dict = Field(..., description="Datos del usuario")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "username": "admin",
                    "role": "admin",
                    "name": "Administrator"
                }
            }
        }
    )


class TokenPair(BaseModel):
    """Par de tokens (access + refresh)."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field("bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Segundos hasta expiracion del access token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }
    )


class TokenData(BaseModel):
    """Datos contenidos en el token JWT."""
    username: str = Field(..., description="Username")
    exp: datetime = Field(..., description="Expiracion")
    token_type: str = Field("access", description="Tipo: access o refresh")


class CurrentUser(BaseModel):
    """Usuario actual autenticado."""
    username: str = Field(..., description="Username")
    role: str = Field(..., description="Rol")
    name: str = Field(..., description="Nombre")
    exp: float = Field(..., description="Timestamp de expiracion")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "role": "admin",
                "name": "Administrator",
                "exp": 1737120000.0
            }
        }
    )


# Export all
__all__ = [
    'UserRole',
    'UserLogin',
    'LoginRequest',
    'RefreshRequest',
    'RevokeRequest',
    'UserBase',
    'UserCreate',
    'RegisterRequest',
    'UserUpdate',
    'UserResponse',
    'ChangePasswordRequest',
    'ResetPasswordRequest',
    'SetPasswordRequest',
    'TokenResponse',
    'TokenPair',
    'TokenData',
    'CurrentUser',
]
