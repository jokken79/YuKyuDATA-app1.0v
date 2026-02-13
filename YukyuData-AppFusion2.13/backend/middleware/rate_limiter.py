"""
Rate Limiter Middleware - User-Aware Implementation
Sistema de rate limiting avanzado con soporte para:
- Rate limiting por IP (usuarios anónimos)
- Rate limiting por user_id (usuarios autenticados)
- Límites diferentes por endpoint
- Headers informativos de rate limit
"""

from collections import defaultdict
from time import time
from fastapi import Request, HTTPException, status, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple, Optional, Any
import logging
import re

logger = logging.getLogger(__name__)


# ============================================
# RATE LIMIT CONFIGURATION
# ============================================

RATE_LIMITS = {
    # Default limits
    'default': {'requests': 100, 'window': 60},           # 100 req/min para anónimos
    'authenticated': {'requests': 200, 'window': 60},     # 200 req/min para autenticados

    # Auth endpoints - muy restrictivos (prevenir brute force)
    'api/auth/login': {'requests': 5, 'window': 60},      # 5 intentos/min
    'api/auth/register': {'requests': 3, 'window': 60},   # 3 registros/min
    'api/auth/refresh': {'requests': 10, 'window': 60},   # 10 refresh/min
    'api/auth/change-password': {'requests': 3, 'window': 60},

    # Sync endpoints - muy limitados (operaciones costosas)
    'api/sync': {'requests': 2, 'window': 60},            # 2 syncs/min
    'api/sync-genzai': {'requests': 2, 'window': 60},
    'api/sync-ukeoi': {'requests': 2, 'window': 60},
    'api/sync-staff': {'requests': 2, 'window': 60},

    # Leave requests - moderado
    'api/leave-requests': {'requests': 30, 'window': 60},

    # Employees - moderado
    'api/employees': {'requests': 50, 'window': 60},

    # Reports - limitado (generación costosa)
    'api/reports': {'requests': 10, 'window': 60},
    'api/reports/pdf': {'requests': 5, 'window': 60},

    # Notifications - relajado
    'api/notifications': {'requests': 100, 'window': 60},

    # Health/status - muy relajado
    'api/health': {'requests': 300, 'window': 60},
    'api/project-status': {'requests': 60, 'window': 60},

    # Analytics - moderado
    'api/analytics': {'requests': 30, 'window': 60},

    # Compliance checks
    'api/compliance': {'requests': 20, 'window': 60},
    'api/expiring-soon': {'requests': 20, 'window': 60},

    # ✅ FIX (BUG #16-18): Rate limiting en endpoints sensibles
    # Yukyu endpoints - limitado (acceso a datos de vacaciones sensibles)
    'yukyu/usage-details': {'requests': 20, 'window': 60},       # 20 req/min
    'yukyu/monthly-summary': {'requests': 15, 'window': 60},
    'yukyu/kpi-stats': {'requests': 15, 'window': 60},
    'yukyu/by-employee-type': {'requests': 15, 'window': 60},
    'yukyu/employee-summary': {'requests': 20, 'window': 60},

    # System & Audit endpoints - muy restrictivos (acceso a logs sensibles)
    'cache-stats': {'requests': 10, 'window': 60},               # 10 req/min
    'audit-log': {'requests': 15, 'window': 60},                 # 15 req/min para listado
    'orchestrator/status': {'requests': 20, 'window': 60},       # 20 req/min para status
    'orchestrator/history': {'requests': 10, 'window': 60},      # 10 req/min
    'orchestrator/run-compliance-check': {'requests': 5, 'window': 60},  # 5 req/min
    'system/snapshot': {'requests': 10, 'window': 60},
    'system/audit-log': {'requests': 15, 'window': 60},
    'system/activity-report': {'requests': 5, 'window': 60},
}


class RateLimitInfo:
    """Información de estado del rate limit"""

    def __init__(self, limit: int, remaining: int, reset_time: float):
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time

    def to_headers(self) -> Dict[str, str]:
        """Convertir a headers HTTP"""
        return {
            'X-RateLimit-Limit': str(self.limit),
            'X-RateLimit-Remaining': str(max(0, self.remaining)),
            'X-RateLimit-Reset': str(int(self.reset_time)),
        }


