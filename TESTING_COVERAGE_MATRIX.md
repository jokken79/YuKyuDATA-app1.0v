# YuKyuDATA Testing Coverage Matrix

**Last Updated:** 2026-01-17
**Status:** CRITICAL (14% coverage)

---

## Module Coverage Heat Map

```
COVERAGE PERCENTAGE BY MODULE
────────────────────────────────────────────────────────────────────

100% │
     │ ███████████ models/
 90% │ ██████████░
     │
 80% │
     │
 70% │
     │
 60% │
     │
 50% │
     │
 40% │
     │
 30% │
     │ ██░░░░░░░░ middleware/
 20% │
     │
 10% │ █░░░░░░░░░ services/ (avg)
     │ █░░░░░░░░░ database.py
 0%  │ ░░░░░░░░░░ routes/
     │ ░░░░░░░░░░ agents/
     │ ░░░░░░░░░░ static/src/
     └────────────────────────────────────────────────────────────────
       0   10   20   30   40   50   60   70   80   90   100  Lines
```

---

## Critical Modules - Detailed Breakdown

### 1. Fiscal Year (services/fiscal_year.py)
**Status:** 🔴 CRITICAL
**Coverage:** 12% (20 of 160 lines)
**Priority:** 🔴 MUST FIX

```
Function                        Covered  Total   %     Status
─────────────────────────────────────────────────────────────
calculate_seniority_years()     ❌      1       0%    NO TEST
calculate_granted_days()        ❌      1       0%    NO TEST
apply_lifo_deduction()          ❌      25      0%    NO TEST
check_5day_compliance()         ❌      20      0%    NO TEST
process_year_end_carryover()    ❌      50      0%    NO TEST
check_expiring_soon()           ❌      15      0%    NO TEST
apply_fifo_deduction()          ❌      20      0%    NO TEST
get_fiscal_period()             ❌      10      0%    NO TEST
[Other functions]               ✅      18    100%   Basic coverage
─────────────────────────────────────────────────────────────

REQUIRED TESTS:
  [ ] Test all seniority calculations (0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5+ years)
  [ ] Test LIFO deduction with single/multiple years
  [ ] Test LIFO deduction with insufficient balance
  [ ] Test 5-day compliance check (compliant/non-compliant)
  [ ] Test year-end carryover with max 10 days
  [ ] Test expiring soon notifications (3-month threshold)
  [ ] Test edge cases (leap years, boundary conditions)

ESTIMATED EFFORT: 6-8 hours (40+ test cases)
ESTIMATED COVERAGE AFTER: 100%
```

### 2. Routes (routes/)
**Status:** 🔴 CRITICAL
**Coverage:** 2% (6 of 381 lines in employees.py)
**Total:** <5% (estimated 100 of 1,546 lines)
**Priority:** 🔴 MUST FIX

```
Route File              Covered  Total  %    Status
──────────────────────────────────────────────────
employees.py           2        381    0%   ❌ Critical
leave_requests.py      7        141    5%   ❌ Critical
compliance.py          7        70    10%   ⚠️ Low
notifications.py       0        162    0%   ❌ Critical
analytics.py           0        129    0%   ❌ Critical
reports.py             0        143    0%   ❌ Critical
yukyu.py               0        145    0%   ❌ Critical
health.py              0        150    0%   ❌ Critical
auth.py                38       88    43%   ⚠️ Acceptable
system.py              0        178    0%   ❌ Critical
export.py              0        146    0%   ❌ Critical
fiscal.py              0        66     0%   ❌ Critical
calendar.py            0        67     0%   ❌ Critical
genzai.py              0        42     0%   ❌ Critical
ukeoi.py               0        42     0%   ❌ Critical
staff.py               0        42     0%   ❌ Critical
github.py              0        140    0%   ❌ Critical
──────────────────────────────────────────────────────
TOTAL                  54       1,546  3%   ❌ CRITICAL

ENDPOINTS NEEDING TESTS:
  [ ] GET  /api/employees (list all)
  [ ] GET  /api/employees?year=YYYY (filter by year)
  [ ] GET  /api/employees/{emp}/{year} (get specific)
  [ ] POST /api/employees (create) [NEEDS AUTH]
  [ ] PUT  /api/employees/{emp}/{year} (update) [NEEDS AUTH]
  [ ] DELETE /api/employees/{emp}/{year} (delete) [NEEDS AUTH]
  [ ] POST /api/leave-requests (create)
  [ ] GET  /api/leave-requests (list)
  [ ] PATCH /api/leave-requests/{id}/approve [NEEDS AUTH]
  [ ] PATCH /api/leave-requests/{id}/reject [NEEDS AUTH]
  [ ] GET  /api/compliance/5day
  [ ] GET  /api/expiring-soon
  [ ] POST /api/yukyu/usage-details [NEEDS AUTH]
  [ ] PUT  /api/yukyu/usage-details/{id} [NEEDS AUTH]
  [ ] DELETE /api/yukyu/usage-details/{id} [NEEDS AUTH]

ESTIMATED EFFORT: 10-12 hours (30+ test cases)
ESTIMATED COVERAGE AFTER: 70-80%
```

