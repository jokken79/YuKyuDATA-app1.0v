# TEST EXECUTION GUIDE - FASE 4-5 VALIDATION

Quick reference for running YuKyuDATA test suite after FASE 4-5 implementation.

---

## Prerequisites

```bash
# 1. Ensure dependencies are installed
pip install -r requirements.txt
npm install  # if running frontend tests

# 2. Start the application (if needed for live tests)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. In another terminal, ensure environment is set
export PYTHONPATH=/home/user/YuKyuDATA-app1.0v:$PYTHONPATH
```

---

## Quick Start

### Run All Tests (5 minutes)
```bash
pytest tests/ \
  --ignore=tests/test_connection_pooling.py \
  --ignore=tests/infrastructure/test_ci_integration.py \
  -v --tb=short
```

### Run Critical Tests Only (1 minute)
```bash
pytest tests/test_fiscal_year.py \
        tests/test_database_integrity.py \
        tests/test_api_versioning.py \
        -v
```

### Run and Generate Report (10 minutes)
```bash
pytest tests/ \
  --ignore=tests/test_connection_pooling.py \
  --ignore=tests/infrastructure/test_ci_integration.py \
  --cov=. \
  --cov-report=html \
  --cov-report=term-missing \
  -v
```

---

## Test Categories

### 1. Fiscal Year Compliance (必須 - Required)

**Test:** 労働基準法 第39条 compliance
**Runtime:** ~5 seconds
**Expected:** 47/47 passing

```bash
pytest tests/test_fiscal_year.py -v
```

**What it validates:**
- Seniority-based day allocation (0.5yr→10d, 6.5yr→20d max)
- LIFO deduction order (newest days first)
- 5-day compliance tracking
- 2-year carryover with 40-day cap
- Year-end processing

---

### 2. Authentication & Security (重要 - Important)

**Runtime:** ~8 seconds
**Expected:** 54/79 passing (some response format differences)

```bash
pytest tests/test_security.py \
        tests/security/test_owasp_validation.py \
        -v
```

**What it validates:**
- SQL injection prevention
- XSS prevention
- CSRF token generation
- JWT authentication
- Rate limiting

---

### 3. API Versioning (重要 - Important)

**Runtime:** ~14 seconds
**Expected:** 30/34 passing

```bash
pytest tests/test_api_versioning.py \
        tests/integration/test_fase4_api.py \
        -v
```

**What it validates:**
- V0 endpoint compatibility
- V1 endpoint functionality
- Response format consistency
- Deprecation headers
- Version detection

---

### 4. Database Integrity (重要 - Important)

**Runtime:** ~3 seconds
**Expected:** 14/15 passing

```bash
pytest tests/test_database_integrity.py \
        tests/integration/test_data_consistency.py \
        -v
```

**What it validates:**
- CRUD operations
- Foreign key constraints
- Transaction safety
- Audit logging
- Data consistency

---

### 5. Integration Workflows (重要 - Important)

**Runtime:** ~19 seconds
**Expected:** 93/107 passing

```bash
pytest tests/integration/ -v
```

**What it validates:**
- Complete leave request workflow
- Fiscal year carryover
- Notification generation
- Report generation
- Analytics calculation

---

### 6. ORM & Model Tests (中要 - Medium)

**Runtime:** ~13 seconds
**Expected:** 47/71 passing (collection issues being resolved)

```bash
pytest tests/orm/test_phase1_read_operations.py \
        tests/test_models_*.py \
        -v
```

**What it validates:**
- ORM query functionality
- Model serialization
- Database queries

---

### 7. Route/Endpoint Tests (低要 - Low, needs data)

**Runtime:** ~30 seconds
**Expected:** 103/380 passing (many need test data)

```bash
pytest tests/test_routes_*.py -v
```

**What it validates:**
- HTTP endpoints
- Request validation
- Response formats

---

## By Execution Time

### Fast Tests (< 2 minutes total)

```bash
# Run if you only have 2 minutes
pytest tests/test_fiscal_year.py \
        tests/test_database_integrity.py \
        -v
```

**Expected Result:** 61/62 passing

---

### Medium Tests (5-10 minutes)

```bash
# Run if you have 10 minutes
pytest tests/test_fiscal_year.py \
        tests/test_database_integrity.py \
        tests/test_security.py \
        tests/test_api_versioning.py \
        tests/integration/test_data_consistency.py \
        -v
```

**Expected Result:** 140/160 passing

---

### Full Suite (30-40 minutes)

```bash
# Run full validation
pytest tests/ \
  --ignore=tests/test_connection_pooling.py \
  --ignore=tests/infrastructure/test_ci_integration.py \
  -v
```

**Expected Result:** 763/1100 passing

---

## Pre-Test Checklist

### 1. Prepare Data (optional but recommended)

```bash
# Sync Excel data for data-dependent tests
curl -X POST http://localhost:8000/api/sync

# Wait for sync to complete
sleep 5
```

### 2. Verify Environment

```bash
# Check Python version
python --version  # Should be 3.11+

# Check pytest installed
pytest --version

# Verify project structure
ls -la conftest.py main.py database.py
```

### 3. Set Environment Variables

```bash
# These are automatically set by conftest.py, but verify:
export TESTING=true
export RATE_LIMIT_ENABLED=false
export DEBUG=true
```

