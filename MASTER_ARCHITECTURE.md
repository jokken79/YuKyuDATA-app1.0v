# YUKYU PREMIUM - Master Architecture & Project Memory

> **Version**: 3.0 PREMIUM EVOLUTION
> **Last Updated**: 2025-12-15
> **Purpose**: Este documento sirve como la "memoria central" del proyecto y guía para agentes de desarrollo

---

## 1. VISION DEL PRODUCTO

### 1.1 Mission Statement
Crear la mejor aplicación de gestión de 有給休暇 (vacaciones pagadas) del mercado japonés, combinando:
- **Simplicidad** de uso para empleados
- **Potencia** analítica para managers
- **Compliance** con leyes laborales japonesas
- **Experiencia Premium** de usuario

### 1.2 Diferenciadores vs Competencia

| Feature | 有休ノート | KING OF TIME | freee | **YUKYU PREMIUM** |
|---------|-----------|--------------|-------|-------------------|
| 自動付与 (Auto grant) | ✅ | ✅ | ✅ | ✅ + AI Prediction |
| 申請ワークフロー | ❌ | ✅ | ✅ | ✅ + Self-Service Portal |
| 時間単位管理 | ❌ | ✅ | ✅ | ✅ + 半日/1時間 |
| アラート機能 | ✅ | ✅ | ✅ | ✅ + Intelligent Alerts |
| 分析ダッシュボード | 基本 | 基本 | 基本 | **Premium Analytics** |
| 年次有給休暇管理簿 | ✅ | ✅ | ✅ | ✅ Auto-generated |
| Mobile Access | ✅ | ✅ | ✅ | ✅ PWA Ready |
| 価格 | 無料〜 | ¥300/user | ¥300/user | **競争力のある価格** |

---

## 2. ARQUITECTURA DEL SISTEMA

### 2.1 Stack Tecnológico Actual

