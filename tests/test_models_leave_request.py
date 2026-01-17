"""
Tests para models/leave_request.py - Modelos de solicitudes de vacaciones
Tests completos para LeaveRequestCreate, Status enum, etc.
"""

import pytest
from pydantic import ValidationError
import json

from models.leave_request import (
    LeaveRequestStatus,
    LeaveType,
    LeaveRequestBase,
    LeaveRequestCreate,
    LeaveRequestUpdate,
    LeaveRequestResponse,
    LeaveRequestApprove,
    LeaveRequestReject,
    LeaveRequestRevert,
    LeaveRequestFilter,
    LeaveRequestListResponse,
)


# ============================================
# Enum Tests
# ============================================

class TestLeaveRequestStatus:
    """Tests para el enum LeaveRequestStatus."""

    def test_pending_status(self):
        """Test estado pendiente."""
        assert LeaveRequestStatus.PENDING.value == "PENDING"

    def test_approved_status(self):
        """Test estado aprobado."""
        assert LeaveRequestStatus.APPROVED.value == "APPROVED"

    def test_rejected_status(self):
        """Test estado rechazado."""
        assert LeaveRequestStatus.REJECTED.value == "REJECTED"

    def test_all_statuses(self):
        """Test todos los estados."""
        statuses = [s.value for s in LeaveRequestStatus]
        assert len(statuses) == 3
        assert "PENDING" in statuses
        assert "APPROVED" in statuses
        assert "REJECTED" in statuses


class TestLeaveType:
    """Tests para el enum LeaveType."""

    def test_full_day(self):
        """Test dia completo."""
        assert LeaveType.FULL.value == "full"

    def test_half_day_am(self):
        """Test medio dia manana."""
        assert LeaveType.HALF_AM.value == "half_am"

    def test_half_day_pm(self):
        """Test medio dia tarde."""
        assert LeaveType.HALF_PM.value == "half_pm"

    def test_hourly(self):
        """Test por horas."""
        assert LeaveType.HOURLY.value == "hourly"


# ============================================
# LeaveRequestBase Tests
# ============================================

class TestLeaveRequestBase:
    """Tests para el modelo LeaveRequestBase."""

    def test_valid_base(self):
        """Test base valida."""
        base = LeaveRequestBase(
            employee_num="001",
            employee_name="山田太郎",
            start_date="2025-02-01",
            end_date="2025-02-03"
        )
        assert base.employee_num == "001"
        assert base.employee_name == "山田太郎"

    def test_date_format_validation(self):
        """Test validacion de formato de fecha."""
        # Formato invalido
        with pytest.raises(ValidationError):
            LeaveRequestBase(
                employee_num="001",
                employee_name="Test",
                start_date="01-02-2025",  # Formato incorrecto
                end_date="2025-02-03"
            )

    def test_employee_num_constraints(self):
        """Test constraints de employee_num."""
        # Vacio
        with pytest.raises(ValidationError):
            LeaveRequestBase(
                employee_num="",
                employee_name="Test",
                start_date="2025-02-01",
                end_date="2025-02-03"
            )

        # Muy largo
        with pytest.raises(ValidationError):
            LeaveRequestBase(
                employee_num="a" * 21,
                employee_name="Test",
                start_date="2025-02-01",
                end_date="2025-02-03"
            )

    def test_default_leave_type(self):
        """Test tipo de licencia por defecto."""
        base = LeaveRequestBase(
            employee_num="001",
            employee_name="Test",
            start_date="2025-02-01",
            end_date="2025-02-03"
        )
        assert base.leave_type == LeaveType.FULL

    def test_reason_optional(self):
        """Test motivo opcional."""
        base = LeaveRequestBase(
            employee_num="001",
            employee_name="Test",
            start_date="2025-02-01",
            end_date="2025-02-03"
        )
        assert base.reason is None

    def test_reason_max_length(self):
        """Test longitud maxima del motivo."""
        with pytest.raises(ValidationError):
            LeaveRequestBase(
                employee_num="001",
                employee_name="Test",
                start_date="2025-02-01",
                end_date="2025-02-03",
                reason="a" * 501
            )

    def test_whitespace_stripping(self):
        """Test eliminacion de espacios."""
        base = LeaveRequestBase(
            employee_num="  001  ",
            employee_name="  山田太郎  ",
            start_date="2025-02-01",
            end_date="2025-02-03"
        )
        assert base.employee_num == "001"
        assert base.employee_name == "山田太郎"


