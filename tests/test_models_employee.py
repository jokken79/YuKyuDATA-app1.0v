"""
Tests para models/employee.py - Modelos de empleados
Tests completos para EmployeeUpdate, BulkUpdateRequest, etc.
"""

import pytest
from pydantic import ValidationError
import json

from models.employee import (
    EmployeeStatus,
    EmployeeType,
    EmployeeBase,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    BulkUpdateRequest,
    BulkUpdatePreview,
    BulkUpdateResult,
    EmployeeListResponse,
    EmployeeSearchRequest,
)


# ============================================
# Enum Tests
# ============================================

class TestEmployeeStatus:
    """Tests para el enum EmployeeStatus."""

    def test_active_status(self):
        """Test estado activo."""
        assert EmployeeStatus.ACTIVE == "在職中"
        assert EmployeeStatus.ACTIVE.value == "在職中"

    def test_resigned_status(self):
        """Test estado retirado."""
        assert EmployeeStatus.RESIGNED == "退職"
        assert EmployeeStatus.RESIGNED.value == "退職"

    def test_all_values(self):
        """Test todos los valores del enum."""
        values = [e.value for e in EmployeeStatus]
        assert "在職中" in values
        assert "退職" in values


class TestEmployeeType:
    """Tests para el enum EmployeeType."""

    def test_genzai_type(self):
        """Test tipo genzai (despacho)."""
        assert EmployeeType.GENZAI.value == "genzai"

    def test_ukeoi_type(self):
        """Test tipo ukeoi (contratista)."""
        assert EmployeeType.UKEOI.value == "ukeoi"

    def test_staff_type(self):
        """Test tipo staff (oficina)."""
        assert EmployeeType.STAFF.value == "staff"


# ============================================
# EmployeeBase Tests
# ============================================

class TestEmployeeBase:
    """Tests para el modelo EmployeeBase."""

    def test_valid_employee_base(self):
        """Test base de empleado valida."""
        employee = EmployeeBase(
            employee_num="001",
            name="山田太郎",
            haken="ABC株式会社"
        )
        assert employee.employee_num == "001"
        assert employee.name == "山田太郎"
        assert employee.haken == "ABC株式会社"

    def test_whitespace_stripping(self):
        """Test que se eliminan espacios en blanco."""
        employee = EmployeeBase(
            employee_num="  001  ",
            name="  山田太郎  "
        )
        assert employee.employee_num == "001"
        assert employee.name == "山田太郎"

    def test_employee_num_required(self):
        """Test que employee_num es requerido."""
        with pytest.raises(ValidationError):
            EmployeeBase(name="Test")

    def test_employee_num_min_length(self):
        """Test longitud minima de employee_num."""
        with pytest.raises(ValidationError):
            EmployeeBase(employee_num="")

    def test_employee_num_max_length(self):
        """Test longitud maxima de employee_num."""
        with pytest.raises(ValidationError):
            EmployeeBase(employee_num="a" * 21)

    def test_optional_fields(self):
        """Test campos opcionales."""
        employee = EmployeeBase(employee_num="001")
        assert employee.name is None
        assert employee.haken is None


# ============================================
# EmployeeCreate Tests
# ============================================

class TestEmployeeCreate:
    """Tests para el modelo EmployeeCreate."""

    def test_valid_employee_create(self):
        """Test creacion de empleado valida."""
        employee = EmployeeCreate(
            employee_num="001",
            name="山田太郎",
            haken="ABC Corporation",
            year=2025,
            granted=10,
            used=0
        )
        assert employee.year == 2025
        assert employee.granted == 10
        assert employee.used == 0

    def test_default_values(self):
        """Test valores por defecto."""
        employee = EmployeeCreate(
            employee_num="001",
            year=2025
        )
        assert employee.granted == 0
        assert employee.used == 0

    def test_year_constraints(self):
        """Test constraints del ano."""
        # Minimo valido
        employee = EmployeeCreate(employee_num="001", year=2000)
        assert employee.year == 2000

        # Por debajo del minimo
        with pytest.raises(ValidationError):
            EmployeeCreate(employee_num="001", year=1999)

        # Por encima del maximo
        with pytest.raises(ValidationError):
            EmployeeCreate(employee_num="001", year=2101)

    def test_granted_constraints(self):
        """Test constraints de dias otorgados."""
        # Maximo valido (40 dias)
        employee = EmployeeCreate(employee_num="001", year=2025, granted=40)
        assert employee.granted == 40

        # Por encima del maximo
        with pytest.raises(ValidationError):
            EmployeeCreate(employee_num="001", year=2025, granted=41)

        # Negativo
        with pytest.raises(ValidationError):
            EmployeeCreate(employee_num="001", year=2025, granted=-1)

    def test_used_constraints(self):
        """Test constraints de dias usados."""
        # Maximo valido
        employee = EmployeeCreate(employee_num="001", year=2025, used=40)
        assert employee.used == 40

        # Negativo
        with pytest.raises(ValidationError):
            EmployeeCreate(employee_num="001", year=2025, used=-1)

    def test_japanese_data(self):
        """Test con datos japoneses."""
        employee = EmployeeCreate(
            employee_num="EMP001",
            name="佐藤花子",
            haken="東京工場",
            year=2025,
            granted=15.5,
            used=3.5
        )
        assert employee.name == "佐藤花子"
        assert employee.haken == "東京工場"


