"""
Tests para FASE 0 - Riesgos Críticos Legales
Compliance Expert Agent Implementation
"""

import pytest
import os
from datetime import datetime, date, timedelta

# Configurar DATABASE_PATH antes de importar database
os.environ['DATABASE_PATH'] = 'test_compliance_phase0.db'

import sqlite3
from database import get_db, init_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Setup base de datos de prueba"""
    # Inicializar BD
    init_db()
    yield
    # Cleanup
    if os.path.exists('test_compliance_phase0.db'):
        try:
            os.remove('test_compliance_phase0.db')
        except:
            pass


@pytest.fixture
def db():
    """Fixture para obtener conexión a BD"""
    with get_db() as conn:
        yield conn


class TestAutoDesignate5Days:
    """Tests para función auto_designate_5_days()"""

    def test_designate_5_days_when_eligible(self, db):
        """Empleado con 10+ días y <5 usados debe ser designado"""
        from services.fiscal_year import auto_designate_5_days

        # Setup: Crear empleado con 10 días otorgados, 0 usados
        c = db.cursor()
        c.execute('''
            INSERT INTO employees
            (id, employee_num, name, granted, used, balance, year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('EMP001_2025', 'EMP001', 'Test Employee', 10.0, 0.0, 10.0, 2025, datetime.now().isoformat()))
        db.commit()

        # Execute
        result = auto_designate_5_days('EMP001', 2025, 'admin')

        # Assert
        assert result['success'] is True
        assert result['days_designated'] == 5.0
        assert result['employee_num'] == 'EMP001'

        # Verify registrado en audit_log
        audit = c.execute(
            "SELECT * FROM fiscal_year_audit_log WHERE employee_num = ? AND action = ?",
            ('EMP001', 'DESIGNATE_5DAYS')
        ).fetchone()
        assert audit is not None
        assert audit['days_affected'] == 5.0


    def test_designate_5_days_exempt_less_than_10(self, db):
        """Empleado con <10 días no debe ser designado"""
        from services.fiscal_year import auto_designate_5_days

        # Setup
        c = db.cursor()
        c.execute('''
            INSERT INTO employees
            (id, employee_num, name, granted, used, balance, year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('EMP002_2025', 'EMP002', 'Short Tenure', 9.0, 0.0, 9.0, 2025, datetime.now().isoformat()))
        db.commit()

        # Execute
        result = auto_designate_5_days('EMP002', 2025, 'admin')

        # Assert
        assert result['success'] is False
        assert 'exempt' in result['reason'].lower()


    def test_designate_5_days_already_compliant(self, db):
        """Empleado que ya usó 5+ días no debe ser designado"""
        from services.fiscal_year import auto_designate_5_days

        # Setup
        c = db.cursor()
        c.execute('''
            INSERT INTO employees
            (id, employee_num, name, granted, used, balance, year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('EMP003_2025', 'EMP003', 'Compliant Employee', 10.0, 5.0, 5.0, 2025, datetime.now().isoformat()))
        db.commit()

        # Execute
        result = auto_designate_5_days('EMP003', 2025, 'admin')

        # Assert
        assert result['success'] is False
        assert 'already compliant' in result['reason'].lower()


    def test_designate_5_days_partial_usage(self, db):
        """Empleado que usó 2 días debe ser designado solo 3 días"""
        from services.fiscal_year import auto_designate_5_days

        # Setup
        c = db.cursor()
        c.execute('''
            INSERT INTO employees
            (id, employee_num, name, granted, used, balance, year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('EMP004_2025', 'EMP004', 'Partial Usage', 10.0, 2.0, 8.0, 2025, datetime.now().isoformat()))
        db.commit()

        # Execute
        result = auto_designate_5_days('EMP004', 2025, 'admin')

        # Assert
        assert result['success'] is True
        assert result['days_designated'] == 3.0


class TestLifoAuditLogging:
    """Tests para que apply_lifo_deduction() registre en audit_log"""

    def test_lifo_deduction_logged(self, db):
        """Deducción LIFO debe registrarse en audit_log"""
        from services.fiscal_year import apply_lifo_deduction

        # Setup
        c = db.cursor()
        c.execute('''
            INSERT INTO employees
            (id, employee_num, name, granted, used, balance, year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('EMP005_2025', 'EMP005', 'Deduction Test', 10.0, 0.0, 10.0, 2025, datetime.now().isoformat()))
        db.commit()

        # Execute
        result = apply_lifo_deduction('EMP005', 2.0, 2025, performed_by='admin', reason='Test deduction')

        # Assert
        assert result['success'] is True
        assert result['total_deducted'] == 2.0

        # Verify audit_log
        audit = c.execute(
            "SELECT * FROM fiscal_year_audit_log WHERE employee_num = ? AND action = ?",
            ('EMP005', 'DEDUCTION')
        ).fetchone()

        assert audit is not None
        assert audit['days_affected'] == 2.0
        assert audit['performed_by'] == 'admin'
        assert audit['balance_before'] == 10.0
        assert audit['balance_after'] == 8.0


    def test_lifo_audit_details_complete(self, db):
        """Audit log debe tener todos los detalles"""
        from services.fiscal_year import apply_lifo_deduction

        # Setup
        c = db.cursor()
        c.execute('''
            INSERT INTO employees
            (id, employee_num, name, granted, used, balance, year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('EMP006_2025', 'EMP006', 'Detail Test', 10.0, 1.0, 9.0, 2025, datetime.now().isoformat()))
        db.commit()

        # Execute
        result = apply_lifo_deduction('EMP006', 3.0, 2025, performed_by='manager', reason='Annual leave')

        # Assert
        audit = c.execute(
            "SELECT * FROM fiscal_year_audit_log WHERE employee_num = ? AND action = ?",
            ('EMP006', 'DEDUCTION')
        ).fetchone()

        assert audit is not None
        assert audit['balance_before'] == 9.0
        assert audit['balance_after'] == 6.0
        assert audit['reason'] == 'Annual leave'
        assert audit['timestamp'] is not None


class TestHireDateValidation:
    """Tests para validate_hire_date()"""

    def test_valid_hire_date(self):
        """Hire date válido debe ser aceptado"""
        from services.fiscal_year import validate_hire_date

        is_valid, message = validate_hire_date('2020-01-15')
        assert is_valid is True


    def test_future_hire_date_rejected(self):
        """Hire date en futuro debe ser rechazado"""
        from services.fiscal_year import validate_hire_date

        future_date = (date.today() + timedelta(days=1)).isoformat()
        is_valid, message = validate_hire_date(future_date)
        assert is_valid is False
        assert 'future' in message.lower()


    def test_very_old_hire_date_rejected(self):
        """Hire date > 130 años atrás debe ser rechazado"""
        from services.fiscal_year import validate_hire_date

        old_date = (date.today() - timedelta(days=130*365+1)).isoformat()
        is_valid, message = validate_hire_date(old_date)
        assert is_valid is False
        assert 'old' in message.lower()


    def test_invalid_format_rejected(self):
        """Hire date con formato inválido debe ser rechazado"""
        from services.fiscal_year import validate_hire_date

        is_valid, message = validate_hire_date('2020/01/15')
        assert is_valid is False
        assert 'format' in message.lower()


    def test_empty_hire_date_rejected(self):
        """Hire date vacío debe ser rechazado"""
        from services.fiscal_year import validate_hire_date

        is_valid, message = validate_hire_date('')
        assert is_valid is False


class TestTablesAndIndexes:
    """Tests para verificar tablas e índices"""

    def test_fiscal_year_audit_log_table_exists(self, db):
        """Tabla fiscal_year_audit_log debe existir"""
        c = db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fiscal_year_audit_log'")
        result = c.fetchone()
        assert result is not None


    def test_official_leave_designation_table_exists(self, db):
        """Tabla official_leave_designation debe existir"""
        c = db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='official_leave_designation'")
        result = c.fetchone()
        assert result is not None


    def test_carryover_audit_table_exists(self, db):
        """Tabla carryover_audit debe existir"""
        c = db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='carryover_audit'")
        result = c.fetchone()
        assert result is not None


    def test_fiscal_audit_indexes_exist(self, db):
        """Índices de fiscal_year_audit_log deben existir"""
        c = db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_fiscal_audit%'")
        indexes = c.fetchall()
        assert len(indexes) >= 3


    def test_official_leave_indexes_exist(self, db):
        """Índices de official_leave_designation deben existir"""
        c = db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_official_leave%'")
        indexes = c.fetchall()
        assert len(indexes) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
