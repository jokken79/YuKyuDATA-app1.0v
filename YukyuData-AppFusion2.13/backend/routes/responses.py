"""
Standardized API Response Models and Helpers
Modelos y funciones auxiliares para respuestas API estandarizadas

Este modulo proporciona un formato consistente para todas las respuestas API:
- success: bool - Indica si la operacion fue exitosa
- data: Any - Datos de la respuesta (opcional)
- message: str - Mensaje descriptivo (opcional)
- error: str - Descripcion del error (solo cuando success=False)

Uso:
    from routes.responses import success_response, error_response, APIResponse

    # Respuesta exitosa con datos
    return success_response(data={"employees": employees}, message="Data retrieved")

    # Respuesta de error
    return error_response(error="Invalid input", message="El campo 'year' es requerido")
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional, Dict, List, Union
from fastapi.responses import JSONResponse


class APIResponse(BaseModel):
    """
    Modelo estandarizado de respuesta API.

    Attributes:
        success: Indica si la operacion fue exitosa
        status: String "success" o "error" (para compatibilidad con frontend)
        data: Datos de la respuesta (puede ser dict, list, etc.)
        message: Mensaje descriptivo opcional
        error: Descripcion del error (solo cuando success=False)
        count: Numero de items (opcional, para listas)
    """
    success: bool = Field(..., description="Indica si la operacion fue exitosa")
    status: str = Field(..., description="'success' o 'error' para compatibilidad")
    data: Optional[Any] = Field(None, description="Datos de la respuesta")
    message: Optional[str] = Field(None, description="Mensaje descriptivo")
    error: Optional[str] = Field(None, description="Descripcion del error")
    count: Optional[int] = Field(None, description="Numero de items en data (si es lista)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "status": "success",
                    "data": {"id": 1, "name": "Test"},
                    "message": "Operation completed successfully"
                },
                {
                    "success": False,
                    "status": "error",
                    "error": "ValidationError",
                    "message": "Invalid input data"
                }
            ]
        }
    )


class PaginatedResponse(APIResponse):
    """
    Modelo de respuesta paginada.

    Extiende APIResponse con informacion de paginacion.
    """
    pagination: Optional[Dict[str, int]] = Field(
        None,
        description="Informacion de paginacion",
        json_schema_extra={
            "example": {
                "page": 1,
                "limit": 50,
                "total": 150,
                "total_pages": 3
            }
        }
    )


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    count: Optional[int] = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    Crea una respuesta exitosa estandarizada.

    Args:
        data: Datos a incluir en la respuesta
        message: Mensaje descriptivo opcional
        count: Numero de items (se calcula automaticamente si data es lista)
        **extra_fields: Campos adicionales a incluir en la respuesta

    Returns:
        Dict con formato estandarizado:
        {
            "success": True,
            "status": "success",
            "data": ...,
            "message": ...,
            "count": ...
        }

    Examples:
        >>> success_response(data={"id": 1})
        {"success": True, "status": "success", "data": {"id": 1}}

        >>> success_response(data=employees, message="Employees retrieved")
        {"success": True, "status": "success", "data": [...], "message": "...", "count": 10}
    """
    response = {
        "success": True,
        "status": "success"
    }

    if data is not None:
        response["data"] = data
        # Auto-calculate count if data is a list
        if count is None and isinstance(data, (list, tuple)):
            response["count"] = len(data)
        elif count is not None:
            response["count"] = count

    if message:
        response["message"] = message

    # Add any extra fields
    response.update(extra_fields)

    return response


def error_response(
    error: str,
    message: Optional[str] = None,
    status_code: int = 400,
    **extra_fields
) -> Dict[str, Any]:
    """
    Crea una respuesta de error estandarizada.

    Args:
        error: Codigo o tipo de error (ej: "ValidationError", "NotFound")
        message: Mensaje descriptivo del error
        status_code: Codigo HTTP (no se incluye en la respuesta, solo para referencia)
        **extra_fields: Campos adicionales (ej: field_errors para validacion)

    Returns:
        Dict con formato estandarizado:
        {
            "success": False,
            "status": "error",
            "error": ...,
            "message": ...
        }

    Examples:
        >>> error_response(error="NotFound", message="Employee not found")
        {"success": False, "status": "error", "error": "NotFound", "message": "..."}

        >>> error_response(
        ...     error="ValidationError",
        ...     message="Invalid input",
        ...     field_errors={"year": "Must be between 2000 and 2100"}
        ... )
    """
    response = {
        "success": False,
        "status": "error",
        "error": error
    }

    if message:
        response["message"] = message

    # Add any extra fields
    response.update(extra_fields)

    return response


