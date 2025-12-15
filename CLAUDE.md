# CLAUDE.md
Hablame en castellano por favor
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YuKyuDATA-app is an employee management system with three main databases:

1. **Vacation Management (有給休暇)**: Tracks employee paid leave usage and balances
2. **Genzai (現在派遣社員)**: Dispatch employee registry from DBGenzaiX sheet
3. **Ukeoi (請負社員)**: Contract employee registry from DBUkeoiX sheet

**Tech Stack:**
- Backend: FastAPI (Python)
- Database: SQLite (yukyu.db) with 3 tables: `employees`, `genzai`, `ukeoi`
- Frontend: Single-page application with vanilla JavaScript, Chart.js for visualizations
- Data Sources:
  - Vacation data: `有給休暇管理.xlsm`
  - Employee registry: `【新】社員台帳(UNS)T　2022.04.05～.xlsm`

## Development Commands

### Running the Application

```bash
# Start the server with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use the batch file (Windows)
start_app.bat
```

The application will be available at http://localhost:8000

### Dependencies

The project requires these Python packages:
- `fastapi`
- `uvicorn`
- `openpyxl`

Install with: `pip install fastapi uvicorn openpyxl`

## Architecture

### Three-Layer Architecture

1. **API Layer** ([main.py](main.py))
   - FastAPI endpoints for data sync, upload, and retrieval
   - CORS configured for development
   - Serves the static HTML dashboard at root `/`

2. **Service Layer** ([excel_service.py](excel_service.py))
   - Excel file parsing with intelligent header detection
   - Handles multiple column name variations (e.g., "氏名", "名前" for names)
   - **Critical filtering**: Excludes records where `haken == "高雄工業 本社"`
   - Generates composite IDs: `{employeeNum}_{year}`

3. **Data Layer** ([database.py](database.py))
   - SQLite operations with `INSERT OR REPLACE` for idempotent syncs
   - Year-based filtering support
   - Stores: employee number, name, haken (派遣先), granted/used days, balance, usage rate, year

### Data Flow

**Vacation Data:**
```
有給休暇管理.xlsm → excel_service.parse_excel_file() → database.save_employees() → SQLite (employees table)
                                                                                    ↓
                                                                   Browser ← API ← database.get_employees()
```

**Employee Registry Data:**
```
【新】社員台帳(UNS)T.xlsm → excel_service.parse_genzai_sheet() → database.save_genzai() → SQLite (genzai table)
                           ↓
                           excel_service.parse_ukeoi_sheet() → database.save_ukeoi() → SQLite (ukeoi table)
```

## Key Implementation Details

### Excel Parsing Logic

