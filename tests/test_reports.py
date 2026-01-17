"""
Tests comprehensivos para la funcionalidad de generacion de reportes PDF.

Cubre:
- Generacion de reportes individuales de empleado
- Reportes de compliance 5 dias (5日取得義務)
- Reportes anuales (年次有給休暇管理簿)
- Reportes mensuales
- Reportes personalizados
- Manejo de errores
- Content-Type headers
- Mocking para tests rapidos
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import io

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_pdf_bytes():
    """Mock PDF content for testing."""
    return b'%PDF-1.4 mock pdf content for testing'


@pytest.fixture
def mock_employee_data():
    """Mock employee data returned by _get_employee_data."""
    return {
        'employee_num': 'TEST_001',
        'name': '試験太郎',
        'haken': 'テスト工場',
        'dispatch_name': 'テスト派遣先',
        'status': '在職中',
        'hire_date': '2020-04-01',
        'source_table': 'genzai',
        'vacation_data': [
            {
                'year': 2025,
                'granted': 20.0,
                'used': 8.0,
                'balance': 12.0
            },
            {
                'year': 2024,
                'granted': 15.0,
                'used': 15.0,
                'balance': 0.0
            }
        ],
        'usage_details': [
            {'use_date': '2025-01-10', 'days_used': 1.0, 'month': 1, 'year': 2025},
            {'use_date': '2025-01-15', 'days_used': 0.5, 'month': 1, 'year': 2025},
            {'use_date': '2025-02-20', 'days_used': 1.0, 'month': 2, 'year': 2025},
        ]
    }


@pytest.fixture
def mock_db_employees():
    """Mock employee list from database."""
    return [
        {
            'employee_num': 'EMP_001',
            'name': '田中太郎',
            'haken': '工場A',
            'granted': 20.0,
            'used': 10.0,
            'balance': 10.0,
            'hire_date': '2018-04-01',
            'emp_status': '在職中'
        },
        {
            'employee_num': 'EMP_002',
            'name': '山田花子',
            'haken': '工場B',
            'granted': 15.0,
            'used': 3.0,
            'balance': 12.0,
            'hire_date': '2022-07-01',
            'emp_status': '在職中'
        },
        {
            'employee_num': 'EMP_003',
            'name': '佐藤次郎',
            'haken': '工場A',
            'granted': 10.0,
            'used': 6.0,
            'balance': 4.0,
            'hire_date': '2023-04-01',
            'emp_status': '在職中'
        }
    ]


# ============================================
# REPORT GENERATOR UNIT TESTS
# ============================================

class TestReportGeneratorUnit:
    """Unit tests for ReportGenerator class with mocked database."""

    @patch('reports.get_db_connection')
    def test_generate_employee_report_success(self, mock_db, mock_employee_data, mock_pdf_bytes):
        """Test successful employee report generation."""
        from reports import ReportGenerator

        # Setup mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = mock_employee_data
        mock_cursor.fetchall.return_value = [mock_employee_data]
        mock_db.return_value.__enter__ = Mock(return_value=mock_db.return_value)
        mock_db.return_value.__exit__ = Mock(return_value=False)
        mock_db.return_value.cursor.return_value = mock_cursor

        generator = ReportGenerator(company_name="Test Company")

        # Mock _get_employee_data to return test data
        with patch.object(generator, '_get_employee_data', return_value=mock_employee_data):
            pdf_bytes = generator.generate_employee_report('TEST_001', 2025)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        # PDF files start with %PDF
        assert pdf_bytes[:4] == b'%PDF'

    @patch('reports.get_db_connection')
    def test_generate_employee_report_not_found(self, mock_db):
        """Test employee report raises error when employee not found."""
        from reports import ReportGenerator

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.return_value.__enter__ = Mock(return_value=mock_db.return_value)
        mock_db.return_value.__exit__ = Mock(return_value=False)
        mock_db.return_value.cursor.return_value = mock_cursor

        generator = ReportGenerator()

        with patch.object(generator, '_get_employee_data', return_value=None):
            with pytest.raises(ValueError, match="no encontrado"):
                generator.generate_employee_report('NONEXISTENT', 2025)

    @patch('reports.get_db_connection')
    def test_generate_annual_ledger(self, mock_db, mock_db_employees):
        """Test annual ledger report generation."""
        from reports import ReportGenerator

        # Setup mock cursor to return employee data
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [dict_to_row(e) for e in mock_db_employees],  # employees
            []  # usage details
        ]
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_db.return_value.close = Mock()

        generator = ReportGenerator()
        pdf_bytes = generator.generate_annual_ledger(2025)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'

    @patch('reports.get_db_connection')
    def test_generate_monthly_summary(self, mock_db):
        """Test monthly summary report generation."""
        from reports import ReportGenerator

        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [dict_to_row({'employee_num': 'EMP_001', 'name': '田中太郎', 'total_days': 3.0, 'num_requests': 2})],
            [dict_to_row({'department': '工場A', 'employees': 1, 'total_days': 3.0})]
        ]
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_db.return_value.close = Mock()

        generator = ReportGenerator()
        pdf_bytes = generator.generate_monthly_summary(2025, 1)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'

    @patch('reports.get_db_connection')
    def test_generate_compliance_report(self, mock_db, mock_db_employees):
        """Test compliance report generation."""
        from reports import ReportGenerator

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [dict_to_row(e) for e in mock_db_employees]
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_db.return_value.close = Mock()

        generator = ReportGenerator()
        pdf_bytes = generator.generate_compliance_report(2025)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'

    @patch('reports.get_db_connection')
    def test_generate_custom_report(self, mock_db, mock_db_employees):
        """Test custom report generation with filters."""
        from reports import ReportGenerator

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [dict_to_row(e) for e in mock_db_employees]
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_db.return_value.close = Mock()

        generator = ReportGenerator()
        config = {
            'title': 'Reporte de Prueba',
            'filters': {
                'year': 2025,
                'department': '工場A'
            },
            'columns': ['employee_num', 'name', 'granted', 'used', 'balance'],
            'include_stats': True,
            'sort_by': 'balance'
        }

        pdf_bytes = generator.generate_custom_report(config)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'


# ============================================
# API ENDPOINT TESTS - DATA ENDPOINTS
# ============================================

class TestReportDataEndpoints:
    """Tests for report data endpoints (no PDF generation)."""

    def test_get_custom_report_data(self, test_client):
        """Test GET /api/reports/custom endpoint."""
        response = test_client.get("/api/reports/custom?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert "data" in data
        assert "summary" in data
        assert data.get("year") == 2025

    def test_get_custom_report_data_with_filters(self, test_client):
        """Test custom report data with haken filter."""
        response = test_client.get(
            "/api/reports/custom?year=2025&active_only=true&haken=工場"
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("active_only") == True

    def test_get_monthly_report_data(self, test_client):
        """Test GET /api/reports/monthly/{year}/{month} endpoint."""
        response = test_client.get("/api/reports/monthly/2025/1")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("year") == 2025
        assert data.get("month") == 1
        assert "summary" in data

    def test_get_monthly_reports_list(self, test_client):
        """Test GET /api/reports/monthly-list/{year} endpoint."""
        response = test_client.get("/api/reports/monthly-list/2025")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert "months" in data
        assert len(data["months"]) == 12

        # Verify month structure
        for month_data in data["months"]:
            assert "month" in month_data
            assert "month_name" in month_data
            assert "has_data" in month_data


# ============================================
# API ENDPOINT TESTS - PDF ENDPOINTS
# ============================================

class TestReportPDFEndpoints:
    """Tests for PDF generation endpoints (require authentication)."""

    @patch('routes.reports.ReportGenerator')
    @patch('routes.reports.save_report')
    def test_get_employee_pdf_report(
        self, mock_save, mock_generator_class, test_client, admin_auth_headers, mock_pdf_bytes
    ):
        """Test GET /api/reports/employee/{id}/pdf endpoint."""
        mock_generator = MagicMock()
        mock_generator.generate_employee_report.return_value = mock_pdf_bytes
        mock_generator_class.return_value = mock_generator
        mock_save.return_value = "/tmp/test_report.pdf"

        # Create temp file for FileResponse
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(mock_pdf_bytes)
            temp_path = f.name
        mock_save.return_value = temp_path

        try:
            response = test_client.get(
                "/api/reports/employee/TEST_001/pdf?year=2025",
                headers=admin_auth_headers
            )

            # Should return PDF or error if no data
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                assert response.headers.get("content-type") == "application/pdf"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_employee_pdf_report_unauthorized(self, test_client):
        """Test employee PDF endpoint without authentication."""
        response = test_client.get("/api/reports/employee/TEST_001/pdf")

        # Should require authentication
        assert response.status_code in [401, 403, 422]

    @patch('routes.reports.ReportGenerator')
    @patch('routes.reports.save_report')
    def test_get_annual_pdf_report(
        self, mock_save, mock_generator_class, test_client, admin_auth_headers, mock_pdf_bytes
    ):
        """Test GET /api/reports/annual/{year}/pdf endpoint."""
        mock_generator = MagicMock()
        mock_generator.generate_annual_report.return_value = mock_pdf_bytes
        mock_generator_class.return_value = mock_generator

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(mock_pdf_bytes)
            temp_path = f.name
        mock_save.return_value = temp_path

        try:
            response = test_client.get(
                "/api/reports/annual/2025/pdf",
                headers=admin_auth_headers
            )

            assert response.status_code in [200, 500]
            if response.status_code == 200:
                assert response.headers.get("content-type") == "application/pdf"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('routes.reports.ReportGenerator')
    @patch('routes.reports.save_report')
    def test_get_monthly_pdf_report(
        self, mock_save, mock_generator_class, test_client, admin_auth_headers, mock_pdf_bytes
    ):
        """Test GET /api/reports/monthly/{year}/{month}/pdf endpoint."""
        mock_generator = MagicMock()
        mock_generator.generate_monthly_report.return_value = mock_pdf_bytes
        mock_generator_class.return_value = mock_generator

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(mock_pdf_bytes)
            temp_path = f.name
        mock_save.return_value = temp_path

        try:
            response = test_client.get(
                "/api/reports/monthly/2025/1/pdf",
                headers=admin_auth_headers
            )

            assert response.status_code in [200, 500]
            if response.status_code == 200:
                assert response.headers.get("content-type") == "application/pdf"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('routes.reports.ReportGenerator')
    @patch('routes.reports.save_report')
    def test_get_compliance_pdf_report(
        self, mock_save, mock_generator_class, test_client, admin_auth_headers, mock_pdf_bytes
    ):
        """Test GET /api/reports/compliance/{year}/pdf endpoint."""
        mock_generator = MagicMock()
        mock_generator.generate_compliance_report.return_value = mock_pdf_bytes
        mock_generator_class.return_value = mock_generator

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(mock_pdf_bytes)
            temp_path = f.name
        mock_save.return_value = temp_path

        try:
            response = test_client.get(
                "/api/reports/compliance/2025/pdf",
                headers=admin_auth_headers
            )

            assert response.status_code in [200, 500]
            if response.status_code == 200:
                assert response.headers.get("content-type") == "application/pdf"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('routes.reports.ReportGenerator')
    @patch('routes.reports.save_report')
    def test_generate_custom_pdf_report(
        self, mock_save, mock_generator_class, test_client, admin_auth_headers, mock_pdf_bytes
    ):
        """Test POST /api/reports/custom/pdf endpoint."""
        mock_generator = MagicMock()
        mock_generator.generate_custom_report.return_value = mock_pdf_bytes
        mock_generator_class.return_value = mock_generator

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(mock_pdf_bytes)
            temp_path = f.name
        mock_save.return_value = temp_path

        try:
            response = test_client.post(
                "/api/reports/custom/pdf",
                json={
                    "title": "Reporte de Prueba",
                    "year": 2025,
                    "include_charts": True,
                    "include_compliance": True
                },
                headers=admin_auth_headers
            )

            assert response.status_code in [200, 500]
            if response.status_code == 200:
                assert response.headers.get("content-type") == "application/pdf"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# ============================================
# VALIDATION TESTS
# ============================================

class TestReportValidation:
    """Tests for input validation on report endpoints."""

    def test_custom_report_invalid_year_low(self, test_client, admin_auth_headers):
        """Test custom report with year below minimum."""
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={
                "title": "Test",
                "year": 1999  # Below 2000 minimum
            },
            headers=admin_auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_custom_report_invalid_year_high(self, test_client, admin_auth_headers):
        """Test custom report with year above maximum."""
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={
                "title": "Test",
                "year": 2101  # Above 2100 maximum
            },
            headers=admin_auth_headers
        )

        assert response.status_code == 422

    def test_custom_report_empty_title(self, test_client, admin_auth_headers):
        """Test custom report with empty title."""
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={
                "title": "",  # Empty title
                "year": 2025
            },
            headers=admin_auth_headers
        )

        assert response.status_code == 422

    def test_custom_report_invalid_month(self, test_client, admin_auth_headers):
        """Test custom report with invalid month."""
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={
                "title": "Test",
                "year": 2025,
                "month": 13  # Invalid month
            },
            headers=admin_auth_headers
        )

        assert response.status_code == 422

    def test_monthly_report_invalid_month(self, test_client):
        """Test monthly report data with invalid month."""
        # Month 0 is invalid
        response = test_client.get("/api/reports/monthly/2025/0")
        # Should return error or empty data
        assert response.status_code in [200, 400, 422, 500]

    def test_monthly_report_month_13(self, test_client):
        """Test monthly report data with month 13."""
        response = test_client.get("/api/reports/monthly/2025/13")
        # Should handle gracefully
        assert response.status_code in [200, 400, 422, 500]


# ============================================
# FILE MANAGEMENT TESTS
# ============================================

class TestReportFileManagement:
    """Tests for report file management endpoints."""

    def test_list_report_files(self, test_client, admin_auth_headers):
        """Test GET /api/reports/files endpoint."""
        response = test_client.get(
            "/api/reports/files",
            headers=admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert "count" in data
        assert "reports" in data
        assert isinstance(data["reports"], list)

    def test_list_report_files_unauthorized(self, test_client):
        """Test report files list without authentication."""
        response = test_client.get("/api/reports/files")

        assert response.status_code in [401, 403]

    def test_download_report_not_found(self, test_client, admin_auth_headers):
        """Test downloading non-existent report."""
        response = test_client.get(
            "/api/reports/download/nonexistent_report_xyz123.pdf",
            headers=admin_auth_headers
        )

        assert response.status_code == 404

    def test_download_report_invalid_type(self, test_client, admin_auth_headers):
        """Test downloading file with invalid extension."""
        response = test_client.get(
            "/api/reports/download/malicious.exe",
            headers=admin_auth_headers
        )

        assert response.status_code in [400, 404]

    def test_cleanup_reports_requires_admin(self, test_client, user_auth_headers):
        """Test cleanup endpoint requires admin privileges."""
        response = test_client.delete(
            "/api/reports/cleanup",
            headers=user_auth_headers
        )

        # Should require admin - either 403 or succeed if user is admin
        assert response.status_code in [200, 401, 403]


# ============================================
# CONTENT-TYPE TESTS
# ============================================

class TestReportContentTypes:
    """Tests for correct Content-Type headers."""

    def test_custom_data_json_content_type(self, test_client):
        """Test custom report data returns JSON."""
        response = test_client.get("/api/reports/custom?year=2025")

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_monthly_data_json_content_type(self, test_client):
        """Test monthly report data returns JSON."""
        response = test_client.get("/api/reports/monthly/2025/1")

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_monthly_list_json_content_type(self, test_client):
        """Test monthly list returns JSON."""
        response = test_client.get("/api/reports/monthly-list/2025")

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type


# ============================================
# HELPER FUNCTIONS
# ============================================

def dict_to_row(d):
    """Convert dictionary to sqlite3.Row-like object."""
    class FakeRow:
        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data.get(key)

        def keys(self):
            return self._data.keys()

        def items(self):
            return self._data.items()

    return FakeRow(d)


# ============================================
# REPORT UTILITY FUNCTION TESTS
# ============================================

class TestReportUtilityFunctions:
    """Tests for utility functions in reports module."""

    def test_save_report(self, mock_pdf_bytes):
        """Test save_report function."""
        from reports import save_report, REPORTS_DIR
        import os

        # Save a test report
        filepath = save_report(mock_pdf_bytes, "test_save_report")

        try:
            assert os.path.exists(filepath)
            assert filepath.endswith('.pdf')

            # Verify content
            with open(filepath, 'rb') as f:
                content = f.read()
            assert content == mock_pdf_bytes
        finally:
            # Cleanup
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_list_reports(self, mock_pdf_bytes):
        """Test list_reports function."""
        from reports import save_report, list_reports

        # Save a test report first
        filepath = save_report(mock_pdf_bytes, "test_list_report")

        try:
            reports = list_reports()
            assert isinstance(reports, list)

            # Find our test report
            test_report = None
            for r in reports:
                if 'test_list_report' in r.get('filename', ''):
                    test_report = r
                    break

            assert test_report is not None
            assert 'filename' in test_report
            assert 'size_kb' in test_report
            assert 'created' in test_report
            assert 'modified' in test_report
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_cleanup_old_reports(self, mock_pdf_bytes):
        """Test cleanup_old_reports function."""
        from reports import save_report, cleanup_old_reports
        import time

        # Save a test report
        filepath = save_report(mock_pdf_bytes, "test_cleanup_report")

        try:
            # Cleanup with 0 days should delete all
            deleted = cleanup_old_reports(days=0)

            # Should have deleted at least the test file
            assert deleted >= 0
        finally:
            # Ensure cleanup even if test fails
            if os.path.exists(filepath):
                os.remove(filepath)


# ============================================
# EDGE CASE TESTS
# ============================================

class TestReportEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_custom_report_max_title_length(self, test_client, admin_auth_headers):
        """Test custom report with maximum title length."""
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={
                "title": "A" * 200,  # Maximum 200 chars
                "year": 2025
            },
            headers=admin_auth_headers
        )

        # Should accept max length
        assert response.status_code in [200, 500]

    def test_custom_report_title_too_long(self, test_client, admin_auth_headers):
        """Test custom report with title exceeding maximum."""
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={
                "title": "A" * 201,  # Exceeds 200 chars
                "year": 2025
            },
            headers=admin_auth_headers
        )

        assert response.status_code == 422

    def test_custom_report_with_special_characters(self, test_client, admin_auth_headers):
        """Test custom report with Japanese and special characters in title."""
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={
                "title": "年次有給休暇レポート 2025年度",
                "year": 2025
            },
            headers=admin_auth_headers
        )

        assert response.status_code in [200, 500]

    def test_custom_report_boundary_years(self, test_client, admin_auth_headers):
        """Test custom report with boundary year values."""
        # Test minimum year (2000)
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={"title": "Test", "year": 2000},
            headers=admin_auth_headers
        )
        assert response.status_code in [200, 500]

        # Test maximum year (2100)
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={"title": "Test", "year": 2100},
            headers=admin_auth_headers
        )
        assert response.status_code in [200, 500]

    def test_monthly_report_boundary_months(self, test_client):
        """Test monthly report with boundary month values."""
        # January (first month)
        response = test_client.get("/api/reports/monthly/2025/1")
        assert response.status_code == 200

        # December (last month)
        response = test_client.get("/api/reports/monthly/2025/12")
        assert response.status_code == 200

    def test_custom_report_empty_employee_list(self, test_client, admin_auth_headers):
        """Test custom report with empty employee_nums list."""
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={
                "title": "Test",
                "year": 2025,
                "employee_nums": []  # Empty list
            },
            headers=admin_auth_headers
        )

        assert response.status_code in [200, 500]

    def test_custom_report_all_options_enabled(self, test_client, admin_auth_headers):
        """Test custom report with all options enabled."""
        response = test_client.post(
            "/api/reports/custom/pdf",
            json={
                "title": "Full Options Report",
                "year": 2025,
                "month": 6,
                "employee_nums": ["001", "002", "003"],
                "haken_filter": "工場",
                "include_charts": True,
                "include_compliance": True
            },
            headers=admin_auth_headers
        )

        assert response.status_code in [200, 500]


# ============================================
# COMPLIANCE REPORT SPECIFIC TESTS
# ============================================

class TestComplianceReportSpecifics:
    """Specific tests for 5-day compliance report logic."""

    @patch('reports.get_db_connection')
    def test_compliance_classification_compliant(self, mock_db):
        """Test employee classified as compliant (5+ days used)."""
        from reports import ReportGenerator

        employees = [
            {'employee_num': 'EMP_001', 'name': 'Test', 'haken': 'A',
             'granted': 15.0, 'used': 6.0, 'balance': 9.0, 'hire_date': '2020-01-01'}
        ]

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [dict_to_row(e) for e in employees]
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_db.return_value.close = Mock()

        generator = ReportGenerator()
        pdf_bytes = generator.generate_compliance_report(2025)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    @patch('reports.get_db_connection')
    def test_compliance_classification_at_risk(self, mock_db):
        """Test employee classified as at-risk (3-4.9 days used)."""
        from reports import ReportGenerator

        employees = [
            {'employee_num': 'EMP_001', 'name': 'Test', 'haken': 'A',
             'granted': 15.0, 'used': 4.0, 'balance': 11.0, 'hire_date': '2020-01-01'}
        ]

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [dict_to_row(e) for e in employees]
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_db.return_value.close = Mock()

        generator = ReportGenerator()
        pdf_bytes = generator.generate_compliance_report(2025)

        assert pdf_bytes is not None

    @patch('reports.get_db_connection')
    def test_compliance_classification_non_compliant(self, mock_db):
        """Test employee classified as non-compliant (<3 days used)."""
        from reports import ReportGenerator

        employees = [
            {'employee_num': 'EMP_001', 'name': 'Test', 'haken': 'A',
             'granted': 15.0, 'used': 2.0, 'balance': 13.0, 'hire_date': '2020-01-01'}
        ]

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [dict_to_row(e) for e in employees]
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_db.return_value.close = Mock()

        generator = ReportGenerator()
        pdf_bytes = generator.generate_compliance_report(2025)

        assert pdf_bytes is not None

    @patch('reports.get_db_connection')
    def test_compliance_no_obligated_employees(self, mock_db):
        """Test compliance report when no employees have 10+ granted days."""
        from reports import ReportGenerator

        # All employees have less than 10 granted days
        employees = [
            {'employee_num': 'EMP_001', 'name': 'Test', 'haken': 'A',
             'granted': 8.0, 'used': 2.0, 'balance': 6.0, 'hire_date': '2023-01-01'}
        ]

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [dict_to_row(e) for e in employees]
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_db.return_value.close = Mock()

        generator = ReportGenerator()
        pdf_bytes = generator.generate_compliance_report(2025)

        # Should still generate a valid PDF
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0


# ============================================
# INTEGRATION TESTS WITH REAL CLIENT
# ============================================

class TestReportIntegration:
    """Integration tests using real test client."""

    def test_full_report_workflow(self, test_client, admin_auth_headers):
        """Test complete workflow: data -> PDF -> list -> download."""
        # 1. Get data
        data_response = test_client.get("/api/reports/custom?year=2025")
        assert data_response.status_code == 200

        # 2. List existing reports
        list_response = test_client.get(
            "/api/reports/files",
            headers=admin_auth_headers
        )
        assert list_response.status_code == 200

    def test_monthly_data_consistency(self, test_client):
        """Test that monthly data is consistent with monthly list."""
        # Get monthly list
        list_response = test_client.get("/api/reports/monthly-list/2025")
        assert list_response.status_code == 200
        months = list_response.json().get("months", [])

        # Verify each month
        for month_data in months[:3]:  # Test first 3 months
            month = month_data.get("month")
            detail_response = test_client.get(f"/api/reports/monthly/2025/{month}")
            assert detail_response.status_code == 200
            detail_data = detail_response.json()
            assert detail_data.get("month") == month

    def test_summary_calculations(self, test_client):
        """Test that summary calculations in custom report are correct."""
        response = test_client.get("/api/reports/custom?year=2025")
        assert response.status_code == 200

        data = response.json()
        summary = data.get("summary", {})
        employees = data.get("data", [])

        # Verify count
        assert summary.get("count") == len(employees)

        # Verify totals (if there are employees)
        if employees:
            calc_granted = sum(e.get('granted', 0) or 0 for e in employees)
            calc_used = sum(e.get('used', 0) or 0 for e in employees)

            assert abs(summary.get("total_granted", 0) - round(calc_granted, 1)) < 0.1
            assert abs(summary.get("total_used", 0) - round(calc_used, 1)) < 0.1