# ============================================
# EmployeeUpdate Tests
# ============================================

class TestEmployeeUpdate:
    """Tests para el modelo EmployeeUpdate."""

    def test_valid_employee_update(self):
        """Test actualizacion de empleado valida."""
        update = EmployeeUpdate(
            name="山田次郎",
            granted=15.5,
            used=5.0
        )
        assert update.name == "山田次郎"
        assert update.granted == 15.5
        assert update.used == 5.0

    def test_all_fields_optional(self):
        """Test que todos los campos son opcionales."""
        update = EmployeeUpdate()
        assert update.name is None
        assert update.haken is None
        assert update.granted is None
        assert update.used is None

    def test_validate_limit_default(self):
        """Test valor por defecto de validate_limit."""
        update = EmployeeUpdate(granted=20)
        assert update.validate_limit is True

    def test_granted_constraints(self):
        """Test constraints de dias otorgados."""
        # Valido con decimales
        update = EmployeeUpdate(granted=10.5)
        assert update.granted == 10.5

        # Maximo valido
        update = EmployeeUpdate(granted=40)
        assert update.granted == 40

        # Por encima del maximo
        with pytest.raises(ValidationError):
            EmployeeUpdate(granted=40.1)

        # Negativo
        with pytest.raises(ValidationError):
            EmployeeUpdate(granted=-0.1)

    def test_partial_update(self):
        """Test actualizacion parcial."""
        update = EmployeeUpdate(haken="新しい工場")
        assert update.haken == "新しい工場"
        assert update.name is None
        assert update.granted is None

    def test_json_serialization(self):
        """Test serializacion JSON."""
        update = EmployeeUpdate(
            name="Test",
            granted=10.5,
            validate_limit=False
        )
        json_str = update.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["name"] == "Test"
        assert parsed["granted"] == 10.5


# ============================================
# EmployeeResponse Tests
# ============================================

class TestEmployeeResponse:
    """Tests para el modelo EmployeeResponse."""

    def test_valid_employee_response(self):
        """Test respuesta de empleado valida."""
        response = EmployeeResponse(
            id="001_2025",
            employee_num="001",
            name="山田太郎",
            haken="ABC Corporation",
            granted=15,
            used=5,
            balance=10,
            expired=0,
            usage_rate=33.33,
            year=2025
        )
        assert response.id == "001_2025"
        assert response.balance == 10
        assert response.usage_rate == 33.33

    def test_default_values(self):
        """Test valores por defecto."""
        response = EmployeeResponse(
            id="001_2025",
            employee_num="001",
            year=2025
        )
        assert response.granted == 0
        assert response.used == 0
        assert response.balance == 0
        assert response.expired == 0
        assert response.usage_rate == 0

    def test_optional_fields(self):
        """Test campos opcionales."""
        response = EmployeeResponse(
            id="001_2025",
            employee_num="001",
            year=2025
        )
        assert response.name is None
        assert response.haken is None
        assert response.created_at is None
        assert response.updated_at is None
        assert response.employee_type is None

    def test_id_format(self):
        """Test formato del ID compuesto."""
        response = EmployeeResponse(
            id="EMP001_2025",
            employee_num="EMP001",
            year=2025
        )
        assert "_" in response.id
        assert "2025" in response.id


# ============================================
# BulkUpdateRequest Tests
# ============================================

