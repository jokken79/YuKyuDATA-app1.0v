"""
Tests para models/vacation.py - Modelos de vacaciones
Tests completos para UsageDetailCreate, YukyuSummary, etc.
"""

import pytest
from pydantic import ValidationError
import json

from models.vacation import (
    UsageDetailBase,
    UsageDetailCreate,
    UsageDetailUpdate,
    UsageDetailResponse,
    YukyuSummary,
    BalanceBreakdown,
    BalanceBreakdownResponse,
    MonthlySummary,
    YearlyUsageSummary,
    YukyuHistoryRecord,
)


# ============================================
# UsageDetailBase Tests
# ============================================

class TestUsageDetailBase:
    """Tests para el modelo UsageDetailBase."""

    def test_valid_base(self):
        """Test base valida."""
        detail = UsageDetailBase(
            employee_num="001",
            use_date="2025-01-20",
            days_used=1.0
        )
        assert detail.employee_num == "001"
        assert detail.use_date == "2025-01-20"
        assert detail.days_used == 1.0

    def test_employee_num_constraints(self):
        """Test constraints de employee_num."""
        # Vacio
        with pytest.raises(ValidationError):
            UsageDetailBase(
                employee_num="",
                use_date="2025-01-20",
                days_used=1.0
            )

        # Muy largo
        with pytest.raises(ValidationError):
            UsageDetailBase(
                employee_num="a" * 21,
                use_date="2025-01-20",
                days_used=1.0
            )

    def test_date_format_validation(self):
        """Test validacion de formato de fecha."""
        with pytest.raises(ValidationError):
            UsageDetailBase(
                employee_num="001",
                use_date="20-01-2025",  # Formato incorrecto
                days_used=1.0
            )

    def test_days_used_constraints(self):
        """Test constraints de dias usados."""
        # Minimo valido (0.25 = cuarto de dia)
        detail = UsageDetailBase(
            employee_num="001",
            use_date="2025-01-20",
            days_used=0.25
        )
        assert detail.days_used == 0.25

        # Maximo valido (1 dia)
        detail = UsageDetailBase(
            employee_num="001",
            use_date="2025-01-20",
            days_used=1.0
        )
        assert detail.days_used == 1.0

        # Por debajo del minimo
        with pytest.raises(ValidationError):
            UsageDetailBase(
                employee_num="001",
                use_date="2025-01-20",
                days_used=0.1
            )

        # Por encima del maximo
        with pytest.raises(ValidationError):
            UsageDetailBase(
                employee_num="001",
                use_date="2025-01-20",
                days_used=1.5
            )


# ============================================
# UsageDetailCreate Tests
# ============================================

class TestUsageDetailCreate:
    """Tests para el modelo UsageDetailCreate."""

    def test_valid_create(self):
        """Test creacion valida."""
        detail = UsageDetailCreate(
            employee_num="001",
            name="山田太郎",
            use_date="2025-01-20",
            days_used=1.0
        )
        assert detail.name == "山田太郎"
        assert detail.days_used == 1.0

    def test_name_required(self):
        """Test que name es requerido."""
        with pytest.raises(ValidationError):
            UsageDetailCreate(
                employee_num="001",
                use_date="2025-01-20",
                days_used=1.0
            )

    def test_name_constraints(self):
        """Test constraints del nombre."""
        # Vacio
        with pytest.raises(ValidationError):
            UsageDetailCreate(
                employee_num="001",
                name="",
                use_date="2025-01-20",
                days_used=1.0
            )

        # Muy largo
        with pytest.raises(ValidationError):
            UsageDetailCreate(
                employee_num="001",
                name="a" * 101,
                use_date="2025-01-20",
                days_used=1.0
            )

    def test_valid_days_used_values(self):
        """Test valores validos de dias usados."""
        valid_values = [0.25, 0.5, 0.75, 1.0]
        for value in valid_values:
            detail = UsageDetailCreate(
                employee_num="001",
                name="Test",
                use_date="2025-01-20",
                days_used=value
            )
            assert detail.days_used == value

    def test_invalid_days_used_values(self):
        """Test valores invalidos de dias usados."""
        invalid_values = [0.1, 0.3, 0.6, 0.8, 0.9]
        for value in invalid_values:
            with pytest.raises(ValidationError):
                UsageDetailCreate(
                    employee_num="001",
                    name="Test",
                    use_date="2025-01-20",
                    days_used=value
                )

    def test_half_day(self):
        """Test medio dia."""
        detail = UsageDetailCreate(
            employee_num="001",
            name="田中花子",
            use_date="2025-01-20",
            days_used=0.5
        )
        assert detail.days_used == 0.5

    def test_json_serialization(self):
        """Test serializacion JSON."""
        detail = UsageDetailCreate(
            employee_num="001",
            name="山田太郎",
            use_date="2025-01-20",
            days_used=1.0
        )
        json_str = detail.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["name"] == "山田太郎"
        assert parsed["days_used"] == 1.0


