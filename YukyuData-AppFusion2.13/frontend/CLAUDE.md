# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Rules

**IMPORTANT**: Always communicate with the user in Spanish. All responses, explanations, questions, and documentation should be in Spanish, even though the codebase uses English for variable names and comments.

## Project Overview

**Yukyu Pro** is a React-based leave management system for Japanese paid leave (有給休暇) compliance. It helps companies track whether employees with 10+ granted days take the legally required 5+ days annually (Labor Standards Act Article 39).

**Tech Stack**: React 19 + TypeScript + Vite + Tailwind CSS (via CDN)

## Commands

```bash
npm install          # Install dependencies
npm run dev          # Start dev server at http://localhost:3000
npm run build        # Production build to dist/
npm run preview      # Preview production build
```

No test or lint commands are configured.

## Environment Setup

Create `.env.local` in the project root:
```env
GEMINI_API_KEY=your_api_key_here
```

**Important**: The Gemini API key is optional. The app handles missing keys gracefully by showing an info message instead of crashing. The key is exposed via Vite's `define` config as both `process.env.API_KEY` and `process.env.GEMINI_API_KEY`.

## Directory Structure

```
/
├── App.tsx                          # Root component with tab navigation and global state
├── index.tsx                        # React entry point
├── index.html                       # HTML shell with Tailwind CDN + CSS theme variables
├── types.ts                         # All TypeScript interfaces
├── vite.config.ts                   # Vite config (port 3000, @/ alias, env vars)
├── tsconfig.json                    # TypeScript config (ES2022, react-jsx)
├── package.json                     # Dependencies and scripts
├── metadata.json                    # App metadata
│
├── components/                      # React UI components
│   ├── Dashboard.tsx                # KPIs, charts (Recharts), AI insights
│   ├── EmployeeList.tsx             # Employee roster with fuzzy search (Fuse.js)
│   ├── LeaveRequest.tsx             # Leave application form
│   ├── ApplicationManagement.tsx    # Approve/reject leave requests (single & bulk)
│   ├── AccountingReports.tsx        # Payroll reports with configurable cut-off dates
│   ├── ExcelSync.tsx                # Excel import (DAICHO + YUKYU files)
│   ├── Sidebar.tsx                  # Tab navigation with ARIA labels
│   ├── ThemeToggle.tsx              # Dark/light theme switch
│   ├── DigitalHanko.tsx             # Japanese digital seal (判子) rendered on Canvas
│   ├── Skeleton.tsx                 # Loading skeleton components (shimmer animation)
│   └── DebugEmployeeData.tsx        # Debug tool for inspecting employee data
│
├── contexts/
│   └── ThemeContext.tsx              # Theme provider (dark/light) with localStorage
│
├── hooks/
│   └── useKeyboardShortcuts.ts      # Global keyboard shortcuts hook
│
├── services/                        # Business logic layer
│   ├── db.ts                        # localStorage CRUD with auto-migration pipeline
│   ├── balanceCalculator.ts         # SINGLE SOURCE OF TRUTH for balance calculations
│   ├── validationService.ts         # Pre-approval validation with error codes
│   ├── expirationService.ts         # Automatic period expiration recalculation
│   ├── migrationService.ts          # Data migration v1→v2 with automatic backup
│   ├── mergeService.ts              # Intelligent Excel data merge (first_sync vs re_sync)
│   ├── geminiService.ts             # Google Gemini AI integration for compliance analysis
│   ├── exportService.ts             # CSV, PDF, and Excel export
│   ├── nameConverter.ts             # Romaji→Katakana conversion (Vietnamese, Portuguese)
│   ├── dataIntegrityValidator.ts    # Data integrity validation with severity levels
│   └── dataRepairService.ts         # Automatic data repair and consistency enforcement
│
├── utils/
│   └── csvSanitizer.ts              # CSV formula injection protection (OWASP CWE-1236)
│
├── public/
│   └── uns-logo.png                 # Company logo with CSS text fallback
│
├── skills/                          # Claude Code specialized skills (6 modules)
│   ├── yukyu-performance-optimizer/ # React profiling, bundle analysis
│   ├── yukyu-compliance-sentinel/   # Legal compliance monitoring (労働基準法39条)
│   ├── yukyu-excel-master/          # Excel import/export debugging
│   ├── yukyu-test-suite/            # Unit, component, integration tests
│   ├── yukyu-integrity-guardian/    # Data integrity validation and repair
│   └── yukyu-ui-architect/          # UI/UX auditing, WCAG 2.1 AA compliance
│
└── .claude/
    └── settings.local.json          # Claude Code permissions (git, npm, node)
```

