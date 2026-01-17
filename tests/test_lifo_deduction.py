"""
Tests for LIFO Deduction Logic - Critical Business Logic

Tests the apply_lifo_deduction() function which handles:
- Deducting vacation days using LIFO (Last In, First Out) logic
- Prioritizing newest days first
- Handling multiple years of balance
- Edge cases with insufficient balance

Based on Japanese Labor Law Article 39.
"""

import pytest
import sqlite3
from datetime import datetime, date
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.fiscal_year import (
    apply_lifo_deduction,
    get_employee_balance_breakdown,
    calculate_granted_days,
    calculate_seniority_years,
    GRANT_TABLE,
    FISCAL_CONFIG,
)


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_yukyu.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Create employees table
    conn.execute('''
        CREATE TABLE employees (
            id TEXT PRIMARY KEY,
            employee_num TEXT NOT NULL,
            name TEXT,
            haken TEXT,
            granted REAL DEFAULT 0,
            used REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            usage_rate REAL DEFAULT 0,
            year INTEGER NOT NULL,
            grant_year INTEGER,
            last_updated TEXT
        )
    ''')

    # Create genzai table for employee info
    conn.execute('''
        CREATE TABLE genzai (
            id TEXT PRIMARY KEY,
            employee_num TEXT NOT NULL,
            name TEXT,
            hire_date TEXT
        )
    ''')

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def db_with_employees(temp_db):
    """Populate database with test employees."""
    conn = sqlite3.connect(temp_db)

    # Employee 001 with balance in 2025 (20 days) and 2024 (10 days carry-over)
    conn.execute('''
        INSERT INTO employees (id, employee_num, name, granted, used, balance, year)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('001_2025', '001', 'Tanaka Taro', 20, 0, 20, 2025))

    conn.execute('''
        INSERT INTO employees (id, employee_num, name, granted, used, balance, year)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('001_2024', '001', 'Tanaka Taro', 15, 5, 10, 2024))

    # Employee 002 with only current year balance
    conn.execute('''
        INSERT INTO employees (id, employee_num, name, granted, used, balance, year)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('002_2025', '002', 'Yamada Hanako', 15, 3, 12, 2025))

    # Employee 003 with zero balance (edge case)
    conn.execute('''
        INSERT INTO employees (id, employee_num, name, granted, used, balance, year)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('003_2025', '003', 'Suzuki Ichiro', 10, 10, 0, 2025))

    # Employee 004 with small balance (edge case for exhaustion)
    conn.execute('''
        INSERT INTO employees (id, employee_num, name, granted, used, balance, year)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('004_2025', '004', 'Sato Yuki', 10, 8, 2, 2025))

    conn.commit()
    conn.close()

    return temp_db


class TestLIFODeductionBasic:
    """Basic LIFO deduction tests."""

    def test_lifo_deduction_from_current_year_only(self, db_with_employees):
        """Test that deduction comes from current year first (LIFO)."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            result = apply_lifo_deduction('001', 5.0, 2025)

            assert result['success'] is True
            assert result['total_deducted'] == 5.0
            assert result['remaining_not_deducted'] == 0

            # Should deduct from 2025 first (newest)
            deductions = result['deductions_by_year']
            assert len(deductions) == 1
            assert deductions[0]['year'] == 2025
            assert deductions[0]['days_deducted'] == 5.0

    def test_lifo_deduction_spanning_multiple_years(self, db_with_employees):
        """Test deduction that spans current and previous year."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            # Deduct 25 days (20 from 2025 + 5 from 2024)
            result = apply_lifo_deduction('001', 25.0, 2025)

            assert result['success'] is True
            assert result['total_deducted'] == 25.0

            # Should use all of 2025 first, then some from 2024
            deductions = result['deductions_by_year']
            assert len(deductions) == 2

            # First deduction from 2025 (newest)
            assert deductions[0]['year'] == 2025
            assert deductions[0]['days_deducted'] == 20.0

            # Second deduction from 2024 (older)
            assert deductions[1]['year'] == 2024
            assert deductions[1]['days_deducted'] == 5.0

    def test_lifo_deduction_exact_balance(self, db_with_employees):
        """Test deduction that exactly matches available balance."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            # Employee 001 has exactly 30 days total (20 + 10)
            result = apply_lifo_deduction('001', 30.0, 2025)

            assert result['success'] is True
            assert result['total_deducted'] == 30.0
            assert result['remaining_not_deducted'] == 0


class TestLIFODeductionEdgeCases:
    """Edge case tests for LIFO deduction."""

    def test_lifo_deduction_insufficient_balance(self, db_with_employees):
        """Test deduction when balance is insufficient."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            # Try to deduct more than available (30 available, request 35)
            result = apply_lifo_deduction('001', 35.0, 2025)

            assert result['success'] is False
            assert result['total_deducted'] == 30.0  # Only 30 available
            assert result['remaining_not_deducted'] == 5.0

    def test_lifo_deduction_zero_balance(self, db_with_employees):
        """Test deduction when employee has zero balance."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            result = apply_lifo_deduction('003', 5.0, 2025)

            assert result['success'] is False
            assert result['total_deducted'] == 0
            assert result['remaining_not_deducted'] == 5.0

    def test_lifo_deduction_zero_days_requested(self, db_with_employees):
        """Test deduction of zero days."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            result = apply_lifo_deduction('001', 0.0, 2025)

            assert result['success'] is True
            assert result['total_deducted'] == 0
            assert result['remaining_not_deducted'] == 0
            assert len(result['deductions_by_year']) == 0

    def test_lifo_deduction_half_day(self, db_with_employees):
        """Test deduction of half day (0.5)."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            result = apply_lifo_deduction('001', 0.5, 2025)

            assert result['success'] is True
            assert result['total_deducted'] == 0.5
            assert len(result['deductions_by_year']) == 1
            assert result['deductions_by_year'][0]['days_deducted'] == 0.5

    def test_lifo_deduction_exhausts_small_balance(self, db_with_employees):
        """Test deduction that exhausts a small balance completely."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            # Employee 004 has only 2 days
            result = apply_lifo_deduction('004', 3.0, 2025)

            assert result['success'] is False
            assert result['total_deducted'] == 2.0
            assert result['remaining_not_deducted'] == 1.0


class TestLIFODeductionFloatingPoint:
    """Tests for floating point precision in LIFO deduction."""

    def test_lifo_deduction_preserves_decimal_precision(self, db_with_employees):
        """Test that decimal precision is preserved."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            result = apply_lifo_deduction('001', 2.5, 2025)

            assert result['total_deducted'] == 2.5
            # Check no floating point errors
            assert abs(result['total_deducted'] - 2.5) < 0.0001

    def test_lifo_deduction_quarter_day(self, db_with_employees):
        """Test deduction of quarter day (hourly leave)."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            result = apply_lifo_deduction('001', 0.25, 2025)

            assert result['success'] is True
            assert result['total_deducted'] == 0.25


class TestBalanceBreakdown:
    """Tests for get_employee_balance_breakdown function."""

    def test_balance_breakdown_multiple_years(self, db_with_employees):
        """Test balance breakdown shows all years correctly."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            breakdown = get_employee_balance_breakdown('001', 2025)

            assert breakdown['employee_num'] == '001'
            assert breakdown['reference_year'] == 2025
            assert breakdown['total_available'] == 30.0  # 20 + 10

            # Should have 2 years of data
            assert len(breakdown['by_year']) == 2

            # LIFO order should have newest first
            lifo = breakdown['lifo_order']
            assert lifo[0]['year'] == 2025
            assert lifo[0]['days'] == 20.0

    def test_balance_breakdown_single_year(self, db_with_employees):
        """Test balance breakdown with only one year."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            breakdown = get_employee_balance_breakdown('002', 2025)

            assert breakdown['total_available'] == 12.0
            assert len(breakdown['lifo_order']) == 1

    def test_balance_breakdown_zero_balance(self, db_with_employees):
        """Test balance breakdown when employee has zero balance."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            breakdown = get_employee_balance_breakdown('003', 2025)

            assert breakdown['total_available'] == 0
            assert len(breakdown['lifo_order']) == 0


class TestGrantTableCalculation:
    """Tests for grant table calculations."""

    @pytest.mark.parametrize("years,expected_days", [
        (0.0, 0),      # Less than 6 months
        (0.4, 0),      # Just under 6 months
        (0.5, 10),     # Exactly 6 months
        (0.6, 10),     # Just over 6 months
        (1.0, 10),     # 1 year
        (1.5, 11),     # 1.5 years
        (2.5, 12),     # 2.5 years
        (3.5, 14),     # 3.5 years
        (4.5, 16),     # 4.5 years
        (5.5, 18),     # 5.5 years
        (6.5, 20),     # 6.5 years (maximum)
        (10.0, 20),    # 10 years (still maximum)
        (20.0, 20),    # 20 years (still maximum)
    ])
    def test_calculate_granted_days(self, years, expected_days):
        """Test grant table calculation for various seniority levels."""
        result = calculate_granted_days(years)
        assert result == expected_days

    def test_calculate_granted_days_negative(self):
        """Test that negative years returns 0."""
        result = calculate_granted_days(-1.0)
        assert result == 0


class TestSeniorityCalculation:
    """Tests for seniority calculation."""

    def test_calculate_seniority_valid_date(self):
        """Test seniority calculation with valid hire date."""
        # Use a fixed reference date for testing
        ref_date = date(2025, 7, 1)
        hire_date = "2024-01-01"

        result = calculate_seniority_years(hire_date, ref_date)

        # Should be approximately 1.5 years
        assert 1.4 < result < 1.6

    def test_calculate_seniority_empty_date(self):
        """Test seniority calculation with empty hire date."""
        result = calculate_seniority_years("")
        assert result == 0.0

    def test_calculate_seniority_none_date(self):
        """Test seniority calculation with None hire date."""
        result = calculate_seniority_years(None)
        assert result == 0.0

    def test_calculate_seniority_invalid_format(self):
        """Test seniority calculation with invalid date format."""
        result = calculate_seniority_years("invalid-date")
        assert result == 0.0

    def test_calculate_seniority_future_date(self):
        """Test seniority calculation with future hire date."""
        ref_date = date(2025, 1, 1)
        hire_date = "2026-01-01"

        result = calculate_seniority_years(hire_date, ref_date)

        # Future date should give negative years
        assert result < 0


class TestDatabaseIntegrity:
    """Tests to verify database integrity after LIFO operations."""

    def test_balance_updated_after_deduction(self, db_with_employees):
        """Test that database balance is correctly updated after deduction."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            # Deduct 5 days
            apply_lifo_deduction('001', 5.0, 2025)

            # Verify balance in database
            conn = sqlite3.connect(db_with_employees)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT balance FROM employees WHERE id = ?',
                ('001_2025',)
            ).fetchone()
            conn.close()

            assert row['balance'] == 15.0  # 20 - 5

    def test_used_days_updated_after_deduction(self, db_with_employees):
        """Test that used days counter is updated after deduction."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            # Deduct 5 days
            apply_lifo_deduction('001', 5.0, 2025)

            # Verify used in database
            conn = sqlite3.connect(db_with_employees)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT used FROM employees WHERE id = ?',
                ('001_2025',)
            ).fetchone()
            conn.close()

            assert row['used'] == 5.0  # 0 + 5

    def test_multiple_deductions_accumulate(self, db_with_employees):
        """Test that multiple deductions accumulate correctly."""
        with patch('fiscal_year.DB_NAME', db_with_employees):
            # First deduction
            apply_lifo_deduction('001', 3.0, 2025)
            # Second deduction
            apply_lifo_deduction('001', 2.0, 2025)

            # Verify total in database
            conn = sqlite3.connect(db_with_employees)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT balance, used FROM employees WHERE id = ?',
                ('001_2025',)
            ).fetchone()
            conn.close()

            assert row['balance'] == 15.0  # 20 - 3 - 2
            assert row['used'] == 5.0  # 0 + 3 + 2


class TestConfigurationLimits:
    """Tests for configuration limits."""

    def test_max_accumulated_days_limit(self):
        """Test that max accumulated days limit is configured."""
        assert FISCAL_CONFIG['max_accumulated_days'] == 40

    def test_max_carry_over_years_limit(self):
        """Test that max carry over years is configured."""
        assert FISCAL_CONFIG['max_carry_over_years'] == 2

    def test_minimum_annual_use_requirement(self):
        """Test that 5-day minimum requirement is configured."""
        assert FISCAL_CONFIG['minimum_annual_use'] == 5

    def test_minimum_days_for_obligation(self):
        """Test that 10-day threshold for obligation is configured."""
        assert FISCAL_CONFIG['minimum_days_for_obligation'] == 10
