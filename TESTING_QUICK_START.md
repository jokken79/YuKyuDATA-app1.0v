# YuKyuDATA Testing - Quick Start Guide

**TL;DR:** Follow these 5 steps to fix blockers and improve coverage from 14% → 35%

---

## Step 1: Understand Current State (5 minutes)

```bash
cd /home/user/YuKyuDATA-app1.0v

# Read the summary
cat TESTING_SUMMARY.txt

# Check coverage report
open htmlcov/index.html  # Or: cat htmlcov/index.html (in terminal)

# See current test results
python -m pytest tests/test_models_common.py tests/test_models_employee.py -v --tb=short
```

**Key Facts:**
- General coverage: 14%
- Tests passing: 141
- Tests blocked: 17 (import errors)
- Tests failing: 1 (validation)

---

## Step 2: Fix AssetService Import (15 minutes)

### Problem:
```
services/__init__.py:97 imports AssetService which doesn't exist
This blocks 17 tests from running
```

### Solution A: Check if needed
```bash
# Look for AssetService usage in the codebase
grep -r "AssetService" /home/user/YuKyuDATA-app1.0v --exclude-dir=.git

# If not used, comment it out:
# Edit services/__init__.py
```

### Solution B: Check the file
```bash
cat services/asset_service.py | head -20
# If class doesn't exist, comment out the import
```

### Quick Fix:
```bash
# Edit services/__init__.py
# Line 97: Comment out this line
# from .asset_service import AssetService

# Line 165: Comment out this export
# "AssetService",
```

**Verify fix:**
```bash
python -c "from services import SearchService; print('✓ Import works')"
```

---

## Step 3: Fix test_year_must_be_integer (15 minutes)

### Problem:
```
Test expects ValidationError when year is string "2025"
But Pydantic v2 coerces string to int (valid)
```

### Solution:
```bash
# Edit tests/test_models_common.py around line 466

# OLD (fails):
def test_year_must_be_integer(self):
    with pytest.raises(ValidationError):
        YearFilter(year="2025")  # ← Coerces to int 2025

# NEW (passes):
def test_year_must_be_integer(self):
    with pytest.raises(ValidationError):
        YearFilter(year="not_a_number")  # ← Cannot coerce

def test_year_coercion(self):
    # Accept Pydantic v2 behavior
    yf = YearFilter(year="2025")
    assert yf.year == 2025
    assert isinstance(yf.year, int)
```

**Verify fix:**
```bash
pytest tests/test_models_common.py::TestYearFilter::test_year_must_be_integer -v
# Should PASS
```

---

## Step 4: Fix pyo3_runtime Issues (30 minutes)

### Problem:
```
Tests using bettersqlite3 fail with:
pyo3_runtime.PanicException: Python API call failed
```

### Affects:
- test_fiscal_year.py
- test_lifo_deduction.py
- test_connection_pooling.py
- test_database_compatibility.py
- test_database_integrity.py
- test_full_text_search.py
- test_postgresql_integration.py

### Solution A: Reinstall bettersqlite3
```bash
pip install --upgrade --force-reinstall bettersqlite3
pip install --upgrade --force-reinstall sqlcipher
```

### Solution B: Use standard sqlite3 in tests
```bash
# In test files, replace:
import bettersqlite3 as db
# With:
import sqlite3 as db
```

### Solution C: Skip tests if extension unavailable
```bash
# In conftest.py, add:
@pytest.fixture(scope="session", autouse=True)
def check_sqlite_extensions():
    try:
        import bettersqlite3
    except ImportError:
        pytest.skip("bettersqlite3 not available")
```

**Verify fix:**
```bash
pytest tests/test_fiscal_year.py -v --tb=short
# Should run or skip gracefully
```

---

## Step 5: Run Full Test Suite (20 minutes)

```bash
# Clean up
rm -rf .pytest_cache __pycache__ tests/__pycache__

# Run all tests with coverage
pytest tests/ -v --tb=short --cov=. --cov-report=html --cov-report=term-missing | tee test_results.txt

# Check coverage
grep "TOTAL" test_results.txt
# Expected: ~35% (up from 14%)

# View report
open htmlcov/index.html
# or: python -m http.server 8888 (then open htmlcov/index.html in browser)
```

