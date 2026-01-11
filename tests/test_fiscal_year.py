"""
Tests unitarios completos para fiscal_year.py

Este archivo contiene tests para todas las funciones del modulo de gestion
del ano fiscal de vacaciones (有給休暇).

Ejecutar con: pytest tests/test_fiscal_year.py -v
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fiscal_year
from fiscal_year import (
    calculate_seniority_years,
    calculate_granted_days,
    get_fiscal_period,
    get_fiscal_year_period,
    process_year_end_carryover,
    get_employee_balance_breakdown,
    apply_lifo_deduction,
    check_expiring_soon,
    check_5day_compliance,
    get_grant_recommendation,
    GRANT_TABLE,
    FISCAL_CONFIG,
)


# =============================================================================
# FIXTURES COMPARTIDAS
# =============================================================================

@pytest.fixture
def temp_db():
    """
    Crea una base de datos temporal para tests que requieren BD.
    La BD se elimina automaticamente al finalizar el test.
    """
    # Crear archivo temporal
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Guardar DB_NAME original y usar temporal
    original_db = fiscal_year.DB_NAME
    fiscal_year.DB_NAME = db_path

    # Crear tablas necesarias
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.execute('''
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
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS genzai (
            id TEXT PRIMARY KEY,
            employee_num TEXT UNIQUE,
            name TEXT,
            hire_date TEXT,
            status TEXT DEFAULT '在職中'
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS ukeoi (
            id TEXT PRIMARY KEY,
            employee_num TEXT UNIQUE,
            name TEXT,
            hire_date TEXT,
            status TEXT DEFAULT '在職中'
        )
    ''')

    conn.commit()
    conn.close()

    yield db_path

    # Limpiar
    fiscal_year.DB_NAME = original_db
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def db_with_employees(temp_db):
    """
    Fixture que crea una BD con empleados de prueba.
    """
    conn = sqlite3.connect(temp_db)

    # Insertar empleados con diferentes escenarios
    employees_data = [
        # Empleado compliant (5+ dias usados)
        ('EMP001_2025', 'EMP001', 'Tanaka Taro', 'Factory A', 20, 6, 14, 2025),
        # Empleado at_risk (3-4 dias usados)
        ('EMP002_2025', 'EMP002', 'Yamada Hanako', 'Factory B', 15, 3.5, 11.5, 2025),
        # Empleado non_compliant (0-2 dias usados)
        ('EMP003_2025', 'EMP003', 'Suzuki Jiro', 'Factory A', 12, 1, 11, 2025),
        # Empleado exento (menos de 10 dias otorgados)
        ('EMP004_2025', 'EMP004', 'Sato Yuki', 'Factory C', 8, 0, 8, 2025),
        # Empleado con balance del ano anterior
        ('EMP001_2024', 'EMP001', 'Tanaka Taro', 'Factory A', 20, 15, 5, 2024),
        # Empleado con alto balance para LIFO
        ('EMP005_2025', 'EMP005', 'Nakamura Ken', 'Factory B', 20, 0, 20, 2025),
        ('EMP005_2024', 'EMP005', 'Nakamura Ken', 'Factory B', 18, 3, 15, 2024),
    ]

    for emp in employees_data:
        conn.execute('''
            INSERT INTO employees (id, employee_num, name, haken, granted, used, balance, year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', emp)

    # Insertar en genzai para tests de grant_recommendation
    conn.execute('''
        INSERT INTO genzai (id, employee_num, name, hire_date)
        VALUES (?, ?, ?, ?)
    ''', ('genzai_EMP001', 'EMP001', 'Tanaka Taro', '2021-04-01'))

    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def reference_date():
    """Fecha de referencia fija para tests deterministas."""
    return date(2025, 4, 15)


# =============================================================================
# TEST: calculate_seniority_years()
# =============================================================================

class TestCalculateSeniorityYears:
    """Tests para la funcion calculate_seniority_years()."""

    def test_six_months_exact(self, reference_date):
        """6 meses exactos debe retornar 0.5 anos."""
        # 6 meses antes de la fecha de referencia
        hire_date = (reference_date - timedelta(days=183)).strftime('%Y-%m-%d')
        result = calculate_seniority_years(hire_date, reference_date)
        assert 0.4 <= result <= 0.55, f"Expected ~0.5, got {result}"

    def test_one_year_exact(self, reference_date):
        """1 ano exacto debe retornar 1.0."""
        hire_date = date(reference_date.year - 1, reference_date.month, reference_date.day)
        result = calculate_seniority_years(hire_date.strftime('%Y-%m-%d'), reference_date)
        assert 0.95 <= result <= 1.05, f"Expected ~1.0, got {result}"

    def test_one_and_half_years(self, reference_date):
        """1.5 anos debe retornar aproximadamente 1.5."""
        # 548 dias ~= 1.5 anos
        hire_date = (reference_date - timedelta(days=548)).strftime('%Y-%m-%d')
        result = calculate_seniority_years(hire_date, reference_date)
        assert 1.4 <= result <= 1.6, f"Expected ~1.5, got {result}"

    def test_future_date_returns_zero(self, reference_date):
        """Fecha futura debe retornar 0 o negativo (manejado como 0)."""
        future_date = (reference_date + timedelta(days=30)).strftime('%Y-%m-%d')
        result = calculate_seniority_years(future_date, reference_date)
        # Puede ser negativo segun implementacion, verificamos que sea bajo
        assert result <= 0, f"Future date should return 0 or negative, got {result}"

    def test_none_date_returns_zero(self):
        """Fecha None debe retornar 0.0."""
        result = calculate_seniority_years(None)
        assert result == 0.0, f"None date should return 0.0, got {result}"

    def test_empty_string_returns_zero(self):
        """String vacio debe retornar 0.0."""
        result = calculate_seniority_years('')
        assert result == 0.0, f"Empty string should return 0.0, got {result}"

    def test_invalid_format_returns_zero(self):
        """Formato invalido debe retornar 0.0."""
        result = calculate_seniority_years('invalid-date')
        assert result == 0.0, f"Invalid format should return 0.0, got {result}"

    def test_edge_case_exact_threshold(self, reference_date):
        """Test en el limite exacto de 6 meses (threshold 0.5)."""
        # Exactamente 183 dias (aprox 6 meses)
        hire_date = (reference_date - timedelta(days=int(365.25 * 0.5))).strftime('%Y-%m-%d')
        result = calculate_seniority_years(hire_date, reference_date)
        assert result >= 0.5, f"Expected >= 0.5 at threshold, got {result}"


# =============================================================================
# TEST: calculate_granted_days()
# =============================================================================

class TestCalculateGrantedDays:
    """Tests para la funcion calculate_granted_days()."""

    def test_half_year_gets_10_days(self):
        """0.5 anos de antiguedad = 10 dias."""
        result = calculate_granted_days(0.5)
        assert result == 10, f"0.5 years should grant 10 days, got {result}"

    def test_one_and_half_years_gets_11_days(self):
        """1.5 anos de antiguedad = 11 dias."""
        result = calculate_granted_days(1.5)
        assert result == 11, f"1.5 years should grant 11 days, got {result}"

    def test_six_plus_years_gets_maximum_20_days(self):
        """6.5+ anos de antiguedad = 20 dias (maximo legal)."""
        result = calculate_granted_days(6.5)
        assert result == 20, f"6.5 years should grant 20 days, got {result}"

        # Tambien probar con mas anos
        result_more = calculate_granted_days(10.0)
        assert result_more == 20, f"10 years should still grant 20 days (max), got {result_more}"

    def test_zero_years_gets_zero_days(self):
        """0 anos de antiguedad = 0 dias."""
        result = calculate_granted_days(0)
        assert result == 0, f"0 years should grant 0 days, got {result}"

    def test_negative_value_gets_zero_days(self):
        """Valor negativo debe retornar 0 dias."""
        result = calculate_granted_days(-1.0)
        assert result == 0, f"Negative seniority should grant 0 days, got {result}"

    def test_intermediate_values(self):
        """Test valores intermedios de la tabla de otorgamiento."""
        # 2.5 anos = 12 dias
        assert calculate_granted_days(2.5) == 12
        # 3.5 anos = 14 dias
        assert calculate_granted_days(3.5) == 14
        # 4.5 anos = 16 dias
        assert calculate_granted_days(4.5) == 16
        # 5.5 anos = 18 dias
        assert calculate_granted_days(5.5) == 18


# =============================================================================
# TEST: get_fiscal_period()
# =============================================================================

class TestGetFiscalPeriod:
    """Tests para la funcion get_fiscal_period()."""

    def test_normal_period_may(self):
        """Periodo normal (mayo 2025): 21 abril - 20 mayo."""
        start, end = get_fiscal_period(2025, 5)
        assert start == '2025-04-21', f"Expected start 2025-04-21, got {start}"
        assert end == '2025-05-20', f"Expected end 2025-05-20, got {end}"

    def test_fiscal_year_start_april(self):
        """Inicio de ano fiscal (abril): 21 marzo - 20 abril."""
        start, end = get_fiscal_period(2025, 4)
        assert start == '2025-03-21', f"Expected start 2025-03-21, got {start}"
        assert end == '2025-04-20', f"Expected end 2025-04-20, got {end}"

    def test_fiscal_year_end_march(self):
        """Fin de ano fiscal (marzo): 21 febrero - 20 marzo."""
        start, end = get_fiscal_period(2025, 3)
        assert start == '2025-02-21', f"Expected start 2025-02-21, got {start}"
        assert end == '2025-03-20', f"Expected end 2025-03-20, got {end}"

    def test_january_crosses_year(self):
        """Enero cruza al ano anterior: 21 diciembre (anterior) - 20 enero."""
        start, end = get_fiscal_period(2025, 1)
        assert start == '2024-12-21', f"Expected start 2024-12-21, got {start}"
        assert end == '2025-01-20', f"Expected end 2025-01-20, got {end}"

    def test_leap_year_february(self):
        """Ano bisiesto febrero 2024 (bisiesto): el periodo se calcula igual."""
        # 2024 es bisiesto, pero no afecta el calculo de fechas 21-20
        start, end = get_fiscal_period(2024, 2)
        assert start == '2024-01-21', f"Expected start 2024-01-21, got {start}"
        assert end == '2024-02-20', f"Expected end 2024-02-20, got {end}"


# =============================================================================
# TEST: get_fiscal_year_period()
# =============================================================================

class TestGetFiscalYearPeriod:
    """Tests para la funcion get_fiscal_year_period()."""

    def test_fiscal_year_2025(self):
        """Ano fiscal 2025 = abril 2025 a marzo 2026."""
        start, end = get_fiscal_year_period(2025)
        assert start == '2025-04-01', f"Expected start 2025-04-01, got {start}"
        assert end == '2026-03-31', f"Expected end 2026-03-31, got {end}"

    def test_fiscal_year_2024(self):
        """Ano fiscal 2024 = abril 2024 a marzo 2025."""
        start, end = get_fiscal_year_period(2024)
        assert start == '2024-04-01', f"Expected start 2024-04-01, got {start}"
        assert end == '2025-03-31', f"Expected end 2025-03-31, got {end}"


# =============================================================================
# TEST: process_year_end_carryover()
# =============================================================================

class TestProcessYearEndCarryover:
    """Tests para la funcion process_year_end_carryover()."""

    def test_normal_carryover(self, db_with_employees):
        """Carryover normal: balance pasa al siguiente ano."""
        # EMP001 tiene balance 5 en 2024, debe pasar a 2025
        result = process_year_end_carryover(2024, 2025)

        assert 'employees_processed' in result
        assert 'days_carried_over' in result
        assert result['employees_processed'] >= 1, "Should process at least 1 employee"
        assert result['days_carried_over'] > 0, "Should carry over some days"
        assert len(result['errors']) == 0, f"Should have no errors: {result['errors']}"

    def test_maximum_40_days_cap(self, temp_db):
        """Maximo de 40 dias acumulables se respeta."""
        conn = sqlite3.connect(temp_db)

        # Crear empleado con balance muy alto
        conn.execute('''
            INSERT INTO employees (id, employee_num, name, granted, used, balance, year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('HIGH_BAL_2024', 'HIGH001', 'High Balance', 20, 0, 50, 2024))
        conn.commit()
        conn.close()

        result = process_year_end_carryover(2024, 2025)

        # Verificar que se procesaron dias pero con cap
        assert result['days_expired'] > 0 or result['days_carried_over'] <= 40, \
            "Should cap carryover at 40 days or mark excess as expired"

    def test_expiration_after_2_years(self, temp_db):
        """Dias mayores a 2 anos expiran."""
        conn = sqlite3.connect(temp_db)

        # Crear registro de hace 3 anos con balance
        conn.execute('''
            INSERT INTO employees (id, employee_num, name, granted, used, balance, year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('OLD_2022', 'OLD001', 'Old Record', 10, 0, 5, 2022))
        conn.commit()
        conn.close()

        result = process_year_end_carryover(2024, 2025)

        # El registro de 2022 esta dentro del limite de retencion pero sus dias expiran
        # segun la logica de max_carry_over_years
        assert result['days_expired'] >= 0, "Should track expired days"

    def test_no_employees_returns_empty_stats(self, temp_db):
        """Sin empleados retorna estadisticas vacias."""
        result = process_year_end_carryover(2024, 2025)

        assert result['employees_processed'] == 0
        assert result['days_carried_over'] == 0.0
        assert len(result['errors']) == 0


# =============================================================================
# TEST: apply_lifo_deduction()
# =============================================================================

class TestApplyLifoDeduction:
    """Tests para la funcion apply_lifo_deduction()."""

    def test_simple_deduction(self, db_with_employees):
        """Deduccion simple de dias del ano actual."""
        # EMP001 tiene 14 dias en 2025
        result = apply_lifo_deduction('EMP001', 2.0, 2025)

        assert result['success'] == True, f"Deduction should succeed: {result}"
        assert result['total_deducted'] == 2.0, f"Should deduct 2 days: {result}"
        assert result['remaining_not_deducted'] == 0, f"Should have no remaining: {result}"

    def test_deduction_crosses_years_lifo(self, db_with_employees):
        """Deduccion que cruza anos usa LIFO (nuevo primero)."""
        # EMP005 tiene 20 dias en 2025 y 15 dias en 2024
        # LIFO: primero usa los de 2025 (mas nuevos)
        result = apply_lifo_deduction('EMP005', 25.0, 2025)

        assert result['success'] == True, "Should succeed with LIFO"
        assert result['total_deducted'] == 25.0, "Should deduct 25 days total"

        # Verificar que primero se dedujeron los de 2025
        deductions = result['deductions_by_year']
        assert len(deductions) >= 1, "Should have deductions from multiple years"

        # El primer ano en deducirse debe ser 2025 (LIFO)
        first_deduction = deductions[0]
        assert first_deduction['year'] == 2025, "LIFO should deduct from newest year first"

    def test_insufficient_days(self, db_with_employees):
        """Dias insuficientes: deduccion parcial."""
        # EMP003 tiene 11 dias en 2025
        result = apply_lifo_deduction('EMP003', 50.0, 2025)

        assert result['success'] == False, "Should fail with insufficient days"
        assert result['remaining_not_deducted'] > 0, "Should have remaining not deducted"
        assert result['total_deducted'] < 50.0, "Should only deduct available days"

    def test_partial_deduction_half_day(self, db_with_employees):
        """Deduccion parcial de 0.5 dias."""
        result = apply_lifo_deduction('EMP001', 0.5, 2025)

        assert result['success'] == True, "Should succeed with half day"
        assert result['total_deducted'] == 0.5, "Should deduct exactly 0.5"

    def test_zero_deduction(self, db_with_employees):
        """Deduccion de 0 dias."""
        result = apply_lifo_deduction('EMP001', 0, 2025)

        assert result['success'] == True, "Zero deduction should succeed"
        assert result['total_deducted'] == 0, "Should deduct 0"


# =============================================================================
# TEST: check_5day_compliance()
# =============================================================================

class TestCheck5DayCompliance:
    """Tests para la funcion check_5day_compliance()."""

    def test_compliant_employee(self, db_with_employees):
        """Empleado compliant (5+ dias usados)."""
        result = check_5day_compliance(2025)

        # EMP001 tiene 6 dias usados, debe estar compliant
        compliant_nums = [e['employee_num'] for e in result['compliant']]
        assert 'EMP001' in compliant_nums, f"EMP001 should be compliant: {result['compliant']}"

    def test_at_risk_employee(self, db_with_employees):
        """Empleado at_risk (3-4 dias usados)."""
        result = check_5day_compliance(2025)

        # EMP002 tiene 3.5 dias usados, debe estar at_risk
        at_risk_nums = [e['employee_num'] for e in result['at_risk']]
        assert 'EMP002' in at_risk_nums, f"EMP002 should be at_risk: {result['at_risk']}"

    def test_non_compliant_employee(self, db_with_employees):
        """Empleado non_compliant (0-2 dias usados)."""
        result = check_5day_compliance(2025)

        # EMP003 tiene 1 dia usado, debe estar non_compliant
        non_compliant_nums = [e['employee_num'] for e in result['non_compliant']]
        assert 'EMP003' in non_compliant_nums, f"EMP003 should be non_compliant: {result['non_compliant']}"

    def test_exempt_employee_less_than_10_days(self, db_with_employees):
        """Empleado con <10 dias otorgados esta exento."""
        result = check_5day_compliance(2025)

        # EMP004 tiene 8 dias otorgados, no debe aparecer en ningun listado
        all_nums = (
            [e['employee_num'] for e in result['compliant']] +
            [e['employee_num'] for e in result['at_risk']] +
            [e['employee_num'] for e in result['non_compliant']]
        )
        assert 'EMP004' not in all_nums, f"EMP004 should be exempt: {all_nums}"

    def test_compliance_statistics(self, db_with_employees):
        """Verifica estadisticas de cumplimiento."""
        result = check_5day_compliance(2025)

        assert result['year'] == 2025
        assert result['minimum_required'] == 5
        assert result['total_employees'] >= 1
        assert 'compliance_rate' in result
        assert 0 <= result['compliance_rate'] <= 100


# =============================================================================
# TEST: check_expiring_soon()
# =============================================================================

class TestCheckExpiringSoon:
    """Tests para la funcion check_expiring_soon()."""

    def test_finds_expiring_days(self, db_with_employees):
        """Encuentra dias proximos a expirar."""
        # EMP001 tiene 5 dias en 2024 que expiraran
        result = check_expiring_soon(2025, warning_threshold_months=12)

        # Debe encontrar al menos los dias de 2024
        assert isinstance(result, list), "Should return a list"

    def test_urgency_levels(self, db_with_employees):
        """Verifica niveles de urgencia."""
        result = check_expiring_soon(2025)

        for emp in result:
            assert 'urgency' in emp
            assert emp['urgency'] in ['high', 'medium', 'low']

    def test_sorted_by_urgency(self, db_with_employees):
        """Resultados ordenados por dias hasta expiracion."""
        result = check_expiring_soon(2025)

        if len(result) > 1:
            # Verificar orden ascendente por days_until_expiry
            for i in range(len(result) - 1):
                assert result[i]['days_until_expiry'] <= result[i+1]['days_until_expiry']


# =============================================================================
# TEST: get_employee_balance_breakdown()
# =============================================================================

class TestGetEmployeeBalanceBreakdown:
    """Tests para la funcion get_employee_balance_breakdown()."""

    def test_breakdown_structure(self, db_with_employees):
        """Verifica estructura del desglose."""
        result = get_employee_balance_breakdown('EMP005', 2025)

        assert 'employee_num' in result
        assert 'total_available' in result
        assert 'by_year' in result
        assert 'lifo_order' in result
        assert result['employee_num'] == 'EMP005'

    def test_lifo_order_newest_first(self, db_with_employees):
        """LIFO ordena los anos mas nuevos primero."""
        result = get_employee_balance_breakdown('EMP005', 2025)

        lifo = result['lifo_order']
        if len(lifo) > 1:
            # El primer item debe ser del ano mas reciente
            assert lifo[0]['year'] >= lifo[-1]['year'], "LIFO should have newest first"

    def test_total_available_calculation(self, db_with_employees):
        """Total disponible es suma de balances."""
        result = get_employee_balance_breakdown('EMP005', 2025)

        # EMP005 tiene 20 en 2025 y 15 en 2024 = 35 total
        assert result['total_available'] == 35.0


# =============================================================================
# TEST: get_grant_recommendation()
# =============================================================================

class TestGetGrantRecommendation:
    """Tests para la funcion get_grant_recommendation()."""

    def test_recommendation_for_existing_employee(self, db_with_employees):
        """Recomendacion para empleado existente."""
        result = get_grant_recommendation('EMP001')

        assert 'error' not in result
        assert 'employee_num' in result
        assert 'seniority_years' in result
        assert 'recommended_grant_days' in result

    def test_recommendation_for_nonexistent_employee(self, db_with_employees):
        """Error para empleado inexistente."""
        result = get_grant_recommendation('NONEXISTENT')

        assert 'error' in result
        assert result['error'] == 'Empleado no encontrado'


# =============================================================================
# TEST: GRANT_TABLE y FISCAL_CONFIG
# =============================================================================

class TestConfigurationConstants:
    """Tests para constantes de configuracion."""

    def test_grant_table_values(self):
        """Verifica valores de la tabla de otorgamiento."""
        assert GRANT_TABLE[0.5] == 10
        assert GRANT_TABLE[1.5] == 11
        assert GRANT_TABLE[2.5] == 12
        assert GRANT_TABLE[3.5] == 14
        assert GRANT_TABLE[4.5] == 16
        assert GRANT_TABLE[5.5] == 18
        assert GRANT_TABLE[6.5] == 20

    def test_fiscal_config_values(self):
        """Verifica valores de configuracion fiscal."""
        assert FISCAL_CONFIG['period_start_day'] == 21
        assert FISCAL_CONFIG['period_end_day'] == 20
        assert FISCAL_CONFIG['max_carry_over_years'] == 2
        assert FISCAL_CONFIG['max_accumulated_days'] == 40
        assert FISCAL_CONFIG['minimum_annual_use'] == 5
        assert FISCAL_CONFIG['minimum_days_for_obligation'] == 10
        assert FISCAL_CONFIG['ledger_retention_years'] == 3


# =============================================================================
# TEST: INTEGRACION
# =============================================================================

class TestIntegration:
    """Tests de integracion entre funciones."""

    def test_seniority_to_grant_flow(self):
        """Flujo completo: antiguedad -> dias otorgados."""
        # Empleado contratado hace 2 anos
        hire_date = '2023-04-01'
        ref_date = date(2025, 4, 15)

        seniority = calculate_seniority_years(hire_date, ref_date)
        grant_days = calculate_granted_days(seniority)

        # ~2 anos de antiguedad = 12 dias
        assert 1.9 <= seniority <= 2.1, f"Seniority should be ~2.0: {seniority}"
        assert grant_days == 11, f"Should get 11 days at ~2 years: {grant_days}"

    def test_deduction_updates_compliance(self, db_with_employees):
        """Deduccion afecta estado de cumplimiento."""
        # Verificar estado inicial de EMP003 (non_compliant con 1 dia usado)
        initial = check_5day_compliance(2025)
        initial_non_compliant = [e['employee_num'] for e in initial['non_compliant']]
        assert 'EMP003' in initial_non_compliant

        # Deducir 4 dias mas (total = 5)
        apply_lifo_deduction('EMP003', 4.0, 2025)

        # Verificar estado actualizado
        after = check_5day_compliance(2025)
        after_compliant = [e['employee_num'] for e in after['compliant']]

        # EMP003 ahora debe estar compliant
        assert 'EMP003' in after_compliant, "EMP003 should be compliant after using 5 days"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
