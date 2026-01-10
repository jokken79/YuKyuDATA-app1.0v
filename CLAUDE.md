# CLAUDE.md

Hablame en castellano por favor

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **IMPORTANTE**: Lee también `CLAUDE_MEMORY.md` para contexto de sesiones anteriores,
> decisiones de arquitectura, errores conocidos y features ya implementadas.

---

## 1. Project Overview

**YuKyuDATA-app** is a comprehensive employee management system specialized in Japanese labor law compliance for vacation (有給休暇) tracking and management.

### Core Databases

The system manages four integrated employee databases:
1. **Vacation Management (有給休暇)** - Tracks paid leave usage, balances, and carry-over compliance
2. **Genzai (現在派遣社員)** - Dispatch employee registry with hourly wage tracking
3. **Ukeoi (請負社員)** - Contract employee registry with employment terms
4. **Staff (DBStaffX)** - Office staff with visa and address information

### Tech Stack

**Backend:** FastAPI (Python 5,000+ lines) + SQLite + openpyxl

**Frontend:** Vanilla JavaScript (4,000+ lines) with ES6 modules, Chart.js, GSAP, CSS design system (3,500+ lines)

**Data Sources:**
- `有給休暇管理.xlsm` - Vacation tracking master
- `【新】社員台帳(UNS)T　2022.04.05～.xlsm` - Employee registry (DBGenzaiX, DBUkeoiX, DBStaffX sheets)

---

## 2. Development Commands

### Running the Application

```bash
# Start with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start with dynamic port (Recommended)
script\start_app_dynamic.bat
```

### Testing

```bash
# Backend tests
pytest tests/ -v
pytest --cov=. tests/

# Frontend tests
npx jest
npx jest --watch
npx jest --coverage
```

### Dependencies

```bash
pip install fastapi uvicorn openpyxl python-multipart pydantic PyJWT python-dotenv XlsxWriter
npm install  # for frontend testing
```

---

## 3. Architecture Overview

### Four-Layer Architecture

```
API Layer (main.py)              ← FastAPI endpoints, JWT auth
    ↓
Service Layer                     ← excel_service.py (parsing), fiscal_year.py (business logic)
    ↓
Data Layer (database.py)          ← SQLite CRUD operations
    ↓
Database (yukyu.db)               ← 7 tables with 15+ indexes
```

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 5,058 | FastAPI app with ~30 endpoints |
| `database.py` | 1,104 | SQLite operations, backup system |
| `excel_service.py` | 476 | Intelligent Excel parsing |
| `fiscal_year.py` | 513 | **CRITICAL** Japanese labor law logic |
| `static/js/app.js` | 4,000+ | Main SPA application |
| `static/css/main.css` | 2,344 | Global styles |

---

## 4. Business Logic & Fiscal Year Management ⭐ CRITICAL

The `fiscal_year.py` module implements **Japanese labor law (労働基準法 第39条)** with unique features:

### Grant Table (Based on Seniority)

```python
GRANT_TABLE = {
    0.5: 10,   # 6 months → 10 days
    1.5: 11,   # 1.5 years → 11 days
    2.5: 12,   # 2.5 years → 12 days
    3.5: 14, 4.5: 16, 5.5: 18, 6.5: 20  # 6+ years → 20 days (max)
}
```

### Key Configuration

- **Period:** 21日〜20日 (21st to 20th of each month)
- **Carry-over:** Maximum 2 years
- **Max Accumulation:** 40 days total
- **5-Day Mandate:** 5日取得義務 (employees with 10+ days must use min 5)
- **Audit Trail:** 3 years retention

### Core Functions

**Seniority:** `calculate_seniority_years(hire_date: str) -> float`

**Grant Days:** `calculate_granted_days(seniority_years: float) -> int`

**Fiscal Period:** `get_fiscal_period(year: int, month: int) -> Tuple[str, str]`
- Returns (start_date, end_date) for 21日〜20日 period

**LIFO Deduction:** `apply_lifo_deduction(emp_num: str, days: float, year: int) -> Dict`
- Newest days consumed first (protects older days from expiration)

**Year-End Processing:** `process_year_end_carryover(from_year: int, to_year: int) -> Dict`
- Moves unused days to next year (up to 2-year max)
- Expires days older than 2 years