### Analysis/Debug Scripts (root level)

These are standalone Node.js scripts for debugging Excel import issues:
- `analyze_daicho.mjs` - Analyze employee registry Excel structure
- `analyze_yukyu_excel.mjs` / `.cjs` - Analyze leave management Excel structure
- `test_new_employee.cjs` - Simulate new employee creation
- `debug_console_script.js` - Browser console debug script
- `debug_excel_parser.ts` - Excel parser debugging
- `test_kenji_simulation.cjs` / `check_kenji.cjs` - Kanji character verification

## Dependencies

### Runtime
| Package | Purpose |
|---------|---------|
| `react` / `react-dom` ^19.2.3 | UI framework |
| `@google/genai` ^1.34.0 | Google Gemini AI for compliance insights |
| `recharts` ^3.6.0 | Charts and data visualization |
| `xlsx` ^0.18.5 | Excel file parsing and generation |
| `jspdf` ^2.5.1 | PDF generation |
| `html2canvas` ^1.4.1 | HTML-to-canvas for PDF export |
| `framer-motion` ^12.23.26 | Tab transition animations |
| `fuse.js` ^7.1.0 | Fuzzy search in employee list |
| `focus-trap-react` ^11.0.4 | Focus trap for modals (a11y) |
| `react-hot-toast` ^2.6.0 | Toast notifications |

### Dev
| Package | Purpose |
|---------|---------|
| `vite` ^6.2.0 | Build tool |
| `@vitejs/plugin-react` ^5.0.0 | React Fast Refresh |
| `typescript` ~5.8.2 | Type checking |
| `@types/node` ^22.14.0 | Node.js type definitions |

## Architecture

### Data Flow
The app is **fully client-side** with localStorage persistence:
```
localStorage ("yukyu_pro_storage")
    → db.loadData()
        → Auto-migration (v1→v2)
        → Expiration recalculation
        → Data integrity validation
        → Auto-repair if needed
    → AppData {employees[], records[], config}
    → React component state
    → UI rendering
```

**Critical**: No backend API exists. All data is stored in browser localStorage. External API: Google Gemini AI for compliance analysis only.

### Data Load Pipeline

When `db.loadData()` executes, it runs this pipeline sequentially:
1. **Legacy migration**: Records without `status` field get `status: 'approved'`
2. **v1→v2 migration** (`migrationService.ts`): Adds `periodHistory`, `currentXXX`/`historicalXXX` fields, creates backup
3. **Expiration recalculation** (`expirationService.ts`): Updates `isExpired` for each period, recalculates current vs historical totals
4. **Integrity validation** (`dataIntegrityValidator.ts`): Detects critical/error/warning issues
5. **Auto-repair** (`dataRepairService.ts`): Fixes detected inconsistencies automatically

### State Management Pattern
Components follow a **shared state refresh pattern**:
- `App.tsx` holds the root `appData` state loaded from `db.loadData()`
- Child components receive `data` prop and `onUpdate`/`onSyncComplete` callbacks
- After mutations (approve, import, etc.), components call the callback which triggers `refreshData()` in App
- `refreshData()` re-runs `db.loadData()` to sync with latest localStorage state

### localStorage Keys

| Key | Purpose |
|-----|---------|
| `yukyu_pro_storage` | Main data store (employees, records, config) |
| `uns-yukyu-theme` | Theme preference (`'dark'` or `'light'`) |
| `yukyu_sync_status` | Excel sync status and timestamps |
| `yukyu_pro_backup_v1` | Auto-backup before v1→v2 migration |

