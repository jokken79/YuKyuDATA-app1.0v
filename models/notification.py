"""
Notification Models - Schemas de notificaciones
Modelos Pydantic para el sistema de notificaciones
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class NotificationType(str, Enum):
    """Tipo de notificacion."""
    LEAVE_CREATED = "leave_created"
    LEAVE_APPROVED = "leave_approved"
    LEAVE_REJECTED = "leave_rejected"
    EXPIRING_DAYS = "expiring_days"
    COMPLIANCE_WARNING = "compliance_warning"
    SYSTEM = "system"
    INFO = "info"


class NotificationPriority(str, Enum):
    """Prioridad de la notificacion."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============================================
# BASE MODELS
# ============================================

class NotificationBase(BaseModel):
    """Campos base para notificaciones."""
    title: str = Field(..., min_length=1, max_length=200, description="Titulo")
    message: str = Field(..., min_length=1, max_length=1000, description="Mensaje")
    type: NotificationType = Field(
        NotificationType.INFO,
        description="Tipo de notificacion"
    )
    priority: NotificationPriority = Field(
        NotificationPriority.NORMAL,
        description="Prioridad"
    )

    model_config = ConfigDict(
        use_enum_values=True
    )


class NotificationCreate(NotificationBase):
    """Modelo para crear una notificacion."""
    employee_num: Optional[str] = Field(
        None,
        description="Empleado relacionado (opcional)"
    )
    link: Optional[str] = Field(
        None,
        max_length=500,
        description="URL de accion"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Fecha de expiracion"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Vacation days expiring",
                "message": "You have 5 days expiring in 30 days",
                "type": "expiring_days",
                "priority": "high",
                "employee_num": "001",
                "link": "/vacation/details"
            }
        }
    )


class NotificationResponse(BaseModel):
    """Modelo de respuesta para notificacion."""
    id: str = Field(..., description="ID de la notificacion")
    title: str = Field(..., description="Titulo")
    message: str = Field(..., description="Mensaje")
    type: str = Field(..., description="Tipo")
    priority: str = Field(..., description="Prioridad")
    employee_num: Optional[str] = Field(None, description="Empleado relacionado")
    link: Optional[str] = Field(None, description="URL de accion")
    is_read: bool = Field(False, description="Si fue leida")
    read_at: Optional[datetime] = Field(None, description="Cuando se leyo")
    created_at: datetime = Field(..., description="Fecha de creacion")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiracion")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "notif_001",
                "title": "Vacation days expiring",
                "message": "You have 5 days expiring in 30 days",
                "type": "expiring_days",
                "priority": "high",
                "employee_num": "001",
                "is_read": False,
                "created_at": "2025-01-17T10:00:00"
            }
        }
    )


# ============================================
# SETTINGS MODELS
# ============================================

class NotificationSettingsUpdate(BaseModel):
    """Modelo para actualizar configuracion de notificaciones."""
    # SMTP Settings
    smtp_host: Optional[str] = Field(None, description="Servidor SMTP")
    smtp_port: Optional[int] = Field(None, ge=1, le=65535, description="Puerto SMTP")
    smtp_user: Optional[str] = Field(None, description="Usuario SMTP")
    smtp_password: Optional[str] = Field(None, description="Password SMTP")
    smtp_from: Optional[str] = Field(None, description="Email remitente")
    smtp_from_name: Optional[str] = Field(None, description="Nombre remitente")
    email_enabled: Optional[bool] = Field(None, description="Email habilitado")

    # Slack Settings
    slack_webhook_url: Optional[str] = Field(None, description="URL webhook Slack")
    slack_channel: Optional[str] = Field(None, description="Canal Slack")
    slack_enabled: Optional[bool] = Field(None, description="Slack habilitado")

    # Notification triggers
    notify_on_leave_created: Optional[bool] = Field(
        None,
        description="Notificar al crear solicitud"
    )
    notify_on_leave_approved: Optional[bool] = Field(
        None,
        description="Notificar al aprobar"
    )
    notify_on_leave_rejected: Optional[bool] = Field(
        None,
        description="Notificar al rechazar"
    )
    notify_on_expiring_days: Optional[bool] = Field(
        None,
        description="Notificar dias por expirar"
    )
    notify_on_compliance_warning: Optional[bool] = Field(
        None,
        description="Notificar alertas de compliance"
    )

    # Recipients
    manager_emails: Optional[str] = Field(
        None,
        description="Emails de managers (separados por coma)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "email_enabled": True,
                "notify_on_leave_created": True
            }
        }
    )


class NotificationSettingsResponse(BaseModel):
    """Respuesta con configuracion actual de notificaciones."""
    email_enabled: bool = Field(False)
    slack_enabled: bool = Field(False)
    smtp_configured: bool = Field(False)
    slack_configured: bool = Field(False)
    notify_on_leave_created: bool = Field(True)
    notify_on_leave_approved: bool = Field(True)
    notify_on_leave_rejected: bool = Field(True)
    notify_on_expiring_days: bool = Field(True)
    notify_on_compliance_warning: bool = Field(True)


# ============================================
# ACTION MODELS
# ============================================

class MarkAllNotificationsReadRequest(BaseModel):
    """Request para marcar multiples notificaciones como leidas."""
    notification_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Lista de IDs de notificaciones"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "notification_ids": ["notif_001", "notif_002", "notif_003"]
            }
        }
    )


class TestEmailRequest(BaseModel):
    """Modelo para enviar email de prueba."""
    to: str = Field(
        ...,
        description="Email destinatario",
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to": "test@example.com"
            }
        }
    )


# ============================================
# LIST MODELS
# ============================================

class NotificationListResponse(BaseModel):
    """Respuesta para lista de notificaciones."""
    status: str = Field("success")
    data: List[NotificationResponse] = Field(..., description="Notificaciones")
    count: int = Field(..., description="Total")
    unread_count: int = Field(0, description="No leidas")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": [],
                "count": 10,
                "unread_count": 3
            }
        }
    )


class UnreadCountResponse(BaseModel):
    """Respuesta con conteo de no leidas."""
    unread_count: int = Field(..., ge=0, description="Notificaciones no leidas")


# Export all
__all__ = [
    'NotificationType',
    'NotificationPriority',
    'NotificationBase',
    'NotificationCreate',
    'NotificationResponse',
    'NotificationSettingsUpdate',
    'NotificationSettingsResponse',
    'MarkAllNotificationsReadRequest',
    'TestEmailRequest',
    'NotificationListResponse',
    'UnreadCountResponse',
]
