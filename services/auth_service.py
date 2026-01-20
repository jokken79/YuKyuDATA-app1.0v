"""
Authentication Service
Servicio mejorado de autenticacion con OAuth2, refresh tokens y seguridad robusta
Refresh tokens almacenados en base de datos para persistencia y seguridad
"""

import jwt
import secrets
import hashlib
import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, status
from pydantic import BaseModel

# Database imports are lazy to avoid circular import issues
# They are imported within __init__ and methods as needed

# Configuracion de seguridad
SECRET_KEY = secrets.token_urlsafe(32)  # Generar key aleatoria
REFRESH_SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"

# Tiempos de expiracion actualizados (v5.17)
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutos para access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 dias para refresh tokens


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
    expires_in: int  # segundos hasta expiracion del access token


class AuthService:
    """Servicio de autenticacion con OAuth2 y refresh tokens persistentes en BD"""

    # Cache para las funciones de database importadas (lazy)
    _db_functions = None

    def _get_db_functions(self):
        """Get database functions lazily to avoid circular imports."""
        if AuthService._db_functions is None:
            from database import (
                init_refresh_tokens_table,
                store_refresh_token,
                get_refresh_token_by_hash,
                revoke_refresh_token as db_revoke_refresh_token,
                revoke_all_user_refresh_tokens,
                is_refresh_token_valid,
                cleanup_expired_refresh_tokens,
                get_user_active_refresh_tokens,
                get_refresh_token_stats
            )
            AuthService._db_functions = {
                'init_refresh_tokens_table': init_refresh_tokens_table,
                'store_refresh_token': store_refresh_token,
                'get_refresh_token_by_hash': get_refresh_token_by_hash,
                'db_revoke_refresh_token': db_revoke_refresh_token,
                'revoke_all_user_refresh_tokens': revoke_all_user_refresh_tokens,
                'is_refresh_token_valid': is_refresh_token_valid,
                'cleanup_expired_refresh_tokens': cleanup_expired_refresh_tokens,
                'get_user_active_refresh_tokens': get_user_active_refresh_tokens,
                'get_refresh_token_stats': get_refresh_token_stats,
            }
        return AuthService._db_functions

    def __init__(self):
        # Almacen de tokens revocados (blacklist para access tokens)
        # Los access tokens son de corta duracion, se puede mantener en memoria
        self.revoked_tokens: set = set()

        # Base de datos de usuarios (en produccion usar BD real)
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

    def initialize(self):
        """Inicializar servicios dependientes (DB, etc.)"""
        try:
            db_funcs = self._get_db_functions()
            db_funcs['init_refresh_tokens_table']()
        except Exception as e:
            print(f"Warning: Could not initialize refresh_tokens table: {e}")

    def _hash_token(self, token: str) -> str:
        """
        Genera un hash SHA-256 del token para almacenamiento seguro.
        Nunca almacenamos el token en texto plano.

        Args:
            token: Token JWT en texto plano

        Returns:
            Hash SHA-256 del token en hexadecimal
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar contrasena contra hash"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def get_password_hash(self, password: str) -> str:
        """Generar hash de contrasena"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """
        Autenticar usuario con username y password

        Args:
            username: Nombre de usuario
            password: Contrasena en texto plano

        Returns:
            Datos del usuario si autenticacion exitosa, None si falla
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
            expires_delta: Tiempo de expiracion personalizado

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

    def create_refresh_token(
        self,
        username: str,
        user_agent: str = None,
        ip_address: str = None
    ) -> str:
        """
        Crear refresh token para renovar access tokens.
        El token se almacena hasheado en la base de datos.

        Args:
            username: Nombre de usuario
            user_agent: User-Agent del cliente (para tracking de sesiones)
            ip_address: IP del cliente (para tracking de sesiones)

        Returns:
            Refresh token JWT
        """
        # Generar ID unico para el token
        token_id = str(uuid.uuid4())

        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": username,
            "exp": expire,
            "type": "refresh",
            "jti": token_id,  # JWT ID para identificacion unica
            "iat": datetime.utcnow()
        }

        refresh_token = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

        # Almacenar hash del token en la base de datos
        token_hash = self._hash_token(refresh_token)
        db_funcs = self._get_db_functions()
        db_funcs['store_refresh_token'](
            token_id=token_id,
            user_id=username,
            token_hash=token_hash,
            expires_at=expire.isoformat(),
            user_agent=user_agent,
            ip_address=ip_address
        )

        return refresh_token

    def create_token_pair(
        self,
        username: str,
        user_agent: str = None,
        ip_address: str = None
    ) -> TokenPair:
        """
        Crear par de tokens (access + refresh)

        Args:
            username: Nombre de usuario
            user_agent: User-Agent del cliente (opcional)
            ip_address: IP del cliente (opcional)

        Returns:
            TokenPair con access_token y refresh_token
        """
        access_token = self.create_access_token(username)
        refresh_token = self.create_refresh_token(username, user_agent, ip_address)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convertir a segundos
        )

    def verify_access_token(self, token: str) -> dict:
        """
        Verificar y decodificar access token

        Args:
            token: Token JWT

        Returns:
            Payload decodificado

        Raises:
            HTTPException: Si token invalido o expirado
        """
        # Verificar si token esta revocado
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
                    detail="Tipo de token invalido",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalido: falta username",
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
        Verificar refresh token contra la base de datos

        Args:
            token: Refresh token JWT

        Returns:
            Username del token

        Raises:
            HTTPException: Si token invalido
        """
        # Verificar primero en la base de datos usando el hash
        token_hash = self._hash_token(token)

        if not is_refresh_token_valid(token_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalido o expirado"
            )

        try:
            payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

            # Verificar tipo de token
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tipo de token invalido"
                )

            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalido"
                )

            return username

        except jwt.ExpiredSignatureError:
            # El token expiro - revocar en BD
            db_revoke_refresh_token(token_hash)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expirado"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se pudo validar el refresh token"
            )

    def refresh_access_token(
        self,
        refresh_token: str,
        user_agent: str = None,
        ip_address: str = None
    ) -> TokenPair:
        """
        Generar nuevo access token usando refresh token.
        Implementa rotacion de refresh tokens por seguridad.

        Args:
            refresh_token: Refresh token valido
            user_agent: User-Agent del cliente (opcional)
            ip_address: IP del cliente (opcional)

        Returns:
            Nuevo par de tokens
        """
        username = self.verify_refresh_token(refresh_token)

        # Revocar el refresh token antiguo (rotacion de tokens)
        old_token_hash = self._hash_token(refresh_token)
        db_revoke_refresh_token(old_token_hash)

        # Generar nuevo par de tokens
        return self.create_token_pair(username, user_agent, ip_address)

    def revoke_token(self, token: str):
        """
        Revocar access token (logout)

        Args:
            token: Token a revocar
        """
        self.revoked_tokens.add(token)

        # Limpiar tokens antiguos de la blacklist para no consumir memoria
        # Solo mantener los que aun no expirarian naturalmente
        self._cleanup_revoked_tokens()

    def _cleanup_revoked_tokens(self):
        """
        Limpiar tokens revocados que ya expirarian naturalmente.
        Los access tokens tienen 15 min de vida, mantener blacklist por 20 min max.
        """
        # Esta es una limpieza simple - en produccion usar Redis con TTL
        if len(self.revoked_tokens) > 1000:
            # Si hay muchos tokens, limpiar los mas antiguos
            # En produccion, mejor usar Redis con expiracion automatica
            self.revoked_tokens = set(list(self.revoked_tokens)[-500:])

    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revocar refresh token

        Args:
            refresh_token: Refresh token a revocar

        Returns:
            True si se revoco correctamente
        """
        token_hash = self._hash_token(refresh_token)
        return db_revoke_refresh_token(token_hash)

    def revoke_all_user_tokens(self, username: str) -> int:
        """
        Revocar todos los refresh tokens de un usuario (logout de todas las sesiones)

        Args:
            username: Nombre de usuario

        Returns:
            Numero de tokens revocados
        """
        return revoke_all_user_refresh_tokens(username)

    def get_user_sessions(self, username: str) -> list:
        """
        Obtener todas las sesiones activas de un usuario

        Args:
            username: Nombre de usuario

        Returns:
            Lista de sesiones activas (tokens sin el hash)
        """
        return get_user_active_refresh_tokens(username)

    def get_token_stats(self) -> dict:
        """
        Obtener estadisticas de tokens

        Returns:
            Dict con estadisticas
        """
        return get_refresh_token_stats()

    def cleanup_tokens(self) -> int:
        """
        Limpiar tokens expirados de la base de datos.
        Debe llamarse periodicamente (ej: cada hora)

        Returns:
            Numero de tokens eliminados
        """
        return cleanup_expired_refresh_tokens()

    def get_user(self, username: str) -> Optional[dict]:
        """
        Obtener informacion de usuario

        Args:
            username: Nombre de usuario

        Returns:
            Datos del usuario (sin password hash)
        """
        user = self.users_db.get(username)
        if user:
            # No retornar hash de contrasena
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
            password: Contrasena en texto plano
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


# Instancia global del servicio de autenticacion
auth_service = AuthService()
