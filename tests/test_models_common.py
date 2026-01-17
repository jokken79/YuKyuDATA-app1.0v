"""
Tests para models/common.py - Modelos de respuesta API
Tests completos para APIResponse, ErrorResponse, PaginatedResponse, etc.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
import json

from models.common import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginationInfo,
    PaginationParams,
    DateRangeQuery,
    StatusResponse,
    YearFilter,
)


# ============================================
# APIResponse Tests
# ============================================

class TestAPIResponse:
    """Tests para el modelo APIResponse."""

    def test_valid_success_response(self):
        """Test respuesta exitosa valida."""
        response = APIResponse(
            success=True,
            status="success",
            data={"id": 1, "name": "Test"},
            message="Operation completed"
        )
        assert response.success is True
        assert response.status == "success"
        assert response.data == {"id": 1, "name": "Test"}
        assert response.message == "Operation completed"
        assert response.error is None

    def test_valid_error_response(self):
        """Test respuesta de error valida."""
        response = APIResponse(
            success=False,
            status="error",
            error="ValidationError",
            message="Invalid input"
        )
        assert response.success is False
        assert response.status == "error"
        assert response.error == "ValidationError"
        assert response.data is None

    def test_response_with_count(self):
        """Test respuesta con count."""
        response = APIResponse(
            success=True,
            status="success",
            data=[1, 2, 3],
            count=3
        )
        assert response.count == 3

    def test_response_with_japanese_data(self):
        """Test respuesta con datos japoneses."""
        response = APIResponse(
            success=True,
            status="success",
            data={"name": "山田太郎", "company": "株式会社ABC"},
            message="処理が完了しました"
        )
        assert response.data["name"] == "山田太郎"
        assert response.message == "処理が完了しました"

    def test_json_serialization(self):
        """Test serializacion JSON."""
        response = APIResponse(
            success=True,
            status="success",
            data={"test": "data"}
        )
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        assert parsed["data"]["test"] == "data"

    def test_missing_required_fields(self):
        """Test campos requeridos faltantes."""
        with pytest.raises(ValidationError):
            APIResponse()  # success and status are required

    def test_response_with_list_data(self):
        """Test respuesta con lista de datos."""
        employees = [
            {"id": "001", "name": "田中一郎"},
            {"id": "002", "name": "鈴木花子"},
        ]
        response = APIResponse(
            success=True,
            status="success",
            data=employees,
            count=len(employees)
        )
        assert len(response.data) == 2
        assert response.count == 2


# ============================================
# ErrorResponse Tests
# ============================================

class TestErrorResponse:
    """Tests para el modelo ErrorResponse."""

    def test_valid_error_response(self):
        """Test error response valido."""
        error = ErrorResponse(
            error="ValidationError",
            message="Field 'year' is required"
        )
        assert error.success is False
        assert error.status == "error"
        assert error.error == "ValidationError"

    def test_error_with_field_errors(self):
        """Test error con errores por campo."""
        error = ErrorResponse(
            error="ValidationError",
            message="Multiple validation errors",
            field_errors={
                "year": "Must be between 2000 and 2100",
                "employee_num": "Required field"
            }
        )
        assert error.field_errors["year"] == "Must be between 2000 and 2100"
        assert len(error.field_errors) == 2

    def test_error_with_japanese_message(self):
        """Test error con mensaje japones."""
        error = ErrorResponse(
            error="NotFound",
            message="従業員が見つかりません"
        )
        assert error.message == "従業員が見つかりません"

    def test_missing_error_field(self):
        """Test campo error faltante."""
        with pytest.raises(ValidationError):
            ErrorResponse(message="Some message")

    def test_json_serialization(self):
        """Test serializacion JSON."""
        error = ErrorResponse(
            error="ServerError",
            message="Internal error"
        )
        json_str = error.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["success"] is False
        assert parsed["error"] == "ServerError"


# ============================================
# PaginatedResponse Tests
# ============================================

class TestPaginatedResponse:
    """Tests para el modelo PaginatedResponse."""

    def test_valid_paginated_response(self):
        """Test respuesta paginada valida."""
        response = PaginatedResponse(
            success=True,
            status="success",
            data=[{"id": 1}, {"id": 2}],
            pagination={
                "page": 1,
                "limit": 50,
                "total": 150,
                "total_pages": 3
            }
        )
        assert response.pagination["page"] == 1
        assert response.pagination["total_pages"] == 3

    def test_paginated_without_pagination_info(self):
        """Test respuesta paginada sin info de paginacion."""
        response = PaginatedResponse(
            success=True,
            status="success",
            data=[]
        )
        assert response.pagination is None

    def test_inherits_from_api_response(self):
        """Test que hereda de APIResponse."""
        response = PaginatedResponse(
            success=True,
            status="success",
            data=[],
            message="Test"
        )
        assert hasattr(response, 'success')
        assert hasattr(response, 'message')


# ============================================
# PaginationInfo Tests
# ============================================

class TestPaginationInfo:
    """Tests para el modelo PaginationInfo."""

    def test_valid_pagination_info(self):
        """Test informacion de paginacion valida."""
        info = PaginationInfo(
            page=1,
            limit=50,
            total=150,
            total_pages=3,
            has_next=True,
            has_prev=False
        )
        assert info.page == 1
        assert info.has_next is True
        assert info.has_prev is False

    def test_page_must_be_positive(self):
        """Test que page debe ser >= 1."""
        with pytest.raises(ValidationError):
            PaginationInfo(
                page=0,
                limit=50,
                total=100,
                total_pages=2,
                has_next=True,
                has_prev=False
            )

    def test_limit_constraints(self):
        """Test constraints de limit."""
        # limit debe ser >= 1
        with pytest.raises(ValidationError):
            PaginationInfo(
                page=1,
                limit=0,
                total=100,
                total_pages=2,
                has_next=True,
                has_prev=False
            )

        # limit debe ser <= 500
        with pytest.raises(ValidationError):
            PaginationInfo(
                page=1,
                limit=501,
                total=100,
                total_pages=2,
                has_next=True,
                has_prev=False
            )

    def test_total_non_negative(self):
        """Test que total debe ser >= 0."""
        with pytest.raises(ValidationError):
            PaginationInfo(
                page=1,
                limit=50,
                total=-1,
                total_pages=0,
                has_next=False,
                has_prev=False
            )


# ============================================
# PaginationParams Tests
# ============================================

class TestPaginationParams:
    """Tests para el modelo PaginationParams."""

    def test_default_values(self):
        """Test valores por defecto."""
        params = PaginationParams()
        assert params.page == 1
        assert params.per_page == 20
        assert params.sort_order == "asc"

    def test_custom_values(self):
        """Test valores personalizados."""
        params = PaginationParams(
            page=2,
            per_page=50,
            sort_by="name",
            sort_order="desc"
        )
        assert params.page == 2
        assert params.per_page == 50
        assert params.sort_by == "name"
        assert params.sort_order == "desc"

    def test_page_must_be_positive(self):
        """Test que page debe ser >= 1."""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

    def test_per_page_constraints(self):
        """Test constraints de per_page."""
        # per_page debe ser >= 1
        with pytest.raises(ValidationError):
            PaginationParams(per_page=0)

        # per_page debe ser <= 100
        with pytest.raises(ValidationError):
            PaginationParams(per_page=101)

    def test_sort_order_pattern(self):
        """Test patron de sort_order."""
        # Valido: asc
        params = PaginationParams(sort_order="asc")
        assert params.sort_order == "asc"

        # Valido: desc
        params = PaginationParams(sort_order="desc")
        assert params.sort_order == "desc"

        # Invalido
        with pytest.raises(ValidationError):
            PaginationParams(sort_order="ascending")


# ============================================
# DateRangeQuery Tests
# ============================================

class TestDateRangeQuery:
    """Tests para el modelo DateRangeQuery."""

    def test_valid_date_range(self):
        """Test rango de fechas valido."""
        query = DateRangeQuery(
            start_date="2025-01-01",
            end_date="2025-12-31"
        )
        assert query.start_date == "2025-01-01"
        assert query.end_date == "2025-12-31"

    def test_invalid_date_format(self):
        """Test formato de fecha invalido."""
        # Formato incorrecto
        with pytest.raises(ValidationError):
            DateRangeQuery(
                start_date="01-01-2025",
                end_date="2025-12-31"
            )

        # Fecha invalida
        with pytest.raises(ValidationError):
            DateRangeQuery(
                start_date="2025/01/01",
                end_date="2025-12-31"
            )

    def test_missing_dates(self):
        """Test fechas faltantes."""
        with pytest.raises(ValidationError):
            DateRangeQuery(start_date="2025-01-01")

        with pytest.raises(ValidationError):
            DateRangeQuery(end_date="2025-12-31")

    def test_json_serialization(self):
        """Test serializacion JSON."""
        query = DateRangeQuery(
            start_date="2025-04-01",
            end_date="2026-03-31"
        )
        json_str = query.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["start_date"] == "2025-04-01"


# ============================================
# StatusResponse Tests
# ============================================

class TestStatusResponse:
    """Tests para el modelo StatusResponse."""

    def test_valid_status_response(self):
        """Test respuesta de estado valida."""
        response = StatusResponse(
            status="ok",
            version="5.16",
            uptime=86400.5
        )
        assert response.status == "ok"
        assert response.version == "5.16"
        assert response.uptime == 86400.5

    def test_status_with_checks(self):
        """Test estado con health checks."""
        response = StatusResponse(
            status="warning",
            checks={
                "database": "healthy",
                "disk": "warning",
                "memory": "healthy"
            }
        )
        assert response.checks["disk"] == "warning"

    def test_timestamp_default(self):
        """Test timestamp por defecto."""
        response = StatusResponse(status="ok")
        assert response.timestamp is not None
        assert isinstance(response.timestamp, datetime)

    def test_optional_fields(self):
        """Test campos opcionales."""
        response = StatusResponse(status="ok")
        assert response.version is None
        assert response.uptime is None
        assert response.checks is None


# ============================================
# YearFilter Tests
# ============================================

class TestYearFilter:
    """Tests para el modelo YearFilter."""

    def test_valid_year(self):
        """Test ano valido."""
        filter_obj = YearFilter(year=2025)
        assert filter_obj.year == 2025

    def test_year_boundary_low(self):
        """Test limite inferior del ano."""
        # Minimo valido
        filter_obj = YearFilter(year=2000)
        assert filter_obj.year == 2000

        # Por debajo del minimo
        with pytest.raises(ValidationError):
            YearFilter(year=1999)

    def test_year_boundary_high(self):
        """Test limite superior del ano."""
        # Maximo valido
        filter_obj = YearFilter(year=2100)
        assert filter_obj.year == 2100

        # Por encima del maximo
        with pytest.raises(ValidationError):
            YearFilter(year=2101)

    def test_year_must_be_integer(self):
        """Test que year debe ser entero (acepta coerción de string a int en Pydantic v2)."""
        # Pydantic v2 coerciona string numérico a int - esto es válido
        yf = YearFilter(year="2025")
        assert yf.year == 2025
        assert isinstance(yf.year, int)

        # Pero string no numérico debe fallar
        with pytest.raises(ValidationError):
            YearFilter(year="not_a_number")

        # Float tampoco es válido
        with pytest.raises(ValidationError):
            YearFilter(year=2025.5)

    def test_missing_year(self):
        """Test ano faltante."""
        with pytest.raises(ValidationError):
            YearFilter()


# ============================================
# Integration Tests
# ============================================

class TestCommonModelsIntegration:
    """Tests de integracion entre modelos comunes."""

    def test_api_response_to_dict(self):
        """Test conversion a diccionario."""
        response = APIResponse(
            success=True,
            status="success",
            data={"employees": []},
            count=0
        )
        data = response.model_dump()
        assert isinstance(data, dict)
        assert data["success"] is True

    def test_error_response_model_dump(self):
        """Test model_dump de ErrorResponse."""
        error = ErrorResponse(
            error="TestError",
            message="Test message",
            field_errors={"field1": "error1"}
        )
        data = error.model_dump()
        assert data["success"] is False
        assert data["field_errors"]["field1"] == "error1"

    def test_pagination_full_scenario(self):
        """Test escenario completo de paginacion."""
        # Simular primera pagina
        params = PaginationParams(page=1, per_page=10)
        info = PaginationInfo(
            page=params.page,
            limit=params.per_page,
            total=25,
            total_pages=3,
            has_next=True,
            has_prev=False
        )
        assert info.has_next is True
        assert info.has_prev is False

        # Simular segunda pagina
        params2 = PaginationParams(page=2, per_page=10)
        info2 = PaginationInfo(
            page=params2.page,
            limit=params2.per_page,
            total=25,
            total_pages=3,
            has_next=True,
            has_prev=True
        )
        assert info2.has_next is True
        assert info2.has_prev is True