# ============================================
# LeaveRequestCreate Tests
# ============================================

class TestLeaveRequestCreate:
    """Tests para el modelo LeaveRequestCreate."""

    def test_valid_create(self):
        """Test creacion valida."""
        request = LeaveRequestCreate(
            employee_num="001",
            employee_name="山田太郎",
            start_date="2025-02-01",
            end_date="2025-02-03",
            days_requested=3,
            leave_type="full"
        )
        assert request.days_requested == 3
        assert request.hours_requested == 0

    def test_days_requested_constraints(self):
        """Test constraints de dias solicitados."""
        # Cero valido
        request = LeaveRequestCreate(
            employee_num="001",
            employee_name="Test",
            start_date="2025-02-01",
            end_date="2025-02-01",
            days_requested=0,
            hours_requested=4,
            leave_type="hourly"
        )
        assert request.days_requested == 0

        # Maximo valido
        request = LeaveRequestCreate(
            employee_num="001",
            employee_name="Test",
            start_date="2025-02-01",
            end_date="2025-03-12",
            days_requested=40,
            leave_type="full"
        )
        assert request.days_requested == 40

        # Por encima del maximo
        with pytest.raises(ValidationError):
            LeaveRequestCreate(
                employee_num="001",
                employee_name="Test",
                start_date="2025-02-01",
                end_date="2025-03-12",
                days_requested=41,
                leave_type="full"
            )

    def test_hours_requested_constraints(self):
        """Test constraints de horas solicitadas."""
        # Maximo valido (320 horas = 40 dias * 8 horas)
        request = LeaveRequestCreate(
            employee_num="001",
            employee_name="Test",
            start_date="2025-02-01",
            end_date="2025-02-01",
            days_requested=0,
            hours_requested=320,
            leave_type="hourly"
        )
        assert request.hours_requested == 320

        # Por encima del maximo
        with pytest.raises(ValidationError):
            LeaveRequestCreate(
                employee_num="001",
                employee_name="Test",
                start_date="2025-02-01",
                end_date="2025-02-01",
                days_requested=0,
                hours_requested=321,
                leave_type="hourly"
            )

    def test_leave_type_validation(self):
        """Test validacion de tipo de licencia."""
        # Tipo valido
        for lt in ['full', 'half_am', 'half_pm', 'hourly']:
            request = LeaveRequestCreate(
                employee_num="001",
                employee_name="Test",
                start_date="2025-02-01",
                end_date="2025-02-01",
                days_requested=1,
                leave_type=lt
            )
            assert request.leave_type == lt

        # Tipo invalido
        with pytest.raises(ValidationError):
            LeaveRequestCreate(
                employee_num="001",
                employee_name="Test",
                start_date="2025-02-01",
                end_date="2025-02-01",
                days_requested=1,
                leave_type="invalid_type"
            )

    def test_date_validation_end_after_start(self):
        """Test que end_date sea posterior a start_date."""
        with pytest.raises(ValidationError):
            LeaveRequestCreate(
                employee_num="001",
                employee_name="Test",
                start_date="2025-02-10",
                end_date="2025-02-05",  # Anterior a start_date
                days_requested=1,
                leave_type="full"
            )

    def test_same_start_end_date(self):
        """Test mismo dia inicio y fin."""
        request = LeaveRequestCreate(
            employee_num="001",
            employee_name="Test",
            start_date="2025-02-10",
            end_date="2025-02-10",
            days_requested=1,
            leave_type="full"
        )
        assert request.start_date == request.end_date

    def test_half_day_request(self):
        """Test solicitud de medio dia."""
        request = LeaveRequestCreate(
            employee_num="001",
            employee_name="山田太郎",
            start_date="2025-02-10",
            end_date="2025-02-10",
            days_requested=0.5,
            leave_type="half_am"
        )
        assert request.days_requested == 0.5
        assert request.leave_type == "half_am"

    def test_json_serialization(self):
        """Test serializacion JSON."""
        request = LeaveRequestCreate(
            employee_num="001",
            employee_name="山田太郎",
            start_date="2025-02-01",
            end_date="2025-02-03",
            days_requested=3,
            leave_type="full",
            reason="家族旅行"
        )
        json_str = request.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["employee_name"] == "山田太郎"
        assert parsed["reason"] == "家族旅行"


# ============================================
# LeaveRequestUpdate Tests
# ============================================