### Tab-Based Navigation
Six main modules accessed via Sidebar:
1. **Dashboard** - Analytics, charts, AI-generated compliance insights
2. **EmployeeList** - Roster with search, filtering, pagination
3. **LeaveRequest** - Submit new leave applications
4. **ApplicationManagement** - Approve/reject leave requests (single & bulk)
5. **AccountingReports** - Financial/payroll reporting
6. **ExcelSync** - Import data from two Excel file types

### Keyboard Shortcuts

Defined in `App.tsx` via `useKeyboardShortcuts` hook:
- `Ctrl+D` - Switch to Dashboard
- `Ctrl+E` - Switch to Employees
- `Ctrl+N` - Switch to New Request
- `Ctrl+A` - Switch to Applications
- `Ctrl+R` - Switch to Reports
- `Ctrl+S` - Switch to Sync

Shortcuts are ignored when focus is on INPUT, TEXTAREA, SELECT, or contentEditable elements.

### Key Services (`/services`)

#### Core Data (`db.ts`)
- localStorage CRUD wrapper (`yukyu_pro_storage` key)
- `loadData()` runs the full migration/validation/repair pipeline
- `saveData()` persists to localStorage with QuotaExceededError handling
- `addRecord()` - Creates pending leave requests with auto-generated ID
- `approveRecord()`/`rejectRecord()` - Single approval actions, auto-updates employee balances
- `approveMultiple()`/`rejectMultiple()` - Bulk approval operations
- Auto-migration: Old records without status get `status: 'approved'` on load

#### Balance Calculator (`balanceCalculator.ts`) — SINGLE SOURCE OF TRUTH
- Calculates granted days based on Japanese labor law anniversary periods
- Counts used days from `yukyuDates[]` (supports half-day: `"YYYY-MM-DD:half"` = 0.5)
- Identifies expired periods (2-year validity window)
- Provides consistent balance across the entire app
- `isLegalRisk()` uses `currentGrantedTotal`/`currentUsedTotal` (only non-expired periods) for compliance checks
- Key functions: `getEmployeeBalance()`, `getEmployeePeriods()`, `isLegalRisk()`, `getDaysNeededForCompliance()`

#### Validation (`validationService.ts`)
- Pre-approval validation before approving leave requests
- Returns typed `ValidationResult` with error codes:
  - `INSUFFICIENT_BALANCE` - Not enough leave days
  - `DUPLICATE_DATE` - Date already taken
  - `EMPLOYEE_RETIRED` - Employee is 退社
  - `EMPLOYEE_NOT_FOUND` - Employee doesn't exist
  - `INVALID_DATE` - Bad date format
  - `FUTURE_DATE` - Warning for future dates

#### Expiration (`expirationService.ts`)
- Recalculates period expirations automatically
- Generates new periods if needed based on `entryDate`
- Enforces 40-day legal maximum balance
- Splits values into `currentXXX` (active periods) vs `historicalXXX` (all periods)
- `currentUsedTotal` includes local approvals (`localModifications.approvedDates`) not tracked in `period.used`

#### Migration (`migrationService.ts`)
- Detects data version and migrates v1→v2
- Creates automatic backup before migration (`yukyu_pro_backup_v1`)
- Adds `periodHistory`, generates periods from `entryDate`
- Syncs approved records to `yukyuDates`

#### Merge (`mergeService.ts`)
- Intelligent merge of Excel import data with existing local data
- Distinguishes `first_sync` (use Excel completely) vs `re_sync` (combine Excel + all local yukyuDates)
- Re-sync preserves all existing `yukyuDates[]` (includes previous Excel + local approvals)
- Detects and reports conflicts and warnings

#### Data Integrity (`dataIntegrityValidator.ts`)
- Full integrity validation with severity levels: `critical`, `error`, `warning`, `info`
- Validates: periodHistory existence, currentXXX defined, balance consistency, negative balances

