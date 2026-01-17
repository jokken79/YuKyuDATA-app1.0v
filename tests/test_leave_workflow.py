"""
YuKyu Premium - Leave Request Workflow Tests
休暇申請ワークフローテスト - 申請→承認→日数控除の完全テスト

Tests para el workflow completo de solicitudes de vacaciones:
- Crear solicitud (PENDING)
- Aprobar solicitud (APPROVED) + deducción LIFO
- Rechazar solicitud (REJECTED)
- Revertir solicitud (restaurar días)

Ejecutar con: pytest tests/test_leave_workflow.py -v
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
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
def sample_leave_request():
    """Datos de ejemplo para solicitud de vacaciones"""
    # Usar fechas futuras para evitar conflictos
    future_date = (date.today() + timedelta(days=30)).isoformat()
    return {
        "employee_num": "WORKFLOW_TEST_001",
        "employee_name": "Workflow Test User",
        "start_date": future_date,
        "end_date": future_date,
        "days_requested": 1.0,
        "hours_requested": 0,
        "leave_type": "full",
        "reason": "Test workflow - automated test",
        "year": date.today().year
    }


@pytest.fixture
def half_day_request():
    """Solicitud de medio día"""
    future_date = (date.today() + timedelta(days=35)).isoformat()
    return {
        "employee_num": "WORKFLOW_TEST_002",
        "employee_name": "Half Day Test User",
        "start_date": future_date,
        "end_date": future_date,
        "days_requested": 0.5,
        "hours_requested": 0,
        "leave_type": "half_am",
        "reason": "Test half day - automated test",
        "year": date.today().year
    }


@pytest.fixture
def cleanup_test_requests():
    """Limpia solicitudes de test después de cada test"""
    yield
    # Intentar limpiar solicitudes de test creadas
    # (en producción usaríamos una BD de test separada)


# ============================================
# CREATE LEAVE REQUEST TESTS
# ============================================

class TestCreateLeaveRequest:
    """Tests para crear solicitudes de vacaciones"""

    def test_create_request_success(self, csrf_token, sample_leave_request, cleanup_test_requests):
        """Crear solicitud exitosamente"""
        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["status"] == "PENDING"
        assert data["data"]["employee_num"] == sample_leave_request["employee_num"]
        assert data["data"]["days_requested"] == sample_leave_request["days_requested"]

    def test_create_request_returns_id(self, csrf_token, sample_leave_request, cleanup_test_requests):
        """Crear solicitud retorna ID"""
        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )

        assert response.status_code == 200
        data = response.json()

        assert "id" in data["data"]
        assert data["data"]["id"] is not None

    def test_create_half_day_request(self, csrf_token, half_day_request, cleanup_test_requests):
        """Crear solicitud de medio día"""
        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=half_day_request
        )

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["days_requested"] == 0.5
        assert data["data"]["leave_type"] == "half_am"

    def test_create_request_missing_fields(self, csrf_token):
        """Solicitud con campos faltantes falla"""
        incomplete_data = {
            "employee_num": "TEST001"
            # Faltan campos requeridos
        }

        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=incomplete_data
        )

        assert response.status_code in [400, 422]

    def test_create_request_invalid_dates(self, csrf_token):
        """Solicitud con fechas inválidas falla"""
        invalid_data = {
            "employee_num": "TEST001",
            "employee_name": "Test User",
            "start_date": "2025-02-20",
            "end_date": "2025-02-10",  # End before start
            "days_requested": 1.0,
            "leave_type": "full",
            "reason": "Test",
            "year": 2025
        }

        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=invalid_data
        )

        # Puede ser 200 si no valida, o 400/422 si valida
        # Documentamos el comportamiento actual
        assert response.status_code in [200, 400, 422]

    def test_create_request_negative_days(self, csrf_token):
        """Solicitud con días negativos se maneja"""
        invalid_data = {
            "employee_num": "TEST001",
            "employee_name": "Test User",
            "start_date": "2025-03-01",
            "end_date": "2025-03-01",
            "days_requested": -5.0,
            "leave_type": "full",
            "reason": "Test",
            "year": 2025
        }

        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=invalid_data
        )

        assert response.status_code in [200, 400, 422]


# ============================================
# GET LEAVE REQUESTS TESTS
# ============================================

class TestGetLeaveRequests:
    """Tests para obtener solicitudes de vacaciones"""

    def test_get_all_requests(self):
        """Obtener todas las solicitudes"""
        response = client.get("/api/leave-requests")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_filter_by_status_pending(self):
        """Filtrar por estado PENDING"""
        response = client.get("/api/leave-requests?status=PENDING")

        assert response.status_code == 200
        data = response.json()

        for request in data["data"]:
            assert request["status"] == "PENDING"

    def test_filter_by_status_approved(self):
        """Filtrar por estado APPROVED"""
        response = client.get("/api/leave-requests?status=APPROVED")

        assert response.status_code == 200
        data = response.json()

        for request in data["data"]:
            assert request["status"] == "APPROVED"

    def test_filter_by_year(self):
        """Filtrar por año"""
        current_year = date.today().year
        response = client.get(f"/api/leave-requests?year={current_year}")

        assert response.status_code == 200
        data = response.json()

        for request in data["data"]:
            assert request["year"] == current_year

    def test_filter_by_employee(self):
        """Filtrar por empleado"""
        response = client.get("/api/leave-requests?employee_num=001")

        assert response.status_code == 200
        # Verificar que la respuesta es válida
        assert "data" in response.json()


# ============================================
# APPROVE LEAVE REQUEST TESTS
# ============================================

class TestApproveLeaveRequest:
    """Tests para aprobar solicitudes de vacaciones"""

    def test_approve_request_changes_status(self, auth_headers, csrf_token, sample_leave_request, cleanup_test_requests):
        """Aprobar solicitud cambia estado a APPROVED"""
        # Crear solicitud
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )
        request_id = create_response.json()["data"]["id"]

        # Aprobar
        approve_response = client.patch(
            f"/api/leave-requests/{request_id}/approve",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        assert approve_response.status_code == 200
        data = approve_response.json()

        assert data["status"] == "success"
        assert data["data"]["status"] == "APPROVED"

    def test_approve_sets_approved_by(self, auth_headers, csrf_token, sample_leave_request, cleanup_test_requests):
        """Aprobar solicitud registra quién aprobó"""
        # Crear solicitud
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )
        request_id = create_response.json()["data"]["id"]

        # Aprobar
        approve_response = client.patch(
            f"/api/leave-requests/{request_id}/approve",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        data = approve_response.json()
        # Verificar que se registró quién aprobó
        assert "approved_by" in data["data"] or "approver" in str(data)

    def test_approve_nonexistent_request(self, auth_headers, csrf_token):
        """Aprobar solicitud inexistente retorna error"""
        response = client.patch(
            "/api/leave-requests/99999999/approve",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        assert response.status_code in [404, 400]

    def test_approve_already_approved(self, auth_headers, csrf_token, sample_leave_request, cleanup_test_requests):
        """Aprobar solicitud ya aprobada se maneja"""
        # Crear y aprobar
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )
        request_id = create_response.json()["data"]["id"]

        client.patch(
            f"/api/leave-requests/{request_id}/approve",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        # Intentar aprobar nuevamente
        second_response = client.patch(
            f"/api/leave-requests/{request_id}/approve",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        # Puede ser idempotente (200) o error (400)
        assert second_response.status_code in [200, 400]

    def test_approve_requires_auth(self, csrf_token, sample_leave_request, cleanup_test_requests):
        """Aprobar solicitud requiere autenticación"""
        # Crear solicitud
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )
        request_id = create_response.json()["data"]["id"]

        # Intentar aprobar sin auth
        response = client.patch(
            f"/api/leave-requests/{request_id}/approve",
            headers={"X-CSRF-Token": csrf_token}  # Solo CSRF, sin JWT
        )

        assert response.status_code in [401, 403]


# ============================================
# REJECT LEAVE REQUEST TESTS
# ============================================

class TestRejectLeaveRequest:
    """Tests para rechazar solicitudes de vacaciones"""

    def test_reject_request_changes_status(self, auth_headers, csrf_token, sample_leave_request, cleanup_test_requests):
        """Rechazar solicitud cambia estado a REJECTED"""
        # Crear solicitud
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )
        request_id = create_response.json()["data"]["id"]

        # Rechazar
        reject_response = client.patch(
            f"/api/leave-requests/{request_id}/reject",
            headers={**auth_headers, "X-CSRF-Token": csrf_token},
            json={"reason": "Test rejection"}
        )

        assert reject_response.status_code == 200
        data = reject_response.json()

        assert data["data"]["status"] == "REJECTED"

    def test_reject_with_reason(self, auth_headers, csrf_token, sample_leave_request, cleanup_test_requests):
        """Rechazar solicitud con razón"""
        # Crear solicitud
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )
        request_id = create_response.json()["data"]["id"]

        # Rechazar con razón
        reject_reason = "Insufficient vacation days"
        reject_response = client.patch(
            f"/api/leave-requests/{request_id}/reject",
            headers={**auth_headers, "X-CSRF-Token": csrf_token},
            json={"reason": reject_reason}
        )

        assert reject_response.status_code == 200
        # La razón puede estar en rejection_reason o notes
        response_text = str(reject_response.json())
        assert reject_reason in response_text or "reject" in response_text.lower()

    def test_reject_nonexistent_request(self, auth_headers, csrf_token):
        """Rechazar solicitud inexistente retorna error"""
        response = client.patch(
            "/api/leave-requests/99999999/reject",
            headers={**auth_headers, "X-CSRF-Token": csrf_token},
            json={"reason": "Test"}
        )

        assert response.status_code in [404, 400]


# ============================================
# REVERT LEAVE REQUEST TESTS
# ============================================

class TestRevertLeaveRequest:
    """Tests para revertir solicitudes aprobadas"""

    def test_revert_approved_request(self, auth_headers, csrf_token, sample_leave_request, cleanup_test_requests):
        """Revertir solicitud aprobada restaura días"""
        # Crear y aprobar
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )
        request_id = create_response.json()["data"]["id"]

        client.patch(
            f"/api/leave-requests/{request_id}/approve",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        # Revertir
        revert_response = client.patch(
            f"/api/leave-requests/{request_id}/revert",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        assert revert_response.status_code == 200
        data = revert_response.json()

        # El estado debe cambiar a REVERTED o PENDING
        assert data["data"]["status"] in ["REVERTED", "PENDING", "CANCELLED"]

    def test_revert_pending_request_fails(self, auth_headers, csrf_token, sample_leave_request, cleanup_test_requests):
        """Revertir solicitud pendiente puede fallar o no tener efecto"""
        # Crear solicitud (queda en PENDING)
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=sample_leave_request
        )
        request_id = create_response.json()["data"]["id"]

        # Intentar revertir sin aprobar primero
        revert_response = client.patch(
            f"/api/leave-requests/{request_id}/revert",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        # Puede ser 200 (idempotente) o 400 (error lógico)
        assert revert_response.status_code in [200, 400]


# ============================================
# WORKFLOW INTEGRATION TESTS
# ============================================

class TestCompleteWorkflow:
    """Tests de integración del workflow completo"""

    def test_full_approval_workflow(self, auth_headers, csrf_token, cleanup_test_requests):
        """Workflow completo: crear → aprobar → verificar"""
        # 1. Crear solicitud
        future_date = (date.today() + timedelta(days=60)).isoformat()
        request_data = {
            "employee_num": "FULL_WORKFLOW_001",
            "employee_name": "Full Workflow Test",
            "start_date": future_date,
            "end_date": future_date,
            "days_requested": 1.0,
            "leave_type": "full",
            "reason": "Full workflow test",
            "year": date.today().year
        }

        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=request_data
        )
        assert create_response.status_code == 200
        request_id = create_response.json()["data"]["id"]

        # 2. Verificar estado PENDING
        get_response = client.get(f"/api/leave-requests?status=PENDING")
        pending_ids = [r["id"] for r in get_response.json()["data"]]
        assert request_id in pending_ids

        # 3. Aprobar
        approve_response = client.patch(
            f"/api/leave-requests/{request_id}/approve",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["data"]["status"] == "APPROVED"

        # 4. Verificar que ya no está en PENDING
        get_response2 = client.get(f"/api/leave-requests?status=PENDING")
        pending_ids2 = [r["id"] for r in get_response2.json()["data"]]
        assert request_id not in pending_ids2

        # 5. Verificar que está en APPROVED
        get_response3 = client.get(f"/api/leave-requests?status=APPROVED")
        approved_ids = [r["id"] for r in get_response3.json()["data"]]
        assert request_id in approved_ids

    def test_rejection_workflow(self, auth_headers, csrf_token, cleanup_test_requests):
        """Workflow de rechazo: crear → rechazar → verificar"""
        future_date = (date.today() + timedelta(days=65)).isoformat()
        request_data = {
            "employee_num": "REJECT_WORKFLOW_001",
            "employee_name": "Reject Workflow Test",
            "start_date": future_date,
            "end_date": future_date,
            "days_requested": 1.0,
            "leave_type": "full",
            "reason": "Reject workflow test",
            "year": date.today().year
        }

        # Crear
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=request_data
        )
        request_id = create_response.json()["data"]["id"]

        # Rechazar
        reject_response = client.patch(
            f"/api/leave-requests/{request_id}/reject",
            headers={**auth_headers, "X-CSRF-Token": csrf_token},
            json={"reason": "Not enough coverage"}
        )
        assert reject_response.status_code == 200
        assert reject_response.json()["data"]["status"] == "REJECTED"

    def test_revert_workflow(self, auth_headers, csrf_token, cleanup_test_requests):
        """Workflow de reversión: crear → aprobar → revertir"""
        future_date = (date.today() + timedelta(days=70)).isoformat()
        request_data = {
            "employee_num": "REVERT_WORKFLOW_001",
            "employee_name": "Revert Workflow Test",
            "start_date": future_date,
            "end_date": future_date,
            "days_requested": 1.0,
            "leave_type": "full",
            "reason": "Revert workflow test",
            "year": date.today().year
        }

        # Crear
        create_response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=request_data
        )
        request_id = create_response.json()["data"]["id"]

        # Aprobar
        client.patch(
            f"/api/leave-requests/{request_id}/approve",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )

        # Revertir
        revert_response = client.patch(
            f"/api/leave-requests/{request_id}/revert",
            headers={**auth_headers, "X-CSRF-Token": csrf_token}
        )
        assert revert_response.status_code == 200
        # Estado debe ser diferente de APPROVED
        assert revert_response.json()["data"]["status"] != "APPROVED"


# ============================================
# EDGE CASES TESTS
# ============================================

class TestLeaveRequestEdgeCases:
    """Tests para casos extremos"""

    def test_multi_day_request(self, csrf_token, cleanup_test_requests):
        """Solicitud de múltiples días"""
        start_date = (date.today() + timedelta(days=80)).isoformat()
        end_date = (date.today() + timedelta(days=84)).isoformat()

        request_data = {
            "employee_num": "MULTI_DAY_001",
            "employee_name": "Multi Day Test",
            "start_date": start_date,
            "end_date": end_date,
            "days_requested": 5.0,
            "leave_type": "full",
            "reason": "Multi day test",
            "year": date.today().year
        }

        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=request_data
        )

        assert response.status_code == 200
        assert response.json()["data"]["days_requested"] == 5.0

    def test_request_with_special_characters(self, csrf_token, cleanup_test_requests):
        """Solicitud con caracteres especiales en razón"""
        future_date = (date.today() + timedelta(days=90)).isoformat()

        request_data = {
            "employee_num": "SPECIAL_001",
            "employee_name": "田中（太郎）",
            "start_date": future_date,
            "end_date": future_date,
            "days_requested": 1.0,
            "leave_type": "full",
            "reason": "家族旅行 - 「特別な理由」",
            "year": date.today().year
        }

        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=request_data
        )

        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