class TestLeaveRequestUpdate:
    """Tests para el modelo LeaveRequestUpdate."""

    def test_all_fields_optional(self):
        """Test que todos los campos son opcionales."""
        update = LeaveRequestUpdate()
        assert update.start_date is None
        assert update.end_date is None
        assert update.days_requested is None

    def test_partial_update(self):
        """Test actualizacion parcial."""
        update = LeaveRequestUpdate(
            days_requested=2,
            reason="Motivo actualizado"
        )
        assert update.days_requested == 2
        assert update.reason == "Motivo actualizado"
        assert update.start_date is None

    def test_date_format_validation(self):
        """Test validacion de formato de fecha."""
        with pytest.raises(ValidationError):
            LeaveRequestUpdate(start_date="invalid-date")


# ============================================
# LeaveRequestResponse Tests
# ============================================

class TestLeaveRequestResponse:
    """Tests para el modelo LeaveRequestResponse."""

    def test_valid_response(self):
        """Test respuesta valida."""
        response = LeaveRequestResponse(
            id=1,
            employee_num="001",
            employee_name="山田太郎",
            start_date="2025-02-01",
            end_date="2025-02-03",
            days_requested=3.0,
            leave_type="full",
            status=LeaveRequestStatus.PENDING,
            year=2025
        )
        assert response.id == 1
        assert response.status == LeaveRequestStatus.PENDING

    def test_approved_response(self):
        """Test respuesta aprobada."""
        from datetime import datetime
        response = LeaveRequestResponse(
            id=1,
            employee_num="001",
            employee_name="山田太郎",
            start_date="2025-02-01",
            end_date="2025-02-03",
            days_requested=3.0,
            leave_type="full",
            status=LeaveRequestStatus.APPROVED,
            year=2025,
            approver="admin",
            approved_at=datetime.now()
        )
        assert response.status == LeaveRequestStatus.APPROVED
        assert response.approver == "admin"

    def test_rejected_response(self):
        """Test respuesta rechazada."""
        response = LeaveRequestResponse(
            id=1,
            employee_num="001",
            employee_name="山田太郎",
            start_date="2025-02-01",
            end_date="2025-02-03",
            days_requested=3.0,
            leave_type="full",
            status=LeaveRequestStatus.REJECTED,
            year=2025,
            rejection_reason="Insufficient balance"
        )
        assert response.status == LeaveRequestStatus.REJECTED
        assert response.rejection_reason == "Insufficient balance"


# ============================================
# Action Models Tests
# ============================================

class TestLeaveRequestApprove:
    """Tests para el modelo LeaveRequestApprove."""

    def test_approve_without_comment(self):
        """Test aprobacion sin comentario."""
        approve = LeaveRequestApprove()
        assert approve.approver_comment is None

    def test_approve_with_comment(self):
        """Test aprobacion con comentario."""
        approve = LeaveRequestApprove(
            approver_comment="承認しました"
        )
        assert approve.approver_comment == "承認しました"

    def test_comment_max_length(self):
        """Test longitud maxima del comentario."""
        with pytest.raises(ValidationError):
            LeaveRequestApprove(approver_comment="a" * 501)


class TestLeaveRequestReject:
    """Tests para el modelo LeaveRequestReject."""

    def test_reject_requires_reason(self):
        """Test que rechazo requiere motivo."""
        with pytest.raises(ValidationError):
            LeaveRequestReject()

    def test_reject_with_reason(self):
        """Test rechazo con motivo."""
        reject = LeaveRequestReject(
            rejection_reason="残高不足です"
        )
        assert reject.rejection_reason == "残高不足です"

    def test_reason_min_length(self):
        """Test longitud minima del motivo."""
        with pytest.raises(ValidationError):
            LeaveRequestReject(rejection_reason="")

    def test_reason_max_length(self):
        """Test longitud maxima del motivo."""
        with pytest.raises(ValidationError):
            LeaveRequestReject(rejection_reason="a" * 501)


class TestLeaveRequestRevert:
    """Tests para el modelo LeaveRequestRevert."""

    def test_revert_without_reason(self):
        """Test reversion sin motivo."""
        revert = LeaveRequestRevert()
        assert revert.revert_reason is None

    def test_revert_with_reason(self):
        """Test reversion con motivo."""
        revert = LeaveRequestRevert(
            revert_reason="社員がキャンセルしました"
        )
        assert revert.revert_reason == "社員がキャンセルしました"


