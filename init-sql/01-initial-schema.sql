-- YuKyuDATA PostgreSQL Initial Schema
-- This script creates all tables for the vacation management system
-- Created: 2025-12-23
-- Version: 1.0

-- ============================================
-- Table: employees
-- Purpose: Vacation/paid leave management
-- Contains: Annual vacation data with balance tracking
-- ============================================
CREATE TABLE IF NOT EXISTS employees (
    id VARCHAR(50) PRIMARY KEY,
    employee_num VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    haken VARCHAR(255),
    granted NUMERIC(10,2),
    used NUMERIC(10,2),
    balance NUMERIC(10,2),
    expired NUMERIC(10,2),
    usage_rate NUMERIC(5,2),
    year INTEGER NOT NULL,
    grant_year INTEGER,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for employees table
CREATE INDEX IF NOT EXISTS idx_emp_num ON employees(employee_num);
CREATE INDEX IF NOT EXISTS idx_emp_year ON employees(year);
CREATE INDEX IF NOT EXISTS idx_emp_num_year ON employees(employee_num, year);
CREATE INDEX IF NOT EXISTS idx_emp_haken ON employees(haken);
CREATE INDEX IF NOT EXISTS idx_emp_created ON employees(created_at DESC);

-- ============================================
-- Table: yukyu_usage_details
-- Purpose: Granular tracking of vacation usage by date
-- Contains: Individual day-by-day usage records
-- ============================================
CREATE TABLE IF NOT EXISTS yukyu_usage_details (
    id SERIAL PRIMARY KEY,
    employee_num VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    use_date DATE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    days_used NUMERIC(10,2) DEFAULT 1.0,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_num, use_date)
);

-- Indexes for yukyu_usage_details table
CREATE INDEX IF NOT EXISTS idx_usage_employee_year ON yukyu_usage_details(employee_num, year);
CREATE INDEX IF NOT EXISTS idx_usage_date ON yukyu_usage_details(use_date);
CREATE INDEX IF NOT EXISTS idx_usage_month ON yukyu_usage_details(year, month);