# ============================================
# UsageDetailUpdate Tests
# ============================================

class TestUsageDetailUpdate:
    """Tests para el modelo UsageDetailUpdate."""

    def test_all_fields_optional(self):
        """Test que todos los campos son opcionales."""
        update = UsageDetailUpdate()
        assert update.days_used is None
        assert update.use_date is None

    def test_partial_update(self):
        """Test actualizacion parcial."""
        update = UsageDetailUpdate(days_used=0.5)
        assert update.days_used == 0.5
        assert update.use_date is None

    def test_valid_days_used_values(self):
        """Test valores validos de dias usados."""
        for value in [0.25, 0.5, 0.75, 1.0]:
            update = UsageDetailUpdate(days_used=value)
            assert update.days_used == value

    def test_invalid_days_used_values(self):
        """Test valores invalidos de dias usados."""
        with pytest.raises(ValidationError):
            UsageDetailUpdate(days_used=0.3)

    def test_date_format_validation(self):
        """Test validacion de formato de fecha."""
        with pytest.raises(ValidationError):
            UsageDetailUpdate(use_date="invalid-date")


# ============================================
# UsageDetailResponse Tests
# ============================================

class TestUsageDetailResponse:
    """Tests para el modelo UsageDetailResponse."""

    def test_valid_response(self):
        """Test respuesta valida."""
        response = UsageDetailResponse(
            id=1,
            employee_num="001",
            name="山田太郎",
            use_date="2025-01-20",
            days_used=1.0,
            year=2025,
            month=1
        )
        assert response.id == 1
        assert response.year == 2025
        assert response.month == 1

    def test_optional_fields(self):
        """Test campos opcionales."""
        response = UsageDetailResponse(
            id=1,
            employee_num="001",
            use_date="2025-01-20",
            days_used=1.0,
            year=2025,
            month=1
        )
        assert response.name is None
        assert response.source is None
        assert response.created_at is None


# ============================================
# YukyuSummary Tests
# ============================================

class TestYukyuSummary:
    """Tests para el modelo YukyuSummary."""

    def test_valid_summary(self):
        """Test resumen valido."""
        summary = YukyuSummary(
            employee_num="001",
            name="山田太郎",
            year=2025,
            granted=15,
            used=6,
            balance=9,
            expired=0,
            usage_rate=40.0,
            compliant_5day=True
        )
        assert summary.granted == 15
        assert summary.balance == 9
        assert summary.compliant_5day is True

    def test_default_values(self):
        """Test valores por defecto."""
        summary = YukyuSummary(
            employee_num="001",
            year=2025
        )
        assert summary.granted == 0
        assert summary.used == 0
        assert summary.balance == 0
        assert summary.expired == 0
        assert summary.usage_rate == 0
        assert summary.compliant_5day is False

    def test_with_expiry_info(self):
        """Test con informacion de expiracion."""
        summary = YukyuSummary(
            employee_num="001",
            year=2025,
            granted=15,
            used=3,
            balance=12,
            days_until_expiry=90,
            compliant_5day=False
        )
        assert summary.days_until_expiry == 90

    def test_non_compliant_employee(self):
        """Test empleado que no cumple 5 dias."""
        summary = YukyuSummary(
            employee_num="001",
            name="田中一郎",
            year=2025,
            granted=12,
            used=3,
            balance=9,
            compliant_5day=False
        )
        assert summary.compliant_5day is False
        # Necesita usar 2 dias mas para cumplir


