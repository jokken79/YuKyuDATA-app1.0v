"""
Authentication Routes
Endpoints de autenticación, login, logout, refresh tokens
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from services.auth_service import auth_service, TokenPair
from middleware.security import security, verify_token, get_current_user
from middleware.rate_limiter import rate_limiter_strict

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Request body para login"""
    username: str = Field(..., min_length=1, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class RefreshRequest(BaseModel):
    """Request body para refresh token"""
    refresh_token: str = Field(..., description="Refresh token")


class RegisterRequest(BaseModel):
    """Request body para registro de usuario"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")
    email: str = Field(..., regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    full_name: str = Field(..., min_length=1)


@router.post("/login", response_model=TokenPair, dependencies=[Depends(rate_limiter_strict)])
async def login(credentials: LoginRequest):
    """
    Autenticar usuario y obtener tokens

    Retorna par de tokens (access_token y refresh_token)

    **Rate limit**: 30 requests/minuto
    """
    user = auth_service.authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar par de tokens
    tokens = auth_service.create_token_pair(credentials.username)

    return tokens


@router.post("/refresh", response_model=TokenPair, dependencies=[Depends(rate_limiter_strict)])
async def refresh_token(request: RefreshRequest):
    """
    Renovar access token usando refresh token

    Retorna nuevo par de tokens

    **Rate limit**: 30 requests/minuto
    """
    try:
        tokens = auth_service.refresh_access_token(request.refresh_token)
        return tokens

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo renovar el token"
        )


@router.post("/logout", dependencies=[Depends(rate_limiter_strict)])
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Cerrar sesión y revocar token

    **Requiere autenticación**

    **Rate limit**: 30 requests/minuto
    """
    token = credentials.credentials

    # Revocar access token
    auth_service.revoke_token(token)

    return {"message": "Sesión cerrada exitosamente"}


@router.post("/logout-all", dependencies=[Depends(rate_limiter_strict)])
async def logout_all(current_user: dict = Depends(get_current_user)):
    """
    Cerrar todas las sesiones del usuario (revocar todos los refresh tokens)

    **Requiere autenticación**

    **Rate limit**: 30 requests/minuto
    """
    username = current_user["username"]

    # Revocar todos los refresh tokens del usuario
    tokens_to_remove = [
        token for token, user in auth_service.active_refresh_tokens.items()
        if user == username
    ]

    for token in tokens_to_remove:
        auth_service.revoke_refresh_token(token)

    return {"message": f"Se cerraron {len(tokens_to_remove)} sesiones"}


@router.get("/verify")
async def verify_token_endpoint(payload: dict = Depends(verify_token)):
    """
    Verificar validez de token actual

    **Requiere autenticación**

    Retorna información del token si es válido
    """
    return {
        "valid": True,
        "username": payload.get("sub"),
        "expires_at": payload.get("exp"),
        "token_type": payload.get("type")
    }


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Obtener información del usuario autenticado

    **Requiere autenticación**

    Retorna datos del usuario (sin contraseña)
    """
    return current_user


@router.post("/register", status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limiter_strict)])
async def register_user(user_data: RegisterRequest):
    """
    Registrar nuevo usuario

    **Requiere**: username, password, email, full_name

    **Rate limit**: 30 requests/minuto
    """
    # En producción, validar contraseña fuerte, email único, etc.
    try:
        new_user = auth_service.register_user(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            full_name=user_data.full_name,
            role="user"
        )

        return {
            "message": "Usuario registrado exitosamente",
            "user": new_user
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar usuario"
        )


@router.post("/change-password", dependencies=[Depends(rate_limiter_strict)])
async def change_password(
    current_password: str = Field(..., min_length=1),
    new_password: str = Field(..., min_length=8),
    current_user: dict = Depends(get_current_user)
):
    """
    Cambiar contraseña del usuario actual

    **Requiere autenticación**

    **Rate limit**: 30 requests/minuto
    """
    username = current_user["username"]

    # Verificar contraseña actual
    user_db = auth_service.users_db.get(username)
    if not user_db or not auth_service.verify_password(current_password, user_db["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    # Actualizar contraseña
    user_db["hashed_password"] = auth_service.get_password_hash(new_password)

    return {"message": "Contraseña actualizada exitosamente"}
