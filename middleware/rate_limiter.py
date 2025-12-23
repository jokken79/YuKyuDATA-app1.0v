"""
Rate Limiter Middleware
Limitador de tasa de requests para prevenir abuso
"""

from collections import defaultdict
from time import time
from fastapi import Request, HTTPException, status
from typing import Dict, Tuple


class RateLimiter:
    """
    Rate limiter simple basado en IP

    En producción, usar Redis o similar para rate limiting distribuido
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Inicializar rate limiter

        Args:
            requests_per_minute: Número máximo de requests por minuto por IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)

    async def __call__(self, request: Request):
        """
        Verificar rate limit para la request

        Args:
            request: FastAPI Request object

        Raises:
            HTTPException: Si se excede el rate limit
        """
        # Obtener IP del cliente
        client_ip = request.client.host

        # Obtener timestamp actual
        current_time = time()

        # Limpiar requests antiguas (más de 1 minuto)
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
        """
        Obtener uso actual de rate limit

        Args:
            client_ip: IP del cliente

        Returns:
            Tupla (requests_usadas, límite)
        """
        current_time = time()
        cutoff_time = current_time - 60

        active_requests = [
            req_time for req_time in self.requests.get(client_ip, [])
            if req_time > cutoff_time
        ]

        return (len(active_requests), self.requests_per_minute)

    def reset(self, client_ip: str = None):
        """
        Resetear contador de rate limit

        Args:
            client_ip: IP específica a resetear (None = todas)
        """
        if client_ip:
            self.requests[client_ip] = []
        else:
            self.requests.clear()


# Instancias de rate limiter con diferentes límites
rate_limiter_strict = RateLimiter(requests_per_minute=30)  # Para endpoints sensibles
rate_limiter_normal = RateLimiter(requests_per_minute=60)  # Para uso general
rate_limiter_relaxed = RateLimiter(requests_per_minute=120)  # Para lectura