```
┌──────────────────────────────────────────────────────────────┐
│                      FRONTEND (SPA)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  HTML5 + CSS3 (Glassmorphism) + Vanilla JS + Chart.js  │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │ HTTP/JSON                       │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   FastAPI Backend                       │ │
│  │  ┌──────────┐  ┌───────────────┐  ┌─────────────────┐  │ │
│  │  │ main.py  │──│ excel_service │──│   database.py   │  │ │
│  │  │ (Routes) │  │   (Parser)    │  │    (SQLite)     │  │ │
│  │  └──────────┘  └───────────────┘  └─────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    yukyu.db (SQLite)                    │ │
│  │  ┌──────────┐ ┌────────┐ ┌───────┐ ┌───────────────┐  │ │
│  │  │employees │ │ genzai │ │ ukeoi │ │leave_requests │  │ │
│  │  └──────────┘ └────────┘ └───────┘ └───────────────┘  │ │
│  │  ┌────────────────────┐                               │ │
│  │  │yukyu_usage_details │                               │ │
│  │  └────────────────────┘                               │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Arquitectura Target (v3.0)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     YUKYU PREMIUM v3.0                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Employee     │  │ Manager      │  │ Admin        │              │
│  │ Self-Service │  │ Dashboard    │  │ Console      │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └─────────────────┼─────────────────┘                       │
│                           ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    API Gateway (FastAPI)                    │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │    │
│  │  │ Auth Module │ │ Rate Limiter│ │ Request Validator   │   │    │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────┘    │
│                           │                                         │
│         ┌─────────────────┼─────────────────┐                       │
│         ▼                 ▼                 ▼                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Leave Request│  │ Analytics    │  │ Notification │              │
│  │ Service      │  │ Service      │  │ Service      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         │                 │                 │                       │
│         └─────────────────┼─────────────────┘                       │
│                           ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   Data Layer                                │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │    │
│  │  │ SQLite DB   │ │ Cache Layer │ │ Audit Log           │   │    │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   AGENT SYSTEM                              │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │    │
│  │  │ Orchestrator│ │ Data Parser │ │ Doc Agent           │   │    │
│  │  │ Agent       │ │ Agent       │ │ (Memory)            │   │    │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. MODELO DE DATOS

### 3.1 Schema Actual (Tablas Existentes)

#### employees (Datos de Vacaciones)
```sql
CREATE TABLE employees (
    id TEXT PRIMARY KEY,          -- {employee_num}_{year}
    employee_num TEXT,
    name TEXT,
    haken TEXT,                   -- 派遣先 (Factory/Location)
    granted REAL,                 -- 付与日数
    used REAL,                    -- 使用日数
    balance REAL,                 -- 残日数
    expired REAL,                 -- 期限切れ
    usage_rate REAL,              -- 消化率 (%)
    year INTEGER,
    last_updated TEXT
);
```

#### genzai (派遣社員 - Dispatch Employees)
```sql
CREATE TABLE genzai (
    id TEXT PRIMARY KEY,          -- genzai_{employee_num}
    status TEXT,                  -- 在職中/退社
    employee_num TEXT,
    dispatch_id TEXT,
    dispatch_name TEXT,           -- 派遣先名
    department TEXT,
    line TEXT,
    job_content TEXT,
    name TEXT,
    kana TEXT,
    gender TEXT,
    nationality TEXT,
    birth_date TEXT,
    age INTEGER,
    hourly_wage INTEGER,
    wage_revision TEXT,
    last_updated TEXT
);
```

#### ukeoi (請負社員 - Contract Employees)
```sql
CREATE TABLE ukeoi (
    id TEXT PRIMARY KEY,          -- ukeoi_{employee_num}
    status TEXT,
    employee_num TEXT,
    contract_business TEXT,       -- 請負業務
    name TEXT,
    kana TEXT,
    gender TEXT,
    nationality TEXT,
    birth_date TEXT,
    age INTEGER,
    hourly_wage INTEGER,
    wage_revision TEXT,
    last_updated TEXT
);
```

#### leave_requests (申請 - Leave Requests)
```sql
CREATE TABLE leave_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_num TEXT NOT NULL,
    employee_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    days_requested REAL NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'PENDING',  -- PENDING/APPROVED/REJECTED
    requested_at TEXT NOT NULL,
    approved_by TEXT,
    approved_at TEXT,
    year INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
```

### 3.2 Nuevas Tablas Propuestas (v3.0)

#### leave_types (Tipos de Licencia)
```sql
CREATE TABLE leave_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,      -- 'YUKYU', 'SICK', 'SPECIAL', etc.
    name_ja TEXT NOT NULL,          -- '有給休暇', '病気休暇', etc.
    name_en TEXT,
    is_paid BOOLEAN DEFAULT 1,
    requires_approval BOOLEAN DEFAULT 1,
    max_days_per_year REAL,
    min_unit TEXT DEFAULT 'day',    -- 'hour', 'half_day', 'day'
    color TEXT,                     -- UI color code
    is_active BOOLEAN DEFAULT 1
);
```

#### leave_balances (Balance Tracking)
```sql
CREATE TABLE leave_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_num TEXT NOT NULL,
    leave_type_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    granted REAL DEFAULT 0,
    carried_over REAL DEFAULT 0,    -- From previous year
    used REAL DEFAULT 0,
    pending REAL DEFAULT 0,         -- In pending requests
    expired REAL DEFAULT 0,
    available REAL GENERATED ALWAYS AS (granted + carried_over - used - pending - expired) STORED,
    grant_date TEXT,                -- 付与日
    expiry_date TEXT,               -- 有効期限
    UNIQUE(employee_num, leave_type_id, year),
    FOREIGN KEY (leave_type_id) REFERENCES leave_types(id)
);
```

#### audit_log (Historial de Cambios)
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,           -- 'CREATE', 'UPDATE', 'DELETE', 'APPROVE', etc.
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    user_id TEXT,
    old_values TEXT,                -- JSON
    new_values TEXT,                -- JSON
    ip_address TEXT
);
```

