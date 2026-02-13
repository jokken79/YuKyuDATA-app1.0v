"""
Security Middleware
Middleware para autenticación y autorización
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth_service import auth_service

# Security scheme para Swagger UI
security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verificar token JWT en request

    Args:
        credentials: Credenciales Bearer del header Authorization

    Returns:
        Payload del token decodificado

    Raises:
        HTTPException: Si token inválido
    """
    token = credentials.credentials
    payload = auth_service.verify_access_token(token)
    return payload


async def get_current_user(payload: dict = Depends(verify_token)) -> dict:
    """
    Obtener usuario actual desde token

    Args:
        payload: Payload del token JWT

    Returns:
        Datos del usuario actual

    Raises:
        HTTPException: Si usuario no existe
    """
    username = payload.get("sub")
    user = auth_service.get_user(username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_role(required_role: str):
    """
    Dependency para requerir rol específico

    Args:
        required_role: Rol requerido ("admin", "manager", "user")

    Returns:
        Dependency function
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")

        # Jerarquía de roles: admin > manager > user
        role_hierarchy = {"admin": 3, "manager": 2, "user": 1}

        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere rol: {required_role}"
            )

        return current_user

    return role_checker