# ============================================
# BalanceBreakdown Tests
# ============================================

class TestBalanceBreakdown:
    """Tests para el modelo BalanceBreakdown."""

    def test_valid_breakdown(self):
        """Test desglose valido."""
        breakdown = BalanceBreakdown(
            grant_year=2024,
            original_granted=10,
            used_from_this_grant=5,
            remaining=5,
            expiry_date="2026-03-20",
            is_expired=False
        )
        assert breakdown.grant_year == 2024
        assert breakdown.remaining == 5
        assert breakdown.is_expired is False

    def test_expired_grant(self):
        """Test otorgamiento expirado."""
        breakdown = BalanceBreakdown(
            grant_year=2023,
            original_granted=10,
            used_from_this_grant=5,
            remaining=0,
            expiry_date="2025-03-20",
            is_expired=True
        )
        assert breakdown.is_expired is True

    def test_default_values(self):
        """Test valores por defecto."""
        breakdown = BalanceBreakdown(
            grant_year=2024,
            original_granted=10,
            remaining=10
        )
        assert breakdown.used_from_this_grant == 0
        assert breakdown.is_expired is False


# ============================================
# BalanceBreakdownResponse Tests
# ============================================

class TestBalanceBreakdownResponse:
    """Tests para el modelo BalanceBreakdownResponse."""

    def test_valid_response(self):
        """Test respuesta valida."""
        response = BalanceBreakdownResponse(
            employee_num="001",
            year=2025,
            total_balance=15,
            breakdown=[
                BalanceBreakdown(
                    grant_year=2024,
                    original_granted=10,
                    remaining=5
                ),
                BalanceBreakdown(
                    grant_year=2025,
                    original_granted=12,
                    remaining=10
                )
            ]
        )
        assert response.total_balance == 15
        assert len(response.breakdown) == 2


# ============================================
# MonthlySummary Tests
# ============================================

class TestMonthlySummary:
    """Tests para el modelo MonthlySummary."""

    def test_valid_summary(self):
        """Test resumen mensual valido."""
        summary = MonthlySummary(
            month=1,
            year=2025,
            total_days_used=45.5,
            employee_count=20,
            requests_count=25
        )
        assert summary.month == 1
        assert summary.total_days_used == 45.5

    def test_month_constraints(self):
        """Test constraints del mes."""
        # Minimo valido
        summary = MonthlySummary(month=1, year=2025)
        assert summary.month == 1

        # Maximo valido
        summary = MonthlySummary(month=12, year=2025)
        assert summary.month == 12

        # Por debajo del minimo
        with pytest.raises(ValidationError):
            MonthlySummary(month=0, year=2025)

        # Por encima del maximo
        with pytest.raises(ValidationError):
            MonthlySummary(month=13, year=2025)

    def test_default_values(self):
        """Test valores por defecto."""
        summary = MonthlySummary(month=1, year=2025)
        assert summary.total_days_used == 0
        assert summary.employee_count == 0
        assert summary.requests_count == 0


# ============================================
# YearlyUsageSummary Tests
# ============================================

class TestYearlyUsageSummary:
    """Tests para el modelo YearlyUsageSummary."""

    def test_valid_summary(self):
        """Test resumen anual valido."""
        monthly_data = [
            MonthlySummary(month=i, year=2025, total_days_used=20.0)
            for i in range(1, 13)
        ]
        summary = YearlyUsageSummary(
            year=2025,
            monthly_data=monthly_data,
            total_days_used=240.0,
            total_days_granted=500,
            overall_usage_rate=48.0
        )
        assert summary.year == 2025
        assert len(summary.monthly_data) == 12
        assert summary.overall_usage_rate == 48.0

    def test_default_values(self):
        """Test valores por defecto."""
        summary = YearlyUsageSummary(
            year=2025,
            monthly_data=[]
        )
        assert summary.total_days_used == 0
        assert summary.total_days_granted == 0
        assert summary.overall_usage_rate == 0