**Expected Output:**
```
======================== test session starts ==========================
...
141 passed, 1 failed, 3 skipped in X.XXs

Name                              Stmts   Miss  Cover   Missing
─────────────────────────────────────────────────────────────────
TOTAL                            18749  11825    37%   (improved!)
```

---

## Done! What's Next?

### If you got to 35%+ coverage:
✅ **Phase 1 Complete** - Go to Step 6

### If you got stuck:
- Check TESTING_ACTION_PLAN.md for detailed solutions
- Check TESTING_AUDIT_REPORT.md for full analysis
- Run individual problematic tests with `-vv` flag for more debug info

---

## Step 6 (Optional): Implement Critical Tests (Next Day)

Once Phase 1 is done, implement these files for Phase 2:

```bash
# Create critical tests directory
mkdir -p tests/extended

# Create Phase 2 test files (see TESTING_ACTION_PLAN.md for content):
touch tests/extended/test_fiscal_year_extended.py
touch tests/extended/test_routes_comprehensive.py
touch tests/extended/test_excel_service_extended.py

# Run Phase 2 tests
pytest tests/extended/ -v --cov=. --cov-report=term-missing

# Expected: 60%+ coverage
```

---

## Verification Checklist

### Phase 1 Success Criteria:

- [ ] AssetService import fixed (no import errors)
- [ ] test_year_must_be_integer passes
- [ ] No pyo3_runtime panics
- [ ] 141 tests passing
- [ ] Coverage ≥ 35%
- [ ] htmlcov/index.html generated

### Command to verify all:
```bash
pytest tests/ -v --cov=. --cov-report=html 2>&1 | grep -E "passed|failed|coverage"
```

---

## Troubleshooting

### Tests still failing after fixes?

```bash
# Clear cache
rm -rf .pytest_cache __pycache__

# Try with minimal imports
pytest tests/test_models_employee.py -v

# Check Python version
python --version  # Should be 3.11+

# Check if pytest installed
pip list | grep pytest

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Coverage not calculating?

```bash
# Remove old coverage data
rm -rf .coverage htmlcov/

# Reinstall coverage
pip install --upgrade pytest-cov

# Try again
pytest tests/ --cov=. --cov-report=html
```

### Still stuck?

1. Read full report: `/home/user/YuKyuDATA-app1.0v/TESTING_AUDIT_REPORT.md`
2. Check detailed plan: `/home/user/YuKyuDATA-app1.0v/TESTING_ACTION_PLAN.md`
3. Review coverage matrix: `/home/user/YuKyuDATA-app1.0v/TESTING_COVERAGE_MATRIX.md`

---

## Timeline

```
Phase 1 Blocker Fixes:
├─ Step 1: Understand State         [5 min]  ✓
├─ Step 2: Fix AssetService         [15 min] ✓
├─ Step 3: Fix Validation Test      [15 min] ✓
├─ Step 4: Fix pyo3 Issues          [30 min] ✓
├─ Step 5: Run Full Suite           [20 min] ✓
└─ TOTAL: ~1.5 hours → 35% Coverage ✓

Phase 2 Critical Tests (Next Day):
├─ Fiscal Year Tests                [4-5 hours]
├─ Routes Tests                     [3-4 hours]
├─ Excel Service Tests              [2-3 hours]
└─ TOTAL: ~12 hours → 60% Coverage ✓
```

---

## Resources

- 📄 Full Audit Report: `TESTING_AUDIT_REPORT.md`
- 📋 Action Plan: `TESTING_ACTION_PLAN.md`
- 📊 Coverage Matrix: `TESTING_COVERAGE_MATRIX.md`
- 📝 Executive Summary: `TESTING_SUMMARY.txt`
- 🌐 Coverage Report: `htmlcov/index.html`

---

**Good luck! You've got this! 🚀**

Questions? See the audit report or action plan for details.