**Compliance Check:** `check_5day_compliance(year: int) -> Dict`
- Returns: { compliant: [], at_risk: [], non_compliant: [] }

**Expiring Soon:** `check_expiring_soon(year: int, threshold_months: int = 3) -> List[Dict]`
- Identifies employees with days expiring soon

---

## 5. Database Schema (Complete)

### 5.1 employees (Vacation Data)

**PK:** `{employee_num}_{year}` (composite ID)

| Column | Type | Purpose |
|--------|------|---------|
| `id` | TEXT | Composite: `001_2025` |
| `employee_num` | TEXT | Unique identifier |
| `name` | TEXT | Full name |
| `haken` | TEXT | Dispatch location / department |
| `granted` | REAL | Days granted this year |
| `used` | REAL | Days consumed |
| `balance` | REAL | Remaining days |
| `usage_rate` | REAL | (used / granted) * 100 |
| `year` | INTEGER | Fiscal year (April YYYY to March YYYY+1) |
| `grant_year` | INTEGER | Year days were granted (for LIFO) |

### 5.2 genzai (Dispatch Employees)

**PK:** `genzai_{employee_num}`

Fields: status, employee_num, dispatch_id, dispatch_name, department, line, job_content, name, kana, gender, nationality, birth_date, age, hourly_wage, wage_revision, hire_date, leave_date, last_updated

**Filtering:** Active employees (status != '退社') in most queries

### 5.3 ukeoi (Contract Employees)

**PK:** `ukeoi_{employee_num}`

Similar to genzai but without dispatch-specific fields.

### 5.4 staff (Office Staff) ⭐ NEW

**PK:** `staff_{employee_num}`

18 fields with comprehensive contact, visa, and position information.

### 5.5 yukyu_usage_details ⭐ NEW

Individual usage dates with leave_type (full/half_am/half_pm/hourly)

### 5.6 leave_requests ⭐ NEW

**Workflow:** PENDING → APPROVED/REJECTED → CANCELLED

On approval: Deducts days from employee balance via `apply_lifo_deduction()`

On revert: Restores balance to employee

---

## 6. Backend Architecture

### 6.1 Service Layer (excel_service.py)

**Intelligent Header Detection:**
- Scans first 10 rows for "氏名" or "名前"
- Flexible column mapping with multi-keyword support

**Column Keywords:**
```python
employee_num: ['従業員番号', '社員番号', '番号', 'id', 'no', '№']
name: ['氏名', '名前', 'name']
haken: ['派遣先', '所属', '部署', '現場']
granted: ['付与日数', '付与', '総日数', '有給残日数']
used: ['使用日数', '使用', '消化']
year: ['年度', '年', 'year', '対象年度']
```

**Parsers:**
- `parse_excel_file()` - Vacation data
- `parse_genzai_sheet()` - Dispatch employees
- `parse_ukeoi_sheet()` - Contract employees
- `parse_staff_sheet()` - Office staff

### 6.2 Data Layer (database.py)

**Pattern:** Context manager for safe connections

```python
with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE year = ?", (2025,))
```

**CRUD:** `save_employees()`, `get_employees()`, `get_employees_enhanced()` (JOINs)

**Backup System:**
```python
create_backup() → backup filename
list_backups() → List[Dict]
restore_backup(filename) → bool
```

Uses `INSERT OR REPLACE` for idempotent syncs (no duplicate accumulation).

### 6.3 Business Logic (fiscal_year.py)

See **Section 4** for complete reference.

---

## 7. Complete API Reference (~30+ Endpoints)

**Base URL:** `http://localhost:8000`

### 7.1 Authentication ⭐ NEW

**POST /auth/login** - Generate JWT token (24h expiration)

**GET /auth/me** - Current user info (requires token)

### 7.2 Vacation Data

- **GET /api/employees?year={year}** - Fetch employee vacation data
- **POST /api/sync** - Sync from default Excel
- **POST /api/upload** - Upload custom Excel
- **DELETE /api/reset** - Clear employees table
- **GET /api/available-years** - List fiscal years in DB

### 7.3 Employee Registries

**Genzai (Dispatch):**
- GET /api/genzai
- POST /api/sync-genzai
- DELETE /api/reset-genzai

**Ukeoi (Contract):**
- GET /api/ukeoi
- POST /api/sync-ukeoi
- DELETE /api/reset-ukeoi

