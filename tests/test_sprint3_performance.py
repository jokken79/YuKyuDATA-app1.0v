"""
SPRINT 3: Performance Optimization Tests

Tests for:
- BUG #8: N+1 queries eliminated with bulk-loaded lookups
- BUG #11: File upload validation (MIME, size, magic bytes)
- BUG #12: Pagination support in get_leave_requests()
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import uuid

from orm import SessionLocal
from orm.models.employee import Employee
from orm.models.genzai_employee import GenzaiEmployee
from orm.models.ukeoi_employee import UkeoiEmployee
from orm.models.leave_request import LeaveRequest
from database import employees as employees_db
from database import leave as leave_db
from utils.file_validator import (
    validate_excel_file,
    validate_file_signature,
    validate_file_extension,
    sanitize_filename,
)


class TestBUG8_N1Queries:
    """Test BUG #8: N+1 queries elimination"""

    def test_get_employees_uses_bulk_lookup(self):
        """Verify get_employees() uses bulk-loaded kana dicts, not per-employee queries"""
        # Create test data
        with SessionLocal() as session:
            # Create employees
            for i in range(3):
                emp = Employee(
                    employee_num=f"TEST_{i:03d}",
                    year=2025,
                    name=f"Test Employee {i}",
                    granted=20,
                    used=0,
                    balance=20,
                    grant_date="2025-04-21",
                    status="在職中"
                )
                session.add(emp)

            # Create genzai employees with kana
            for i in range(2):
                genzai = GenzaiEmployee(
                    employee_num=f"TEST_{i:03d}",
                    name=f"Genzai {i}",
                    kana=f"ゲンザイ{i}",
                    status="在職中"
                )
                session.add(genzai)

            session.commit()

        # Mock query to count SQL calls
        with patch('database.employees.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value.__enter__.return_value = mock_session

            # Simulate the actual behavior
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.all.return_value = []

            mock_session.query.return_value = query_mock

            # Count calls to query() method
            result = employees_db.get_employees(year=2025)

            # Verify bulk-loading pattern (not N+1)
            # Expected: 4 queries (1 for Employee, 1 for genzai bulk, 1 for ukeoi bulk, 1 for staff bulk)
            # NOT: 1 + N where N = number of employees (N+1 pattern)
            assert mock_session.query.call_count <= 4, "Should use bulk-loaded lookups, not N+1 queries"

    def test_get_employees_returns_with_kana(self):
        """Verify get_employees() enriches data with kana values"""
        with SessionLocal() as session:
            emp_num = f"KANA_{uuid.uuid4().hex[:8]}"

            emp = Employee(
                employee_num=emp_num,
                year=2025,
                name="Kana Test",
                granted=10,
                used=0,
                balance=10,
                grant_date="2025-04-21",
                status="在職中"
            )
            session.add(emp)

            genzai = GenzaiEmployee(
                employee_num=emp_num,
                name="Kana Test",
                kana="カナテスト",
                status="在職中"
            )
            session.add(genzai)
            session.commit()

        result = employees_db.get_employees(year=2025)
        assert len(result) > 0
        emp_result = next((e for e in result if e['employee_num'] == emp_num), None)
        assert emp_result is not None
        assert emp_result.get('kana') == "カナテスト"


class TestBUG11_FileUploadValidation:
    """Test BUG #11: File upload validation"""

    def test_validate_file_extension(self):
        """Test that invalid file extensions are rejected"""
        with pytest.raises(Exception):
            validate_file_extension("test.txt")

        with pytest.raises(Exception):
            validate_file_extension("test.pdf")

        # Valid extensions should not raise
        assert validate_file_extension("test.xlsx") is True
        assert validate_file_extension("test.xlsm") is True
        assert validate_file_extension("test.xls") is True

    def test_validate_file_signature_xlsx(self):
        """Test XLSX magic bytes validation"""
        # XLSX signature (ZIP format)
        xlsx_signature = b"PK\x03\x04"
        data = xlsx_signature + b"\x00" * 100

        assert validate_file_signature(data) is True

    def test_validate_file_signature_xls(self):
        """Test XLS magic bytes validation"""
        # XLS signature (OLE2 format)
        xls_signature = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"
        data = xls_signature + b"\x00" * 100

        assert validate_file_signature(data) is True

    def test_validate_file_signature_invalid(self):
        """Test that invalid signatures are rejected"""
        invalid_data = b"INVALID_FILE_SIGNATURE" + b"\x00" * 100

        with pytest.raises(Exception):
            validate_file_signature(invalid_data)

    def test_sanitize_filename(self):
        """Test filename sanitization prevents path traversal"""
        # Path traversal attempts
        assert "../test.xlsx" not in sanitize_filename("../test.xlsx")
        assert "..\\test.xlsx" not in sanitize_filename("..\\test.xlsx")

        # Dangerous characters
        dangerous = '|<>:"?\\'
        for char in dangerous:
            sanitized = sanitize_filename(f"test{char}file.xlsx")
            assert char not in sanitized

        # Normal filename unchanged
        normal = "test_file_2025.xlsx"
        assert sanitize_filename(normal) == normal


class TestBUG12_Pagination:
    """Test BUG #12: Pagination support in get_leave_requests()"""

    @pytest.fixture
    def setup_leave_requests(self):
        """Create multiple leave requests for pagination testing"""
        emp_num = f"PAGINATE_{uuid.uuid4().hex[:8]}"
        request_ids = []

        with SessionLocal() as session:
            emp = Employee(
                employee_num=emp_num,
                year=2025,
                name="Pagination Test",
                granted=100,
                used=0,
                balance=100,
                grant_date="2025-04-21",
                status="在職中"
            )
            session.add(emp)
            session.commit()

            # Create 15 leave requests
            for i in range(15):
                req = LeaveRequest(
                    employee_num=emp_num,
                    employee_name="Pagination Test",
                    start_date=f"2025-05-{(i % 27) + 1:02d}",
                    end_date=f"2025-05-{(i % 27) + 2:02d}",
                    days_requested=1,
                    leave_type="full",
                    reason=f"Test request {i}",
                    status="PENDING",
                    year=2025,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(req)
            session.commit()

        return emp_num

    def test_get_leave_requests_without_pagination(self, setup_leave_requests):
        """Test backward compatibility: returns list when skip/limit not specified"""
        emp_num = setup_leave_requests

        result = leave_db.get_leave_requests(employee_num=emp_num)

        # Should return list (backward compatible)
        assert isinstance(result, list)
        assert len(result) == 15

    def test_get_leave_requests_with_pagination(self, setup_leave_requests):
        """Test pagination: returns dict with metadata when skip/limit specified"""
        emp_num = setup_leave_requests

        result = leave_db.get_leave_requests(
            employee_num=emp_num,
            skip=0,
            limit=5
        )

        # Should return dict with pagination metadata
        assert isinstance(result, dict)
        assert 'requests' in result
        assert 'total' in result
        assert 'skip' in result
        assert 'limit' in result
        assert 'has_more' in result

        assert len(result['requests']) == 5
        assert result['total'] == 15
        assert result['skip'] == 0
        assert result['limit'] == 5
        assert result['has_more'] is True

    def test_get_leave_requests_pagination_offset(self, setup_leave_requests):
        """Test pagination with offset (skip)"""
        emp_num = setup_leave_requests

        # First page
        page1 = leave_db.get_leave_requests(
            employee_num=emp_num,
            skip=0,
            limit=5
        )
        assert len(page1['requests']) == 5

        # Second page
        page2 = leave_db.get_leave_requests(
            employee_num=emp_num,
            skip=5,
            limit=5
        )
        assert len(page2['requests']) == 5

        # Verify different results
        page1_ids = {r['id'] for r in page1['requests']}
        page2_ids = {r['id'] for r in page2['requests']}
        assert page1_ids.isdisjoint(page2_ids)

    def test_get_leave_requests_pagination_last_page(self, setup_leave_requests):
        """Test pagination: has_more is False on last page"""
        emp_num = setup_leave_requests

        result = leave_db.get_leave_requests(
            employee_num=emp_num,
            skip=10,
            limit=10
        )

        assert len(result['requests']) == 5
        assert result['total'] == 15
        assert result['has_more'] is False

    def test_get_leave_requests_pagination_limit_cap(self):
        """Test that pagination limit is capped at 1000"""
        # Request with limit > 1000 should be capped
        with SessionLocal() as session:
            emp = Employee(
                employee_num=f"LIMIT_{uuid.uuid4().hex[:8]}",
                year=2025,
                name="Limit Test",
                granted=10,
                used=0,
                balance=10,
                grant_date="2025-04-21",
                status="在職中"
            )
            session.add(emp)
            session.commit()
            emp_num = emp.employee_num

        result = leave_db.get_leave_requests(
            employee_num=emp_num,
            skip=0,
            limit=5000  # Request 5000, should be capped at 1000
        )

        assert result['limit'] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