The parser ([excel_service.py:18-30](excel_service.py#L18-L30)) scans the first 10 rows to locate headers containing "氏名" or "名前", then maps columns using flexible matching:
- Employee number: `['従業員番号', '社員番号', '番号', 'id', 'no', '№']`
- Name: `['氏名', '名前', 'name']`
- Haken (dispatch location): `['派遣先', '所属', '部署', '現場']`
- Granted days: `['付与日数', '付与', '総日数', '有給残日数']`
- Used days: `['使用日数', '使用', '消化']`
- Year: `['年度', '年', 'year', '対象年度']`

### Data Filtering Rules

**Vacation Data:**
- Records are skipped if the name field is missing ([excel_service.py:59-60](excel_service.py#L59-L60))
- All other records are included, even if granted/used days are 0

**Genzai/Ukeoi Data:**
- Records are skipped if employee number or name is missing
- All other records are included

### Database Schema

**Table: `employees` (Vacation/Leave Data)**
- `id` (TEXT, PRIMARY KEY): Composite key `{employeeNum}_{year}`
- `employee_num`, `name`, `haken`: TEXT fields
- `granted`, `used`, `balance`, `usage_rate`: REAL (floating point)
- `year`: INTEGER
- `last_updated`: TEXT (ISO timestamp)

**Table: `genzai` (Dispatch Employees from DBGenzaiX)**
- `id` (TEXT, PRIMARY KEY): `genzai_{employeeNum}`
- `status`: TEXT (現在状態: 在職中, 退社, etc.)
- `employee_num`, `dispatch_id`, `dispatch_name`: TEXT
- `department`, `line`, `job_content`: TEXT
- `name`, `kana`, `gender`, `nationality`: TEXT
- `birth_date`: TEXT (YYYY-MM-DD format)
- `age`: INTEGER
- `hourly_wage`: INTEGER
- `wage_revision`: TEXT (wage change history)
- `last_updated`: TEXT (ISO timestamp)

**Table: `ukeoi` (Contract Employees from DBUkeoiX)**
- `id` (TEXT, PRIMARY KEY): `ukeoi_{employeeNum}`
- `status`: TEXT (現在状態: 在職中, 退社, etc.)
- `employee_num`, `contract_business`: TEXT
- `name`, `kana`, `gender`, `nationality`: TEXT
- `birth_date`: TEXT (YYYY-MM-DD format)
- `age`: INTEGER
- `hourly_wage`: INTEGER
- `wage_revision`: TEXT
- `last_updated`: TEXT (ISO timestamp)

## API Endpoints

### Vacation Data Endpoints
- `GET /` - Serves the dashboard HTML
- `GET /api/employees?year={year}` - Returns employee vacation data (optionally filtered by year)
- `POST /api/sync` - Syncs data from default Excel file at `D:\YuKyuDATA-app\有給休暇管理.xlsm`
- `POST /api/upload` - Accepts manual Excel file upload
- `DELETE /api/reset` - Clears employees table

### Genzai (Dispatch Employees) Endpoints
- `GET /api/genzai` - Returns all dispatch employees from genzai table
- `POST /api/sync-genzai` - Syncs DBGenzaiX sheet from employee registry Excel file
- `DELETE /api/reset-genzai` - Clears genzai table

### Ukeoi (Contract Employees) Endpoints
- `GET /api/ukeoi` - Returns all contract employees from ukeoi table
- `POST /api/sync-ukeoi` - Syncs DBUkeoiX sheet from employee registry Excel file
- `DELETE /api/reset-ukeoi` - Clears ukeoi table

## Frontend Architecture

The dashboard ([templates/index.html](templates/index.html)) is a single-file SPA with:
- Year-based filtering system
- Four KPI cards showing aggregate metrics
- Chart.js visualizations (usage rate distribution, top 10 users)
- Interactive data table with modal detail view
- Dark mode toggle with localStorage persistence

State is managed in a global `AppState` object with properties: `data`, `charts`, `theme`, `selectedYear`, `availableYears`.

## File Organization

```
Main application files:
├── main.py              # FastAPI app and routes
├── database.py          # SQLite operations
├── excel_service.py     # Excel parsing logic
├── templates/
│   └── index.html      # Dashboard SPA
└── yukyu.db            # SQLite database (generated)

Development/Debug files:
├── test_parser*.py     # Excel parsing tests
├── inspect_db*.py      # Database inspection utilities
├── check_*.py          # Various data validation scripts
└── *.txt               # Debug output files
```

## Important Constraints

1. **Path Dependencies**:
   - Vacation Excel: `D:\YuKyuDATA-app\有給休暇管理.xlsm` ([main.py:26](main.py#L26))
   - Employee Registry: `D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm` ([main.py:27](main.py#L27))
2. **No Authentication**: API endpoints are unprotected
3. **Multi-Table Database**:
   - Vacation data uses year discrimination via the `year` column
   - Genzai and Ukeoi are separate tables with employee snapshots
4. **Frontend-Backend Coupling**: The HTML dashboard currently only displays vacation data
5. **Sheet Name Dependencies**: Genzai and Ukeoi parsers expect exact sheet names "DBGenzaiX" and "DBUkeoiX"

## Common Development Tasks

### Testing the New Genzai/Ukeoi Integration

Run the test script:
```bash
python test_new_features.py
```

This will:
- Parse both DBGenzaiX and DBUkeoiX sheets
- Save data to respective tables
- Verify retrieval from database

### Adding a New Data Column to Vacation Data

1. Update database schema in [database.py:17-31](database.py#L17-L31)
2. Add column mapping in [excel_service.py:38-45](excel_service.py#L38-L45)
3. Update extraction logic in [excel_service.py:92-103](excel_service.py#L92-L103)
4. Modify API response serialization in [database.py:78-93](database.py#L78-L93)
5. Update frontend table/modal in [templates/index.html](templates/index.html)

### Adding a New Column to Genzai/Ukeoi Tables

1. Update schema in [database.py](database.py) (genzai: lines 34-54, ukeoi: lines 57-73)
2. Update parser in [excel_service.py](excel_service.py):
   - For Genzai: [parse_genzai_sheet()](excel_service.py#L114-L179)
   - For Ukeoi: [parse_ukeoi_sheet()](excel_service.py#L182-L243)
3. Update save functions in [database.py](database.py):
   - For Genzai: [save_genzai()](database.py#L151-L183)
   - For Ukeoi: [save_ukeoi()](database.py#L204-L233)

### Syncing Employee Registry Data

Use the API endpoints:
```bash
# Sync dispatch employees (Genzai)
curl -X POST http://localhost:8000/api/sync-genzai

# Sync contract employees (Ukeoi)
curl -X POST http://localhost:8000/api/sync-ukeoi

# Get data
curl http://localhost:8000/api/genzai
curl http://localhost:8000/api/ukeoi
```

### Modifying Filtering Logic

- Vacation data filtering: [excel_service.py:51-77](excel_service.py#L51-L77)
- Genzai filtering: [excel_service.py:145-146](excel_service.py#L145-L146)
- Ukeoi filtering: [excel_service.py:213-214](excel_service.py#L213-L214)

Changes here affect what data enters the database during sync operations.

### Debugging Excel Parsing Issues

Use the debug scripts:
- `test_new_features.py` - Test Genzai/Ukeoi parsing and database operations
- `test_parser.py` / `test_parser_v2.py` - Test vacation data parsing
- `debug_excel.py` / `debug_excel_rows.py` - Inspect raw Excel row data
- `check_*.py` - Various data quality checks