#### notifications (通知)
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id TEXT NOT NULL,
    type TEXT NOT NULL,             -- 'REQUEST_SUBMITTED', 'REQUEST_APPROVED', 'BALANCE_LOW', etc.
    title TEXT NOT NULL,
    message TEXT,
    is_read BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL,
    read_at TEXT
);
```

---

## 4. API ENDPOINTS

### 4.1 Endpoints Existentes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/employees` | Lista empleados con balance |
| POST | `/api/sync` | Sincroniza desde Excel |
| POST | `/api/upload` | Sube archivo Excel |
| GET | `/api/genzai` | Lista dispatch employees |
| GET | `/api/ukeoi` | Lista contract employees |
| GET | `/api/leave-requests` | Lista solicitudes |
| POST | `/api/leave-requests` | Nueva solicitud |
| POST | `/api/leave-requests/{id}/approve` | Aprobar |
| POST | `/api/leave-requests/{id}/reject` | Rechazar |
| GET | `/api/employees/{num}/leave-info` | Info completa empleado |
| GET | `/api/stats/by-factory` | Stats por fábrica |
| GET | `/api/yukyu/usage-details` | Fechas individuales |
| GET | `/api/yukyu/monthly-summary/{year}` | Resumen mensual |

### 4.2 Nuevos Endpoints Propuestos (v3.0)

#### Self-Service Portal
```
POST /api/auth/login                    # Login empleado
GET  /api/me                            # Mi perfil
GET  /api/me/balance                    # Mi balance actual
GET  /api/me/requests                   # Mis solicitudes
POST /api/me/requests                   # Nueva solicitud (self-service)
GET  /api/me/calendar                   # Mi calendario de uso
```

#### Manager Dashboard
```
GET  /api/manager/team                  # Equipo del manager
GET  /api/manager/pending               # Solicitudes pendientes
POST /api/manager/bulk-approve          # Aprobar múltiples
GET  /api/manager/analytics             # Analytics del equipo
GET  /api/manager/alerts                # Alertas (low balance, etc.)
```

#### Admin Console
```
GET  /api/admin/users                   # Gestión usuarios
POST /api/admin/grant-leave             # Otorgar días manualmente
GET  /api/admin/reports/compliance      # Reporte compliance
GET  /api/admin/reports/annual-ledger   # 年次有給休暇管理簿
POST /api/admin/settings                # Configuración sistema
```

#### Notifications
```
GET  /api/notifications                 # Mis notificaciones
POST /api/notifications/{id}/read       # Marcar como leída
```

---

## 5. FEATURES ROADMAP

### Phase 1: Foundation Enhancement (Current Sprint)
- [x] Sistema básico de 申請 (requests)
- [x] Balance tracking
- [x] UI Premium (Deep Ocean theme)
- [ ] **Employee Self-Service Portal**
- [ ] **Improved Request Workflow**
- [ ] **Alert System**

### Phase 2: Compliance & Reporting
- [ ] 年次有給休暇管理簿 auto-generation
- [ ] 5日取得義務 tracking & alerts
- [ ] Time-unit leave (時間単位有給)
- [ ] Half-day leave (半日有給)
- [ ] Carry-over automation

### Phase 3: Intelligence & Analytics
- [ ] Usage pattern analysis
- [ ] Predictive balance alerts
- [ ] Team coverage optimization
- [ ] Department comparison
- [ ] Export reports (PDF, Excel)

### Phase 4: Enterprise Features
- [ ] Multi-tenant support
- [ ] Role-based access control
- [ ] API authentication (OAuth2/JWT)
- [ ] Audit logging
- [ ] Integration APIs (Slack, Teams)

---

## 6. SISTEMA DE AGENTES

### 6.1 Agente Orquestador (Orchestrator)

