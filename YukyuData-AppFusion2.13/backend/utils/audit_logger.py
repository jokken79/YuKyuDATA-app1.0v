"""
Audit Logger
Utilities for logging system actions and changes
"""

import functools
import logging
from typing import Optional, Any, Callable
from fastapi import Request
from datetime import datetime

# Setup logger
logger = logging.getLogger("audit")

def get_client_info(request: Request) -> dict:
    """Get client IP and user agent from request."""
    return {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }

def log_audit_action(
    request: Request,
    action: str,
    entity_type: str,
    entity_id: str = None,
    old_value: Any = None,
    new_value: Any = None,
    user: Any = None,
    additional_info: dict = None
):
    """
    Registrar manualmente una accion en el audit log.
    
    Args:
        request: FastAPI request object
        action: Tipo de accion (CREATE, UPDATE, DELETE, etc.)
        entity_type: Tipo de entidad modificada
        entity_id: ID de la entidad
        old_value: Valor anterior (para updates)
        new_value: Nuevo valor
        user: Usuario que realiza la accion (opcional, intenta obtenerlo del request)
        additional_info: Info adicional
    """
    try:
        # Intentar obtener usuario del request si no se proporciona
        if not user and hasattr(request, "state") and hasattr(request.state, "user"):
            user = request.state.user
            
        username = "anonymous"
        if user:
            if isinstance(user, dict):
                username = user.get("username", "unknown")
            elif hasattr(user, "username"):
                username = user.username
            else:
                username = str(user)
                
        # Preparar mensaje de log
        client_host = request.client.host if request.client else "unknown"
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user": username,
            "ip": client_host,
            "old_value": old_value,
            "new_value": new_value,
            "path": request.url.path,
            "method": request.method
        }
        
        if additional_info:
            log_data.update(additional_info)
            
        # Loggear como info estructurada
        logger.info(f"AUDIT: {action} {entity_type} {entity_id or ''} by {username} - {log_data}")
        
    except Exception as e:
        logger.error(f"Error logging audit action: {str(e)}")


def audit_action(
    action: str,
    entity_type: str,
    get_entity_id: Callable = None,
    get_old_value: Callable = None
):
    """
    Decorador para registrar automaticamente acciones en el audit log.
    
    Args:
        action: Tipo de accion (CREATE, UPDATE, DELETE, APPROVE, REJECT, etc.)
        entity_type: Tipo de entidad (LEAVE_REQUEST, EMPLOYEE, etc.)
        get_entity_id: Funcion lambda para obtener el ID de los argumentos: lambda kwargs: kwargs.get('id')
        get_old_value: Funcion lambda opcional para obtener valor anterior
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Ejecutar la funcion original
            result = await func(*args, **kwargs)
            
            try:
                # Obtener request de kwargs
                request = kwargs.get('request')
                if not request:
                    # Buscar request en args si es posicional (menos comun en FastAPI endpoints con Depends)
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                
                if request:
                    # Determinar Entity ID
                    entity_id = None
                    if get_entity_id:
                        try:
                            entity_id = get_entity_id(kwargs)
                        except Exception:
                            pass
                            
                    # Determinar Old Value (si aplica)
                    old_val = None
                    if get_old_value:
                        try:
                            old_val = get_old_value(kwargs)
                        except Exception:
                            pass
                    
                    # Loggear
                    log_audit_action(
                        request=request,
                        action=action,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        old_value=old_val,
                        new_value=str(result) if action in ['CREATE'] else None
                    )
            except Exception as e:
                # No fallar el request si falla el audit log
                logger.error(f"Audit decorator error: {str(e)}")
                
            return result
        return wrapper
    return decorator