-- ============================================
-- Table: genzai
-- Purpose: Dispatch employee registry (派遣社員)
-- Contains: Information about temporary dispatch workers
-- ============================================
CREATE TABLE IF NOT EXISTS genzai (
    id VARCHAR(50) PRIMARY KEY,
    status VARCHAR(50),
    employee_num VARCHAR(20) NOT NULL,
    dispatch_id VARCHAR(50),
    dispatch_name VARCHAR(255),
    department VARCHAR(255),
    line VARCHAR(255),
    job_content TEXT,
    name VARCHAR(255) NOT NULL,
    kana VARCHAR(255),
    gender VARCHAR(20),
    nationality VARCHAR(50),
    birth_date TEXT,  -- ENCRYPTED
    age INTEGER,
    hourly_wage INTEGER,  -- ENCRYPTED
    wage_revision TEXT,
    hire_date DATE,
    leave_date DATE,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for genzai table
CREATE INDEX IF NOT EXISTS idx_genzai_emp ON genzai(employee_num);
CREATE INDEX IF NOT EXISTS idx_genzai_status ON genzai(status);
CREATE INDEX IF NOT EXISTS idx_genzai_dispatch ON genzai(dispatch_id);
CREATE INDEX IF NOT EXISTS idx_genzai_dates ON genzai(hire_date, leave_date);

-- ============================================
-- Table: ukeoi
-- Purpose: Contract employee registry (請負社員)
-- Contains: Information about contract/outsourced workers
-- ============================================
CREATE TABLE IF NOT EXISTS ukeoi (
    id VARCHAR(50) PRIMARY KEY,
    status VARCHAR(50),
    employee_num VARCHAR(20) NOT NULL,
    contract_business VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    kana VARCHAR(255),
    gender VARCHAR(20),
    nationality VARCHAR(50),
    birth_date TEXT,  -- ENCRYPTED
    age INTEGER,
    hourly_wage INTEGER,  -- ENCRYPTED
    wage_revision TEXT,
    hire_date DATE,
    leave_date DATE,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for ukeoi table
CREATE INDEX IF NOT EXISTS idx_ukeoi_emp ON ukeoi(employee_num);
CREATE INDEX IF NOT EXISTS idx_ukeoi_status ON ukeoi(status);
CREATE INDEX IF NOT EXISTS idx_ukeoi_contract ON ukeoi(contract_business);
CREATE INDEX IF NOT EXISTS idx_ukeoi_dates ON ukeoi(hire_date, leave_date);

-- ============================================
-- Table: staff
-- Purpose: Direct staff registry (社員)
-- Contains: Information about full-time employees
-- ============================================
CREATE TABLE IF NOT EXISTS staff (
    id VARCHAR(50) PRIMARY KEY,
    status VARCHAR(50),
    employee_num VARCHAR(20) NOT NULL,
    office VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    kana VARCHAR(255),
    gender VARCHAR(20),
    nationality VARCHAR(50),
    birth_date TEXT,  -- ENCRYPTED
    age INTEGER,
    visa_expiry DATE,
    visa_type TEXT,  -- ENCRYPTED
    spouse VARCHAR(255),
    postal_code TEXT,  -- ENCRYPTED
    address TEXT,  -- ENCRYPTED
    building VARCHAR(255),
    hire_date DATE,
    leave_date DATE,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for staff table
CREATE INDEX IF NOT EXISTS idx_staff_emp ON staff(employee_num);
CREATE INDEX IF NOT EXISTS idx_staff_status ON staff(status);
CREATE INDEX IF NOT EXISTS idx_staff_office ON staff(office);
CREATE INDEX IF NOT EXISTS idx_staff_dates ON staff(hire_date, leave_date);
CREATE INDEX IF NOT EXISTS idx_staff_visa ON staff(visa_expiry);

-- ============================================
-- Table: leave_requests
-- Purpose: Vacation request workflow
-- Contains: Request tracking, approval status, cost calculations
-- ============================================
CREATE TABLE IF NOT EXISTS leave_requests (
    id SERIAL PRIMARY KEY,
    employee_num VARCHAR(20) NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days_requested NUMERIC(10,2) NOT NULL,
    hours_requested NUMERIC(10,2) DEFAULT 0,
    leave_type VARCHAR(50),  -- full, half_am, half_pm, hourly
    reason TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, APPROVED, REJECTED, CANCELLED
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    year INTEGER NOT NULL,
    hourly_wage INTEGER DEFAULT 0,
    cost_estimate NUMERIC(12,2) DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for leave_requests table
CREATE INDEX IF NOT EXISTS idx_lr_emp_num ON leave_requests(employee_num);
CREATE INDEX IF NOT EXISTS idx_lr_status ON leave_requests(status);
CREATE INDEX IF NOT EXISTS idx_lr_year ON leave_requests(year);
CREATE INDEX IF NOT EXISTS idx_lr_dates ON leave_requests(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_lr_requested ON leave_requests(requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_lr_emp_year ON leave_requests(employee_num, year);

-- ============================================
-- Sequences for auto-increment
-- ============================================
CREATE SEQUENCE IF NOT EXISTS yukyu_usage_details_id_seq;
CREATE SEQUENCE IF NOT EXISTS leave_requests_id_seq;

-- ============================================
-- Comments/Documentation
-- ============================================
COMMENT ON TABLE employees IS 'Annual vacation management (有給休暇管理)';
COMMENT ON TABLE genzai IS 'Dispatch employee registry from DBGenzaiX (派遣社員台帳)';
COMMENT ON TABLE ukeoi IS 'Contract employee registry from DBUkeoiX (請負社員台帳)';
COMMENT ON TABLE staff IS 'Direct staff registry from DBStaffX (社員台帳)';
COMMENT ON TABLE leave_requests IS 'Vacation request workflow with approval tracking (休暇申請ワークフロー)';
COMMENT ON TABLE yukyu_usage_details IS 'Individual vacation usage dates for granular tracking (有給使用詳細)';

-- Encrypted fields note:
-- - birth_date (genzai, ukeoi, staff): Encrypted with AES-256-GCM
-- - hourly_wage (genzai, ukeoi): Encrypted with AES-256-GCM
-- - address, postal_code, visa_type (staff): Encrypted with AES-256-GCM
-- Encryption is handled at application level, not database level

COMMIT;
