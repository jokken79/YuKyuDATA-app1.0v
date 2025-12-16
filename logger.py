"""
Sistema de logging centralizado para YuKyuDATA-app

Características:
- Logs rotativos (máximo 10MB, 5 backups)
- Formato consistente con timestamps
- Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Crear directorio de logs si no existe
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)


def setup_logger(name: str = 'yukyu') -> logging.Logger:
    """
    Configura y retorna un logger con handlers para archivo y consola.

    Args:
        name: Nombre del logger

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Evitar duplicar handlers si ya existe
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Formato detallado
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para archivo (rotativo, max 10MB, 5 backups)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Handler para errores (archivo separado)
    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'error.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # Handler para consola (solo warnings y errores)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    console_handler.setLevel(logging.WARNING)

    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger


# Logger global para importar en otros módulos
logger = setup_logger()


# Funciones de conveniencia
def log_api_request(method: str, path: str, status: int, duration_ms: float = None):
    """Log de request API"""
    msg = f"API {method} {path} -> {status}"
    if duration_ms:
        msg += f" ({duration_ms:.2f}ms)"
    logger.info(msg)


def log_db_operation(operation: str, table: str, count: int = None, details: str = None):
    """Log de operación de base de datos"""
    msg = f"DB {operation} on {table}"
    if count is not None:
        msg += f" ({count} rows)"
    if details:
        msg += f" - {details}"
    logger.info(msg)


def log_sync_event(source: str, records: int, status: str = "success"):
    """Log de evento de sincronización"""
    logger.info(f"SYNC {source}: {records} records - {status}")


def log_leave_request(action: str, request_id: int, employee: str, details: str = None):
    """Log de solicitud de vacaciones"""
    msg = f"LEAVE_REQUEST {action}: ID={request_id}, Employee={employee}"
    if details:
        msg += f" - {details}"
    logger.info(msg)


def log_fiscal_event(event: str, year: int, details: str = None):
    """Log de evento de año fiscal"""
    msg = f"FISCAL {event}: Year={year}"
    if details:
        msg += f" - {details}"
    logger.info(msg)
