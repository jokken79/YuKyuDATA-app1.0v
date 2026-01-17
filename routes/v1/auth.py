"""
Authentication Routes
Endpoints de autenticacion, login, logout, refresh tokens
Sistema de refresh tokens con persistencia en base de datos (v5.17)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from services.auth_service import auth_service, TokenPair
from middleware.security import security, verify_token, get_current_user
from middleware.rate_limiter import rate_limiter_strict
from ..responses import success_response, error_response

# Import centralized Pydantic models
from models import (
    LoginRequest,
    RefreshRequest,
    RevokeRequest,
    RegisterRequest,
    ChangePasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_info(request: Request) -> tuple:
    """
    Extrae informacion del cliente de la request.

    Returns:
        tuple: (user_agent, ip_address)
    """
    user_agent = request.headers.get("user-agent", "unknown")
    # Obtener IP real considerando proxies
    ip_address = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    if "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()
    return user_agent, ip_address


@router.post("/login", response_model=TokenPair, dependencies=[Depends(rate_limiter_strict)])
async def login(credentials: LoginRequest, request: Request):
    """
    Autenticar usuario y obtener tokens

    Retorna par de tokens (access_token y refresh_token)

    - **access_token**: Expira en 15 minutos
    - **refresh_token**: Expira en 7 dias, almacenado en base de datos
    - **expires_in**: Segundos hasta expiracion del access_token (900)

    **Rate limit**: 30 requests/minuto
    """
    user = auth_service.authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contrasena incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Obtener informacion del cliente para tracking de sesiones
    user_agent, ip_address = _get_client_info(request)

    # Generar par de tokens
    tokens = auth_service.create_token_pair(
        credentials.username,
        user_agent=user_agent,
        ip_address=ip_address
    )

    return tokens


@router.post("/refresh", response_model=TokenPair, dependencies=[Depends(rate_limiter_strict)])
async def refresh_token(request_body: RefreshRequest, request: Request):
    """
    Renovar access token usando refresh token

    Implementa rotacion de refresh tokens: el refresh token usado se revoca
    y se genera uno nuevo junto con el access token.

    Retorna nuevo par de tokens

    **Rate limit**: 30 requests/minuto
    """
    try:
        # Obtener informacion del cliente
        user_agent, ip_address = _get_client_info(request)

        tokens = auth_service.refresh_access_token(
            request_body.refresh_token,
            user_agent=user_agent,
            ip_address=ip_address
        )
        return tokens

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo renovar el token"
        )


@router.post("/revoke", dependencies=[Depends(rate_limiter_strict)])
async def revoke_refresh_token(request_body: RevokeRequest):
    """
    Revocar un refresh token especifico

    Util para cerrar una sesion especifica sin afectar otras sesiones.
    El token se marca como revocado en la base de datos.

    **Rate limit**: 30 requests/minuto
    """
    success = auth_service.revoke_refresh_token(request_body.refresh_token)

    if success:
        return success_response(message="Token revocado exitosamente")
    else:
        return success_response(
            message="Token no encontrado o ya revocado",
            warning=True
        )


@router.post("/logout", dependencies=[Depends(rate_limiter_strict)])
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Cerrar sesion y revocar token

    Revoca el access token actual (se agrega a blacklist en memoria).

    **Requiere autenticacion**

    **Rate limit**: 30 requests/minuto
    """
    token = credentials.credentials

    # Revocar access token
    auth_service.revoke_token(token)

    return success_response(message="Sesion cerrada exitosamente")


@router.post("/logout-all", dependencies=[Depends(rate_limiter_strict)])
async def logout_all(current_user: dict = Depends(get_current_user)):
    """
    Cerrar todas las sesiones del usuario (revocar todos los refresh tokens)

    Revoca todos los refresh tokens del usuario en la base de datos.
    Util cuando se sospecha de compromiso de credenciales.

    **Requiere autenticacion**

    **Rate limit**: 30 requests/minuto
    """
    username = current_user["username"]

    # Revocar todos los refresh tokens del usuario en BD
    revoked_count = auth_service.revoke_all_user_tokens(username)

    return success_response(
        message=f"Se cerraron {revoked_count} sesiones",
        data={"sessions_closed": revoked_count}
    )


@router.get("/sessions")
async def get_user_sessions(current_user: dict = Depends(get_current_user)):
    """
    Obtener todas las sesiones activas del usuario

    Retorna lista de sesiones con informacion de dispositivo y ubicacion.

    **Requiere autenticacion**
    """
    username = current_user["username"]

    sessions = auth_service.get_user_sessions(username)

    return success_response(
        data={
            "sessions": sessions,
            "count": len(sessions)
        }
    )


@router.get("/verify")
async def verify_token_endpoint(payload: dict = Depends(verify_token)):
    """
    Verificar validez de token actual

    **Requiere autenticacion**

    Retorna informacion del token si es valido
    """
    return success_response(
        data={
            "valid": True,
            "username": payload.get("sub"),
            "expires_at": payload.get("exp"),
            "token_type": payload.get("type")
        },
        message="Token is valid"
    )


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Obtener informacion del usuario autenticado

    **Requiere autenticacion**

    Retorna datos del usuario (sin contrasena)
    """
    return success_response(data=current_user)


@router.post("/register", status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limiter_strict)])
async def register_user(user_data: RegisterRequest):
    """
    Registrar nuevo usuario

    **Requiere**: username, password, email, full_name

    **Rate limit**: 30 requests/minuto
    """
    # En produccion, validar contrasena fuerte, email unico, etc.
    try:
        new_user = auth_service.register_user(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            full_name=user_data.full_name,
            role="user"
        )

        return success_response(
            data={"user": new_user},
            message="Usuario registrado exitosamente"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar usuario"
        )


@router.post("/change-password", dependencies=[Depends(rate_limiter_strict)])
async def change_password(
    request_body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Cambiar contrasena del usuario actual

    Despues de cambiar la contrasena, se recomienda revocar todas las sesiones
    usando /logout-all

    **Requiere autenticacion**

    **Rate limit**: 30 requests/minuto
    """
    username = current_user["username"]

    # Verificar contrasena actual
    user_db = auth_service.users_db.get(username)
    if not user_db or not auth_service.verify_password(request_body.current_password, user_db["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contrasena actual incorrecta"
        )

    # Actualizar contrasena
    user_db["hashed_password"] = auth_service.get_password_hash(request_body.new_password)

    return success_response(message="Contrasena actualizada exitosamente")


@router.get("/stats")
async def get_token_stats(current_user: dict = Depends(get_current_user)):
    """
    Obtener estadisticas de tokens (solo admin)

    Retorna estadisticas de refresh tokens: total, activos, revocados, expirados

    **Requiere autenticacion con rol admin**
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden ver estadisticas"
        )

    stats = auth_service.get_token_stats()

    return success_response(data=stats)


@router.post("/cleanup", dependencies=[Depends(rate_limiter_strict)])
async def cleanup_tokens(current_user: dict = Depends(get_current_user)):
    """
    Limpiar tokens expirados de la base de datos (solo admin)

    Elimina todos los refresh tokens expirados o revocados hace mas de 24 horas.
    Se recomienda ejecutar periodicamente (ej: cada hora via cron).

    **Requiere autenticacion con rol admin**

    **Rate limit**: 30 requests/minuto
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden limpiar tokens"
        )

    deleted_count = auth_service.cleanup_tokens()

    return success_response(
        message=f"Se eliminaron {deleted_count} tokens expirados/revocados",
        data={"deleted_count": deleted_count}
    )
