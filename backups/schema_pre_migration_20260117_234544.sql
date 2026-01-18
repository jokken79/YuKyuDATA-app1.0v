BEGIN TRANSACTION;
CREATE TABLE audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    user_id TEXT,
                    old_values TEXT,
                    new_values TEXT,
                    metadata TEXT
                );
CREATE TABLE carryover_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_year INTEGER NOT NULL,
                to_year INTEGER NOT NULL,
                employee_num TEXT NOT NULL,
                days_carried_over REAL,
                days_expired REAL,
                days_capped REAL,
                executed_at TEXT NOT NULL,
                executed_by TEXT,
                executed_reason TEXT,
                UNIQUE(from_year, to_year, employee_num)
            );
CREATE TABLE compliance_audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    employee_num TEXT NOT NULL,
                    employee_name TEXT NOT NULL,
                    action_description TEXT NOT NULL,
                    details TEXT,
                    performed_by TEXT,
                    previous_state TEXT,
                    new_state TEXT,
                    hash_value TEXT UNIQUE NOT NULL,
                    previous_hash TEXT,
                    is_reversal_of TEXT,
                    reversible BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
CREATE TABLE employees (
                id TEXT PRIMARY KEY,
                employee_num TEXT,
                name TEXT,
                haken TEXT,
                granted REAL,
                used REAL,
                balance REAL,
                expired REAL,
                usage_rate REAL,
                year INTEGER,
                last_updated TEXT
            , grant_year INTEGER);
INSERT INTO "employees" VALUES('TEST001_2025','TEST001','Test User',NULL,10.0,0.0,10.0,NULL,NULL,2025,'2026-01-17T15:46:04.116533',NULL);
INSERT INTO "employees" VALUES('TEST002_2025','TEST002','Test User 2',NULL,10.0,2.0,8.0,NULL,NULL,2025,'2026-01-17T15:46:04.171699',NULL);
CREATE TABLE fiscal_year_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                employee_num TEXT NOT NULL,
                year INTEGER NOT NULL,
                days_affected REAL,
                balance_before REAL,
                balance_after REAL,
                performed_by TEXT,
                reason TEXT,
                timestamp TEXT NOT NULL,
                UNIQUE(employee_num, year, action, timestamp)
            );
INSERT INTO "fiscal_year_audit_log" VALUES(1,'DESIGNATE_5DAYS','TEST001',2025,5.0,10.0,10.0,'admin','Legal 5-day requirement - official designation','2026-01-17T15:46:04.129356');
INSERT INTO "fiscal_year_audit_log" VALUES(2,'DEDUCTION','TEST002',2025,2.0,10.0,8.0,'admin','Test deduction','2026-01-17T15:46:04.171699');
CREATE TABLE genzai (
                id TEXT PRIMARY KEY,
                status TEXT,
                employee_num TEXT,
                dispatch_id TEXT,
                dispatch_name TEXT,
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
            , hire_date TEXT, leave_date TEXT);
CREATE TABLE leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_num TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                days_requested REAL NOT NULL,
                hours_requested REAL DEFAULT 0,
                leave_type TEXT DEFAULT 'full',
                reason TEXT,
                status TEXT DEFAULT 'PENDING',
                requested_at TEXT NOT NULL,
                approved_by TEXT,
                approved_at TEXT,
                year INTEGER NOT NULL,
                hourly_wage INTEGER DEFAULT 0,
                cost_estimate REAL DEFAULT 0,
                created_at TEXT NOT NULL
            );
CREATE TABLE notification_reads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                read_at TEXT NOT NULL,
                UNIQUE(notification_id, user_id)
            );
CREATE TABLE official_leave_designation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_num TEXT NOT NULL,
                year INTEGER NOT NULL,
                designated_date TEXT NOT NULL,
                days REAL DEFAULT 1.0,
                reason TEXT,
                designated_by TEXT,
                designated_at TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                UNIQUE(employee_num, year, designated_date)
            );
INSERT INTO "official_leave_designation" VALUES(1,'TEST001',2025,'2026-01-17T15:46:04.129356',5.0,'Legal 5-day requirement (年5日の取得義務)','admin','2026-01-17T15:46:04.129356','CONFIRMED');
CREATE TABLE refresh_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                revoked INTEGER DEFAULT 0,
                revoked_at TEXT,
                user_agent TEXT,
                ip_address TEXT
            );