### 3. Excel Service (services/excel_service.py)
**Status:** 🔴 CRITICAL
**Coverage:** 6% (25 of 401 lines)
**Priority:** 🔴 MUST FIX

```
Function                        Covered  Total   %     Status
─────────────────────────────────────────────────────────────
parse_vacation_excel()          ❌       30      0%    NO TEST
parse_registry_excel()          ❌       70      0%    NO TEST
validate_parsed_data()          ❌       40      0%    NO TEST
detect_excel_file_type()        ❌       30      0%    NO TEST
calculate_years_to_include()    ❌       25      0%    NO TEST
[Utility functions]             ✅       25    100%   Basic
─────────────────────────────────────────────────────────────

REQUIRED TESTS:
  [ ] Parse vacation Excel file (valid)
  [ ] Parse vacation Excel file (missing columns)
  [ ] Parse vacation Excel file (corrupted)
  [ ] Parse registry Excel (genzai, ukeoi, staff sheets)
  [ ] Validate parsed employee data
  [ ] Handle encoding (UTF-8, Shift-JIS)
  [ ] Handle empty cells
  [ ] Handle date formats (YYYY-MM-DD, DD/MM/YYYY)
  [ ] Handle whitespace in cells
  [ ] Large file performance (1000+ employees)

ESTIMATED EFFORT: 5-6 hours (25+ test cases)
ESTIMATED COVERAGE AFTER: 80-90%
```

### 4. Agents (agents/)
**Status:** 🔴 CRITICAL
**Coverage:** 0% (0 of 4,070 lines)
**Priority:** 🔴 MUST FIX

```
Agent Module           Lines  Tests  %    Status
──────────────────────────────────────────────────
orchestrator.py        282    0      0%   ❌
memory.py              599    0      0%   ❌
compliance.py          211    0      0%   ❌
performance.py         290    0      0%   ❌
security.py            346    0      0%   ❌
testing.py             372    0      0%   ❌
ui_designer.py         429    0      0%   ❌
ux_analyst.py          361    0      0%   ❌
figma.py               291    0      0%   ❌
canvas.py              295    0      0%   ❌
documentor.py          218    0      0%   ❌
data_parser.py         197    0      0%   ❌
nerd.py                337    0      0%   ❌
──────────────────────────────────────────────────
TOTAL                 4,028   0      0%   ❌ CRITICAL

TEST STRATEGY:
  [ ] Unit tests for each agent (~5 tests per agent)
  [ ] Integration tests for orchestrator
  [ ] Mock dependencies where possible
  [ ] Focus on public methods first

ESTIMATED EFFORT: 15-20 hours (65+ test cases)
ESTIMATED COVERAGE AFTER: 60-70%
```

### 5. Frontend (static/src/)
**Status:** 🔴 CRITICAL
**Coverage:** 0% (0 of 11,500 lines)
**Priority:** 🔴 SHOULD FIX

```
Component Module       Lines  Status
─────────────────────────────────────
Modal.js              685    ❌ NO TESTS
Form.js              1,071   ❌ NO TESTS
Table.js              985    ❌ NO TESTS
Select.js             975    ❌ NO TESTS
DatePicker.js         935    ❌ NO TESTS
Alert.js              883    ❌ NO TESTS
Card.js               595    ❌ NO TESTS
Loader.js             591    ❌ NO TESTS
Pagination.js         576    ❌ NO TESTS
Button.js             553    ❌ NO TESTS
Input.js              543    ❌ NO TESTS
Tooltip.js            408    ❌ NO TESTS
Badge.js              389    ❌ NO TESTS
[Pages modules]     3,200    ❌ NO TESTS
[Store/Config]        450    ❌ NO TESTS
─────────────────────────────────────

REQUIRED TESTS (Jest):
  [ ] Component render tests (all 14 components)
  [ ] User interaction tests (click, type, select)
  [ ] Props validation
  [ ] Event handling
  [ ] Page routing tests
  [ ] State management tests

REQUIRED TESTS (Playwright):
  [ ] End-to-end workflows
  [ ] Cross-browser compatibility
  [ ] Mobile responsiveness
  [ ] Accessibility compliance

ESTIMATED EFFORT: 20-25 hours (80+ test cases)
ESTIMATED COVERAGE AFTER: 50-60%
```

---

## Coverage Goals by Phase

