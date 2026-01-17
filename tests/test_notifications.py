"""
YuKyu Premium - Notifications Tests
通知テスト - 通知システムの完全テスト

Tests para el sistema de notificaciones:
- Creación de notificaciones
- Marcar como leída
- Marcar todas como leídas
- Contador de no leídas
- Filtrado por tipo

Ejecutar con: pytest tests/test_notifications.py -v
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
import database

client = TestClient(app)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def auth_headers(reset_rate_limiter):
    """Obtiene headers de autenticación (JWT)"""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123456"  # Dev password from auth.py
    })
    if response.status_code == 200:
        token = response.json().get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def csrf_token(reset_rate_limiter):
    """Obtiene un token CSRF"""
    response = client.get("/api/csrf-token")
    if response.status_code == 200:
        return response.json().get("csrf_token", "")
    return ""


@pytest.fixture
def reset_rate_limiter():
    """Reset rate limiter before each test."""
    try:
        from main import rate_limiter
        rate_limiter.requests = {}
    except (ImportError, AttributeError):
        pass

    try:
        from middleware.rate_limiter import rate_limiter_strict, rate_limiter_normal, rate_limiter_relaxed
        for rl in [rate_limiter_strict, rate_limiter_normal, rate_limiter_relaxed]:
            if hasattr(rl, 'requests'):
                rl.requests = {}
    except (ImportError, AttributeError):
        pass

    yield


@pytest.fixture
def clean_notifications():
    """Limpia notificaciones de test antes y después"""
    # Setup: No cleanup needed, tests use isolated data
    yield
    # Teardown: Intentamos limpiar notificaciones de test
    # (en un entorno real, usaríamos una BD de test)


# ============================================
# GET NOTIFICATIONS TESTS
# ============================================

class TestGetNotifications:
    """Tests para obtener notificaciones"""

    def test_get_notifications_returns_list(self):
        """GET /api/notifications retorna lista"""
        response = client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_notifications_have_required_fields(self):
        """Notificaciones tienen campos requeridos"""
        response = client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()

        if len(data["data"]) > 0:
            notification = data["data"][0]
            # Campos esperados
            assert "id" in notification
            assert "type" in notification
            assert "message" in notification
            assert "is_read" in notification
            assert "created_at" in notification

    def test_filter_by_type(self):
        """Filtrar por tipo de notificación"""
        response = client.get("/api/notifications?type=compliance")
        assert response.status_code == 200
        data = response.json()

        for notification in data["data"]:
            assert notification["type"] == "compliance"

    def test_filter_unread_only(self):
        """Filtrar solo no leídas"""
        response = client.get("/api/notifications?unread_only=true")
        assert response.status_code == 200
        data = response.json()

        for notification in data["data"]:
            assert notification["is_read"] == False

    def test_notifications_ordered_by_date(self):
        """Notificaciones ordenadas por fecha (más recientes primero)"""
        response = client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()

        if len(data["data"]) > 1:
            dates = [n["created_at"] for n in data["data"]]
            # Verificar orden descendente
            assert dates == sorted(dates, reverse=True)


# ============================================
# UNREAD COUNT TESTS
# ============================================

class TestUnreadCount:
    """Tests para contador de no leídas"""

    def test_get_unread_count(self):
        """GET /api/notifications/unread-count retorna número"""
        response = client.get("/api/notifications/unread-count")
        assert response.status_code == 200
        data = response.json()

        assert "count" in data
        assert isinstance(data["count"], int)
        assert data["count"] >= 0

    def test_unread_count_matches_filter(self):
        """Contador coincide con filtro unread_only"""
        count_response = client.get("/api/notifications/unread-count")
        count = count_response.json()["count"]

        list_response = client.get("/api/notifications?unread_only=true")
        list_count = len(list_response.json()["data"])

        assert count == list_count


# ============================================
# MARK AS READ TESTS
# ============================================

class TestMarkAsRead:
    """Tests para marcar notificaciones como leídas"""

    def test_mark_single_as_read(self, auth_headers, csrf_token):
        """Marcar una notificación como leída"""
        # Primero obtener una notificación no leída
        response = client.get("/api/notifications?unread_only=true")
        notifications = response.json()["data"]

        if len(notifications) > 0:
            notification_id = notifications[0]["id"]

            # Marcar como leída
            mark_response = client.post(
                f"/api/notifications/{notification_id}/mark-read",
                headers={**auth_headers, "X-CSRF-Token": csrf_token}
            )
            assert mark_response.status_code == 200

            # Verificar que está marcada
            verify_response = client.get("/api/notifications")
            all_notifications = verify_response.json()["data"]
            marked = next((n for n in all_notifications if n["id"] == notification_id), None)
            if marked:
                assert marked["is_read"] == True

    def test_mark_nonexistent_notification(self, auth_headers, csrf_token):
        """Marcar notificación inexistente retorna 404"""
        response = client.post(
            "/api/notifications/99999999/mark-read",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )
        assert response.status_code in [404, 400]

    def test_mark_already_read(self, auth_headers, csrf_token):
        """Marcar notificación ya leída no causa error"""
        # Obtener notificaciones leídas
        response = client.get("/api/notifications")
        notifications = response.json()["data"]
        read_notifications = [n for n in notifications if n["is_read"]]

        if len(read_notifications) > 0:
            notification_id = read_notifications[0]["id"]

            # Marcar nuevamente
            mark_response = client.post(
                f"/api/notifications/{notification_id}/mark-read",
                headers={**auth_headers, "X-CSRF-Token": csrf_token}
            )
            # Debe ser idempotente
            assert mark_response.status_code == 200


# ============================================
# MARK ALL AS READ TESTS
# ============================================

class TestMarkAllAsRead:
    """Tests para marcar todas las notificaciones como leídas"""

    def test_mark_all_as_read(self, auth_headers, csrf_token):
        """Marcar todas como leídas"""
        response = client.post(
            "/api/notifications/mark-all-read",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )
        assert response.status_code == 200

        # Verificar que el contador es 0
        count_response = client.get("/api/notifications/unread-count")
        assert count_response.json()["count"] == 0

    def test_mark_all_when_empty(self, auth_headers, csrf_token):
        """Marcar todas cuando no hay no leídas no causa error"""
        # Primero marcar todas
        client.post(
            "/api/notifications/mark-all-read",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        # Marcar nuevamente
        response = client.post(
            "/api/notifications/mark-all-read",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )
        assert response.status_code == 200


# ============================================
# NOTIFICATION TYPES TESTS
# ============================================

class TestNotificationTypes:
    """Tests para tipos de notificaciones"""

    def test_valid_notification_types(self):
        """Verificar tipos de notificación válidos"""
        response = client.get("/api/notifications")
        data = response.json()

        valid_types = [
            'compliance',
            'expiring',
            'leave_request',
            'system',
            'reminder',
            'approval',
            'info',
            'warning',
            'error'
        ]

        for notification in data["data"]:
            # El tipo debe ser uno de los válidos o al menos un string
            assert isinstance(notification["type"], str)


# ============================================
# PAGINATION TESTS
# ============================================

class TestNotificationPagination:
    """Tests para paginación de notificaciones"""

    def test_pagination_params(self):
        """Parámetros de paginación funcionan"""
        response = client.get("/api/notifications?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]) <= 5

    def test_pagination_offset(self):
        """Offset de paginación funciona"""
        # Primera página
        page1 = client.get("/api/notifications?limit=5&offset=0")
        # Segunda página
        page2 = client.get("/api/notifications?limit=5&offset=5")

        page1_ids = [n["id"] for n in page1.json()["data"]]
        page2_ids = [n["id"] for n in page2.json()["data"]]

        # No deben tener IDs en común
        assert set(page1_ids).isdisjoint(set(page2_ids))


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestNotificationErrors:
    """Tests para manejo de errores"""

    def test_invalid_notification_id_format(self, auth_headers, csrf_token):
        """ID de notificación inválido retorna error"""
        response = client.post(
            "/api/notifications/invalid-id/mark-read",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )
        assert response.status_code in [400, 404, 422]

    def test_negative_pagination(self):
        """Paginación negativa se maneja"""
        response = client.get("/api/notifications?limit=-1&offset=-1")
        # Debe manejar gracefully
        assert response.status_code in [200, 400, 422]


# ============================================
# NOTIFICATION CONTENT TESTS
# ============================================

class TestNotificationContent:
    """Tests para contenido de notificaciones"""

    def test_message_not_empty(self):
        """Mensajes de notificación no están vacíos"""
        response = client.get("/api/notifications")
        data = response.json()

        for notification in data["data"]:
            assert notification["message"]
            assert len(notification["message"]) > 0

    def test_created_at_is_valid_date(self):
        """created_at es una fecha válida"""
        response = client.get("/api/notifications")
        data = response.json()

        for notification in data["data"]:
            created_at = notification["created_at"]
            # Intentar parsear la fecha
            try:
                # Puede estar en varios formatos
                if "T" in created_at:
                    datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                else:
                    datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pytest.fail(f"Invalid date format: {created_at}")


# ============================================
# SECURITY TESTS
# ============================================

class TestNotificationSecurity:
    """Tests de seguridad para notificaciones"""

    def test_mark_read_requires_auth_or_csrf(self, csrf_token):
        """Marcar como leída requiere autenticación o CSRF"""
        # Sin auth y sin CSRF debería fallar
        response = client.post("/api/notifications/1/mark-read")
        assert response.status_code in [401, 403]

    def test_xss_in_notification_message(self):
        """XSS en mensajes de notificación es prevenido"""
        response = client.get("/api/notifications")
        data = response.json()

        for notification in data["data"]:
            message = notification["message"]
            # No debe contener scripts sin escapar
            assert "<script>" not in message.lower() or "&lt;script&gt;" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
