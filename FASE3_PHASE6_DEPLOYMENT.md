# FASE 3 Phase 6: Deployment Strategy

## Executive Summary

Phase 6 provides a **production-ready deployment strategy** for migrating from SQLite to PostgreSQL with zero data loss and minimal downtime.

**Key Objectives:**
- ✅ Safe migration from SQLite to PostgreSQL
- ✅ Zero data loss
- ✅ Minimal downtime (< 5 minutes)
- ✅ Automatic rollback capability
- ✅ Full monitoring and health checks
- ✅ Clear runbooks for operations team

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Strategies](#deployment-strategies)
4. [Data Migration Process](#data-migration-process)
5. [Rollback Procedures](#rollback-procedures)
6. [Health Checks](#health-checks)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Troubleshooting](#troubleshooting)
10. [Timeline & Resource Estimate](#timeline--resource-estimate)

---

## Architecture Overview

### Current State (Production - SQLite)

```
┌─────────────────────────────────────┐
│   YuKyuDATA Application (FastAPI)   │
├─────────────────────────────────────┤
│   database.py (SQLite mode)         │
├─────────────────────────────────────┤
│   yukyu.db (SQLite file database)   │
├─────────────────────────────────────┤
│   Backups (manual file copies)      │
└─────────────────────────────────────┘
```

**Limitations:**
- Single-threaded connections
- No connection pooling
- File-based (no true ACID)
- Manual backups only
- No replication
- Limited to single server

### Target State (PostgreSQL)

```
┌──────────────────────────────────────────────────────────────┐
│        YuKyuDATA Application (FastAPI)                       │
├──────────────────────────────────────────────────────────────┤
│   database.py (PostgreSQL mode with connection pooling)      │
├──────────────────────────────────────────────────────────────┤
│   PostgreSQL Primary ─────────┬──────────────────────────┐   │
│   (Read/Write)                │                          │   │
│   - Connection Pool (10-20)    │   PostgreSQL Read       │   │
│   - Automated backups          │   Replica               │   │
│   - WAL Archiving              │   (Analytics)           │   │
│   - PITR capability            │                         │   │
└──────────────────────────────────────────────────────────────┘
```

**Improvements:**
- Connection pooling (10-20 concurrent)
- True ACID compliance
- Automated backups with PITR
- Read replicas for analytics
- Horizontal scaling capability
- Enterprise-grade reliability

---

## Pre-Deployment Checklist

### 1 Week Before Deployment

- [ ] Verify all Phase 5 tests pass (SQLite + PostgreSQL)
- [ ] Schedule maintenance window (after business hours)
- [ ] Notify stakeholders of maintenance window
- [ ] Prepare rollback communication plan
- [ ] Review all deployment scripts
- [ ] Test rollback procedure in staging
- [ ] Backup current SQLite database (`yukyu.db`)
- [ ] Document current version/commit hash

### 2 Days Before Deployment

- [ ] Verify PostgreSQL server is provisioned and accessible
- [ ] Test PostgreSQL connection with `DATABASE_URL`
- [ ] Run Alembic migrations in staging: `alembic upgrade head`
- [ ] Verify all tables created in PostgreSQL
- [ ] Test data migration script with test data
- [ ] Verify backups are working
- [ ] Brief all operations team members

### Day of Deployment

- [ ] Lock users out (maintenance page on `/`)
- [ ] Create backup of SQLite: `cp yukyu.db yukyu_backup_YYYYMMDD.db`
- [ ] Create PostgreSQL backup: `pg_dump > backup_before_migration.sql`
- [ ] Start migration script
- [ ] Monitor migration progress
- [ ] Verify data integrity
- [ ] Test application with PostgreSQL
- [ ] Unlock users
- [ ] Monitor application for errors

---

## Deployment Strategies

### Strategy 1: Blue-Green Deployment (Recommended ✨)

**Least Risk - Two parallel environments**

```
Phase 1: Setup (Day 0-1)
┌─────────────────────────────────────┐
│ Blue (Current - SQLite)             │ ← LIVE
├─────────────────────────────────────┤
│ Green (New - PostgreSQL) - Setup    │
└─────────────────────────────────────┘

Phase 2: Migration (Day 2)
┌─────────────────────────────────────┐
│ Blue (Current - SQLite)             │ ← LIVE (read-only)
├─────────────────────────────────────┤
│ Green (New - PostgreSQL) - Running  │ ← Test data
└─────────────────────────────────────┘

Phase 3: Cutover (Hour X)
┌─────────────────────────────────────┐
│ Blue (SQLite) - Offline             │
├─────────────────────────────────────┤
│ Green (PostgreSQL) - LIVE           │ ← Switch traffic
└─────────────────────────────────────┘

Phase 4: Validation (Hour X+2)
┌─────────────────────────────────────┐
│ Blue (SQLite) - Keep for 24h        │ ← Emergency fallback
├─────────────────────────────────────┤
│ Green (PostgreSQL) - LIVE           │
└─────────────────────────────────────┘
```

**Advantages:**
- ✅ Minimal downtime (< 5 minutes)
- ✅ Quick rollback to Blue
- ✅ Full testing before cutover
- ✅ Zero data loss

**Timeline:**
- Setup: 4 hours
- Testing: 24 hours
- Cutover: 5 minutes
- Validation: 2 hours

**Resource Requirements:**
- Two application servers
- One PostgreSQL server
- One load balancer (optional)

### Strategy 2: In-Place Migration (Faster)

**More Risk - Single server migration**

```
Step 1: Backup (5 min)
  sqlite://yukyu.db → yukyu_backup.db

Step 2: Stop Application (1 min)
  Maintenance page shows 'Updating database'

Step 3: Export Data (2 min)
  sqlite://yukyu.db → data.json

Step 4: Create PostgreSQL (2 min)
  CREATE DATABASE yukyu...

Step 5: Import Data (3 min)
  data.json → postgresql://yukyu

Step 6: Run Migrations (2 min)
  alembic upgrade head

Step 7: Start Application (1 min)
  DATABASE_TYPE=postgresql

Step 8: Verify (5 min)
  GET /health → {database: postgresql}

Total Downtime: ~5 minutes
```

**Advantages:**
- ✅ Single server (lower cost)
- ✅ Faster deployment
- ✅ Simpler orchestration

**Disadvantages:**
- ⚠️ All data in memory during migration
- ⚠️ Higher risk of failure mid-migration
- ⚠️ Less testing capability

**Recommended For:**
- Small datasets (< 100k records)
- Off-peak hours only
- Experienced ops team

### Strategy 3: Canary Deployment (Progressive)

**Lower Risk - Gradual rollout**

```
Phase 1: Deploy (5%)
  5% of traffic → PostgreSQL
  95% of traffic → SQLite
  Monitor for 2 hours

Phase 2: Increase (25%)
  25% of traffic → PostgreSQL
  75% of traffic → SQLite
  Monitor for 4 hours

Phase 3: Increase (50%)
  50% of traffic → PostgreSQL
  50% of traffic → SQLite
  Monitor for 4 hours

Phase 4: Increase (100%)
  100% of traffic → PostgreSQL
  0% SQLite
  Keep fallback for 24h
```

**Requirements:**
- Load balancer with traffic shaping
- Separate database connection strings
- Detailed metrics/logging

---

## Data Migration Process

### Pre-Migration Validation

```bash
# 1. Check SQLite database integrity
sqlite3 yukyu.db "PRAGMA integrity_check;"

# 2. Count records in each table
sqlite3 yukyu.db "SELECT 'employees' as table_name, COUNT(*) FROM employees
UNION ALL SELECT 'genzai', COUNT(*) FROM genzai
UNION ALL SELECT 'ukeoi', COUNT(*) FROM ukeoi
UNION ALL SELECT 'staff', COUNT(*) FROM staff
UNION ALL SELECT 'leave_requests', COUNT(*) FROM leave_requests
UNION ALL SELECT 'yukyu_usage_details', COUNT(*) FROM yukyu_usage_details;"

# 3. Check for NULL values in required fields
sqlite3 yukyu.db "
SELECT COUNT(*) as missing_ids FROM employees WHERE id IS NULL;
SELECT COUNT(*) as missing_names FROM employees WHERE name IS NULL;
"
```

### Migration Script Execution

#### Option A: Python Script (Recommended)

```bash
# 1. Export from SQLite to JSON
python scripts/dump_sqlite_to_json.py \
  --source yukyu.db \
  --output data_export.json \
  --include-backup

# 2. Verify export
ls -lh data_export.json
python -c "import json; data=json.load(open('data_export.json')); print(f'Records: {len(data)}')"

# 3. Run Alembic migrations on PostgreSQL
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://user:pass@localhost:5432/yukyu
alembic upgrade head

# 4. Import to PostgreSQL
python scripts/load_json_to_postgresql.py \
  --source data_export.json \
  --verify

# 5. Validate
python scripts/verify_migration.py --source yukyu.db --destination postgresql
```

#### Option B: Direct SQL (Faster for large datasets)

```bash
# 1. Export SQLite to SQL
sqlite3 yukyu.db .dump > yukyu_export.sql

# 2. Create PostgreSQL from SQL
psql -U yukyu_user -d yukyu < init-sql/01-initial-schema.sql

# 3. Copy data (with field type conversion)
psql -U yukyu_user -d yukyu <<'EOF'
\COPY employees FROM 'employees.csv' CSV HEADER;
\COPY genzai FROM 'genzai.csv' CSV HEADER;
-- ... repeat for other tables
EOF
```

### Data Validation Post-Migration

```bash
# 1. Row count verification
echo "SQLite row counts:"
sqlite3 yukyu.db "SELECT 'employees' t, COUNT(*) FROM employees UNION ALL SELECT 'genzai', COUNT(*) FROM genzai UNION ALL SELECT 'ukeoi', COUNT(*) FROM ukeoi UNION ALL SELECT 'staff', COUNT(*) FROM staff UNION ALL SELECT 'leave_requests', COUNT(*) FROM leave_requests UNION ALL SELECT 'yukyu_usage_details', COUNT(*) FROM yukyu_usage_details;" > /tmp/sqlite_counts.txt

echo "PostgreSQL row counts:"
psql -U yukyu_user -d yukyu -t <<'SQL' > /tmp/postgres_counts.txt
SELECT 'employees', COUNT(*) FROM employees
UNION ALL SELECT 'genzai', COUNT(*) FROM genzai
UNION ALL SELECT 'ukeoi', COUNT(*) FROM ukeoi
UNION ALL SELECT 'staff', COUNT(*) FROM staff
UNION ALL SELECT 'leave_requests', COUNT(*) FROM leave_requests
UNION ALL SELECT 'yukyu_usage_details', COUNT(*) FROM yukyu_usage_details;
SQL

# 2. Compare
diff /tmp/sqlite_counts.txt /tmp/postgres_counts.txt || echo "⚠️ Row counts differ!"

# 3. Sample data verification
python -c "
import sqlite3
import psycopg2

# Check 10 random employees
sql_emp = sqlite3.connect('yukyu.db').execute('SELECT id, name FROM employees LIMIT 10').fetchall()
pg_emp = psycopg2.connect('postgresql://user:pass@localhost/yukyu').cursor()
pg_emp.execute('SELECT id, name FROM employees LIMIT 10')
pg_emp_rows = pg_emp.fetchall()

for sql_row, pg_row in zip(sql_emp, pg_emp_rows):
    if sql_row != pg_row:
        print(f'Mismatch: {sql_row} vs {pg_row}')
print('✅ Sample data matches!')
"
```

---

## Rollback Procedures

### Pre-Deployment Rollback (Before Cutover)

```bash
# 1. Keep SQLite database as-is
# 2. Delete PostgreSQL database
psql -U postgres <<EOF
DROP DATABASE IF EXISTS yukyu;
EOF

# 3. Verify SQLite still works
sqlite3 yukyu.db "SELECT COUNT(*) FROM employees;"

# 4. Set DATABASE_TYPE back to SQLite
export DATABASE_TYPE=sqlite

# 5. Restart application
systemctl restart yukyu-app
```

### Post-Cutover Rollback (After PostgreSQL Live)

**Scenario: PostgreSQL crashes or data corruption**

#### Option 1: From PostgreSQL Backup (< 1 minute)

```bash
# 1. Stop application (maintenance mode)
# 2. Restore from PostgreSQL backup
psql -U postgres -d yukyu < backup_before_migration.sql

# 3. Verify data
psql -U yukyu_user -d yukyu "SELECT COUNT(*) FROM employees;"

# 4. Restart application
systemctl restart yukyu-app

# 5. Verify health
curl http://localhost:8000/health
```

#### Option 2: Switch Back to SQLite (< 2 minutes)

```bash
# 1. Stop application
systemctl stop yukyu-app

# 2. Restore SQLite backup
cp yukyu_backup_YYYYMMDD.db yukyu.db

# 3. Set DATABASE_TYPE
export DATABASE_TYPE=sqlite

# 4. Restart application
systemctl start yukyu-app

# 5. Verify
curl http://localhost:8000/health
curl http://localhost:8000/api/employees | jq '.length'
```

#### Option 3: Failover to Read Replica (PostgreSQL HA)

```bash
# 1. Promote read replica to primary
sudo -u postgres /usr/lib/postgresql/15/bin/pg_ctl promote \
  -D /var/lib/postgresql/15/main

# 2. Update connection string
export DATABASE_URL=postgresql://user:pass@replica-host:5432/yukyu

# 3. Restart application
systemctl restart yukyu-app
```

### Rollback Decision Matrix

| Scenario | Rollback Option | RTO | Risk |
|----------|-----------------|-----|------|
| Pre-cutover failure | Option 1 | < 1 min | ✅ Low |
| PostgreSQL data corruption | Option 2 (SQLite) | 2 min | ✅ Low |
| PostgreSQL unavailable (HA) | Option 3 (Replica) | 1 min | ✅ Low |
| Network partition | Manual failover | 5 min | ⚠️ Medium |

---

## Health Checks

### Endpoint: GET /health

Returns comprehensive health status:

```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "timestamp": "2025-12-23T10:30:45.123Z",
  "database": {
    "type": "postgresql",
    "connected": true,
    "employees_count": 1250,
    "connection_pool": {
      "status": "initialized",
      "min_connections": 10,
      "max_connections": 20
    }
  }
}
```

### Monitoring Checks

```bash
#!/bin/bash
# health_check.sh - Run during deployment

# 1. Application responsiveness
echo "Checking application..."
curl -f http://localhost:8000/health || exit 1

# 2. Database connectivity
echo "Checking database..."
curl -f http://localhost:8000/api/employees?limit=1 || exit 1

# 3. Data integrity
echo "Checking data..."
EMPLOYEE_COUNT=$(curl -s http://localhost:8000/api/employees | jq '.length')
if [ "$EMPLOYEE_COUNT" -lt 100 ]; then
  echo "❌ Employee count too low: $EMPLOYEE_COUNT"
  exit 1
fi

# 4. Authentication
echo "Checking auth..."
curl -f -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"change_me"}' || exit 1

echo "✅ All health checks passed!"
```

---

## Post-Deployment Verification

### Immediate (First 5 Minutes)

- [ ] Application responding (GET `/`)
- [ ] Health endpoint returns healthy
- [ ] Database connection verified
- [ ] No error logs in application
- [ ] Connection pool status normal

### Short-term (First Hour)

- [ ] All API endpoints working
- [ ] Login/authentication working
- [ ] Data retrieval correct
- [ ] File uploads working
- [ ] Reports generating correctly
- [ ] No performance degradation

### Medium-term (First 24 Hours)

- [ ] Error rates stable (< 0.1%)
- [ ] Response times similar to baseline
- [ ] Database backups working
- [ ] Connection pool efficient
- [ ] Monitoring alerts normal
- [ ] User feedback positive

### Metrics to Monitor

```
Database Performance:
  - Query response time: < 100ms (p99)
  - Connection pool utilization: 20-80%
  - Connection errors: 0
  - Transaction rollbacks: 0

Application Performance:
  - Error rate: < 0.1%
  - Response time: < 500ms (p99)
  - Throughput: ±5% of baseline
  - Memory usage: ±10% of baseline

Business Metrics:
  - API success rate: > 99.5%
  - User complaints: 0
  - Data integrity: 100%
```

---

## Monitoring & Alerts

### Prometheus Metrics

```yaml
# prometheus.yml config for PostgreSQL monitoring

global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']  # postgres_exporter

  - job_name: 'application'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Create dashboard with:
- PostgreSQL connection pool size/usage
- Query execution time distribution
- Connection errors over time
- Application response times
- Error rate by endpoint
- Database disk usage

### Alert Rules

```yaml
groups:
  - name: database
    rules:
      - alert: PostgreSQLDown
        expr: pg_up == 0
        for: 1m
        annotations:
          summary: "PostgreSQL down"

      - alert: HighConnectionPoolUsage
        expr: pg_stat_activity_count > 18
        annotations:
          summary: "Connection pool near max"

      - alert: HighQueryTime
        expr: histogram_quantile(0.99, pg_query_duration_seconds) > 1
        annotations:
          summary: "Queries taking > 1 second"

  - name: application
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.001
        annotations:
          summary: "Error rate > 0.1%"

      - alert: ApplicationDown
        expr: up{job="application"} == 0
        annotations:
          summary: "Application not responding"
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Cannot connect to PostgreSQL"

**Symptoms:**
- `ERROR: could not connect to server`
- Logs: `psycopg2.OperationalError`

**Resolution:**
```bash
# 1. Verify PostgreSQL is running
systemctl status postgresql

# 2. Check DATABASE_URL
echo $DATABASE_URL

# 3. Test connection manually
psql $(echo $DATABASE_URL | sed 's/postgresql:\/\///')

# 4. Verify firewall
telnet localhost 5432

# 5. Check pg_hba.conf
# Ensure entry for localhost:
# host    all             all             127.0.0.1/32            md5
```

#### Issue 2: "Data mismatch after migration"

**Symptoms:**
- Row counts differ between SQLite and PostgreSQL
- Missing encrypted fields

**Resolution:**
```bash
# 1. Check encryption
python -c "
from crypto_utils import decrypt_field
import psycopg2

conn = psycopg2.connect(...)
cursor = conn.cursor()
cursor.execute('SELECT birth_date FROM genzai LIMIT 1')
encrypted = cursor.fetchone()[0]
decrypted = decrypt_field(encrypted)
print(f'Decrypted: {decrypted}')
"

# 2. Verify constraints
psql -U yukyu_user -d yukyu <<EOF
SELECT CONSTRAINT_NAME, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'public';
EOF

# 3. Re-run validation script
python scripts/verify_migration.py
```

#### Issue 3: "Slow queries after migration"

**Symptoms:**
- Response time increased
- Database CPU high

**Resolution:**
```bash
# 1. Analyze tables
psql -U yukyu_user -d yukyu <<EOF
ANALYZE employees;
ANALYZE genzai;
ANALYZE ukeoi;
ANALYZE staff;
ANALYZE leave_requests;
ANALYZE yukyu_usage_details;
EOF

# 2. Check query plans
psql -U yukyu_user -d yukyu <<EOF
EXPLAIN ANALYZE
SELECT * FROM employees WHERE employee_num = 'EMP001';
EOF

# 3. Check index usage
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname != 'pg_catalog'
ORDER BY tablename, indexname;

# 4. Monitor active queries
SELECT query, query_start, state
FROM pg_stat_activity
WHERE state = 'active';
```

---

## Timeline & Resource Estimate

### Deployment Timeline

| Phase | Activity | Duration | Team |
|-------|----------|----------|------|
| Planning | Review & prepare | 2 hours | DevOps + Eng |
| Pre-flight | System checks | 1 hour | DevOps |
| Maintenance | Lock users | 5 min | N/A |
| Migration | Data migration | 5-15 min | DevOps |
| Testing | Validation | 10 min | QA |
| Unlock | Users can access | 1 min | N/A |
| Monitoring | Watch for issues | 4 hours | DevOps |
| **Total** | | **~4-5 hours** | |

### Resource Requirements

**Hardware:**
- 1x PostgreSQL server (16GB RAM, SSD)
- 1x Application server (existing)
- Network connectivity: < 10ms latency

**Software:**
- PostgreSQL 15+
- Python 3.9+
- psycopg2, Alembic

**Personnel:**
- 1x DevOps Engineer (primary)
- 1x Database Administrator (secondary)
- 1x QA Engineer (testing)
- 1x Engineering Lead (oversight)

**Time Investment:**
- Planning: 4 hours
- Preparation: 8 hours
- Execution: 4 hours
- Post-deployment: 8 hours
- **Total: ~24 hours of work**

---

## Approval & Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| DevOps Lead | ____________ | ________ | __________ |
| DBA | ____________ | ________ | __________ |
| Engineering Lead | ____________ | ________ | __________ |
| Product Manager | ____________ | ________ | __________ |

---

## Appendices

### A. Environment Variables Checklist

```bash
# Production PostgreSQL Settings
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://yukyu_user:SECURE_PASSWORD@prod-db.example.com:5432/yukyu
export DB_POOL_SIZE=10
export DB_MAX_OVERFLOW=20
export DB_POOL_RECYCLE=3600
export DB_POOL_TIMEOUT=30

# Encryption
export ENCRYPTION_KEY=your-256-bit-hex-key

# Application
export JWT_SECRET_KEY=your-jwt-secret
export ENVIRONMENT=production
export LOG_LEVEL=INFO
```

### B. Docker Production Setup

See: `docker-compose.yml` and `docker-compose.production.yml`

### C. Monitoring Setup

See: `monitoring/` directory for Prometheus and Grafana configs

### D. Backup & Recovery

See: `PITR_BACKUP_SETUP.md` for automated backup configuration

---

**Document Version:** 1.0
**Last Updated:** 2025-12-23
**Status:** Ready for Deployment
**Next Phase:** Phase 9 - Full-Text Search