**Responsabilidad**: Coordinar tareas complejas entre múltiples agentes y servicios.

```python
# Pseudo-código del Orchestrator
class OrchestratorAgent:
    """
    Coordina el flujo de trabajo entre agentes especializados.

    Capacidades:
    - Descomponer tareas complejas en subtareas
    - Asignar subtareas a agentes especializados
    - Monitorear progreso y manejar errores
    - Consolidar resultados
    """

    def process_request(self, request_type, data):
        if request_type == "SYNC_ALL":
            return self.orchestrate_full_sync(data)
        elif request_type == "GENERATE_REPORT":
            return self.orchestrate_report_generation(data)
        elif request_type == "BULK_OPERATION":
            return self.orchestrate_bulk_operation(data)

    def orchestrate_full_sync(self, excel_path):
        """Sincronización completa con validación y notificaciones."""
        steps = [
            ("parse", DataParserAgent.parse_excel),
            ("validate", DataParserAgent.validate_data),
            ("save", DatabaseService.save_all),
            ("notify", NotificationService.notify_sync_complete),
            ("document", DocumentorAgent.log_sync)
        ]
        return self.execute_pipeline(steps, excel_path)
```

### 6.2 Agente Parseador de Datos (Data Parser)

**Responsabilidad**: Parsear y validar datos de múltiples fuentes (Excel, CSV, API).

```python
class DataParserAgent:
    """
    Especializado en parsing inteligente de datos.

    Capacidades:
    - Detección automática de headers
    - Mapeo flexible de columnas
    - Validación de datos
    - Transformación de formatos
    - Detección de anomalías
    """

    COLUMN_MAPPINGS = {
        'employee_num': ['社員№', '従業員番号', '社員番号', '番号', 'id', 'no'],
        'name': ['氏名', '名前', 'name', '社員名'],
        'granted': ['付与数', '付与日数', '付与', '総日数'],
        'used': ['消化日数', '使用日数', '使用', '消化'],
        'balance': ['期末残高', 'balance', 'remaining', '残高', '残り'],
        # ... más mappings
    }

    def parse_excel(self, file_path):
        """Parse Excel con detección inteligente."""
        pass

    def validate_data(self, data):
        """Validar datos parseados."""
        validations = [
            self.check_required_fields,
            self.check_numeric_ranges,
            self.check_date_formats,
            self.check_duplicates,
            self.check_balance_consistency
        ]
        return self.run_validations(validations, data)

    def detect_anomalies(self, data):
        """Detectar valores anómalos."""
        anomalies = []
        for record in data:
            if record['used'] > record['granted']:
                anomalies.append({
                    'type': 'OVERUSE',
                    'record': record,
                    'message': f"Used ({record['used']}) > Granted ({record['granted']})"
                })
        return anomalies
```

### 6.3 Agente Documentador (Memory Agent)

**Responsabilidad**: Mantener la "memoria" del sistema - logs, historial, documentación.

```python
class DocumentorAgent:
    """
    Mantiene la memoria histórica y documentación del sistema.

    Capacidades:
    - Logging estructurado de operaciones
    - Generación de documentación
    - Historial de cambios
    - Búsqueda semántica en logs
    - Generación de reportes de actividad
    """

    def log_operation(self, operation_type, details, result):
        """Registrar operación en el audit log."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation_type,
            'details': details,
            'result': result,
            'context': self.get_current_context()
        }
        self.save_to_audit_log(entry)
        self.update_documentation_if_needed(entry)

    def generate_activity_report(self, period):
        """Generar reporte de actividad."""
        pass

    def search_history(self, query, filters=None):
        """Buscar en historial."""
        pass

    def get_system_state_snapshot(self):
        """Capturar estado actual del sistema."""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_employees': self.count_employees(),
            'pending_requests': self.count_pending_requests(),
            'recent_syncs': self.get_recent_syncs(),
            'system_health': self.check_system_health()
        }
```

### 6.4 Agente de Compliance