class TestBulkUpdateRequest:
    """Tests para el modelo BulkUpdateRequest."""

    def test_valid_bulk_update(self):
        """Test actualizacion masiva valida."""
        request = BulkUpdateRequest(
            employee_nums=["001", "002", "003"],
            year=2025,
            updates={"add_granted": 5}
        )
        assert len(request.employee_nums) == 3
        assert request.updates["add_granted"] == 5

    def test_employee_nums_required(self):
        """Test que employee_nums es requerido."""
        with pytest.raises(ValidationError):
            BulkUpdateRequest(
                year=2025,
                updates={"add_granted": 5}
            )

    def test_employee_nums_min_length(self):
        """Test minimo 1 empleado."""
        with pytest.raises(ValidationError):
            BulkUpdateRequest(
                employee_nums=[],
                year=2025,
                updates={"add_granted": 5}
            )

    def test_employee_nums_max_length(self):
        """Test maximo 50 empleados."""
        employees = [f"{i:03d}" for i in range(51)]
        with pytest.raises(ValidationError):
            BulkUpdateRequest(
                employee_nums=employees,
                year=2025,
                updates={"add_granted": 5}
            )

    def test_updates_required(self):
        """Test que updates es requerido."""
        with pytest.raises(ValidationError):
            BulkUpdateRequest(
                employee_nums=["001"],
                year=2025,
                updates={}
            )

    def test_updates_valid_fields(self):
        """Test campos validos en updates."""
        # Campo valido
        request = BulkUpdateRequest(
            employee_nums=["001"],
            year=2025,
            updates={"set_granted": 20}
        )
        assert request.updates["set_granted"] == 20

        # Campo invalido
        with pytest.raises(ValidationError):
            BulkUpdateRequest(
                employee_nums=["001"],
                year=2025,
                updates={"invalid_field": 10}
            )

    def test_valid_update_operations(self):
        """Test operaciones de actualizacion validas."""
        valid_updates = [
            {"add_granted": 5},
            {"add_used": 2},
            {"set_haken": "新工場"},
            {"set_granted": 15},
            {"set_used": 3}
        ]
        for upd in valid_updates:
            request = BulkUpdateRequest(
                employee_nums=["001"],
                year=2025,
                updates=upd
            )
            assert request.updates == upd

    def test_year_constraints(self):
        """Test constraints del ano."""
        with pytest.raises(ValidationError):
            BulkUpdateRequest(
                employee_nums=["001"],
                year=1999,
                updates={"add_granted": 5}
            )


# ============================================
# BulkUpdatePreview Tests
# ============================================

class TestBulkUpdatePreview:
    """Tests para el modelo BulkUpdatePreview."""

    def test_valid_preview(self):
        """Test preview valido."""
        preview = BulkUpdatePreview(
            employee_nums=["001", "002"],
            year=2025,
            updates={"set_granted": 20}
        )
        assert len(preview.employee_nums) == 2
        assert preview.year == 2025


# ============================================
# BulkUpdateResult Tests
# ============================================

class TestBulkUpdateResult:
    """Tests para el modelo BulkUpdateResult."""

    def test_successful_result(self):
        """Test resultado exitoso."""
        result = BulkUpdateResult(
            success=True,
            updated_count=5,
            failed_count=0
        )
        assert result.success is True
        assert result.updated_count == 5
        assert result.errors is None

    def test_partial_failure(self):
        """Test fallo parcial."""
        result = BulkUpdateResult(
            success=False,
            updated_count=3,
            failed_count=2,
            errors=["Employee 004 not found", "Employee 005 not found"]
        )
        assert result.success is False
        assert result.failed_count == 2
        assert len(result.errors) == 2


# ============================================
# EmployeeListResponse Tests
# ============================================

class TestEmployeeListResponse:
    """Tests para el modelo EmployeeListResponse."""

    def test_valid_list_response(self):
        """Test respuesta de lista valida."""
        employees = [
            EmployeeResponse(
                id="001_2025",
                employee_num="001",
                name="山田太郎",
                year=2025
            )
        ]
        response = EmployeeListResponse(
            data=employees,
            years=[2024, 2025],
            count=1
        )
        assert response.status == "success"
        assert len(response.data) == 1
        assert len(response.years) == 2


# ============================================
# EmployeeSearchRequest Tests
# ============================================

class TestEmployeeSearchRequest:
    """Tests para el modelo EmployeeSearchRequest."""

    def test_valid_search_request(self):
        """Test busqueda valida."""
        search = EmployeeSearchRequest(
            query="山田",
            year=2025,
            limit=50
        )
        assert search.query == "山田"
        assert search.year == 2025

    def test_query_min_length(self):
        """Test longitud minima de query."""
        with pytest.raises(ValidationError):
            EmployeeSearchRequest(query="")

    def test_query_max_length(self):
        """Test longitud maxima de query."""
        with pytest.raises(ValidationError):
            EmployeeSearchRequest(query="a" * 101)

    def test_limit_constraints(self):
        """Test constraints de limit."""
        # Minimo
        search = EmployeeSearchRequest(query="test", limit=1)
        assert search.limit == 1

        # Maximo
        search = EmployeeSearchRequest(query="test", limit=200)
        assert search.limit == 200

        # Por debajo del minimo
        with pytest.raises(ValidationError):
            EmployeeSearchRequest(query="test", limit=0)

        # Por encima del maximo
        with pytest.raises(ValidationError):
            EmployeeSearchRequest(query="test", limit=201)

    def test_default_limit(self):
        """Test limite por defecto."""
        search = EmployeeSearchRequest(query="test")
        assert search.limit == 50

    def test_optional_filters(self):
        """Test filtros opcionales."""
        search = EmployeeSearchRequest(
            query="test",
            year=2025,
            haken="工場A",
            status=EmployeeStatus.ACTIVE
        )
        assert search.haken == "工場A"
        assert search.status == EmployeeStatus.ACTIVE

    def test_japanese_search(self):
        """Test busqueda con caracteres japoneses."""
        search = EmployeeSearchRequest(
            query="田中",
            haken="東京本社"
        )
        assert search.query == "田中"
        assert search.haken == "東京本社"