**Staff (Office):**
- GET /api/staff
- POST /api/sync-staff
- DELETE /api/reset-staff

### 7.4 Leave Requests ⭐ NEW

- **POST /api/leave-requests** - Create request
- **GET /api/leave-requests?status=PENDING** - List requests
- **POST /api/leave-requests/{id}/approve** - Approve (deducts days)
- **POST /api/leave-requests/{id}/reject** - Reject
- **POST /api/leave-requests/{id}/cancel** - Cancel (PENDING only)
- **POST /api/leave-requests/{id}/revert** - Revert APPROVED (restores days)

### 7.5 Analytics & Stats ⭐ NEW

- **GET /api/stats/factory** - Group by haken/factory
- **GET /api/compliance/5day** - 5-day obligation check
- **GET /api/expiring-soon** - Days expiring soon

### 7.6 Exports ⭐ NEW

- **GET /api/exports/approved** - Export approved requests
- **GET /api/exports/monthly** - Monthly summary
- **GET /api/exports/annual** - Annual ledger
- **POST /api/exports/update-master** - Update master Excel

### 7.7 Backups ⭐ NEW

- **POST /api/backups** - Create backup
- **GET /api/backups** - List backups
- **POST /api/backups/restore** - Restore from backup

### 7.8 System

- **GET /api/db-status** - Database health check

---

## 8. Frontend Architecture ⭐ NEW

### 8.1 Module System (ES6)

**8 Core Modules (120 KB total):**

1. **chart-manager.js (22 KB)**
   - Chart.js + ApexCharts orchestration
   - Responsive theme switching
   - Methods: init(), updateUsageChart(), initMonthlyTrend(), initComplianceGauge()

2. **data-service.js (9.5 KB)**
   - API client with 5-minute cache TTL
   - Methods: fetchEmployees(), fetchGenzai(), syncData(), createLeaveRequest()

3. **ui-manager.js (29 KB)**
   - DOM manipulation and rendering
   - Methods: updateKPIs(), updateTable(), showModal(), showToast()

4. **theme-manager.js (3.5 KB)**
   - Dark/light mode with localStorage persistence
   - Methods: getCurrentTheme(), setTheme(), toggleTheme()

5. **utils.js (6.9 KB)**
   - **XSS Prevention:** escapeHtml(), escapeAttr(), sanitizeInput()
   - Formatting: formatCurrency(), formatDate(), formatPercentage()
   - Helpers: debounce(), throttle(), safeNumber()

6. **virtual-table.js (13 KB)**
   - Virtual scrolling for 1000+ rows
   - Only renders visible + buffer rows

7. **export-service.js (7.6 KB)**
   - Excel/CSV export utilities
   - Template-based exports

8. **lazy-loader.js (15 KB)**
   - Code splitting and lazy loading
   - Module caching

### 8.2 Main Application (app.js - 4,000+ lines)

**Singleton Pattern** with global state:

```javascript
App = {
    state: { data, year, charts, currentView, typeFilter, theme },
    init(), setup(), render(), destroy(),
    onYearChange(), onDataSync(), onLeaveRequestSubmit(),
    showDashboard(), showLeaveRequests(), showAnalytics(),
    updateAllViews(), handleError()
}
```

**Initialization:**
1. Load theme from localStorage
2. Fetch available years
3. Initialize modules
4. Bind event listeners

### 8.3 Design System (3,500+ lines)

**Location:** `static/css/design-system/`

- **tokens.css** - Color palette, typography, spacing (8px base)
- **components.css** - Buttons, cards, forms, tables, badges
- **themes.css** - Dark/light mode variants
- **accessibility.css** - WCAG AA compliance

**Glassmorphism:**
```css
.card-glass {
    background: rgba(20, 28, 38, 0.75);
    backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
}
```

### 8.4 Accessibility (WCAG AA)

- ✅ Semantic HTML with proper heading hierarchy
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Focus indicators (3px outline)
- ✅ Screen reader support (ARIA labels, live regions)
- ✅ Color contrast ≥ 4.5:1 (AA standard)
- ✅ Respects prefers-reduced-motion
- ✅ Skip links for main content

---

## 9. Security & Authentication ⭐ NEW

### 9.1 JWT Authentication

**Token Generation:**
```python
create_jwt_token(username: str, role: str = "user") → Token with 24h expiration
```