### Phase 1: Blocker Resolution (1-2 days)
```
Target: 35% coverage (↑21%)

Module                  Current  Target  Tasks
─────────────────────────────────────────────
Services (avg)          15%      25%     Fix imports
Fiscal Year             12%      25%     Basic tests
Routes                  2%       10%     Sample tests
Agents                  0%       2%      Fix imports
OVERALL                 14%      35%     ✅ ACHIEVABLE
```

### Phase 2: Critical Paths (3-5 days)
```
Target: 60% coverage (↑25%)

Module                  Current  Target  Tests
─────────────────────────────────────────────
Fiscal Year             25%      100%    40 tests
Routes                  10%      70%     30 tests
Excel Service           6%       80%     20 tests
Services (avg)          25%      35%     Various
OVERALL                 35%      60%     ✅ ACHIEVABLE
```

### Phase 3: Comprehensive (1-2 weeks)
```
Target: 80% coverage (↑20%)

Module                  Current  Target  Tests
─────────────────────────────────────────────
Agents                  2%       70%     65 tests
Database                10%      85%     30 tests
Middleware              17%      85%     25 tests
Reports                 11%      80%     30 tests
Services                35%      80%     Various
OVERALL                 60%      80%     ✅ ACHIEVABLE
```

### Phase 4: Frontend (1-2 weeks)
```
Target: 75% (incl. frontend) (↓5%)

Module                  Current  Target  Tests
─────────────────────────────────────────────
Components              0%       60%     50 tests
Pages                   0%       50%     20 tests
E2E                     ?        70%     10 specs
OVERALL                 80%      75%     ⚠️  Coverage drops due to frontend weight
```

---

## Test Priority Matrix

### Urgency vs Complexity

```
HIGH URGENCY
│
│  CRITICAL (Fix First)           IMPORTANT (Fix Soon)
│  ┌─────────────────────────┐     ┌─────────────────────────┐
│  │ • Fiscal Year Logic     │     │ • Agents                │
│  │ • Excel Parsing         │     │ • Database Layer        │
│  │ • API Routes (CRUD)     │     │ • Frontend Components   │
│  │ • 5-Day Compliance      │     │ • Analytics             │
│  │ • LIFO Deduction        │     │ • Reports               │
│  └─────────────────────────┘     └─────────────────────────┘
│
│  NICE-TO-HAVE (Fix If Time)     INFRASTRUCTURE (Fix Last)
│  ┌─────────────────────────┐     ┌─────────────────────────┐
│  │ • Performance Tests     │     │ • Load Testing          │
│  │ • UI Polish Tests       │     │ • Chaos Engineering     │
│  │ • Edge Cases            │     │ • Security Scanning     │
│  │ • Documentation Tests   │     │ • Compliance Checks     │
│  └─────────────────────────┘     └─────────────────────────┘
│
└────────────────────────────────────────────────────────────
  LOW URGENCY              Implementation Complexity →         HIGH
```

---

## Risk Heat Map

```
IMPACT vs PROBABILITY

CRITICAL RISKS (Fix First):
┌──────────────────────────────────────────────────────────┐
│ Labor Law Violation (Fiscal Year)                        │
│ Impact: Very High | Probability: Medium | Risk: CRITICAL │
│ Mitigation: 40 tests covering all scenarios              │
├──────────────────────────────────────────────────────────┤
│ Data Corruption (Excel Parsing)                          │
│ Impact: Very High | Probability: High | Risk: CRITICAL   │
│ Mitigation: 20 tests with error cases                    │
├──────────────────────────────────────────────────────────┤
│ API Contract Breaks (Routes)                             │
│ Impact: High | Probability: Medium | Risk: HIGH          │
│ Mitigation: 30 endpoint tests                            │
├──────────────────────────────────────────────────────────┤
│ Performance Degradation (No Perf Tests)                  │
│ Impact: High | Probability: Medium | Risk: HIGH          │
│ Mitigation: Add benchmarks in Phase 5                    │
└──────────────────────────────────────────────────────────┘

HIGH RISKS (Fix Soon):
  • Security vulnerabilities (no security tests)
  • Agent orchestration failures (0% coverage)
  • UI/UX regressions (0% frontend coverage)

MEDIUM RISKS (Fix When Possible):
  • Middleware edge cases (17% coverage)
  • Report generation failures (11% coverage)
```

---

## Test Checklist

### Phase 1: Blocker Resolution ✓ DO THIS FIRST

- [ ] Fix AssetService import error (services/__init__.py:97)
  - [ ] Check if class exists in asset_service.py
  - [ ] Comment out or create placeholder
  - ETA: 15 minutes

- [ ] Fix test_year_must_be_integer validation
  - [ ] Update test with non-coercible value
  - [ ] Run: pytest tests/test_models_common.py::TestYearFilter::test_year_must_be_integer -v
  - ETA: 15 minutes