# ============================================
# Filter Models Tests
# ============================================

class TestLeaveRequestFilter:
    """Tests para el modelo LeaveRequestFilter."""

    def test_empty_filter(self):
        """Test filtro vacio."""
        filter_obj = LeaveRequestFilter()
        assert filter_obj.status is None
        assert filter_obj.employee_num is None
        assert filter_obj.year is None

    def test_filter_by_status(self):
        """Test filtro por estado."""
        filter_obj = LeaveRequestFilter(status=LeaveRequestStatus.PENDING)
        assert filter_obj.status == LeaveRequestStatus.PENDING

    def test_filter_by_year(self):
        """Test filtro por ano."""
        filter_obj = LeaveRequestFilter(year=2025)
        assert filter_obj.year == 2025

        # Ano invalido
        with pytest.raises(ValidationError):
            LeaveRequestFilter(year=1999)

    def test_filter_by_date_range(self):
        """Test filtro por rango de fechas."""
        filter_obj = LeaveRequestFilter(
            start_date_from="2025-01-01",
            start_date_to="2025-12-31"
        )
        assert filter_obj.start_date_from == "2025-01-01"
        assert filter_obj.start_date_to == "2025-12-31"

    def test_date_format_validation(self):
        """Test validacion de formato de fecha."""
        with pytest.raises(ValidationError):
            LeaveRequestFilter(start_date_from="invalid-date")

    def test_multiple_filters(self):
        """Test multiples filtros."""
        filter_obj = LeaveRequestFilter(
            status=LeaveRequestStatus.APPROVED,
            year=2025,
            leave_type=LeaveType.FULL
        )
        assert filter_obj.status == LeaveRequestStatus.APPROVED
        assert filter_obj.year == 2025
        assert filter_obj.leave_type == LeaveType.FULL


# ============================================
# List Response Tests
# ============================================

class TestLeaveRequestListResponse:
    """Tests para el modelo LeaveRequestListResponse."""

    def test_empty_list(self):
        """Test lista vacia."""
        response = LeaveRequestListResponse(
            data=[],
            count=0
        )
        assert response.status == "success"
        assert len(response.data) == 0
        assert response.count == 0

    def test_list_with_pending_count(self):
        """Test lista con conteo de pendientes."""
        response = LeaveRequestListResponse(
            data=[],
            count=10,
            pending_count=3
        )
        assert response.count == 10
        assert response.pending_count == 3


# ============================================
# Integration Tests
# ============================================

class TestLeaveRequestWorkflow:
    """Tests de flujo de trabajo de solicitudes."""

    def test_create_to_approve_workflow(self):
        """Test flujo crear -> aprobar."""
        # Crear solicitud
        create = LeaveRequestCreate(
            employee_num="001",
            employee_name="山田太郎",
            start_date="2025-02-10",
            end_date="2025-02-12",
            days_requested=3,
            leave_type="full",
            reason="家族旅行"
        )

        # Aprobar
        approve = LeaveRequestApprove(
            approver_comment="承認しました"
        )

        # Respuesta aprobada
        response = LeaveRequestResponse(
            id=1,
            employee_num=create.employee_num,
            employee_name=create.employee_name,
            start_date=create.start_date,
            end_date=create.end_date,
            days_requested=create.days_requested,
            leave_type=create.leave_type,
            status=LeaveRequestStatus.APPROVED,
            year=2025,
            approver="admin"
        )

        assert response.status == LeaveRequestStatus.APPROVED

    def test_create_to_reject_workflow(self):
        """Test flujo crear -> rechazar."""
        # Crear solicitud
        create = LeaveRequestCreate(
            employee_num="001",
            employee_name="山田太郎",
            start_date="2025-02-10",
            end_date="2025-03-15",
            days_requested=25,
            leave_type="full"
        )

        # Rechazar
        reject = LeaveRequestReject(
            rejection_reason="残高が不足しています"
        )

        # Respuesta rechazada
        response = LeaveRequestResponse(
            id=1,
            employee_num=create.employee_num,
            employee_name=create.employee_name,
            start_date=create.start_date,
            end_date=create.end_date,
            days_requested=create.days_requested,
            leave_type=create.leave_type,
            status=LeaveRequestStatus.REJECTED,
            year=2025,
            rejection_reason=reject.rejection_reason
        )

        assert response.status == LeaveRequestStatus.REJECTED
        assert response.rejection_reason == "残高が不足しています"