**Verification:** Automatic via FastAPI `Depends(require_auth)`

**Usage:** All sensitive endpoints require JWT token in Authorization header

### 9.2 XSS Prevention

**Frontend:**
```javascript
escapeHtml(text)        // Escape HTML entities
safeSetHTML(elem, html) // Safe DOM insertion
element.textContent     // Always safe for plain text
```

**Backend:** Pydantic validators on all inputs

### 9.3 Rate Limiting

- **Limit:** 100 requests/min per IP
- **Applied to:** All endpoints automatically
- **Response:** 429 Too Many Requests

### 9.4 CORS Configuration

Whitelisted origins: localhost:8000, localhost:3000, 127.0.0.1:8000, 127.0.0.1:3000

### 9.5 Input Validation

All endpoints use Pydantic models for automatic validation:
```python
class LeaveRequestCreate(BaseModel):
    employee_num: str = Field(..., min_length=1, max_length=10)
    days_requested: float = Field(..., ge=0, le=40)
    leave_type: str = Field(..., regex="^(full|half_am|half_pm|hourly)$")
```

---

## 10. Testing Infrastructure ⭐ NEW

### 10.1 Backend Tests (pytest)

**Files:** `test_api.py`, `test_auth.py`, `test_comprehensive.py`

```bash
pytest tests/ -v                    # Run all
pytest tests/test_api.py -v         # Specific file
pytest --cov=. --cov-report=html    # Coverage report
```

**Coverage Threshold:** 80% (branches, functions, lines)

### 10.2 Frontend Tests (Jest)

**Files:** `test-chart-manager.test.js`, `test-data-service.test.js`, etc. (8 modules)

```bash
npx jest                            # Run all
npx jest --watch                    # Watch mode
npx jest --coverage                 # Coverage report
```

**Config:** `jest.config.js` with jsdom, babel-jest, 80% threshold

---

## 11. Agent System ⭐ NEW

**Location:** `agents/` directory (384 KB, 13 Python modules)

### 11.1 Available Agents

| Agent | Purpose |
|-------|---------|
| `orchestrator.py` (26 KB) | Coordinate multi-agent workflows |
| `compliance.py` (22 KB) | Legal/labor law compliance checks |
| `data_parser.py` (19 KB) | Advanced Excel parsing |
| `documentor.py` (19 KB) | Auto-generate documentation |
| `ui_designer.py` (38 KB) | UI component code generation |
| `ux_analyst.py` (39 KB) | UX analysis and recommendations |
| `security.py` (35 KB) | Security audits, vulnerability scanning |
| `testing.py` (33 KB) | Test generation and improvement |
| `performance.py` (31 KB) | Performance profiling and optimization |
| `nerd.py` (38 KB) | Technical deep-dive analysis |
| `canvas.py` (27 KB) | Visual documentation generation |
| `figma.py` (25 KB) | Figma design integration |

### 11.2 Usage Example

```python
from agents.compliance import ComplianceAgent

agent = ComplianceAgent()
report = agent.check_5day_compliance(employees, year=2025)
```

---

## 12. Data Persistence & Auto-Sync

### Auto-Sync on Startup

```python
if database.is_empty() and excel_files_exist():
    excel_service.parse_excel_file() → database.save_employees()
    print("Auto-synced X employees from Excel")
```

**Behavior:**
- First run: Auto-loads from Excel
- Subsequent: Data persists (manual sync needed for updates)

### Database Status

```bash
curl http://localhost:8000/api/db-status
```

Returns: size_mb, employee_count, genzai_count, last_sync, excel_files_exist

### When to Sync

1. New employees added to Excel → Click "Sync"
2. Vacation data updated → Click "Sync"
3. After backup restore → Click "Sync"

---

## 13. Important Constraints

### Path Dependencies

Excel files must be in project root:
```python
VACATION_EXCEL = Path(__file__).parent / "有給休暇管理.xlsm"
REGISTRY_EXCEL = Path(__file__).parent / "【新】社員台帳(UNS)T　2022.04.05～.xlsm"
```

### Sheet Names (Exact Match Required)

- **DBGenzaiX** - Dispatch employees
- **DBUkeoiX** - Contract employees
- **DBStaffX** - Office staff
- **Any name** - Vacation data (detected automatically)

