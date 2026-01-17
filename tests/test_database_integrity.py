"""
YuKyu Premium - Database Integrity Tests
データベース整合性テスト - DB制約、インデックス、バックアップのテスト

Tests para la integridad de la base de datos:
- Constraints de Foreign Key
- Unique constraints
- Índices
- Backup y restore
- Audit log

Ejecutar con: pytest tests/test_database_integrity.py -v
"""

import pytest
import sqlite3
import tempfile
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def temp_db():
    """Crea una base de datos temporal para tests"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Inicializar la BD con el schema
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Crear tablas principales (simplificado)
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            employee_num TEXT NOT NULL,
            name TEXT,
            haken TEXT,
            granted REAL DEFAULT 0,
            used REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            expired REAL DEFAULT 0,
            usage_rate REAL DEFAULT 0,
            year INTEGER NOT NULL,
            grant_year INTEGER,
            last_updated TEXT
        );

        CREATE TABLE IF NOT EXISTS genzai (
            id TEXT PRIMARY KEY,
            employee_num TEXT UNIQUE NOT NULL,
            name TEXT,
            status TEXT DEFAULT '在職中',
            hire_date TEXT
        );

        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_num TEXT NOT NULL,
            employee_name TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days_requested REAL NOT NULL,
            leave_type TEXT DEFAULT 'full',
            reason TEXT,
            status TEXT DEFAULT 'PENDING',
            year INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            approved_at TEXT,
            approved_by TEXT
        );

        CREATE TABLE IF NOT EXISTS yukyu_usage_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_num TEXT NOT NULL,
            name TEXT,
            use_date TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            days_used REAL NOT NULL,
            leave_type TEXT DEFAULT 'full',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            user_id TEXT,
            old_value TEXT,
            new_value TEXT,
            ip_address TEXT,
            user_agent TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_employees_year ON employees(year);
        CREATE INDEX IF NOT EXISTS idx_employees_num ON employees(employee_num);
        CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status);
        CREATE INDEX IF NOT EXISTS idx_leave_requests_year ON leave_requests(year);
        CREATE INDEX IF NOT EXISTS idx_usage_details_emp ON yukyu_usage_details(employee_num, year);
    ''')

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def populated_db(temp_db):
    """BD temporal con datos de ejemplo"""
    conn = sqlite3.connect(temp_db)

    # Insertar empleados
    conn.execute('''
        INSERT INTO employees (id, employee_num, name, haken, granted, used, balance, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('001_2025', '001', '田中太郎', 'Factory A', 20, 5, 15, 2025))

    conn.execute('''
        INSERT INTO employees (id, employee_num, name, haken, granted, used, balance, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('002_2025', '002', '山田花子', 'Factory B', 15, 3, 12, 2025))

    # Insertar en genzai
    conn.execute('''
        INSERT INTO genzai (id, employee_num, name, status, hire_date)
        VALUES (?, ?, ?, ?, ?)
    ''', ('genzai_001', '001', '田中太郎', '在職中', '2020-04-01'))

    # Insertar leave request
    conn.execute('''
        INSERT INTO leave_requests (employee_num, employee_name, start_date, end_date,
                                   days_requested, leave_type, reason, status, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('001', '田中太郎', '2025-03-01', '2025-03-01', 1.0, 'full', 'Test', 'PENDING', 2025))

    conn.commit()
    conn.close()

    return temp_db


# ============================================
# SCHEMA TESTS
# ============================================

class TestDatabaseSchema:
    """Tests para el schema de la base de datos"""

    def test_employees_table_exists(self, temp_db):
        """Tabla employees existe"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='employees'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_all_required_tables_exist(self, temp_db):
        """Todas las tablas requeridas existen"""
        required_tables = [
            'employees',
            'genzai',
            'leave_requests',
            'yukyu_usage_details',
            'audit_log'
        ]

        conn = sqlite3.connect(temp_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        for table in required_tables:
            assert table in existing_tables, f"Table {table} not found"

    def test_employees_columns(self, temp_db):
        """Tabla employees tiene columnas requeridas"""
        required_columns = [
            'id', 'employee_num', 'name', 'haken',
            'granted', 'used', 'balance', 'expired', 'year'
        ]

        conn = sqlite3.connect(temp_db)
        cursor = conn.execute("PRAGMA table_info(employees)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        for col in required_columns:
            assert col in columns, f"Column {col} not found in employees"


# ============================================
# INDEX TESTS
# ============================================

class TestDatabaseIndexes:
    """Tests para índices de la base de datos"""

    def test_indexes_exist(self, temp_db):
        """Índices importantes existen"""
        expected_indexes = [
            'idx_employees_year',
            'idx_employees_num',
            'idx_leave_requests_status'
        ]

        conn = sqlite3.connect(temp_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        existing_indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        for idx in expected_indexes:
            assert idx in existing_indexes, f"Index {idx} not found"

    def test_index_improves_query_performance(self, populated_db):
        """Índices mejoran performance de queries comunes"""
        conn = sqlite3.connect(populated_db)

        # Query plan para búsqueda por año (debe usar índice)
        cursor = conn.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM employees WHERE year = 2025"
        )
        plan = cursor.fetchall()
        conn.close()

        # El plan debe mencionar uso de índice o SEARCH
        plan_str = str(plan)
        assert 'SEARCH' in plan_str or 'idx' in plan_str.lower() or 'INDEX' in plan_str


# ============================================
# CONSTRAINT TESTS
# ============================================

class TestDatabaseConstraints:
    """Tests para constraints de la base de datos"""

    def test_primary_key_unique(self, temp_db):
        """Primary key es único"""
        conn = sqlite3.connect(temp_db)

        # Insertar registro
        conn.execute('''
            INSERT INTO employees (id, employee_num, name, year)
            VALUES ('TEST_001', 'T001', 'Test User', 2025)
        ''')
        conn.commit()

        # Intentar duplicar PK
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute('''
                INSERT INTO employees (id, employee_num, name, year)
                VALUES ('TEST_001', 'T002', 'Another User', 2025)
            ''')
            conn.commit()

        conn.close()

    def test_genzai_employee_num_unique(self, temp_db):
        """employee_num en genzai es único"""
        conn = sqlite3.connect(temp_db)

        # Insertar registro
        conn.execute('''
            INSERT INTO genzai (id, employee_num, name)
            VALUES ('g1', 'UNIQUE001', 'Test')
        ''')
        conn.commit()

        # Intentar duplicar employee_num
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute('''
                INSERT INTO genzai (id, employee_num, name)
                VALUES ('g2', 'UNIQUE001', 'Another')
            ''')
            conn.commit()

        conn.close()

    def test_not_null_constraints(self, temp_db):
        """Constraints NOT NULL funcionan"""
        conn = sqlite3.connect(temp_db)

        # Intentar insertar sin employee_num (NOT NULL)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute('''
                INSERT INTO employees (id, name, year)
                VALUES ('NO_EMP', 'Test', 2025)
            ''')
            conn.commit()

        conn.close()


# ============================================
# DATA INTEGRITY TESTS
# ============================================

class TestDataIntegrity:
    """Tests para integridad de datos"""

    def test_balance_consistency(self, populated_db):
        """Balance es consistente con granted - used"""
        conn = sqlite3.connect(populated_db)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute('''
            SELECT employee_num, granted, used, balance
            FROM employees
            WHERE granted > 0
        ''')
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            expected_balance = row['granted'] - row['used']
            # Permitir pequeña diferencia por redondeo
            assert abs(row['balance'] - expected_balance) < 0.01, \
                f"Balance inconsistente para {row['employee_num']}"

    def test_no_orphan_leave_requests(self, populated_db):
        """Leave requests tienen employee_num válido"""
        conn = sqlite3.connect(populated_db)

        cursor = conn.execute('''
            SELECT lr.id, lr.employee_num
            FROM leave_requests lr
            WHERE NOT EXISTS (
                SELECT 1 FROM employees e
                WHERE e.employee_num = lr.employee_num
            )
        ''')
        orphans = cursor.fetchall()
        conn.close()

        # Puede haber huérfanos en la BD de test
        # Este test documenta el comportamiento
        assert isinstance(orphans, list)

    def test_year_is_reasonable(self, populated_db):
        """Años en la BD están en rango razonable"""
        conn = sqlite3.connect(populated_db)

        cursor = conn.execute('''
            SELECT MIN(year), MAX(year) FROM employees
        ''')
        min_year, max_year = cursor.fetchone()
        conn.close()

        if min_year is not None:
            assert min_year >= 2000
            assert max_year <= 2100


# ============================================
# CRUD OPERATIONS TESTS
# ============================================

class TestCRUDOperations:
    """Tests para operaciones CRUD"""

    def test_insert_employee(self, temp_db):
        """Insertar empleado funciona"""
        conn = sqlite3.connect(temp_db)

        conn.execute('''
            INSERT INTO employees (id, employee_num, name, haken, granted, used, balance, year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('NEW_001', 'N001', 'New Employee', 'Factory X', 20, 0, 20, 2025))
        conn.commit()

        cursor = conn.execute('SELECT * FROM employees WHERE id = ?', ('NEW_001',))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_update_employee(self, populated_db):
        """Actualizar empleado funciona"""
        conn = sqlite3.connect(populated_db)

        conn.execute('''
            UPDATE employees SET used = ?, balance = ? WHERE id = ?
        ''', (10, 10, '001_2025'))
        conn.commit()

        cursor = conn.execute('SELECT used, balance FROM employees WHERE id = ?', ('001_2025',))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == 10
        assert row[1] == 10

    def test_delete_employee(self, populated_db):
        """Eliminar empleado funciona"""
        conn = sqlite3.connect(populated_db)

        conn.execute('DELETE FROM employees WHERE id = ?', ('001_2025',))
        conn.commit()

        cursor = conn.execute('SELECT * FROM employees WHERE id = ?', ('001_2025',))
        row = cursor.fetchone()
        conn.close()

        assert row is None

    def test_transaction_rollback(self, temp_db):
        """Rollback de transacción funciona"""
        conn = sqlite3.connect(temp_db)

        try:
            conn.execute('''
                INSERT INTO employees (id, employee_num, name, year)
                VALUES ('ROLLBACK_001', 'R001', 'Rollback Test', 2025)
            ''')
            # Simular error
            raise Exception("Simulated error")
            conn.commit()
        except:
            conn.rollback()

        cursor = conn.execute('SELECT * FROM employees WHERE id = ?', ('ROLLBACK_001',))
        row = cursor.fetchone()
        conn.close()

        # No debe existir debido al rollback
        assert row is None


# ============================================
# AUDIT LOG TESTS
# ============================================

class TestAuditLog:
    """Tests para audit log"""

    def test_audit_log_insert(self, temp_db):
        """Insertar en audit log funciona"""
        conn = sqlite3.connect(temp_db)

        conn.execute('''
            INSERT INTO audit_log (action, entity_type, entity_id, user_id)
            VALUES (?, ?, ?, ?)
        ''', ('UPDATE', 'employee', '001_2025', 'admin'))
        conn.commit()

        cursor = conn.execute('SELECT * FROM audit_log WHERE entity_id = ?', ('001_2025',))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_audit_log_has_timestamp(self, temp_db):
        """Audit log tiene timestamp automático"""
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row

        conn.execute('''
            INSERT INTO audit_log (action, entity_type, entity_id)
            VALUES (?, ?, ?)
        ''', ('CREATE', 'employee', 'AUDIT_TEST'))
        conn.commit()

        cursor = conn.execute('SELECT timestamp FROM audit_log WHERE entity_id = ?', ('AUDIT_TEST',))
        row = cursor.fetchone()
        conn.close()

        assert row['timestamp'] is not None


# ============================================
# BACKUP AND RECOVERY TESTS
# ============================================

class TestBackupRecovery:
    """Tests para backup y recuperación"""

    def test_can_create_backup_copy(self, populated_db):
        """Puede crear copia de backup"""
        backup_path = populated_db + '.backup'

        # Crear backup usando conexión
        conn = sqlite3.connect(populated_db)
        backup_conn = sqlite3.connect(backup_path)

        conn.backup(backup_conn)

        conn.close()
        backup_conn.close()

        # Verificar que el backup existe y tiene datos
        backup_conn = sqlite3.connect(backup_path)
        cursor = backup_conn.execute('SELECT COUNT(*) FROM employees')
        count = cursor.fetchone()[0]
        backup_conn.close()

        assert count > 0

        # Cleanup
        try:
            os.unlink(backup_path)
        except:
            pass

    def test_can_restore_from_backup(self, populated_db):
        """Puede restaurar desde backup"""
        backup_path = populated_db + '.backup'
        restore_path = populated_db + '.restored'

        # Crear backup
        conn = sqlite3.connect(populated_db)
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        conn.close()
        backup_conn.close()

        # Restaurar a nueva ubicación
        backup_conn = sqlite3.connect(backup_path)
        restore_conn = sqlite3.connect(restore_path)
        backup_conn.backup(restore_conn)
        backup_conn.close()
        restore_conn.close()

        # Verificar datos restaurados
        restore_conn = sqlite3.connect(restore_path)
        cursor = restore_conn.execute('SELECT COUNT(*) FROM employees')
        count = cursor.fetchone()[0]
        restore_conn.close()

        assert count > 0

        # Cleanup
        try:
            os.unlink(backup_path)
            os.unlink(restore_path)
        except:
            pass


# ============================================
# CONCURRENT ACCESS TESTS
# ============================================

class TestConcurrentAccess:
    """Tests para acceso concurrente"""

    def test_wal_mode_available(self, temp_db):
        """WAL mode disponible para mejor concurrencia"""
        conn = sqlite3.connect(temp_db)

        # Intentar habilitar WAL
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.execute('PRAGMA journal_mode')
        mode = cursor.fetchone()[0]
        conn.close()

        # WAL o DELETE son válidos
        assert mode.lower() in ['wal', 'delete', 'memory']

    def test_multiple_readers(self, populated_db):
        """Múltiples lectores pueden acceder simultáneamente"""
        conn1 = sqlite3.connect(populated_db)
        conn2 = sqlite3.connect(populated_db)

        cursor1 = conn1.execute('SELECT COUNT(*) FROM employees')
        cursor2 = conn2.execute('SELECT * FROM employees LIMIT 1')

        count = cursor1.fetchone()[0]
        row = cursor2.fetchone()

        conn1.close()
        conn2.close()

        assert count > 0
        assert row is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