class UserAwareRateLimiter:
    """
    Rate limiter avanzado que distingue entre usuarios autenticados y anónimos.

    Características:
    - Límites por IP para usuarios anónimos
    - Límites por user_id para usuarios autenticados
    - Límites específicos por endpoint
    - Headers informativos de rate limit
    - Limpieza automática de entradas antiguas
    """

    def __init__(
        self,
        default_limit: int = 100,
        default_window: int = 60,
        authenticated_limit: int = 200,
        cleanup_interval: int = 300
    ):
        """
        Inicializar rate limiter.

        Args:
            default_limit: Límite por defecto para anónimos
            default_window: Ventana de tiempo en segundos
            authenticated_limit: Límite por defecto para autenticados
            cleanup_interval: Intervalo de limpieza en segundos
        """
        self.default_limit = default_limit
        self.default_window = default_window
        self.authenticated_limit = authenticated_limit
        self.cleanup_interval = cleanup_interval

        # Almacenamiento separado
        self.ip_requests: Dict[str, list] = defaultdict(list)
        self.user_requests: Dict[str, list] = defaultdict(list)
        self.endpoint_requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

        # Timestamp de última limpieza
        self.last_cleanup = time()

    def _cleanup_old_requests(self):
        """Limpiar requests antiguas de la memoria"""
        now = time()

        # Solo limpiar cada cleanup_interval segundos
        if now - self.last_cleanup < self.cleanup_interval:
            return

        self.last_cleanup = now
        max_window = max(RATE_LIMITS.get(k, {}).get('window', 60) for k in RATE_LIMITS)
        cutoff = now - max_window - 60  # Margen adicional de 60s

        # Limpiar IP requests
        keys_to_delete = []
        for ip, timestamps in self.ip_requests.items():
            self.ip_requests[ip] = [t for t in timestamps if t > cutoff]
            if not self.ip_requests[ip]:
                keys_to_delete.append(ip)
        for key in keys_to_delete:
            del self.ip_requests[key]

        # Limpiar user requests
        keys_to_delete = []
        for user_id, timestamps in self.user_requests.items():
            self.user_requests[user_id] = [t for t in timestamps if t > cutoff]
            if not self.user_requests[user_id]:
                keys_to_delete.append(user_id)
        for key in keys_to_delete:
            del self.user_requests[key]

        # Limpiar endpoint requests
        for endpoint in list(self.endpoint_requests.keys()):
            for key in list(self.endpoint_requests[endpoint].keys()):
                self.endpoint_requests[endpoint][key] = [
                    t for t in self.endpoint_requests[endpoint][key] if t > cutoff
                ]
                if not self.endpoint_requests[endpoint][key]:
                    del self.endpoint_requests[endpoint][key]
            if not self.endpoint_requests[endpoint]:
                del self.endpoint_requests[endpoint]

    def _get_endpoint_key(self, path: str) -> Optional[str]:
        """
        Obtener la clave de configuración del endpoint.

        Busca coincidencias exactas primero, luego prefijos.
        """
        # Normalizar path
        path = path.lstrip('/')

        # Coincidencia exacta
        if path in RATE_LIMITS:
            return path

        # Buscar por prefijo (más largo primero)
        matches = []
        for endpoint_key in RATE_LIMITS.keys():
            if endpoint_key.startswith('api/') and path.startswith(endpoint_key):
                matches.append(endpoint_key)

        if matches:
            # Retornar el match más específico (más largo)
            return max(matches, key=len)

        return None

    def _get_limits(self, path: str, is_authenticated: bool) -> Tuple[int, int]:
        """
        Obtener límites para un path específico.

        Returns:
            Tupla (max_requests, window_seconds)
        """
        endpoint_key = self._get_endpoint_key(path)

        if endpoint_key and endpoint_key in RATE_LIMITS:
            config = RATE_LIMITS[endpoint_key]
            return config['requests'], config['window']

        # Usar límites por defecto según autenticación
        if is_authenticated:
            return self.authenticated_limit, self.default_window
        return self.default_limit, self.default_window

    def _extract_user_from_token(self, request: Request) -> Optional[str]:
        """
        Extraer user_id del token JWT si existe.

        Returns:
            user_id si el token es válido, None si no hay token o es inválido
        """
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header[7:]  # Remover 'Bearer '

        try:
            # Importar aquí para evitar circular imports
            from services.auth import verify_token
            user = verify_token(token)
            if user:
                return user.username
        except Exception as e:
            logger.debug(f"Error extracting user from token: {e}")

        return None

    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP del cliente considerando proxies"""
        # Verificar headers de proxy
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Tomar la primera IP (cliente original)
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()

        # Fallback a la IP directa
        if request.client:
            return request.client.host

        return 'unknown'

    def check_limit(
        self,
        request: Request,
        user_id: Optional[str] = None
    ) -> Tuple[bool, RateLimitInfo]:
        """
        Verificar si una request está dentro del límite.

        Args:
            request: FastAPI Request object
            user_id: ID de usuario si se conoce externamente

        Returns:
            Tupla (is_allowed, rate_limit_info)
        """
        self._cleanup_old_requests()

        now = time()
        path = request.url.path

        # Determinar si el usuario está autenticado
        if user_id is None:
            user_id = self._extract_user_from_token(request)

        is_authenticated = user_id is not None
        max_requests, window = self._get_limits(path, is_authenticated)
        cutoff = now - window

        # Determinar la clave y el storage a usar
        if is_authenticated:
            key = f"user:{user_id}"
            storage = self.user_requests
            storage_key = user_id
        else:
            client_ip = self._get_client_ip(request)
            key = f"ip:{client_ip}"
            storage = self.ip_requests
            storage_key = client_ip

        # También verificar límite por endpoint si es más restrictivo
        endpoint_key = self._get_endpoint_key(path)

        if endpoint_key:
            # Filtrar requests antiguas del endpoint
            self.endpoint_requests[endpoint_key][key] = [
                t for t in self.endpoint_requests[endpoint_key][key]
                if t > cutoff
            ]
            endpoint_count = len(self.endpoint_requests[endpoint_key][key])
        else:
            endpoint_count = 0

        # Filtrar requests antiguas del storage principal
        storage[storage_key] = [t for t in storage[storage_key] if t > cutoff]
        current_count = len(storage[storage_key])

        # Usar el conteo más restrictivo
        effective_count = max(current_count, endpoint_count)
        remaining = max_requests - effective_count - 1  # -1 porque esta request cuenta
        reset_time = cutoff + window

        # Crear info de rate limit
        info = RateLimitInfo(
            limit=max_requests,
            remaining=remaining,
            reset_time=reset_time
        )

        # Verificar si está dentro del límite
        if effective_count >= max_requests:
            logger.warning(
                f"Rate limit exceeded: {key} on {path} "
                f"({effective_count}/{max_requests} in {window}s)"
            )
            return False, info

        # Registrar esta request
        storage[storage_key].append(now)
        if endpoint_key:
            self.endpoint_requests[endpoint_key][key].append(now)

        return True, info

    def get_usage(self, identifier: str) -> Tuple[int, int]:
        """
        Obtener uso actual de rate limit para un identificador.

        Args:
            identifier: 'user:{user_id}' o 'ip:{ip_address}'

        Returns:
            Tupla (requests_usadas, límite_default)
        """
        now = time()
        cutoff = now - self.default_window

        if identifier.startswith('user:'):
            user_id = identifier[5:]
            active = [t for t in self.user_requests.get(user_id, []) if t > cutoff]
            return len(active), self.authenticated_limit
        elif identifier.startswith('ip:'):
            ip = identifier[3:]
            active = [t for t in self.ip_requests.get(ip, []) if t > cutoff]
            return len(active), self.default_limit

        return 0, self.default_limit

    def reset(self, identifier: Optional[str] = None):
        """
        Resetear contador de rate limit.

        Args:
            identifier: 'user:{user_id}', 'ip:{ip}', o None para todo
        """
        if identifier is None:
            self.ip_requests.clear()
            self.user_requests.clear()
            self.endpoint_requests.clear()
            logger.info("All rate limits reset")
            return

        if identifier.startswith('user:'):
            user_id = identifier[5:]
            if user_id in self.user_requests:
                del self.user_requests[user_id]
            # También limpiar de endpoint_requests
            for endpoint in self.endpoint_requests:
                key = f"user:{user_id}"
                if key in self.endpoint_requests[endpoint]:
                    del self.endpoint_requests[endpoint][key]
            logger.info(f"Rate limit reset for user: {user_id}")

        elif identifier.startswith('ip:'):
            ip = identifier[3:]
            if ip in self.ip_requests:
                del self.ip_requests[ip]
            # También limpiar de endpoint_requests
            for endpoint in self.endpoint_requests:
                key = f"ip:{ip}"
                if key in self.endpoint_requests[endpoint]:
                    del self.endpoint_requests[endpoint][key]
            logger.info(f"Rate limit reset for IP: {ip}")

    async def __call__(self, request: Request) -> Optional[RateLimitInfo]:
        """
        Callable para usar como dependencia de FastAPI.

        Raises:
            HTTPException: Si se excede el rate limit

        Returns:
            RateLimitInfo para agregar headers
        """
        is_allowed, info = self.check_limit(request)

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Limit: {info.limit} requests per minute",
                headers={
                    **info.to_headers(),
                    'Retry-After': str(int(info.reset_time - time()))
                }
            )

        return info


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting que agrega headers a todas las respuestas.
    """

    def __init__(self, app, rate_limiter: UserAwareRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        import os

        # Paths excluidos del rate limiting
        excluded_paths = ['/docs', '/redoc', '/openapi.json', '/favicon.ico']

        if any(request.url.path.startswith(p) for p in excluded_paths):
            return await call_next(request)

        # Skip rate limiting in testing mode
        if os.environ.get("TESTING") == "true":
            response = await call_next(request)
            return response

        # Verificar rate limit
        is_allowed, info = self.rate_limiter.check_limit(request)

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    'detail': f'Rate limit exceeded. Limit: {info.limit} requests per minute',
                    'limit': info.limit,
                    'remaining': 0,
                    'reset_at': int(info.reset_time)
                },
                headers={
                    **info.to_headers(),
                    'Retry-After': str(max(1, int(info.reset_time - time())))
                }
            )

        # Procesar request
        response = await call_next(request)

        # Agregar headers de rate limit a la respuesta
        for header_name, header_value in info.to_headers().items():
            response.headers[header_name] = header_value

        return response