**Responsabilidad**: Asegurar cumplimiento con leyes laborales japonesas.

```python
class ComplianceAgent:
    """
    Monitorea y asegura cumplimiento legal.

    Capacidades:
    - Verificar 5日取得義務 (obligación de 5 días)
    - Alertas de expiración de días
    - Generación de 年次有給休暇管理簿
    - Validación de reglas de carry-over
    """

    JAPAN_LABOR_RULES = {
        'minimum_annual_use': 5,              # 5日取得義務
        'carry_over_limit_years': 2,          # 2年繰越
        'max_accumulation': 40,               # Max 40日
        'grant_after_6_months': 10,           # 6ヶ月経過で10日
    }

    def check_5_day_compliance(self, employee_num, year):
        """Verificar cumplimiento de 5日取得義務."""
        usage = self.get_employee_usage(employee_num, year)
        if usage < 5:
            return {
                'compliant': False,
                'current_usage': usage,
                'required': 5,
                'remaining_to_comply': 5 - usage,
                'alert_level': 'WARNING' if usage >= 3 else 'CRITICAL'
            }
        return {'compliant': True}

    def generate_annual_ledger(self, year):
        """Generar 年次有給休暇管理簿 oficial."""
        pass
```

---

## 7. UI/UX IMPROVEMENTS

### 7.1 Employee Self-Service Portal