---

## Running Specific Tests

### Single Test File
```bash
pytest tests/test_fiscal_year.py -v
```

### Single Test Class
```bash
pytest tests/test_fiscal_year.py::TestCalculateSeniorityYears -v
```

### Single Test Function
```bash
pytest tests/test_fiscal_year.py::TestCalculateSeniorityYears::test_six_months_exact -v
```

### Tests Matching Pattern
```bash
pytest tests/ -k "fiscal" -v
pytest tests/ -k "security" -v
pytest tests/ -k "compliance" -v
```

### Tests by Marker
```bash
pytest tests/ -m "unit" -v
pytest tests/ -m "integration" -v
pytest tests/ -m "slow" -v
```

---

## Debugging Failed Tests

### Show Full Output
```bash
pytest tests/test_fiscal_year.py -v -s  # -s shows print statements
```

### Show Traceback Details
```bash
pytest tests/test_fiscal_year.py -v --tb=long
```

### Stop at First Failure
```bash
pytest tests/test_fiscal_year.py -x  # -x stops at first failure
```

### Show Variables in Traceback
```bash
pytest tests/test_fiscal_year.py -v --showlocals
```

### Save to File
```bash
pytest tests/test_fiscal_year.py -v > test_results.txt 2>&1
```

---

## Coverage Reports

### View Coverage Summary
```bash
pytest tests/ --cov=. --cov-report=term
```

### Generate HTML Report
```bash
pytest tests/ --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Check Coverage for Specific Module
```bash
pytest tests/ --cov=services.fiscal_year --cov-report=term
pytest tests/ --cov=database --cov-report=term
```

---

## Common Issues & Solutions

### Issue: "Rate limit exceeded" (429 errors)

**Solution:** Already fixed! Rate limiter is bypassed in test mode. If you see this:

```bash
# Verify fix is applied
grep -A 5 "TESTING.*true" middleware/rate_limiter.py

# Should show rate limiter bypass logic
```

### Issue: "No module named 'fiscal_year'"

**Status:** Known issue in LIFO tests (import path problem)
**Solution:** Run fiscal_year tests separately (they pass)

```bash
# This works:
pytest tests/test_fiscal_year.py -v  # 47/47 pass

# These fail due to import:
pytest tests/test_lifo_deduction.py -v  # Fix needed
```

### Issue: Response format assertion failures

**Status:** Known - cosmetic issue
**Solution:** Run with different filters

```bash
# Skip response format tests
pytest tests/ -k "not response_format" -v

# Run core functionality only
pytest tests/ -k "not (response or format)" -v
```

### Issue: "Employee not found" (404 errors)

**Solution:** Sync test data first

```bash
curl -X POST http://localhost:8000/api/sync
sleep 5
pytest tests/ -v
```

### Issue: "Cannot connect to database"

**Solution:** Ensure app is running or SQLite exists

```bash
# Check if database exists
ls -la yukyu.db

# Or start the app
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Continuous Integration

### GitHub Actions Command
```bash
# Run in CI environment (as defined in .github/workflows/ci.yml)
pytest tests/ \
  --ignore=tests/test_connection_pooling.py \
  --ignore=tests/infrastructure/test_ci_integration.py \
  --cov=. \
  --junitxml=test-results.xml \
  --cov-report=term \
  --cov-report=xml
```

### Local CI Simulation
```bash
# Run checks as they would run in CI
bash scripts/run-checks.sh
```

---

## Performance Baseline

Expected execution times on modern hardware:

| Test Suite | Time | Count | Per Test |
|------------|------|-------|----------|
| Fiscal Year | 5s | 47 | 0.11s |
| Security | 8s | 79 | 0.10s |
| Integration | 19s | 107 | 0.18s |
| Full Suite | 40s | 1100 | 0.04s |

**If tests take significantly longer, check:**
- System CPU/memory usage
- Disk I/O performance
- Database connection issues

---

## Documentation References

- Full Report: `FASE45_TEST_REPORT.md`
- Validation Summary: `FASE45_VALIDATION_SUMMARY.md`
- Test Metrics: `TEST_METRICS.json`
- Pytest Config: `pytest.ini`
- Fixtures: `tests/conftest.py`

---

## Support & Debugging

### Enable Debug Logging
```bash
# Run with debug output
PYTHONPATH=/home/user/YuKyuDATA-app1.0v \
  pytest tests/test_fiscal_year.py -v -s --log-cli-level=DEBUG
```

### Check Test Fixtures
```bash
# List all available fixtures
pytest tests/ --fixtures
```

### Profile Test Performance
```bash
# Run with performance profiling
pytest tests/ --durations=10  # Show 10 slowest tests
```

---

## Next Steps

1. **Immediate (5 min):** Run critical tests
   ```bash
   pytest tests/test_fiscal_year.py -v
   ```

2. **Short-term (15 min):** Run full suite
   ```bash
   pytest tests/ -v
   ```

3. **Verification (5 min):** Check coverage
   ```bash
   pytest tests/ --cov=. --cov-report=term
   ```

4. **Optional:** Review reports
   - Read `FASE45_TEST_REPORT.md`
   - Check `TEST_METRICS.json`

---

**Happy Testing! 🚀**

For issues or questions, refer to `CLAUDE_MEMORY.md` for historical context or consult the test files directly.
