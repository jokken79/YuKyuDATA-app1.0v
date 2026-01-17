"""
Tests para models/notification.py - Modelos de notificaciones
Tests completos para NotificationSettings, etc.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
import json

from models.notification import (
    NotificationType,
    NotificationPriority,
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    MarkAllNotificationsReadRequest,
    TestEmailRequest,
    NotificationListResponse,
    UnreadCountResponse,
)


# ============================================
# Enum Tests
# ============================================

class TestNotificationType:
    """Tests para el enum NotificationType."""

    def test_leave_created(self):
        """Test tipo leave_created."""
        assert NotificationType.LEAVE_CREATED.value == "leave_created"

    def test_leave_approved(self):
        """Test tipo leave_approved."""
        assert NotificationType.LEAVE_APPROVED.value == "leave_approved"

    def test_leave_rejected(self):
        """Test tipo leave_rejected."""
        assert NotificationType.LEAVE_REJECTED.value == "leave_rejected"

    def test_expiring_days(self):
        """Test tipo expiring_days."""
        assert NotificationType.EXPIRING_DAYS.value == "expiring_days"

    def test_compliance_warning(self):
        """Test tipo compliance_warning."""
        assert NotificationType.COMPLIANCE_WARNING.value == "compliance_warning"

    def test_system(self):
        """Test tipo system."""
        assert NotificationType.SYSTEM.value == "system"

    def test_all_types(self):
        """Test todos los tipos."""
        types = [t.value for t in NotificationType]
        assert len(types) == 7
        assert "info" in types


class TestNotificationPriority:
    """Tests para el enum NotificationPriority."""

    def test_low_priority(self):
        """Test prioridad baja."""
        assert NotificationPriority.LOW.value == "low"

    def test_normal_priority(self):
        """Test prioridad normal."""
        assert NotificationPriority.NORMAL.value == "normal"

    def test_high_priority(self):
        """Test prioridad alta."""
        assert NotificationPriority.HIGH.value == "high"

    def test_urgent_priority(self):
        """Test prioridad urgente."""
        assert NotificationPriority.URGENT.value == "urgent"


# ============================================
# NotificationBase Tests
# ============================================

class TestNotificationBase:
    """Tests para el modelo NotificationBase."""

    def test_valid_base(self):
        """Test base valida."""
        notification = NotificationBase(
            title="Test Notification",
            message="This is a test message"
        )
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test message"

    def test_default_type_and_priority(self):
        """Test tipo y prioridad por defecto."""
        notification = NotificationBase(
            title="Test",
            message="Message"
        )
        assert notification.type == NotificationType.INFO
        assert notification.priority == NotificationPriority.NORMAL

    def test_title_constraints(self):
        """Test constraints del titulo."""
        # Vacio
        with pytest.raises(ValidationError):
            NotificationBase(title="", message="Test")

        # Muy largo
        with pytest.raises(ValidationError):
            NotificationBase(title="a" * 201, message="Test")

    def test_message_constraints(self):
        """Test constraints del mensaje."""
        # Vacio
        with pytest.raises(ValidationError):
            NotificationBase(title="Test", message="")

        # Muy largo
        with pytest.raises(ValidationError):
            NotificationBase(title="Test", message="a" * 1001)

    def test_japanese_content(self):
        """Test contenido japones."""
        notification = NotificationBase(
            title="有給休暇のお知らせ",
            message="山田太郎さんの有給休暇申請が承認されました。"
        )
        assert "有給休暇" in notification.title
        assert "山田太郎" in notification.message


# ============================================
# NotificationCreate Tests
# ============================================

class TestNotificationCreate:
    """Tests para el modelo NotificationCreate."""

    def test_valid_create(self):
        """Test creacion valida."""
        notification = NotificationCreate(
            title="Vacation days expiring",
            message="You have 5 days expiring in 30 days",
            type=NotificationType.EXPIRING_DAYS,
            priority=NotificationPriority.HIGH,
            employee_num="001",
            link="/vacation/details"
        )
        assert notification.employee_num == "001"
        assert notification.link == "/vacation/details"

    def test_optional_fields(self):
        """Test campos opcionales."""
        notification = NotificationCreate(
            title="Test",
            message="Message"
        )
        assert notification.employee_num is None
        assert notification.link is None
        assert notification.expires_at is None

    def test_link_max_length(self):
        """Test longitud maxima del link."""
        with pytest.raises(ValidationError):
            NotificationCreate(
                title="Test",
                message="Message",
                link="a" * 501
            )

    def test_with_expiration(self):
        """Test con fecha de expiracion."""
        notification = NotificationCreate(
            title="Temporary Notice",
            message="This expires soon",
            expires_at=datetime(2025, 3, 20)
        )
        assert notification.expires_at == datetime(2025, 3, 20)

    def test_json_serialization(self):
        """Test serializacion JSON."""
        notification = NotificationCreate(
            title="有給休暇のお知らせ",
            message="申請が承認されました",
            type=NotificationType.LEAVE_APPROVED,
            priority=NotificationPriority.NORMAL
        )
        json_str = notification.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["title"] == "有給休暇のお知らせ"


# ============================================
# NotificationResponse Tests
# ============================================

class TestNotificationResponse:
    """Tests para el modelo NotificationResponse."""

    def test_valid_response(self):
        """Test respuesta valida."""
        response = NotificationResponse(
            id="notif_001",
            title="Notification Title",
            message="Notification message",
            type="info",
            priority="normal",
            is_read=False,
            created_at=datetime.now()
        )
        assert response.id == "notif_001"
        assert response.is_read is False

    def test_read_notification(self):
        """Test notificacion leida."""
        read_at = datetime.now()
        response = NotificationResponse(
            id="notif_001",
            title="Title",
            message="Message",
            type="info",
            priority="normal",
            is_read=True,
            read_at=read_at,
            created_at=datetime.now()
        )
        assert response.is_read is True
        assert response.read_at == read_at

    def test_optional_fields(self):
        """Test campos opcionales."""
        response = NotificationResponse(
            id="notif_001",
            title="Title",
            message="Message",
            type="info",
            priority="normal",
            created_at=datetime.now()
        )
        assert response.employee_num is None
        assert response.link is None
        assert response.read_at is None
        assert response.expires_at is None


# ============================================
# NotificationSettingsUpdate Tests
# ============================================

class TestNotificationSettingsUpdate:
    """Tests para el modelo NotificationSettingsUpdate."""

    def test_all_fields_optional(self):
        """Test que todos los campos son opcionales."""
        settings = NotificationSettingsUpdate()
        assert settings.smtp_host is None
        assert settings.email_enabled is None

    def test_smtp_settings(self):
        """Test configuracion SMTP."""
        settings = NotificationSettingsUpdate(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="secret",
            smtp_from="noreply@example.com",
            smtp_from_name="YuKyu System",
            email_enabled=True
        )
        assert settings.smtp_host == "smtp.example.com"
        assert settings.smtp_port == 587
        assert settings.email_enabled is True

    def test_smtp_port_constraints(self):
        """Test constraints del puerto SMTP."""
        # Minimo valido
        settings = NotificationSettingsUpdate(smtp_port=1)
        assert settings.smtp_port == 1

        # Maximo valido
        settings = NotificationSettingsUpdate(smtp_port=65535)
        assert settings.smtp_port == 65535

        # Por debajo del minimo
        with pytest.raises(ValidationError):
            NotificationSettingsUpdate(smtp_port=0)

        # Por encima del maximo
        with pytest.raises(ValidationError):
            NotificationSettingsUpdate(smtp_port=65536)

    def test_slack_settings(self):
        """Test configuracion Slack."""
        settings = NotificationSettingsUpdate(
            slack_webhook_url="https://hooks.slack.com/services/xxx",
            slack_channel="#notifications",
            slack_enabled=True
        )
        assert settings.slack_enabled is True
        assert "#notifications" in settings.slack_channel

    def test_notification_triggers(self):
        """Test triggers de notificacion."""
        settings = NotificationSettingsUpdate(
            notify_on_leave_created=True,
            notify_on_leave_approved=True,
            notify_on_leave_rejected=True,
            notify_on_expiring_days=True,
            notify_on_compliance_warning=True
        )
        assert settings.notify_on_leave_created is True
        assert settings.notify_on_compliance_warning is True

    def test_manager_emails(self):
        """Test emails de managers."""
        settings = NotificationSettingsUpdate(
            manager_emails="manager1@example.com,manager2@example.com"
        )
        assert "manager1@example.com" in settings.manager_emails


# ============================================
# NotificationSettingsResponse Tests
# ============================================

class TestNotificationSettingsResponse:
    """Tests para el modelo NotificationSettingsResponse."""

    def test_default_values(self):
        """Test valores por defecto."""
        response = NotificationSettingsResponse()
        assert response.email_enabled is False
        assert response.slack_enabled is False
        assert response.smtp_configured is False
        assert response.slack_configured is False
        assert response.notify_on_leave_created is True
        assert response.notify_on_leave_approved is True

    def test_configured_settings(self):
        """Test configuracion establecida."""
        response = NotificationSettingsResponse(
            email_enabled=True,
            smtp_configured=True,
            notify_on_leave_created=False
        )
        assert response.email_enabled is True
        assert response.smtp_configured is True
        assert response.notify_on_leave_created is False


# ============================================
# MarkAllNotificationsReadRequest Tests
# ============================================

class TestMarkAllNotificationsReadRequest:
    """Tests para el modelo MarkAllNotificationsReadRequest."""

    def test_valid_request(self):
        """Test request valido."""
        request = MarkAllNotificationsReadRequest(
            notification_ids=["notif_001", "notif_002", "notif_003"]
        )
        assert len(request.notification_ids) == 3

    def test_notification_ids_required(self):
        """Test que notification_ids es requerido."""
        with pytest.raises(ValidationError):
            MarkAllNotificationsReadRequest()

    def test_notification_ids_min_length(self):
        """Test minimo 1 ID."""
        with pytest.raises(ValidationError):
            MarkAllNotificationsReadRequest(notification_ids=[])

    def test_single_id(self):
        """Test con un solo ID."""
        request = MarkAllNotificationsReadRequest(
            notification_ids=["notif_001"]
        )
        assert len(request.notification_ids) == 1


# ============================================
# TestEmailRequest Tests
# ============================================

class TestTestEmailRequest:
    """Tests para el modelo TestEmailRequest."""

    def test_valid_email(self):
        """Test email valido."""
        request = TestEmailRequest(to="test@example.com")
        assert request.to == "test@example.com"

    def test_invalid_email_format(self):
        """Test formato de email invalido."""
        invalid_emails = [
            "invalid",
            "invalid@",
            "@example.com",
            "invalid@.com",
            "invalid@com",
        ]
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                TestEmailRequest(to=email)

    def test_valid_email_formats(self):
        """Test formatos de email validos."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@subdomain.example.com",
        ]
        for email in valid_emails:
            request = TestEmailRequest(to=email)
            assert request.to == email


