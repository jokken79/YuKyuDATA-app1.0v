"""
Tests for standardized API response helpers
Tests para los helpers de respuesta API estandarizados
"""

import pytest
from routes.responses import (
    APIResponse,
    PaginatedResponse,
    success_response,
    error_response,
    paginated_response,
    created_response,
    updated_response,
    deleted_response,
    not_found_response,
    validation_error_response,
    unauthorized_response,
    forbidden_response,
)


class TestSuccessResponse:
    """Tests for success_response helper"""

    def test_basic_success_response(self):
        """Test basic success response without data"""
        result = success_response()
        assert result["success"] is True
        assert result["status"] == "success"
        assert "data" not in result
        assert "message" not in result

    def test_success_with_data(self):
        """Test success response with data"""
        data = {"id": 1, "name": "Test"}
        result = success_response(data=data)
        assert result["success"] is True
        assert result["status"] == "success"
        assert result["data"] == data

    def test_success_with_message(self):
        """Test success response with message"""
        result = success_response(message="Operation completed")
        assert result["message"] == "Operation completed"

    def test_success_auto_count_for_list(self):
        """Test that count is auto-calculated for list data"""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = success_response(data=data)
        assert result["count"] == 3

    def test_success_explicit_count(self):
        """Test explicit count parameter"""
        data = [{"id": 1}]
        result = success_response(data=data, count=100)
        assert result["count"] == 100

    def test_success_with_extra_fields(self):
        """Test success response with extra fields"""
        result = success_response(
            data={"id": 1},
            message="Created",
            year=2025,
            custom_field="value"
        )
        assert result["year"] == 2025
        assert result["custom_field"] == "value"


class TestErrorResponse:
    """Tests for error_response helper"""

    def test_basic_error_response(self):
        """Test basic error response"""
        result = error_response(error="TestError")
        assert result["success"] is False
        assert result["status"] == "error"
        assert result["error"] == "TestError"

    def test_error_with_message(self):
        """Test error response with message"""
        result = error_response(error="ValidationError", message="Invalid input")
        assert result["error"] == "ValidationError"
        assert result["message"] == "Invalid input"

    def test_error_with_extra_fields(self):
        """Test error response with extra fields"""
        result = error_response(
            error="ValidationError",
            message="Invalid input",
            field_errors={"name": "Required"}
        )
        assert result["field_errors"] == {"name": "Required"}


class TestPaginatedResponse:
    """Tests for paginated_response helper"""

    def test_basic_pagination(self):
        """Test basic paginated response"""
        data = [{"id": i} for i in range(10)]
        result = paginated_response(
            data=data,
            page=1,
            limit=10,
            total=50
        )
        assert result["success"] is True
        assert result["status"] == "success"
        assert result["count"] == 10
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["limit"] == 10
        assert result["pagination"]["total"] == 50
        assert result["pagination"]["total_pages"] == 5

    def test_pagination_total_pages_calculation(self):
        """Test that total_pages is calculated correctly"""
        result = paginated_response(
            data=[],
            page=1,
            limit=10,
            total=25
        )
        assert result["pagination"]["total_pages"] == 3

    def test_pagination_with_message(self):
        """Test paginated response with message"""
        result = paginated_response(
            data=[],
            page=1,
            limit=10,
            total=0,
            message="No results found"
        )
        assert result["message"] == "No results found"


class TestCRUDResponses:
    """Tests for CRUD-specific response helpers"""

    def test_created_response(self):
        """Test created response"""
        result = created_response(
            data={"id": 123, "name": "New Item"},
            resource_id=123
        )
        assert result["success"] is True
        assert result["id"] == 123
        assert "Resource created successfully" in result["message"]

    def test_created_response_custom_message(self):
        """Test created response with custom message"""
        result = created_response(
            data={"id": 1},
            message="Employee created"
        )
        assert result["message"] == "Employee created"

    def test_updated_response(self):
        """Test updated response"""
        result = updated_response(data={"id": 1, "name": "Updated"})
        assert result["success"] is True
        assert "updated successfully" in result["message"]

    def test_deleted_response(self):
        """Test deleted response"""
        result = deleted_response(resource_id=123)
        assert result["success"] is True
        assert result["deleted_id"] == 123
        assert "deleted successfully" in result["message"]


class TestErrorHelpers:
    """Tests for specific error response helpers"""

    def test_not_found_response(self):
        """Test not found response"""
        result = not_found_response(resource_type="Employee", resource_id=123)
        assert result["success"] is False
        assert result["error"] == "NotFound"
        assert "Employee" in result["message"]
        assert "123" in result["message"]

    def test_not_found_response_no_id(self):
        """Test not found response without ID"""
        result = not_found_response(resource_type="Employee")
        assert "Employee not found" in result["message"]

    def test_validation_error_response(self):
        """Test validation error response"""
        result = validation_error_response(
            message="Invalid data",
            field_errors={"email": "Invalid format", "name": "Required"}
        )
        assert result["success"] is False
        assert result["error"] == "ValidationError"
        assert result["field_errors"]["email"] == "Invalid format"

    def test_unauthorized_response(self):
        """Test unauthorized response"""
        result = unauthorized_response()
        assert result["success"] is False
        assert result["error"] == "Unauthorized"

    def test_forbidden_response(self):
        """Test forbidden response"""
        result = forbidden_response(message="Admin access required")
        assert result["success"] is False
        assert result["error"] == "Forbidden"
        assert result["message"] == "Admin access required"


class TestAPIResponseModel:
    """Tests for Pydantic APIResponse model"""

    def test_api_response_validation(self):
        """Test that APIResponse validates correctly"""
        response = APIResponse(
            success=True,
            status="success",
            data={"id": 1},
            message="Test"
        )
        assert response.success is True
        assert response.status == "success"

    def test_api_response_error_validation(self):
        """Test APIResponse for error case"""
        response = APIResponse(
            success=False,
            status="error",
            error="TestError",
            message="Something went wrong"
        )
        assert response.success is False
        assert response.error == "TestError"


class TestBackwardsCompatibility:
    """Tests to ensure backwards compatibility with existing frontend"""

    def test_success_response_has_status_field(self):
        """Ensure status field is present for frontend compatibility"""
        result = success_response(data={"test": 1})
        assert "status" in result
        assert result["status"] == "success"

    def test_error_response_has_status_field(self):
        """Ensure status field is present for frontend compatibility"""
        result = error_response(error="TestError")
        assert "status" in result
        assert result["status"] == "error"

    def test_data_field_is_optional(self):
        """Ensure data field is optional"""
        result = success_response(message="Done")
        assert "data" not in result

    def test_message_field_is_optional(self):
        """Ensure message field is optional"""
        result = success_response(data={"test": 1})
        assert "message" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