- [ ] Fix pyo3_runtime.PanicException
  - [ ] Reinstall bettersqlite3: pip install --upgrade --force-reinstall bettersqlite3
  - [ ] Or use standard sqlite3 in tests
  - ETA: 30 minutes

- [ ] Run full test suite
  - [ ] pytest tests/ -v --tb=short
  - [ ] pytest tests/ --cov=. --cov-report=html
  - ETA: 20 minutes

- [ ] Expected result: 35% coverage, 0 blockers

---

### Phase 2: Critical Tests ✓ SECOND PRIORITY

- [ ] Create test_fiscal_year_extended.py
  - [ ] Test calculate_seniority_years (9 cases)
  - [ ] Test calculate_granted_days (9 cases)
  - [ ] Test check_5day_compliance (3 cases)
  - [ ] Test LIFO deduction (5 cases)
  - [ ] Test year-end carryover (3 cases)
  - [ ] Test expiring soon (2 cases)
  - [ ] Test edge cases (5 cases)
  - Total: 40+ tests
  - ETA: 4-5 hours

- [ ] Create test_routes_comprehensive.py
  - [ ] Employee endpoints (6 tests)
  - [ ] Leave request endpoints (7 tests)
  - [ ] Compliance endpoints (3 tests)
  - [ ] Yukyu detail endpoints (5 tests)
  - [ ] Error handling (5 tests)
  - Total: 30+ tests
  - ETA: 3-4 hours

- [ ] Create test_excel_service_extended.py
  - [ ] Parse vacation Excel (3 tests)
  - [ ] Parse registry Excel (4 tests)
  - [ ] Data validation (4 tests)
  - [ ] Encoding handling (2 tests)
  - [ ] Edge cases (7 tests)
  - Total: 20+ tests
  - ETA: 2-3 hours

- [ ] Run tests and validate
  - [ ] pytest tests/test_fiscal_year_extended.py -v
  - [ ] pytest tests/test_routes_comprehensive.py -v
  - [ ] pytest tests/test_excel_service_extended.py -v
  - ETA: 1 hour

- [ ] Generate coverage report
  - [ ] pytest tests/ --cov=. --cov-report=html
  - [ ] Verify 60% coverage
  - ETA: 20 minutes

- [ ] Expected result: 60% coverage, critical paths protected

---

### Phase 3: Comprehensive Coverage ✓ THIRD PRIORITY

- [ ] Create test_agents_comprehensive.py (65+ tests)
- [ ] Create test_database_comprehensive.py (30+ tests)
- [ ] Create test_middleware_comprehensive.py (25+ tests)
- [ ] Create test_reports_comprehensive.py (30+ tests)
- [ ] Expected result: 80% coverage

---

### Phase 4: Frontend Coverage ✓ FOURTH PRIORITY

- [ ] Jest component tests (50+ tests)
- [ ] Jest page tests (20+ tests)
- [ ] Playwright E2E additions (10+ specs)
- [ ] Expected result: 75% overall

---

### Phase 5: Security & Performance ✓ LAST PRIORITY

- [ ] Security tests (20+ tests)
- [ ] Performance tests (15+ tests)
- [ ] Load tests (5+ tests)
- [ ] Expected result: 85% coverage + security baseline

---

## Tracking Progress

### Weekly Status Report Template

```
WEEK OF: ___________

Coverage Progress:
  General: __% (target: __)
  Fiscal Year: __% (target: 100%)
  Routes: __% (target: 95%)
  Excel Service: __% (target: 90%)

Tests Status:
  Passing: ___/ ___ (target: ___)
  Failing: ___ (target: 0)
  Blocked: ___ (target: 0)
  Flaky: ___ (target: 0)

Phase Progress:
  [ ] Phase 1: Completed / In Progress / Not Started
  [ ] Phase 2: Completed / In Progress / Not Started
  [ ] Phase 3: Completed / In Progress / Not Started
  [ ] Phase 4: Completed / In Progress / Not Started
  [ ] Phase 5: Completed / In Progress / Not Started

Blockers:
  1. _________________
  2. _________________

Next Steps:
  1. _________________
  2. _________________
```

---

## Coverage Commands Reference

```bash
# Overall coverage
pytest tests/ --cov=. --cov-report=term-missing

# By module
pytest tests/ --cov=services.fiscal_year --cov=routes --cov-report=term-missing

# Generate HTML
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html

# Show untested lines
pytest tests/ --cov=services/fiscal_year.py --cov-report=term-missing:skip-covered

# Count tests
pytest tests/ --collect-only -q | wc -l
```

---

**Last Updated:** 2026-01-17
**Next Review:** 2026-01-18
**Status:** 🔴 CRITICAL - Requires immediate action