### Multi-Table Design

- **Vacation:** Year-based (multiple records per employee)
- **Registries:** Employee snapshots (one per employee)
- **Leave Requests:** Full audit trail (never deleted)

---

## 14. Common Development Tasks ⭐ ENHANCED

### 14.1 Running Tests

```bash
# Backend
pytest tests/ -v
pytest tests/test_api.py::test_sync_employees

# Frontend
npx jest
npx jest --watch
```

### 14.2 Creating Backup

```bash
curl -X POST http://localhost:8000/api/backups
```

### 14.3 Leave Request Workflow

```bash
# Create
curl -X POST http://localhost:8000/api/leave-requests \
  -d '{"employee_num":"001","leave_start_date":"2025-12-25","days_requested":1.0}'

# Approve (deducts days)
curl -X POST http://localhost:8000/api/leave-requests/123/approve \
  -d '{"approved_by":"manager"}'

# Reject
curl -X POST http://localhost:8000/api/leave-requests/123/reject \
  -d '{"reason":"Coverage issues"}'

# Revert (restores days)
curl -X POST http://localhost:8000/api/leave-requests/123/revert
```

### 14.4 5-Day Compliance Check

```bash
curl http://localhost:8000/api/compliance/5day?year=2025
# Returns: compliant_count, non_compliant_count, compliance_rate
```

### 14.5 Finding Expiring Days

```bash
curl http://localhost:8000/api/expiring-soon?year=2025&threshold_months=3
# Returns: employees with days expiring within 3 months
```

### 14.6 Year-End Processing

```python
from fiscal_year import process_year_end_carryover

stats = process_year_end_carryover(from_year=2024, to_year=2025)
# Returns: employees_processed, days_carried_over, days_expired
```

### 14.7 Adding New Columns

1. Update schema in `database.py`
2. Add column mapping in `excel_service.py`
3. Update API response in `main.py`
4. Update frontend in `app.js`

### 14.8 Debugging Excel Issues

```bash
python test_parser.py              # Test parsing
python debug_excel.py              # Inspect raw data
sqlite3 yukyu.db ".schema"         # Check DB structure
```

---

## 15. File Organization

### Main Application Files

```
├── main.py                        (5,058 lines) FastAPI app
├── database.py                    (1,104 lines) SQLite CRUD
├── excel_service.py               (476 lines)   Excel parsing
├── fiscal_year.py                 (513 lines)   Business logic ⭐
├── templates/index.html           SPA entry point
├── static/js/app.js               (4,000+ lines) Main SPA
├── static/js/modules/             8 ES6 modules (120 KB)
├── static/css/                    Styling (3,500+ lines)
└── yukyu.db                       SQLite database (2.1 MB)
```

### Testing Files

```
tests/
├── test_api.py                    API endpoint tests
├── test_auth.py                   Authentication tests
├── test_comprehensive.py          Integration tests
├── unit/                          Jest frontend tests (8 modules)
├── fixtures/                      Test data
├── setup.js                       Jest configuration
└── jest.config.js                 Jest config
```

### Agent System

```
agents/
├── orchestrator.py                Workflow coordinator
├── compliance.py                  Compliance checks
├── security.py                    Security audits
├── testing.py                     Test generation
├── (9 more agents...)
└── README.md                      Agent guide
```

### Data & Config

```
├── backups/                       Auto-generated backups
├── .env                           Environment variables (git-ignored)
├── .gitignore                     Git exclusions
├── package.json                   NPM packages
├── jest.config.js                 Jest config
└── CLAUDE.md                      This file
```

---

## Quick Reference

### Most Used Commands

```bash
# Development
python -m uvicorn main:app --reload

# Testing
pytest tests/ -v
npx jest

# Sync
curl -X POST http://localhost:8000/api/sync

# Check DB
sqlite3 yukyu.db "SELECT COUNT(*) FROM employees;"
```

### Key Modules to Understand

1. **fiscal_year.py** - Business logic (start here for compliance features)
2. **main.py** - API structure (understand endpoints)
3. **app.js** - Frontend logic (state management)
4. **database.py** - Data patterns (CRUD operations)

### For More Information

- See `AGENTS.md` for agent system details
- See `ANALISIS_COMPLETO_APP.md` for comprehensive architecture analysis
- Each module file contains docstrings and comments
