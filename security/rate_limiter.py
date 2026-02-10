# security/rate_limiter.py
# Sistema de rate limiting avanzado para YuKyuDATA

from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RateLimitManager:
    """
    Manager centralizado de rate limiting
    Soporta límites por:
    - IP address
    - User ID
    - API key
    - Endpoint específico
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            logger.info("Connected to Redis for rate limiting")
        except Exception as e:
            logger.warning(f"Redis unavailable, falling back to in-memory: {e}")
            self.redis = None
            self.in_memory = {}

    def get_identifier(self, request: Request, user_id: Optional[str] = None) -> str:
        """
        Obtener identificador único para rate limiting
        Prioridad: user_id > api_key > ip_address
        """

        if user_id:
            return f"user:{user_id}"

        # Extraer API key del header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
            return f"key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

        # Fallback a IP
        return f"ip:{get_remote_address(request)}"

    def is_allowed(
        self,
        request: Request,
        max_requests: int = 100,
        window_seconds: int = 60,
        user_id: Optional[str] = None,
    ) -> tuple[bool, Dict]:
        """
        Verificar si una solicitud está dentro del límite
        Retorna: (allowed, info_dict)
        """

        identifier = self.get_identifier(request, user_id)
        key = f"rate_limit:{identifier}"

        if self.redis:
            return self._check_redis(key, max_requests, window_seconds)
        else:
            return self._check_in_memory(key, max_requests, window_seconds)

    def _check_redis(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, Dict]:
        """Verificación usando Redis"""

        try:
            pipe = self.redis.pipeline()

            # Incrementar contador
            pipe.incr(key)

            # Establecer expiración si es primera solicitud
            pipe.expire(key, window_seconds)

            # Obtener contador actual
            pipe.get(key)

            results = pipe.execute()
            current_count = int(results[-1])

            info = {
                "limit": max_requests,
                "current": current_count,
                "remaining": max(0, max_requests - current_count),
                "reset_at": datetime.now(timezone.utc) + timedelta(seconds=window_seconds),
            }

            allowed = current_count <= max_requests

            if not allowed:
                logger.warning(f"Rate limit exceeded for {key}: {current_count}/{max_requests}")

            return allowed, info

        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fallback seguro: permitir si Redis falla
            return True, {"error": "rate_limit_check_failed"}

    def _check_in_memory(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, Dict]:
        """Verificación en memoria (fallback)"""

        now = datetime.now(timezone.utc)

        if key not in self.in_memory:
            self.in_memory[key] = {
                "requests": [now],
                "window_start": now,
            }
        else:
            # Limpiar requests viejos
            window_start = self.in_memory[key]["window_start"]
            cutoff = now - timedelta(seconds=window_seconds)

            self.in_memory[key]["requests"] = [
                t for t in self.in_memory[key]["requests"]
                if t > cutoff
            ]

            # Reset window si pasó el tiempo
            if now - window_start > timedelta(seconds=window_seconds):
                self.in_memory[key] = {
                    "requests": [now],
                    "window_start": now,
                }
            else:
                self.in_memory[key]["requests"].append(now)

        current_count = len(self.in_memory[key]["requests"])
        window_reset = self.in_memory[key]["window_start"] + timedelta(seconds=window_seconds)

        info = {
            "limit": max_requests,
            "current": current_count,
            "remaining": max(0, max_requests - current_count),
            "reset_at": window_reset,
        }

        allowed = current_count <= max_requests

        return allowed, info

    def get_status(self, identifier: str) -> Optional[Dict]:
        """Obtener status actual de rate limit"""

        key = f"rate_limit:{identifier}"

        if self.redis:
            current = self.redis.get(key)
            if current:
                return {"current": int(current), "key": key}

        return None

    def reset(self, identifier: str) -> bool:
        """Reset rate limit para un usuario (admin only)"""

        key = f"rate_limit:{identifier}"

        if self.redis:
            self.redis.delete(key)
        elif key in self.in_memory:
            del self.in_memory[key]

        logger.info(f"Rate limit reset for {identifier}")
        return True


class EndpointRateLimiter:
    """Configuración de rate limits por endpoint"""

    LIMITS = {
        # Auth endpoints - muy restrictivos
        "auth.login": {
            "max_requests": 5,
            "window_seconds": 60,
            "description": "Prevenir brute force attacks",
        },
        "auth.mfa_verify": {
            "max_requests": 10,
            "window_seconds": 60,
            "description": "MFA verification attempts",
        },
        "auth.logout": {
            "max_requests": 50,
            "window_seconds": 60,
            "description": "Logout requests",
        },

        # Upload endpoints - moderado
        "data.upload": {
            "max_requests": 10,
            "window_seconds": 3600,  # 1 hour
            "description": "File upload operations",
        },
        "data.sync": {
            "max_requests": 5,
            "window_seconds": 3600,  # 1 hour
            "description": "Data sync operations",
        },

        # Export/reporting - moderado
        "data.export": {
            "max_requests": 20,
            "window_seconds": 3600,  # 1 hour
            "description": "Data export operations",
        },

        # Regular API read - generoso
        "api.get_employees": {
            "max_requests": 100,
            "window_seconds": 60,
            "description": "Read employee data",
        },
        "api.get_genzai": {
            "max_requests": 100,
            "window_seconds": 60,
            "description": "Read dispatch employee data",
        },
        "api.get_ukeoi": {
            "max_requests": 100,
            "window_seconds": 60,
            "description": "Read contract employee data",
        },

        # Admin operations - restrictivos
        "admin.delete": {
            "max_requests": 1,
            "window_seconds": 3600,  # 1 hour
            "description": "Destructive admin operations",
        },
        "admin.settings": {
            "max_requests": 10,
            "window_seconds": 3600,  # 1 hour
            "description": "Admin settings changes",
        },
    }

    @classmethod
    def get_limit(cls, endpoint_key: str) -> Dict:
        """Obtener configuración de límite para un endpoint"""

        if endpoint_key in cls.LIMITS:
            return cls.LIMITS[endpoint_key]

        # Default seguro
        return {
            "max_requests": 100,
            "window_seconds": 60,
            "description": "Default rate limit",
        }


class RateLimitException(HTTPException):
    """Excepción personalizada para rate limit"""

    def __init__(self, retry_after: int, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=429,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )


# Instancia global
rate_limit_manager = RateLimitManager()