CREATE TABLE staff (
                id TEXT PRIMARY KEY,
                status TEXT,
                employee_num TEXT,
                office TEXT,
                name TEXT,
                kana TEXT,
                gender TEXT,
                nationality TEXT,
                birth_date TEXT,
                age INTEGER,
                visa_expiry TEXT,
                visa_type TEXT,
                spouse TEXT,
                postal_code TEXT,
                address TEXT,
                building TEXT,
                hire_date TEXT,
                leave_date TEXT,
                last_updated TEXT
            );
CREATE TABLE ukeoi (
                id TEXT PRIMARY KEY,
                status TEXT,
                employee_num TEXT,
                contract_business TEXT,
                name TEXT,
                kana TEXT,
                gender TEXT,
                nationality TEXT,
                birth_date TEXT,
                age INTEGER,
                hourly_wage INTEGER,
                wage_revision TEXT,
                last_updated TEXT
            , hire_date TEXT, leave_date TEXT);
CREATE TABLE yukyu_usage_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_num TEXT,
                name TEXT,
                use_date TEXT,
                year INTEGER,
                month INTEGER,
                days_used REAL DEFAULT 1.0,
                last_updated TEXT,
                UNIQUE(employee_num, use_date)
            );
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_revoked ON refresh_tokens(revoked);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_usage_employee_year
            ON yukyu_usage_details(employee_num, year)
        ;
CREATE INDEX idx_emp_num ON employees(employee_num);
CREATE INDEX idx_emp_year ON employees(year);
CREATE INDEX idx_emp_num_year ON employees(employee_num, year);
CREATE INDEX idx_employees_granted ON employees(year, granted);
CREATE INDEX idx_lr_emp_num ON leave_requests(employee_num);
CREATE INDEX idx_lr_status ON leave_requests(status);
CREATE INDEX idx_lr_year ON leave_requests(year);
CREATE INDEX idx_lr_dates ON leave_requests(start_date, end_date);
CREATE INDEX idx_lr_employee_date ON leave_requests(employee_num, start_date);
CREATE INDEX idx_genzai_emp ON genzai(employee_num);
CREATE INDEX idx_genzai_status ON genzai(status);
CREATE INDEX idx_ukeoi_emp ON ukeoi(employee_num);
CREATE INDEX idx_ukeoi_status ON ukeoi(status);
CREATE INDEX idx_genzai_hire_date ON genzai(hire_date);
CREATE INDEX idx_genzai_leave_date ON genzai(leave_date);
CREATE INDEX idx_genzai_hire_leave ON genzai(hire_date, leave_date);
CREATE INDEX idx_genzai_status_hire ON genzai(status, hire_date);
CREATE INDEX idx_ukeoi_hire_date ON ukeoi(hire_date);
CREATE INDEX idx_ukeoi_leave_date ON ukeoi(leave_date);
CREATE INDEX idx_staff_emp ON staff(employee_num);
CREATE INDEX idx_staff_status ON staff(status);
CREATE INDEX idx_staff_visa_expiry ON staff(visa_expiry);
CREATE INDEX idx_staff_visa_type ON staff(visa_type);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_notif_reads_user ON notification_reads(user_id);
CREATE INDEX idx_notif_reads_notif ON notification_reads(notification_id);
CREATE INDEX idx_fiscal_audit_emp_year ON fiscal_year_audit_log(employee_num, year);
CREATE INDEX idx_fiscal_audit_action ON fiscal_year_audit_log(action);
CREATE INDEX idx_fiscal_audit_timestamp ON fiscal_year_audit_log(timestamp);
CREATE INDEX idx_official_leave_emp_year ON official_leave_designation(employee_num, year);
CREATE INDEX idx_official_leave_status ON official_leave_designation(status);
CREATE INDEX idx_official_leave_date ON official_leave_designation(designated_date);
CREATE INDEX idx_carryover_years ON carryover_audit(from_year, to_year);
CREATE INDEX idx_carryover_emp ON carryover_audit(employee_num);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('official_leave_designation',1);
INSERT INTO "sqlite_sequence" VALUES('fiscal_year_audit_log',2);
COMMIT;