```
┌─────────────────────────────────────────────────────────────────┐
│  YUKYU PREMIUM - Employee Portal                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Welcome, 田中 太郎 さん              [通知 🔔 3]        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐        │
│  │ 残り日数      │ │ 今年度使用    │ │ 申請中        │        │
│  │   15.5日      │ │   4.5日       │ │   2件         │        │
│  │   ━━━━━━━    │ │               │ │               │        │
│  └───────────────┘ └───────────────┘ └───────────────┘        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📅 有給休暇を申請する                    [+ 新規申請]   │   │
│  │                                                          │   │
│  │  開始日: [2025-01-15 📅] 終了日: [2025-01-17 📅]        │   │
│  │  日数: [3日 ▼]   種類: [全日 ▼]                         │   │
│  │  理由: [私用                                    ]        │   │
│  │                                          [申請する]       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📋 最近の申請                                           │   │
│  │  ──────────────────────────────────────────────────────  │   │
│  │  2025/01/10-12  3日  私用      [承認済 ✅]               │   │
│  │  2025/01/05     1日  通院      [承認済 ✅]               │   │
│  │  2024/12/28-29  2日  年末休暇  [承認済 ✅]               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📊 使用履歴カレンダー                                   │   │
│  │  [2025年 ◀ ▶]                                           │   │
│  │  ┌───┬───┬───┬───┬───┬───┬───┐                         │   │
│  │  │日 │月 │火 │水 │木 │金 │土 │                         │   │
│  │  ├───┼───┼───┼───┼───┼───┼───┤                         │   │
│  │  │   │   │   │ 1 │ 2 │ 3 │ 4 │                         │   │
│  │  │   │   │   │   │   │🟢│   │  ← 有給取得日            │   │
│  │  └───┴───┴───┴───┴───┴───┴───┘                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Manager Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  YUKYU PREMIUM - Manager Dashboard                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ⚠️ 承認待ち: 5件                [一括承認] [全て見る]   │   │
│  │  ──────────────────────────────────────────────────────  │   │
│  │  □ 山田 花子   01/20-22  3日  私用     [✓] [✗]          │   │
│  │  □ 佐藤 一郎   01/25     1日  通院     [✓] [✗]          │   │
│  │  □ 鈴木 次郎   02/01-03  3日  旅行     [✓] [✗]          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🚨 アラート                                             │   │
│  │  ──────────────────────────────────────────────────────  │   │
│  │  🔴 高橋 三郎: 5日取得義務未達成 (現在: 2日/5日)         │   │
│  │  🟡 伊藤 四郎: 残り3日で有効期限切れ                     │   │
│  │  🟡 渡辺 五郎: 今年度未使用                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📊 チーム統計                                           │   │
│  │                                                          │   │
│  │  平均消化率: ━━━━━━━━━━━━━━━ 68%                        │   │
│  │  総残日数:   234.5日                                     │   │
│  │  今月申請:   12件                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. COMPLIANCE CON LEY JAPONESA

### 8.1 年次有給休暇の法定ルール

| 継続勤務年数 | 付与日数 |
|-------------|---------|
| 6ヶ月 | 10日 |
| 1年6ヶ月 | 11日 |
| 2年6ヶ月 | 12日 |
| 3年6ヶ月 | 14日 |
| 4年6ヶ月 | 16日 |
| 5年6ヶ月 | 18日 |
| 6年6ヶ月以上 | 20日 |

### 8.2 Reglas a Implementar

1. **5日取得義務** (desde 2019)
   - Todo empleado con 10+ días debe usar mínimo 5 días/año
   - Sistema debe alertar cuando no se cumple
   - Manager puede designar fechas si empleado no las toma

2. **繰越ルール** (Carry-over)
   - Máximo 2 años de validez
   - Usar FIFO (primero los más antiguos)
   - Alertar antes de expiración

3. **年次有給休暇管理簿**
   - Obligatorio mantener registro por 3 años
   - Debe incluir: 基準日, 付与日数, 取得日, 残日数

---

## 9. ESTADO ACTUAL DEL PROYECTO

### 9.1 Archivos Principales

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `main.py` | 475 | API FastAPI con 20+ endpoints |
| `database.py` | 638 | SQLite operations, 5 tablas |
| `excel_service.py` | ~400 | Parser con detección flexible |
| `templates/index.html` | 187 | Frontend SPA |
| `static/js/app.js` | 425 | Lógica JavaScript |
| `static/css/main.css` | 299 | Estilos premium |

### 9.2 Métricas de Datos

- **Empleados (employees)**: ~1,691 registros
- **Genzai (dispatch)**: ~1,067 empleados
- **Ukeoi (contract)**: ~141 empleados
- **Leave Requests**: Sistema nuevo, pendiente de uso

### 9.3 Commits Recientes

```
1c873b8 feat: Premium UI Redesign and Logic Fixes
2695108 Initial commit
```

---

## 10. PRÓXIMOS PASOS

### Inmediato (Esta sesión)
1. [ ] Crear sistema de agentes (archivos Python)
2. [ ] Mejorar UI del portal de solicitudes
3. [ ] Implementar alertas de compliance
4. [ ] Añadir notificaciones

### Corto plazo (1-2 semanas)
1. [ ] Employee Self-Service Portal completo
2. [ ] Manager Dashboard mejorado
3. [ ] Reportes de compliance
4. [ ] Tests unitarios

### Mediano plazo (1 mes)
1. [ ] Autenticación y autorización
2. [ ] 年次有給休暇管理簿 generator
3. [ ] Time-unit leave support
4. [ ] Mobile PWA

---

## 11. NOTAS DE DESARROLLO

### Convenciones de Código
- **Python**: PEP 8, docstrings en español/japonés
- **JavaScript**: ES6+, JSDoc comments
- **SQL**: UPPERCASE keywords, snake_case names
- **Git**: Commits en inglés, mensajes descriptivos

### Variables de Entorno Requeridas
```bash
# Para producción
DATABASE_URL=sqlite:///yukyu.db
EXCEL_DEFAULT_PATH=/path/to/有給休暇管理.xlsm
EMPLOYEE_REGISTRY_PATH=/path/to/社員台帳.xlsm
SECRET_KEY=your-secret-key
```

---

> **Este documento es la "memoria viva" del proyecto. Debe actualizarse con cada cambio significativo.**

---

*Generated by YUKYU PREMIUM Development Team*
*Last updated: 2025-12-15*