def paginated_response(
    data: List[Any],
    page: int,
    limit: int,
    total: int,
    message: Optional[str] = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    Crea una respuesta paginada estandarizada.

    Args:
        data: Lista de items para la pagina actual
        page: Numero de pagina actual (1-indexed)
        limit: Items por pagina
        total: Total de items en todas las paginas
        message: Mensaje descriptivo opcional
        **extra_fields: Campos adicionales

    Returns:
        Dict con formato estandarizado incluyendo paginacion:
        {
            "success": True,
            "status": "success",
            "data": [...],
            "count": ...,
            "pagination": {
                "page": 1,
                "limit": 50,
                "total": 150,
                "total_pages": 3
            }
        }

    Example:
        >>> paginated_response(
        ...     data=employees[0:50],
        ...     page=1,
        ...     limit=50,
        ...     total=150
        ... )
    """
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    response = {
        "success": True,
        "status": "success",
        "data": data,
        "count": len(data),
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }

    if message:
        response["message"] = message

    response.update(extra_fields)

    return response


def created_response(
    data: Any = None,
    message: str = "Resource created successfully",
    resource_id: Optional[Union[int, str]] = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    Crea una respuesta para recursos recien creados.

    Args:
        data: Datos del recurso creado
        message: Mensaje de confirmacion
        resource_id: ID del recurso creado
        **extra_fields: Campos adicionales

    Returns:
        Dict con formato estandarizado para creacion

    Example:
        >>> created_response(
        ...     data=new_employee,
        ...     resource_id=123,
        ...     message="Employee created"
        ... )
    """
    response = success_response(data=data, message=message, **extra_fields)

    if resource_id is not None:
        response["id"] = resource_id

    return response


def updated_response(
    data: Any = None,
    message: str = "Resource updated successfully",
    **extra_fields
) -> Dict[str, Any]:
    """
    Crea una respuesta para recursos actualizados.

    Args:
        data: Datos actualizados del recurso
        message: Mensaje de confirmacion
        **extra_fields: Campos adicionales

    Returns:
        Dict con formato estandarizado para actualizacion
    """
    return success_response(data=data, message=message, **extra_fields)


def deleted_response(
    message: str = "Resource deleted successfully",
    resource_id: Optional[Union[int, str]] = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    Crea una respuesta para recursos eliminados.

    Args:
        message: Mensaje de confirmacion
        resource_id: ID del recurso eliminado
        **extra_fields: Campos adicionales

    Returns:
        Dict con formato estandarizado para eliminacion
    """
    response = success_response(message=message, **extra_fields)

    if resource_id is not None:
        response["deleted_id"] = resource_id

    return response


# Funciones auxiliares para casos comunes

def not_found_response(
    resource_type: str = "Resource",
    resource_id: Optional[Union[int, str]] = None
) -> Dict[str, Any]:
    """
    Crea una respuesta para recursos no encontrados.

    Args:
        resource_type: Tipo de recurso (ej: "Employee", "Request")
        resource_id: ID del recurso buscado

    Returns:
        Dict con formato de error para not found
    """
    message = f"{resource_type} not found"
    if resource_id is not None:
        message = f"{resource_type} with ID '{resource_id}' not found"

    return error_response(
        error="NotFound",
        message=message
    )


def validation_error_response(
    message: str = "Validation failed",
    field_errors: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Crea una respuesta para errores de validacion.

    Args:
        message: Mensaje general del error
        field_errors: Dict con errores por campo

    Returns:
        Dict con formato de error de validacion
    """
    response = error_response(
        error="ValidationError",
        message=message
    )

    if field_errors:
        response["field_errors"] = field_errors

    return response


def unauthorized_response(
    message: str = "Authentication required"
) -> Dict[str, Any]:
    """
    Crea una respuesta para errores de autenticacion.
    """
    return error_response(
        error="Unauthorized",
        message=message
    )


def forbidden_response(
    message: str = "Permission denied"
) -> Dict[str, Any]:
    """
    Crea una respuesta para errores de autorizacion.
    """
    return error_response(
        error="Forbidden",
        message=message
    )


# Re-export for easy importing
__all__ = [
    # Models
    'APIResponse',
    'PaginatedResponse',
    # Success responses
    'success_response',
    'paginated_response',
    'created_response',
    'updated_response',
    'deleted_response',
    # Error responses
    'error_response',
    'not_found_response',
    'validation_error_response',
    'unauthorized_response',
    'forbidden_response',
]
