"""
Authentication Service
Servicio mejorado de autenticación con OAuth2, refresh tokens y seguridad robusta
"""

import jwt
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, status
from pydantic import BaseModel

# Configuración de seguridad
SECRET_KEY = secrets.token_urlsafe(32)  # Generar key aleatoria
REFRESH_SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class TokenData(BaseModel):
    """Datos contenidos en el token JWT"""
    username: str
    exp: datetime
    token_type: str = "access"  # "access" or "refresh"


class TokenPair(BaseModel):
    """Par de tokens (access + refresh)"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos hasta expiración


class AuthService:
    """Servicio de autenticación con OAuth2 y refresh tokens"""

    def __init__(self):
        # Almacén de refresh tokens válidos (en producción usar Redis)
        self.active_refresh_tokens: Dict[str, str] = {}  # token -> username

        # Almacén de tokens revocados (blacklist)
        self.revoked_tokens: set = set()

        # Base de datos de usuarios (en producción usar BD real)
        self.users_db = {
            "admin": {
                "username": "admin",
                "hashed_password": self.get_password_hash("admin123"),
                "email": "admin@yukyu.com",
                "full_name": "Administrator",
                "role": "admin",
                "is_active": True
            },
            "manager": {
                "username": "manager",
                "hashed_password": self.get_password_hash("manager123"),
                "email": "manager@yukyu.com",
                "full_name": "Manager User",
                "role": "manager",
                "is_active": True
            }
        }

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña contra hash"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def get_password_hash(self, password: str) -> str:
        """Generar hash de contraseña"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """
        Autenticar usuario con username y password

        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano

        Returns:
            Datos del usuario si autenticación exitosa, None si falla
        """
        user = self.users_db.get(username)

        if not user:
            return None

        if not self.verify_password(password, user["hashed_password"]):
            return None

        if not user.get("is_active", True):
            return None

        return user

    def create_access_token(self, username: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crear token de acceso JWT

        Args:
            username: Nombre de usuario
            expires_delta: Tiempo de expiración personalizado

        Returns:
            Token JWT codificado
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "sub": username,
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        }

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, username: str) -> str:
        """
        Crear refresh token para renovar access tokens

        Args:
            username: Nombre de usuario

        Returns:
            Refresh token JWT
        """
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": username,
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        }

        refresh_token = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

        # Almacenar refresh token activo
        self.active_refresh_tokens[refresh_token] = username

        return refresh_token

    def create_token_pair(self, username: str) -> TokenPair:
        """
        Crear par de tokens (access + refresh)

        Args:
            username: Nombre de usuario

        Returns:
            TokenPair con access_token y refresh_token
        """
        access_token = self.create_access_token(username)
        refresh_token = self.create_refresh_token(username)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    def verify_access_token(self, token: str) -> dict:
        """
        Verificar y decodificar access token

        Args:
            token: Token JWT

        Returns:
            Payload decodificado

        Raises:
            HTTPException: Si token inválido o expirado
        """
        # Verificar si token está revocado
        if token in self.revoked_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revocado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Verificar tipo de token
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tipo de token inválido",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido: falta username",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se pudo validar el token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def verify_refresh_token(self, token: str) -> str:
        """
        Verificar refresh token

        Args:
            token: Refresh token JWT

        Returns:
            Username del token

        Raises:
            HTTPException: Si token inválido
        """
        # Verificar si token está activo
        if token not in self.active_refresh_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado"
            )

        try:
            payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

            # Verificar tipo de token
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tipo de token inválido"
                )

            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )

            return username

        except jwt.ExpiredSignatureError:
            # Remover refresh token expirado
            if token in self.active_refresh_tokens:
                del self.active_refresh_tokens[token]

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expirado"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se pudo validar el refresh token"
            )

    def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """
        Generar nuevo access token usando refresh token

        Args:
            refresh_token: Refresh token válido

        Returns:
            Nuevo par de tokens
        """
        username = self.verify_refresh_token(refresh_token)

        # Invalidar refresh token antiguo
        if refresh_token in self.active_refresh_tokens:
            del self.active_refresh_tokens[refresh_token]

        # Generar nuevo par de tokens
        return self.create_token_pair(username)

    def revoke_token(self, token: str):
        """
        Revocar access token (logout)

        Args:
            token: Token a revocar
        """
        self.revoked_tokens.add(token)

    def revoke_refresh_token(self, refresh_token: str):
        """
        Revocar refresh token

        Args:
            refresh_token: Refresh token a revocar
        """
        if refresh_token in self.active_refresh_tokens:
            del self.active_refresh_tokens[refresh_token]

    def get_user(self, username: str) -> Optional[dict]:
        """
        Obtener información de usuario

        Args:
            username: Nombre de usuario

        Returns:
            Datos del usuario (sin password hash)
        """
        user = self.users_db.get(username)
        if user:
            # No retornar hash de contraseña
            return {
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "is_active": user["is_active"]
            }
        return None

    def register_user(self, username: str, password: str, email: str, full_name: str, role: str = "user") -> dict:
        """
        Registrar nuevo usuario

        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano
            email: Email
            full_name: Nombre completo
            role: Rol del usuario (default: "user")

        Returns:
            Datos del usuario creado

        Raises:
            HTTPException: Si usuario ya existe
        """
        if username in self.users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario ya existe"
            )

        hashed_password = self.get_password_hash(password)

        user_data = {
            "username": username,
            "hashed_password": hashed_password,
            "email": email,
            "full_name": full_name,
            "role": role,
            "is_active": True
        }

        self.users_db[username] = user_data

        return self.get_user(username)


# Instancia global del servicio de autenticación
auth_service = AuthService()