# ============================================
# LEGACY COMPATIBILITY - RateLimiter class
# ============================================

class RateLimiter:
    """
    Rate limiter simple basado en IP (compatibilidad hacia atrás).

    DEPRECATED: Usar UserAwareRateLimiter para nuevas implementaciones.
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Inicializar rate limiter.

        Args:
            requests_per_minute: Número máximo de requests por minuto por IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)

    async def __call__(self, request: Request):
        """
        Verificar rate limit para la request.

        Args:
            request: FastAPI Request object

        Raises:
            HTTPException: Si se excede el rate limit
        """
        client_ip = request.client.host if request.client else 'unknown'
        current_time = time()
        cutoff_time = current_time - 60

        # Filtrar requests dentro del último minuto
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff_time
        ]

        # Verificar límite
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiadas peticiones. Límite: {self.requests_per_minute} requests por minuto",
                headers={"Retry-After": "60"}
            )

        # Registrar request actual
        self.requests[client_ip].append(current_time)

    def get_usage(self, client_ip: str) -> Tuple[int, int]:
        """Obtener uso actual de rate limit"""
        current_time = time()
        cutoff_time = current_time - 60

        active_requests = [
            req_time for req_time in self.requests.get(client_ip, [])
            if req_time > cutoff_time
        ]

        return (len(active_requests), self.requests_per_minute)

    def reset(self, client_ip: str = None):
        """Resetear contador de rate limit"""
        if client_ip:
            self.requests[client_ip] = []
        else:
            self.requests.clear()


# ============================================
# INSTANCIAS PRE-CONFIGURADAS
# ============================================

# Rate limiter principal (user-aware)
user_aware_limiter = UserAwareRateLimiter(
    default_limit=100,
    default_window=60,
    authenticated_limit=200
)

# Instancias legacy para compatibilidad
rate_limiter_strict = RateLimiter(requests_per_minute=30)   # Para endpoints sensibles
rate_limiter_normal = RateLimiter(requests_per_minute=60)   # Para uso general
rate_limiter_relaxed = RateLimiter(requests_per_minute=120) # Para lectura


# ============================================
# DEPENDENCY HELPERS
# ============================================

async def check_rate_limit(request: Request) -> RateLimitInfo:
    """
    Dependency para verificar rate limit y obtener info.

    Usage:
        @app.get("/endpoint")
        async def endpoint(rate_info: RateLimitInfo = Depends(check_rate_limit)):
            return {"remaining": rate_info.remaining}
    """
    return await user_aware_limiter(request)


def get_rate_limit_headers(info: RateLimitInfo) -> Dict[str, str]:
    """Obtener headers de rate limit para agregar a respuesta"""
    return info.to_headers()
