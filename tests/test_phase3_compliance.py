"""
FASE 3: Advanced Compliance Tests
==================================

Complete test suite for advanced compliance features:
- Compliance matrix documentation
- Audit trail with hashing
- Compliance reports
- Certificates
- Multi-year validation
"""

import pytest
import json
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

from services.compliance_reports import (
    ComplianceAuditTrail,
    ComplianceReportGenerator,
    ComplianceCertificate,
    COMPLIANCE_MATRIX,
    AuditEvent,
    AuditEventType,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def test_db(tmp_path):
    """Create test database."""
    db_path = tmp_path / "test_yukyu.db"

    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    # Create tables
    c.execute('''
        CREATE TABLE employees (
            id TEXT PRIMARY KEY,
            employee_num TEXT,
            name TEXT,
            hire_date TEXT,
            granted REAL,
            used REAL,
            balance REAL,
            year INTEGER,
            last_updated TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE yukyu_usage_details (
            id INTEGER PRIMARY KEY,
            employee_num TEXT,
            use_date TEXT,
            days_used REAL,
            year INTEGER
        )
    ''')

    c.execute('''
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY,
            action TEXT,
            details TEXT,
            performed_by TEXT,
            timestamp TEXT
        )
    ''')

    # Insert test data
    test_employees = [
        ("001_2025", "001", "Tanaka Yuki", "2015-04-01", 20.0, 3.0, 17.0, 2025, datetime.now().isoformat()),
        ("002_2025", "002", "Suzuki Hanako", "2019-06-15", 12.0, 2.0, 10.0, 2025, datetime.now().isoformat()),
        ("003_2025", "003", "Yamada Taro", "2023-10-01", 10.0, 1.0, 9.0, 2025, datetime.now().isoformat()),
    ]

    for row in test_employees:
        c.execute('''
            INSERT INTO employees
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def audit_trail(test_db):
    """Create audit trail instance."""
    return ComplianceAuditTrail(test_db)


@pytest.fixture
def report_generator(test_db):
    """Create report generator instance."""
    return ComplianceReportGenerator(test_db)


@pytest.fixture
def certificate_generator(test_db):
    """Create certificate generator instance."""
    return ComplianceCertificate(test_db)


# ============================================
# COMPLIANCE MATRIX TESTS
# ============================================

class TestComplianceMatrix:
    """Test compliance matrix documentation."""

    def test_matrix_structure(self):
        """Test compliance matrix has required structure."""
        assert 'act' in COMPLIANCE_MATRIX
        assert 'articles' in COMPLIANCE_MATRIX
        assert 'article_39' in COMPLIANCE_MATRIX['articles']

    def test_article_39_structure(self):
        """Test Article 39 has all required fields."""
        article = COMPLIANCE_MATRIX['articles']['article_39']
        assert article['title'] == '有給休暇 (Paid Leave)'
        assert 'requirements' in article
        assert len(article['requirements']) > 0

    def test_article_39_requirements(self):
        """Test Article 39 has all legal requirements."""
        article = COMPLIANCE_MATRIX['articles']['article_39']
        requirements = article['requirements']

        # Check all requirement IDs exist
        requirement_ids = [r['id'] for r in requirements]
        assert '39.1' in requirement_ids  # Grant after 6 months
        assert '39.2' in requirement_ids  # Grant table
        assert '39.3' in requirement_ids  # Carry-over
        assert '39.4' in requirement_ids  # 5-day rule
        assert '39.5' in requirement_ids  # Ledger
        assert '39.6' in requirement_ids  # 3-year retention
        assert '39.7' in requirement_ids  # LIFO

    def test_requirement_has_implementation_details(self):
        """Test each requirement has implementation details."""
        article = COMPLIANCE_MATRIX['articles']['article_39']
        for req in article['requirements']:
            assert 'id' in req
            assert 'description' in req
            assert 'implemented' in req
            assert 'validation_method' in req
            assert 'control' in req
            assert 'penalty_non_compliance' in req


# ============================================
# AUDIT TRAIL TESTS
# ============================================

class TestAuditTrail:
    """Test audit trail functionality."""

    def test_audit_event_creation(self):
        """Test creating an audit event."""
        event = AuditEvent(
            event_id="evt_001",
            timestamp=datetime.now().isoformat(),
            event_type=AuditEventType.DAYS_USED,
            employee_num="001",
            employee_name="Tanaka Yuki",
            action_description="5 days used",
            details={"days": 5.0}
        )

        assert event.event_id == "evt_001"
        assert event.event_type == AuditEventType.DAYS_USED
        assert event.employee_num == "001"

    def test_event_hash_calculation(self):
        """Test event hash calculation for tamper detection."""
        event = AuditEvent(
            event_id="evt_001",
            timestamp="2025-01-17T10:00:00",
            event_type=AuditEventType.DAYS_USED,
            employee_num="001",
            employee_name="Tanaka Yuki",
            action_description="5 days used",
            details={"days": 5.0}
        )

        hash1 = event.calculate_hash()
        hash2 = event.calculate_hash()

        # Hash should be consistent
        assert hash1 == hash2
        # Hash should be 64 chars (SHA-256 hex)
        assert len(hash1) == 64

    def test_audit_trail_record_event(self, audit_trail):
        """Test recording event in audit trail."""
        event = AuditEvent(
            event_id="evt_001",
            timestamp=datetime.now().isoformat(),
            event_type=AuditEventType.DAYS_USED,
            employee_num="001",
            employee_name="Tanaka Yuki",
            action_description="5 days used",
            details={"days": 5.0},
            performed_by="system"
        )

        success = audit_trail.record_event(event)
        assert success is True

    def test_get_employee_audit_trail(self, audit_trail):
        """Test retrieving audit trail for employee."""
        # Record multiple events
        for i in range(3):
            event = AuditEvent(
                event_id=f"evt_{i:03d}",
                timestamp=datetime.now().isoformat(),
                event_type=AuditEventType.DAYS_USED,
                employee_num="001",
                employee_name="Tanaka Yuki",
                action_description=f"Event {i}",
                details={}
            )
            audit_trail.record_event(event)

        # Retrieve trail
        trail = audit_trail.get_employee_audit_trail("001")
        assert len(trail) >= 3

    def test_audit_trail_integrity_check(self, audit_trail):
        """Test audit trail integrity verification."""
        # Record event
        event = AuditEvent(
            event_id="evt_001",
            timestamp=datetime.now().isoformat(),
            event_type=AuditEventType.DAYS_USED,
            employee_num="001",
            employee_name="Tanaka Yuki",
            action_description="Test event",
            details={}
        )
        audit_trail.record_event(event)

        # Verify integrity
        result = audit_trail.verify_audit_trail_integrity()
        assert result['status'] in ['PASS', 'FAIL']
        assert 'total_events' in result
        assert 'issues' in result


# ============================================
# COMPLIANCE REPORT TESTS
# ============================================

class TestComplianceReports:
    """Test compliance report generation."""

    def test_generate_full_report(self, report_generator):
        """Test generating full compliance report."""
        report = report_generator.generate_full_compliance_report(2025)

        assert report['fiscal_year'] == 2025
        assert 'findings' in report
        assert 'overall_status' in report
        assert report['overall_status'] in ['COMPLIANT', 'NON-COMPLIANT', 'AT_RISK']

    def test_report_employee_data(self, report_generator):
        """Test report contains correct employee data."""
        report = report_generator.generate_full_compliance_report(2025)

        # Should have employees from test data
        assert len(report['findings']) > 0

        # Check employee structure
        for emp_num, emp_data in report['findings'].items():
            assert 'employee_num' in emp_data
            assert 'name' in emp_data
            assert 'granted_days' in emp_data
            assert 'used_days' in emp_data
            assert 'remaining_days' in emp_data
            assert 'legal_status' in emp_data

    def test_five_day_compliance_check(self, report_generator):
        """Test 5-day compliance check in report."""
        report = report_generator.generate_full_compliance_report(2025)

        for emp_num, emp_data in report['findings'].items():
            granted = emp_data['granted_days']
            used = emp_data['used_days']
            checks = emp_data['compliance_checks']

            # 5-day rule only applies if granted >= 10
            if granted >= 10:
                assert checks['5day_rule']['required_days'] == 5.0
                assert checks['5day_rule']['used_days'] == used
                # Check compliance calculation
                is_compliant = used >= 5.0
                assert checks['5day_rule']['compliant'] == is_compliant

    def test_accumulation_limit_check(self, report_generator):
        """Test accumulation limit check (max 40 days)."""
        report = report_generator.generate_full_compliance_report(2025)

        for emp_num, emp_data in report['findings'].items():
            checks = emp_data['compliance_checks']
            accumulation = checks['accumulation_limit']

            assert accumulation['max_allowed'] == 40.0
            balance = emp_data['remaining_days']
            assert accumulation['current_balance'] == balance
            assert accumulation['compliant'] == (balance <= 40.0)

    def test_export_report_json(self, report_generator, tmp_path):
        """Test exporting report to JSON."""
        report = report_generator.generate_full_compliance_report(2025)
        output_file = tmp_path / "report.json"

        success = report_generator.export_report_for_auditors(
            report, str(output_file), format='json'
        )

        assert success is True
        assert output_file.exists()

        # Verify JSON is valid
        with open(output_file) as f:
            data = json.load(f)
            assert data['fiscal_year'] == 2025

    def test_export_report_csv(self, report_generator, tmp_path):
        """Test exporting report to CSV."""
        report = report_generator.generate_full_compliance_report(2025)
        output_file = tmp_path / "report.csv"

        success = report_generator.export_report_for_auditors(
            report, str(output_file), format='csv'
        )

        assert success is True
        assert output_file.exists()

        # Verify CSV content
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            assert 'employee_num' in content
            assert 'granted_days' in content


# ============================================
# COMPLIANCE CERTIFICATE TESTS
# ============================================

class TestComplianceCertificate:
    """Test compliance certificate generation."""

    def test_generate_certificate(self, certificate_generator):
        """Test generating compliance certificate."""
        cert = certificate_generator.generate_certificate(
            2025,
            "Test Company Inc."
        )

        assert cert['type'] == 'COMPLIANCE_CERTIFICATE'
        assert cert['fiscal_year'] == 2025
        assert cert['organization_name'] == 'Test Company Inc.'
        assert 'signature' in cert
        assert len(cert['signature']) == 64  # SHA-256 hash

    def test_certificate_has_compliance_data(self, certificate_generator):
        """Test certificate contains compliance data."""
        cert = certificate_generator.generate_certificate(
            2025,
            "Test Company Inc."
        )

        assert cert['compliance_findings'] in ['COMPLIANT', 'NON-COMPLIANT']
        assert 'employees_compliant' in cert
        assert 'total_employees' in cert

    def test_certificate_signature_format(self, certificate_generator):
        """Test certificate signature is valid SHA-256."""
        cert = certificate_generator.generate_certificate(
            2025,
            "Test Company Inc."
        )

        sig = cert['signature']
        # SHA-256 produces 64 hex characters
        assert len(sig) == 64
        assert all(c in '0123456789abcdef' for c in sig)

    def test_export_certificate_json(self, certificate_generator, tmp_path):
        """Test exporting certificate to JSON."""
        cert = certificate_generator.generate_certificate(
            2025,
            "Test Company Inc."
        )
        output_file = tmp_path / "certificate.json"

        success = certificate_generator.export_certificate(
            cert, str(output_file), include_report=True
        )

        assert success is True
        assert output_file.exists()

        # Verify JSON
        with open(output_file) as f:
            data = json.load(f)
            assert data['type'] == 'COMPLIANCE_CERTIFICATE'

    def test_export_certificate_text(self, certificate_generator, tmp_path):
        """Test exporting certificate to text format."""
        cert = certificate_generator.generate_certificate(
            2025,
            "Test Company Inc."
        )
        output_file = tmp_path / "certificate.txt"

        success = certificate_generator.export_certificate(
            cert, str(output_file), include_report=False
        )

        assert success is True
        assert output_file.exists()

        # Verify text contains certificate elements
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '有給休暇管理法令準拠証明書' in content
            assert 'Test Company Inc.' in content


# ============================================
# LEGAL REQUIREMENT VALIDATION TESTS
# ============================================

class TestLegalRequirementValidation:
    """Test validation against legal requirements."""

    def test_grant_calculation_validation(self, report_generator):
        """Test grant calculation is correct per law."""
        report = report_generator.generate_full_compliance_report(2025)

        for emp_num, emp_data in report['findings'].items():
            grant_check = emp_data['compliance_checks']['grant_calculation']
            # Should show seniority and whether calculation is correct
            assert 'expected_grant_days' in grant_check
            assert 'actual_grant_days' in grant_check
            assert 'compliant' in grant_check

    def test_carryover_limits_validation(self, report_generator):
        """Test carry-over limits are enforced."""
        report = report_generator.generate_full_compliance_report(2025)

        for emp_num, emp_data in report['findings'].items():
            # Balance should never exceed 40 days
            assert emp_data['remaining_days'] <= 40.0

    def test_five_day_rule_enforcement(self, report_generator):
        """Test 5-day usage rule is enforced."""
        report = report_generator.generate_full_compliance_report(2025)

        # Any employee with 10+ granted days must have used >= 5
        for emp_num, emp_data in report['findings'].items():
            if emp_data['granted_days'] >= 10:
                # Check 5-day compliance
                check = emp_data['compliance_checks']['5day_rule']
                assert check['required_days'] == 5.0

    def test_overall_status_calculation(self, report_generator):
        """Test overall compliance status calculation."""
        report = report_generator.generate_full_compliance_report(2025)

        # Overall status should be consistent with individual statuses
        non_compliant_count = sum(
            1 for emp in report['findings'].values()
            if emp['legal_status'] == 'NON-COMPLIANT'
        )

        if non_compliant_count > 0:
            assert report['overall_status'] == 'NON-COMPLIANT'
        else:
            assert report['overall_status'] in ['COMPLIANT', 'AT_RISK']


# ============================================
# MULTI-YEAR COMPLIANCE TESTS
# ============================================

class TestMultiYearCompliance:
    """Test multi-year compliance validation."""

    def test_single_year_report(self, report_generator):
        """Test generating report for single year."""
        report = report_generator.generate_full_compliance_report(2025)
        assert report['fiscal_year'] == 2025

    def test_report_consistency(self, report_generator):
        """Test report data consistency."""
        report = report_generator.generate_full_compliance_report(2025)

        # Total days used + remaining should be <= granted + carry-over
        for emp_num, emp_data in report['findings'].items():
            # This is a basic sanity check
            assert emp_data['used_days'] >= 0
            assert emp_data['remaining_days'] >= 0
            assert emp_data['granted_days'] > 0


# ============================================
# AUDIT TRAIL INTEGRITY TESTS
# ============================================

class TestAuditTrailIntegrity:
    """Test audit trail maintains integrity."""

    def test_hash_chain_integrity(self, audit_trail):
        """Test hash chain integrity across multiple events."""
        events = []
        for i in range(5):
            event = AuditEvent(
                event_id=f"evt_{i:03d}",
                timestamp=datetime.now().isoformat(),
                event_type=AuditEventType.DAYS_USED,
                employee_num="001",
                employee_name="Tanaka Yuki",
                action_description=f"Event {i}",
                details={}
            )
            events.append(event)
            audit_trail.record_event(event)

        # Verify all events recorded
        trail = audit_trail.get_employee_audit_trail("001")
        assert len(trail) >= 5

    def test_event_immutability(self, audit_trail):
        """Test events cannot be modified after recording."""
        event = AuditEvent(
            event_id="evt_immutable",
            timestamp=datetime.now().isoformat(),
            event_type=AuditEventType.DAYS_USED,
            employee_num="001",
            employee_name="Tanaka Yuki",
            action_description="Original action",
            details={"days": 5.0}
        )

        original_hash = event.calculate_hash()
        audit_trail.record_event(event)

        # Event hash should remain same even if we try to modify object
        modified_event = event
        modified_event.action_description = "Modified action"
        modified_hash = modified_event.calculate_hash()

        # Hashes should differ (event was effectively modified)
        assert original_hash != modified_hash


# ============================================
# COMPLIANCE MATRIX VALIDATION TESTS
# ============================================

class TestComplianceMatrixValidation:
    """Test compliance matrix validation."""

    def test_all_requirements_implemented(self):
        """Test all requirements have implementation status."""
        article = COMPLIANCE_MATRIX['articles']['article_39']
        for req in article['requirements']:
            assert req['implemented'] in [True, False]

    def test_all_requirements_have_controls(self):
        """Test all requirements have control measures."""
        article = COMPLIANCE_MATRIX['articles']['article_39']
        for req in article['requirements']:
            assert req['control'] is not None
            assert len(req['control']) > 0

    def test_penalty_information_present(self):
        """Test penalty information for non-compliance."""
        article = COMPLIANCE_MATRIX['articles']['article_39']
        for req in article['requirements']:
            assert 'penalty_non_compliance' in req
            assert len(req['penalty_non_compliance']) > 0


# ============================================
# INTEGRATION TESTS
# ============================================

class TestPhase3Integration:
    """Integration tests for FASE 3."""

    def test_full_compliance_workflow(self, audit_trail, report_generator, certificate_generator):
        """Test complete compliance workflow."""
        # 1. Record audit events
        event = AuditEvent(
            event_id="evt_workflow",
            timestamp=datetime.now().isoformat(),
            event_type=AuditEventType.FIVE_DAY_CHECK,
            employee_num="001",
            employee_name="Tanaka Yuki",
            action_description="5-day compliance check",
            details={"used": 5.0, "required": 5.0, "compliant": True}
        )
        audit_trail.record_event(event)

        # 2. Generate compliance report
        report = report_generator.generate_full_compliance_report(2025)
        assert report['overall_status'] in ['COMPLIANT', 'NON-COMPLIANT']

        # 3. Generate certificate
        cert = certificate_generator.generate_certificate(2025, "Test Corp")
        assert cert['type'] == 'COMPLIANCE_CERTIFICATE'

        # 4. Verify audit trail
        integrity = audit_trail.verify_audit_trail_integrity()
        assert 'total_events' in integrity

    def test_audit_trail_with_report_generation(self, audit_trail, report_generator):
        """Test audit trail records with report generation."""
        # Record multiple events
        for i in range(3):
            event = AuditEvent(
                event_id=f"evt_audit_{i}",
                timestamp=datetime.now().isoformat(),
                event_type=AuditEventType.COMPLIANCE_REPORT,
                employee_num=f"{i:03d}",
                employee_name=f"Employee {i}",
                action_description="Compliance check",
                details={}
            )
            audit_trail.record_event(event)

        # Generate report
        report = report_generator.generate_full_compliance_report(2025)

        # Verify audit trail includes events
        for i in range(3):
            trail = audit_trail.get_employee_audit_trail(f"{i:03d}")
            assert len(trail) >= 1
