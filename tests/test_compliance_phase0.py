"""
Tests para FASE 0 - Riesgos Críticos Legales
Compliance Expert Agent Implementation
"""

import pytest
import os
import sys
from datetime import datetime, date, timedelta

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_hire_date_validation():
    """Test: Validación de hire_date"""
    from services.fiscal_year import validate_hire_date

    # Valid date
    is_valid, msg = validate_hire_date('2020-01-15')
    assert is_valid is True, msg

    # Future date
    future_date = (date.today() + timedelta(days=1)).isoformat()
    is_valid, msg = validate_hire_date(future_date)
    assert is_valid is False, "Future dates should be rejected"

    # Very old date
    old_date = (date.today() - timedelta(days=130*365+1)).isoformat()
    is_valid, msg = validate_hire_date(old_date)
    assert is_valid is False, "Very old dates should be rejected"

    # Invalid format
    is_valid, msg = validate_hire_date('2020/01/15')
    assert is_valid is False, "Invalid format should be rejected"

    # Empty
    is_valid, msg = validate_hire_date('')
    assert is_valid is False, "Empty dates should be rejected"


def test_fiscal_year_audit_log_structure():
    """Test: Estructura de la tabla fiscal_year_audit_log"""
    import sqlite3
    os.environ['DATABASE_PATH'] = 'test_phase0.db'

    # Crear BD
    from database import init_db
    if os.path.exists('test_phase0.db'):
        os.remove('test_phase0.db')

    init_db()

    # Verificar tabla
    conn = sqlite3.connect('test_phase0.db')
    c = conn.cursor()

    # Verificar que la tabla existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fiscal_year_audit_log'")
    assert c.fetchone() is not None, "fiscal_year_audit_log table does not exist"

    # Verificar índices
    c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_fiscal_audit%'")
    indexes = c.fetchall()
    assert len(indexes) >= 2, f"Expected at least 2 indexes, found {len(indexes)}"

    conn.close()
    os.remove('test_phase0.db')


def test_official_leave_designation_table_structure():
    """Test: Estructura de official_leave_designation"""
    import sqlite3
    os.environ['DATABASE_PATH'] = 'test_phase0.db'

    from database import init_db
    if os.path.exists('test_phase0.db'):
        os.remove('test_phase0.db')

    init_db()

    conn = sqlite3.connect('test_phase0.db')
    c = conn.cursor()

    # Verificar tabla
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='official_leave_designation'")
    assert c.fetchone() is not None, "official_leave_designation table does not exist"

    conn.close()
    os.remove('test_phase0.db')


def test_carryover_audit_table_structure():
    """Test: Estructura de carryover_audit"""
    import sqlite3
    os.environ['DATABASE_PATH'] = 'test_phase0.db'

    from database import init_db
    if os.path.exists('test_phase0.db'):
        os.remove('test_phase0.db')

    init_db()

    conn = sqlite3.connect('test_phase0.db')
    c = conn.cursor()

    # Verificar tabla
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='carryover_audit'")
    assert c.fetchone() is not None, "carryover_audit table does not exist"

    conn.close()
    os.remove('test_phase0.db')


def test_5day_designation_function():
    """Test: Función auto_designate_5_days()"""
    import sqlite3
    os.environ['DATABASE_PATH'] = 'test_phase0.db'

    from database import init_db, get_db
    from services.fiscal_year import auto_designate_5_days

    if os.path.exists('test_phase0.db'):
        os.remove('test_phase0.db')

    init_db()

    # Insert test employee
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO employees
            (id, employee_num, name, granted, used, balance, year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('TEST001_2025', 'TEST001', 'Test User', 10.0, 0.0, 10.0, 2025, datetime.now().isoformat()))
        conn.commit()

    # Execute designation
    result = auto_designate_5_days('TEST001', 2025, 'admin')

    assert result['success'] is True, f"Designation failed: {result}"
    assert result['days_designated'] == 5.0, f"Expected 5 days, got {result['days_designated']}"

    # Verify audit log entry
    with get_db() as conn:
        c = conn.cursor()
        audit = c.execute(
            "SELECT * FROM fiscal_year_audit_log WHERE employee_num = ? AND action = ?",
            ('TEST001', 'DESIGNATE_5DAYS')
        ).fetchone()
        assert audit is not None, "No audit log entry found"
        assert audit['days_affected'] == 5.0, "Audit log has wrong days_affected"

    os.remove('test_phase0.db')


def test_lifo_deduction_audit():
    """Test: Función apply_lifo_deduction() registra en audit"""
    import sqlite3
    os.environ['DATABASE_PATH'] = 'test_phase0.db'

    from database import init_db, get_db
    from services.fiscal_year import apply_lifo_deduction

    if os.path.exists('test_phase0.db'):
        os.remove('test_phase0.db')

    init_db()

    # Insert test employee
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO employees
            (id, employee_num, name, granted, used, balance, year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('TEST002_2025', 'TEST002', 'Test User 2', 10.0, 0.0, 10.0, 2025, datetime.now().isoformat()))
        conn.commit()

    # Execute deduction
    result = apply_lifo_deduction('TEST002', 2.0, 2025, performed_by='admin', reason='Test deduction')

    assert result['success'] is True, f"Deduction failed: {result}"
    assert result['total_deducted'] == 2.0, f"Expected 2 days deducted, got {result['total_deducted']}"

    # Verify audit log
    with get_db() as conn:
        c = conn.cursor()
        audit = c.execute(
            "SELECT * FROM fiscal_year_audit_log WHERE employee_num = ? AND action = ?",
            ('TEST002', 'DEDUCTION')
        ).fetchone()
        assert audit is not None, "No audit log entry found"
        assert audit['days_affected'] == 2.0, "Wrong days_affected in audit"
        assert audit['balance_before'] == 10.0, "Wrong balance_before in audit"
        assert audit['balance_after'] == 8.0, "Wrong balance_after in audit"
        assert audit['performed_by'] == 'admin', "Wrong performed_by in audit"

    os.remove('test_phase0.db')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