#### Data Repair (`dataRepairService.ts`)
- Automatic repair of detected inconsistencies
- Recalculates `currentXXX` from active periods
- Recalculates `historicalXXX` from all periods
- Enforces 40-day legal limit

#### AI Integration (`geminiService.ts`)
- Gemini AI integration for compliance analysis
- Lazy initialization pattern (doesn't crash if API key missing)
- Uses `gemini-3-flash-preview` model with JSON schema for structured insights

#### Export (`exportService.ts`)
- CSV export with formula injection protection (via `csvSanitizer.ts`)
- PDF export via html2canvas + jsPDF
- Excel export with XLSX library (40 date columns)

#### Name Conversion (`nameConverter.ts`)
- Romaji to Katakana conversion (supports Vietnamese, Portuguese names)
- `isJapaneseName()` - Detects kanji/hiragana/katakana
- `convertNameToKatakana()` - Full conversion
- `getDisplayName()` - Returns katakana or original

### Data Models (`types.ts`)

#### `Employee`
```typescript
interface Employee {
  id: string;                        // 社員№
  name: string;                      // 氏名
  nameKana?: string;                 // カナ
  client: string;                    // 派遣先
  category?: string;                 // 派遣社員 / 請負社員 / スタッフ
  entryDate?: string;                // 入社日
  elapsedTime?: string;              // 経過月数 (e.g., "5年10ヶ月")
  elapsedMonths?: number;            // 経過月
  yukyuStartDate?: string;           // 有給発生日
  grantedTotal: number;              // 付与数
  carryOver?: number;                // 繰越
  totalAvailable?: number;           // 保有数
  usedTotal: number;                 // 消化日数
  balance: number;                   // 期末残高
  expiredCount: number;              // 時効数
  remainingAfterExpiry?: number;     // 時効後残
  yukyuDates?: string[];             // 有給取得日 (dates consumed)
  status: string;                    // 在職中 / 退社
  lastSync: string;
  // v2 fields
  lastExcelSync?: string;
  localModifications?: {
    approvedDates: string[];
    manualAdjustments: number;
  };
  periodHistory?: PeriodHistory[];
  currentGrantedTotal?: number;      // Active periods only
  currentUsedTotal?: number;
  currentBalance?: number;           // Max 40 days by law
  currentExpiredCount?: number;
  excededDays?: number;              // Days exceeding 40-day legal limit
  historicalGrantedTotal?: number;   // All periods including expired
  historicalUsedTotal?: number;
  historicalBalance?: number;
  historicalExpiredCount?: number;
}
```

#### `LeaveRecord`
```typescript
interface LeaveRecord {
  id?: string;
  employeeId: string;
  date: string;
  type: 'paid' | 'unpaid' | 'special';
  duration: 'full' | 'half';        // 全日 (1日) or 半日 (0.5日)
  note?: string;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: string;
  approvedAt?: string;
  approvedBy?: string;
  syncedToYukyuDates?: boolean;      // v2: whether synced to employee.yukyuDates[]
}
```

#### Other Types
- **`AppData`** - Root state: `{ employees[], records[], config: { companyName, fiscalYearStart } }`
- **`AIInsight`** - Gemini-generated insight: `{ title, description, type: 'warning'|'info'|'success' }`
- **`BalanceInfo`** - Calculated balance: `{ granted, used, remaining, expiredCount }`
- **`ValidationResult`** - Approval validation: `{ isValid, error?, code? }`
- **`MergeResult`** - Excel merge result: `{ employee, conflicts[], warnings[] }`
- **`PeriodHistory`** - Full period tracking (see section below)

## Excel Import (ExcelSync)

Two file types with specific sheet requirements:

**社員台帳 (Employee Registry / DAICHO)**
- Required sheets: `DBGenzaiX` (派遣社員), `DBUkeoiX` (請負社員), `DBStaffX` (スタッフ)
- Imports: employee ID (`社員№`), name, kana, client (`派遣先`), entry date (`入社日`), status (`在職中`/`退社`)
- Each sheet represents a different employee category

**有給休暇管理 (Leave Management / YUKYU)**
- Required sheets: `作業者データ　有給` (派遣社員), `請負` (請負社員)
- Imports: all leave balance fields (`付与数`, `消化日数`, `残高`, etc.)
- **Critical**: Extracts up to 40 leave dates from columns named `"1"` to `"40"` (with or without trailing space)
- Half-day dates: Exported with `半休` suffix (e.g., `44881半休`), imported back as `:half` suffix
- Excel date conversion: `(excelDate - 25569) * 86400 * 1000`
- `excelDateToISO()` handles: numeric Excel dates, string dates (`YYYY/MM/DD`, `YYYY-MM-DD`), numeric strings (`"44881"`), and `半休` suffix

**Import Logic**:
- Files are merged by employee ID (`社員№`)
- DAICHO creates/updates basic employee data
- YUKYU enriches existing employees with leave balance fields and `periodHistory`
- Toggle controls whether retired employees (`退社`) are imported
- Sync status persisted in localStorage (`yukyu_sync_status`)
- Uses `mergeService.ts` for intelligent conflict resolution

**Unicode Normalization**: Column names are normalized with NFKC to handle kanji variations (經→経). The `findValue()` function searches for:
- `経過月` (standard)
- `経過月数` (with 数)
- `經過月` (traditional kanji)
- Automatic calculation from `有給発生日` - `入社日` (fallback)

## Conventions

- **Code language**: English for variables/functions
- **UI language**: Japanese throughout (all user-facing text, error messages, labels)
- **Styling**: Tailwind CSS via CDN with glassmorphism effects and noise texture overlay
- **Theme**: Dark mode default, stored in localStorage (`uns-yukyu-theme`), respects system preference
- **Path alias**: `@/*` resolves to project root
- **Loading patterns**: Skeleton screens on initial load and tab switches (300-600ms delays)
- **Logo**: External image `public/uns-logo.png` with CSS text fallback
- **TOP 10 使用者**: Names displayed in カタカナ using `getDisplayName()`
- **Animations**: Framer Motion for tab transitions; CSS `@keyframes` for skeletons
- **Modals**: Use `focus-trap-react` for accessibility
- **Notifications**: `react-hot-toast` for success/error messages
- **CSV security**: All CSV exports pass through `csvSanitizer.ts` to prevent formula injection

## CSS Theme System

Defined in `index.html` with CSS custom properties:

**Dark mode** (default):
```css
--neon-blue: #00e5ff;    --neon-red: #ff004c;
--deep-black: #050505;   --bg-primary: #0a0a0a;
--glass-bg: rgba(255,255,255,0.03);
```

**Light mode** (`[data-theme="light"]`):
```css
--bg-primary: #f8fafc;   --bg-secondary: #ffffff;
--text-primary: #1e293b; --glass-bg: rgba(255,255,255,0.8);
```

**Effects**: Glassmorphism (backdrop-filter: blur + saturate), scanlines overlay, glitch animation.

**Fonts**: Plus Jakarta Sans (UI), Noto Sans JP (Japanese text) — loaded via Google Fonts CDN.

## Accesibilidad (a11y) - WCAG 2.1 AA

La aplicación implementa mejoras de accesibilidad en todos los componentes principales:

### CSS Global (`index.html`)
- `:focus-visible` con outline azul para navegación por teclado
- `@media (prefers-reduced-motion)` para usuarios sensibles a animaciones
- Clase `.sr-only` para contenido exclusivo de screen readers

### Componentes con ARIA

**Sidebar.tsx**
- `role="navigation"` con `aria-label="メインナビゲーション"`
- `aria-current="page"` en tab activo
- `aria-expanded` y `aria-controls` en hamburger móvil

**EmployeeList.tsx**
- Tabla con `role="grid"` y `aria-sort` en headers ordenables
- Paginación con `<nav aria-label>` y `aria-current="page"`
- Modal con `aria-modal`, `aria-labelledby`, `aria-describedby`

**ApplicationManagement.tsx**
- Filtros de estado con `aria-pressed`
- Checkboxes con `aria-label` dinámico (nombre del empleado)
- Live region `aria-live="polite"` para conteo de selección
- Tabla con `role="grid"` y `role="gridcell"`

**LeaveRequest.tsx**
- Formularios con `<fieldset>` y `<legend>` semánticos
- Labels con `htmlFor` vinculados a inputs
- `aria-invalid` y `aria-describedby` para validación de errores

**Dashboard.tsx**
- Sección KPI con `role="region"` y `aria-labelledby`
- Cards KPI con `role="group"` y `aria-label` descriptivos
- 消化合計 KPI: Validación de NaN/undefined para evitar mostrar "NaN日"
- TOP 10 使用者: Usa `displayName` con カタカナ y tooltip mejorado

**ThemeToggle.tsx**
- `role="switch"` con `aria-checked`
- `aria-hidden="true"` en iconos decorativos

### Puntuación estimada: 8/10 WCAG 2.1 AA

## Key Business Logic

### Legal Compliance Calculation
Dashboard identifies employees at legal risk:
- Employees with `grantedTotal >= 10` AND `status === '在職中'` must take at least 5 days
- `usedTotal < 5` triggers legal risk warning
- Dashboard prominently displays at-risk employees with specific deficit (`5 - usedTotal`)

### Approval Workflow
Leave requests follow a three-state lifecycle:
1. **pending** - Newly created requests (via LeaveRequest tab)
2. **approved** - Manager approved, employee balance auto-decremented
3. **rejected** - Manager rejected, no balance impact

**Important**: Only `pending` requests can be approved/rejected. Approved records cannot be deleted (data integrity protection).

**Validation before approval** (`validationService.ts`):
- Employee must exist and be active (not 退社)
- Balance must be sufficient (≥1 for full day, ≥0.5 for half day)
- Date must not already be in `yukyuDates[]`
- Returns typed error codes for specific UI messages

### 半日有給 (Half-Day Leave) Support

El sistema soporta solicitudes de medio día (0.5日):

**LeaveRecord.duration field**:
- `'full'` - Día completo (1.0日) - default
- `'half'` - Medio día (0.5日)

**Encoding en yukyuDates[]**:
- Día completo: `"YYYY-MM-DD"`
- Medio día: `"YYYY-MM-DD:half"`

**Cálculo de balance** (`balanceCalculator.ts`):
```typescript
function parseYukyuDate(dateStr: string): { date: string; value: number } {
  if (dateStr.endsWith(':half')) {
    return { date: dateStr.replace(':half', ''), value: 0.5 };
  }
  return { date: dateStr, value: 1 };
}
```

**UI indicators**:
- LeaveRequest: Botones 全日/半日 para seleccionar duración
- ApplicationManagement: Muestra "(半日)" o "(全日)" junto al tipo
- EmployeeList: Muestra "(半)" junto a fechas de medio día
- AccountingReports: Muestra "(半)" y calcula totales correctamente

### Fin de Semana Permitido (4x2 Shifts)

El sistema **NO bloquea** sábados y domingos para permitir trabajadores con turnos 4x2 (trabajan 4 días, descansan 2). La validación de fin de semana fue eliminada de `LeaveRequest.tsx`.

### Reportes Contables (AccountingReports)

**Selector de año dinámico**: Muestra desde 2024 hasta el año actual (no hardcodeado).

**Período de corte configurable**: Soporta corte al día 15 o 20 del mes (e.g., 20日締め = 前月21日〜当月20日).

**Cálculo de medios días**: Los reportes calculan correctamente 0.5 para `duration: 'half'`.

**Indicador visual**: Las fechas de medio día muestran "(半)" en amarillo.

**Sello digital (判子)**: `DigitalHanko.tsx` renderiza un sello japonés tradicional en Canvas con variantes: approval (rojo), rejection (gris), custom.

### 40-Day Legal Maximum

El balance máximo acumulable es de 40 días por ley laboral japonesa. `expirationService.ts` aplica este límite:
- Si `currentBalance > 40`, el exceso se registra en `excededDays`
- Los días excedentes se pierden automáticamente

## Sistema de Períodos de Yukyu (periodHistory)

Cada empleado tiene un array `periodHistory` que almacena el historial completo de períodos de yukyu (有給休暇) otorgados a lo largo de su carrera.

### Estructura de datos (`PeriodHistory`)

```typescript
interface PeriodHistory {
  periodIndex: number;      // Índice del período (0, 1, 2...)
  periodName: string;       // Nombre legible (初回(6ヶ月), 1年6ヶ月, 2年6ヶ月...)
  elapsedMonths: number;    // Meses desde entrada (6, 18, 30, 42, 54, 66...)
  yukyuStartDate: string;   // Fecha de inicio de validez
  grantDate: Date;          // Fecha de otorgamiento
  expiryDate: Date;         // Fecha de vencimiento (2 años después)
  granted: number;          // Días otorgados en este período
  used: number;             // Días consumidos
  balance: number;          // Días restantes
  expired: number;          // Días expirados (時効) — source of truth for expiration
  carryOver?: number;       // Días transferidos del período anterior
  isExpired: boolean;       // Si el período ya venció
  isCurrentPeriod: boolean; // Si es el período actual
  yukyuDates: string[];     // Array de fechas de uso (subset for this period)
  source: 'excel';          // Origen de datos
  syncedAt: string;         // Timestamp de última sincronización (ISO)
}
```

### Valores válidos de elapsedMonths

Los períodos de yukyu se otorgan en intervalos específicos según la ley laboral japonesa:

| elapsedMonths | periodName | 付与日数 (días según ley) |
|---------------|------------|---------------------------|
| 6 | 初回(6ヶ月) | 10日 |
| 18 | 1年6ヶ月 | 11日 |
| 30 | 2年6ヶ月 | 12日 |
| 42 | 3年6ヶ月 | 14日 |
| 54 | 4年6ヶ月 | 16日 |
| 66 | 5年6ヶ月 | 18日 |
| 78+ | 6年6ヶ月+ | 20日 (máximo) |

### Lógica de importación (buildPeriodHistory)

1. **Normalización Unicode**: Los nombres de columnas se normalizan con NFKC para manejar variaciones de kanji (経 vs 經)
2. **Fallback de fechas**: Si `経過月` no se encuentra, se calcula desde la diferencia entre `有給発生日` y `入社日`
3. **Deduplicación**: Se usa Map con `elapsedMonths` como key para evitar duplicados
4. **Mergeo de fechas**: Períodos duplicados mergean sus `yukyuDates` sin duplicar

### Cálculo de valores actuales vs históricos

- **currentGrantedTotal/currentBalance**: Solo períodos vigentes (no expirados), máximo 40日
- **historicalGrantedTotal/historicalBalance**: Todos los períodos incluyendo expirados

Los valores "current" se usan para mostrar el balance disponible, mientras que los "historical" se usan para reportes y auditoría.

## Components Detail

### DigitalHanko.tsx
Renders a traditional Japanese seal (判子/印鑑) on an HTML Canvas element. Used in AccountingReports for visual authentication. Supports variants:
- `approval` - Red circle with approval text
- `rejection` - Grey circle with rejection text
- `custom` - Configurable text and color

### Skeleton.tsx
Provides loading skeleton components with shimmer animation:
- `DashboardSkeleton` - Dashboard loading state
- `EmployeeListSkeleton` - Employee list loading
- `ApplicationSkeleton` - Application management loading
- `TableSkeleton` - Generic table skeleton (configurable rows and columns)

### DebugEmployeeData.tsx
Development debug tool for inspecting employee data, periodHistory, and manually recalculating balances.

## Security Considerations

### CSV Formula Injection Protection (`utils/csvSanitizer.ts`)
All CSV exports sanitize values to prevent formula injection attacks:
- Dangerous characters: `=`, `+`, `-`, `@`, `\t`, `\r`
- Protection: Prefixes with single quote `'` to force literal interpretation
- References: OWASP CSV Injection, CWE-1236

### localStorage Limits
- `db.saveData()` catches `QuotaExceededError` and alerts the user
- Recommended: Export data periodically to avoid data loss
