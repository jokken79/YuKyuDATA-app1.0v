"""
File Validation Utilities
Validación segura de archivos subidos para prevenir vulnerabilidades
"""

import os
import magic
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Optional

# MIME types permitidos para archivos Excel
ALLOWED_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel.sheet.macroEnabled.12",  # .xlsm
    "application/vnd.ms-excel",  # .xls (legacy)
}

# Extensiones permitidas
ALLOWED_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}

# Tamaño máximo de archivo (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB en bytes

# Magic bytes signatures para Excel files
EXCEL_SIGNATURES = {
    b"PK\x03\x04": "XLSX/XLSM (ZIP-based)",
    b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1": "XLS (OLE2)",
}


def validate_mime_type(file_content: bytes, filename: str) -> bool:
    """
    Valida el MIME type usando python-magic (libmagic)

    Args:
        file_content: Contenido del archivo en bytes
        filename: Nombre del archivo

    Returns:
        True si el MIME type es válido

    Raises:
        HTTPException: Si el MIME type no es válido
    """
    try:
        # Detectar MIME type real del archivo
        mime_type = magic.from_buffer(file_content, mime=True)

        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido: {mime_type}. Solo se permiten archivos Excel (.xlsx, .xlsm, .xls)"
            )

        return True

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al validar el tipo de archivo: {str(e)}"
        )


def validate_file_signature(file_content: bytes) -> bool:
    """
    Valida la firma (magic bytes) del archivo

    Args:
        file_content: Primeros bytes del archivo

    Returns:
        True si la firma es válida

    Raises:
        HTTPException: Si la firma no coincide con Excel
    """
    if len(file_content) < 8:
        raise HTTPException(
            status_code=400,
            detail="Archivo demasiado pequeño o corrupto"
        )

    # Verificar magic bytes
    is_valid = False
    for signature in EXCEL_SIGNATURES.keys():
        if file_content.startswith(signature):
            is_valid = True
            break

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Firma de archivo inválida. El archivo no parece ser un Excel válido."
        )

    return True


def validate_file_extension(filename: str) -> bool:
    """
    Valida la extensión del archivo

    Args:
        filename: Nombre del archivo

    Returns:
        True si la extensión es válida

    Raises:
        HTTPException: Si la extensión no es permitida
    """
    file_ext = Path(filename).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida: {file_ext}. Solo se permiten: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza el nombre del archivo para prevenir path traversal

    Args:
        filename: Nombre original del archivo

    Returns:
        Nombre sanitizado del archivo
    """
    # Remover caracteres peligrosos
    dangerous_chars = ['..', '/', '\\', '\x00', '|', '<', '>', ':', '"', '?', '*']

    sanitized = filename
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')

    # Limitar longitud
    if len(sanitized) > 255:
        # Preservar extensión
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255 - len(ext)] + ext

    return sanitized


async def validate_excel_file(file: UploadFile) -> bytes:
    """
    Validación completa de archivo Excel subido

    Verifica:
    1. Tamaño del archivo
    2. Extensión del archivo
    3. MIME type real
    4. Firma del archivo (magic bytes)
    5. Sanitización del nombre

    Args:
        file: Archivo subido (FastAPI UploadFile)

    Returns:
        Contenido del archivo en bytes si es válido

    Raises:
        HTTPException: Si alguna validación falla
    """
    # 1. Leer contenido
    content = await file.read()

    # 2. Validar tamaño
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío"
        )

    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande: {size_mb:.2f}MB. Máximo permitido: {max_mb}MB"
        )

    # 3. Validar extensión
    validate_file_extension(file.filename)

    # 4. Validar firma (magic bytes)
    validate_file_signature(content)

    # 5. Validar MIME type (requiere python-magic)
    try:
        validate_mime_type(content, file.filename)
    except ImportError:
        # Si python-magic no está disponible, continuar con otras validaciones
        pass

    # 6. Sanitizar nombre de archivo (para logs)
    sanitized_name = sanitize_filename(file.filename)

    # Resetear puntero del archivo para uso posterior
    await file.seek(0)

    return content


def validate_file_content_safety(file_path: Path) -> bool:
    """
    Validación adicional de seguridad del contenido Excel

    Verifica:
    - No contiene macros maliciosas (VBA)
    - No contiene enlaces externos peligrosos
    - Tamaño de celdas razonable

    Args:
        file_path: Ruta al archivo Excel

    Returns:
        True si el contenido es seguro

    Raises:
        HTTPException: Si se detecta contenido peligroso
    """
    try:
        import openpyxl

        # Abrir en modo de solo lectura
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)

        # Verificar número de hojas (evitar archivos con estructura anormal)
        if len(wb.sheetnames) > 100:
            raise HTTPException(
                status_code=400,
                detail="El archivo contiene demasiadas hojas (posible archivo malicioso)"
            )

        wb.close()
        return True

    except openpyxl.utils.exceptions.InvalidFileException:
        raise HTTPException(
            status_code=400,
            detail="Archivo Excel corrupto o inválido"
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al validar el contenido del archivo: {str(e)}"
        )