# ============================================
# YukyuHistoryRecord Tests
# ============================================

class TestYukyuHistoryRecord:
    """Tests para el modelo YukyuHistoryRecord."""

    def test_valid_record(self):
        """Test registro historico valido."""
        record = YukyuHistoryRecord(
            year=2024,
            granted=12,
            used=10,
            balance=2,
            expired=0,
            carried_over=2
        )
        assert record.year == 2024
        assert record.granted == 12
        assert record.carried_over == 2

    def test_default_values(self):
        """Test valores por defecto."""
        record = YukyuHistoryRecord(year=2024)
        assert record.granted == 0
        assert record.used == 0
        assert record.balance == 0
        assert record.expired == 0
        assert record.carried_over == 0

    def test_year_with_expiration(self):
        """Test ano con expiracion."""
        record = YukyuHistoryRecord(
            year=2023,
            granted=10,
            used=5,
            balance=0,
            expired=5,
            carried_over=0
        )
        assert record.expired == 5
        assert record.balance == 0


# ============================================
# Integration Tests
# ============================================

class TestVacationWorkflow:
    """Tests de flujo de trabajo de vacaciones."""

    def test_create_and_summarize(self):
        """Test crear detalle y resumir."""
        # Crear detalles de uso
        details = [
            UsageDetailCreate(
                employee_num="001",
                name="山田太郎",
                use_date="2025-01-15",
                days_used=1.0
            ),
            UsageDetailCreate(
                employee_num="001",
                name="山田太郎",
                use_date="2025-01-20",
                days_used=0.5
            ),
            UsageDetailCreate(
                employee_num="001",
                name="山田太郎",
                use_date="2025-02-10",
                days_used=1.0
            ),
        ]

        # Calcular total usado
        total_used = sum(d.days_used for d in details)
        assert total_used == 2.5

        # Crear resumen
        summary = YukyuSummary(
            employee_num="001",
            name="山田太郎",
            year=2025,
            granted=15,
            used=total_used,
            balance=15 - total_used,
            usage_rate=(total_used / 15) * 100
        )
        assert summary.balance == 12.5

    def test_lifo_deduction_scenario(self):
        """Test escenario de deduccion LIFO."""
        # Empleado con balance de 2 anos
        breakdown = BalanceBreakdownResponse(
            employee_num="001",
            year=2025,
            total_balance=18,
            breakdown=[
                BalanceBreakdown(
                    grant_year=2024,
                    original_granted=10,
                    used_from_this_grant=2,
                    remaining=8,
                    expiry_date="2026-03-20"
                ),
                BalanceBreakdown(
                    grant_year=2025,
                    original_granted=12,
                    used_from_this_grant=2,
                    remaining=10,
                    expiry_date="2027-03-20"
                )
            ]
        )

        # LIFO: usar primero los mas nuevos (2025)
        # Si solicita 5 dias, se deducen del 2025
        assert breakdown.breakdown[1].remaining == 10  # 2025 tiene 10 disponibles

    def test_yearly_history(self):
        """Test historial anual."""
        history = [
            YukyuHistoryRecord(
                year=2022,
                granted=10,
                used=8,
                balance=2,
                carried_over=2
            ),
            YukyuHistoryRecord(
                year=2023,
                granted=11,
                used=10,
                balance=3,
                expired=0,
                carried_over=3
            ),
            YukyuHistoryRecord(
                year=2024,
                granted=12,
                used=7,
                balance=8,
                expired=0,
                carried_over=8
            ),
        ]

        # El empleado ha ido acumulando balance
        total_granted = sum(h.granted for h in history)
        total_used = sum(h.used for h in history)
        assert total_granted == 33
        assert total_used == 25