# ============================================
# NotificationListResponse Tests
# ============================================

class TestNotificationListResponse:
    """Tests para el modelo NotificationListResponse."""

    def test_empty_list(self):
        """Test lista vacia."""
        response = NotificationListResponse(
            data=[],
            count=0
        )
        assert response.status == "success"
        assert len(response.data) == 0
        assert response.unread_count == 0

    def test_list_with_unread(self):
        """Test lista con no leidas."""
        response = NotificationListResponse(
            data=[],
            count=10,
            unread_count=3
        )
        assert response.count == 10
        assert response.unread_count == 3


# ============================================
# UnreadCountResponse Tests
# ============================================

class TestUnreadCountResponse:
    """Tests para el modelo UnreadCountResponse."""

    def test_valid_count(self):
        """Test conteo valido."""
        response = UnreadCountResponse(unread_count=5)
        assert response.unread_count == 5

    def test_zero_count(self):
        """Test conteo cero."""
        response = UnreadCountResponse(unread_count=0)
        assert response.unread_count == 0

    def test_negative_count_invalid(self):
        """Test conteo negativo invalido."""
        with pytest.raises(ValidationError):
            UnreadCountResponse(unread_count=-1)


# ============================================
# Integration Tests
# ============================================

class TestNotificationWorkflow:
    """Tests de flujo de trabajo de notificaciones."""

    def test_create_and_read_notification(self):
        """Test crear y leer notificacion."""
        # Crear notificacion
        create = NotificationCreate(
            title="休暇申請の承認",
            message="山田太郎さんの休暇申請が承認されました。",
            type=NotificationType.LEAVE_APPROVED,
            priority=NotificationPriority.NORMAL,
            employee_num="001"
        )

        # Respuesta de creacion (no leida)
        response = NotificationResponse(
            id="notif_001",
            title=create.title,
            message=create.message,
            type=create.type.value,
            priority=create.priority.value,
            employee_num=create.employee_num,
            is_read=False,
            created_at=datetime.now()
        )
        assert response.is_read is False

        # Marcar como leida
        mark_read = MarkAllNotificationsReadRequest(
            notification_ids=[response.id]
        )
        assert response.id in mark_read.notification_ids

    def test_compliance_warning_notification(self):
        """Test notificacion de advertencia de compliance."""
        notification = NotificationCreate(
            title="5日取得義務警告",
            message="山田太郎さんは年度末までに2日の有給休暇を取得する必要があります。",
            type=NotificationType.COMPLIANCE_WARNING,
            priority=NotificationPriority.HIGH,
            employee_num="001",
            link="/compliance/5day"
        )
        assert notification.type == NotificationType.COMPLIANCE_WARNING
        assert notification.priority == NotificationPriority.HIGH

    def test_expiring_days_notification(self):
        """Test notificacion de dias por expirar."""
        notification = NotificationCreate(
            title="有給休暇有効期限警告",
            message="5日分の有給休暇が60日後に失効します。",
            type=NotificationType.EXPIRING_DAYS,
            priority=NotificationPriority.HIGH,
            link="/vacation/expiring"
        )
        assert notification.type == NotificationType.EXPIRING_DAYS

    def test_notification_settings_update_flow(self):
        """Test flujo de actualizacion de configuracion."""
        # Configuracion inicial vacia
        current = NotificationSettingsResponse()
        assert current.email_enabled is False

        # Actualizar configuracion
        update = NotificationSettingsUpdate(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            email_enabled=True,
            notify_on_leave_created=True,
            notify_on_compliance_warning=True
        )

        # Nueva configuracion
        new_settings = NotificationSettingsResponse(
            email_enabled=True,
            smtp_configured=True,
            notify_on_leave_created=True,
            notify_on_compliance_warning=True
        )
        assert new_settings.email_enabled is True
        assert new_settings.smtp_configured is True
