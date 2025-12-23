# FASE 3 Phase 6: Deployment Checklist

## Pre-Deployment Verification

This checklist ensures all components are ready before executing the PostgreSQL migration.

**Date:** 2025-12-23
**Phase:** 6 - Deployment Strategy
**Database Migration:** SQLite → PostgreSQL

---

## ✅ Pre-Migration Checklist

### Environment & Configuration
- [ ] PostgreSQL 15+ installed and running
- [ ] psycopg2-binary installed: `pip install psycopg2-binary`
- [ ] Alembic installed and configured
- [ ] All Alembic migrations created and tested
- [ ] `.env` file configured with PostgreSQL credentials
- [ ] `DATABASE_TYPE=postgresql` set in environment
- [ ] `DATABASE_URL` set correctly in environment

### Database Preparation
- [ ] PostgreSQL database created (e.g., `yukyu`)
- [ ] PostgreSQL user created with proper permissions
- [ ] Alembic migrations run successfully: `alembic upgrade head`
- [ ] All tables created in PostgreSQL
- [ ] Indexes created and verified
- [ ] Foreign keys and constraints verified

### Code & Testing
- [ ] All code changes reviewed and tested
- [ ] database.py updated with PostgreSQL support
- [ ] main.py startup/shutdown events configured
- [ ] connection pooling implemented and tested
- [ ] All unit tests passing (SQLite tests)
- [ ] All PostgreSQL integration tests passing
- [ ] Connection pool tests passing
- [ ] Health check endpoint tested and working

### Backup & Recovery
- [ ] SQLite database backed up: `cp yukyu.db yukyu_backup_$(date +%Y%m%d_%H%M%S).db`
- [ ] Backup file verified and tested for restore
- [ ] Rollback procedure documented and tested
- [ ] Rollback scripts created and verified

### Data Preparation
- [ ] Data export script created: `scripts/dump_sqlite_to_json.py`
- [ ] Data import script created: `scripts/load_json_to_postgresql.py`
- [ ] Migration verification script created: `scripts/verify_migration.py`
- [ ] Sample data export executed and validated
- [ ] Sample data import executed and validated

---

## 📋 Deployment Steps (Blue-Green Strategy Recommended)

### Phase 1: Pre-Migration (Downtime: None)

#### Step 1: Verify All Prerequisites
```bash
# Check PostgreSQL
psql -U postgres -d yukyu -c "SELECT version();"

# Check environment
env | grep DATABASE_
env | grep DB_

# Run health checks
python monitoring/health_check.py --detailed
```

**Expected Result:**
- [ ] PostgreSQL version 15+ is running
- [ ] DATABASE_TYPE and DATABASE_URL are set
- [ ] All health checks pass

#### Step 2: Create Backup
```bash
# Backup SQLite
cp yukyu.db yukyu_backup_$(date +%Y%m%d_%H%M%S).db

# Verify backup
ls -lh yukyu_backup_*.db
```

**Expected Result:**
- [ ] Backup file created successfully
- [ ] Backup file size is reasonable (should match original)

#### Step 3: Export SQLite Data
```bash
# Export to JSON
python scripts/dump_sqlite_to_json.py

# Verify export
ls -lh data_export_*.json
```

**Expected Result:**
- [ ] JSON export created
- [ ] File contains all tables and rows
- [ ] File size is reasonable

---

### Phase 2: Data Migration (Downtime: ~1-5 minutes)

#### Step 1: Stop Application
```bash
# Stop running uvicorn
pkill -f "uvicorn main:app" 2>/dev/null || true

# Verify stopped
sleep 2 && netstat -tlnp | grep 8000 || echo "✅ Port 8000 is free"
```

**Expected Result:**
- [ ] Application stopped successfully
- [ ] Port 8000 is available

#### Step 2: Load Data to PostgreSQL
```bash
# Load data with verification
python scripts/load_json_to_postgresql.py \
  --source data_export_*.json \
  --verify

# Monitor for errors
tail -20 load.log
```

**Expected Result:**
- [ ] All data loaded successfully
- [ ] Row counts match SQLite
- [ ] Verification passes

#### Step 3: Verify Migration
```bash
# Run detailed verification
python scripts/verify_migration.py --detailed

# Check specific tables
psql -U yukyu_user -d yukyu -c "SELECT COUNT(*) as total_rows FROM (
  SELECT COUNT(*) FROM employees UNION ALL
  SELECT COUNT(*) FROM genzai UNION ALL
  SELECT COUNT(*) FROM ukeoi UNION ALL
  SELECT COUNT(*) FROM staff UNION ALL
  SELECT COUNT(*) FROM leave_requests UNION ALL
  SELECT COUNT(*) FROM yukyu_usage_details
) t;"
```

**Expected Result:**
- [ ] Verification passes
- [ ] Row counts match
- [ ] No data corruption
- [ ] Encryption fields are intact

---

### Phase 3: Application Restart (Downtime: ~1 minute)

#### Step 1: Update Configuration
```bash
# Verify .env is set correctly
cat .env | grep DATABASE_

# Should show:
# DATABASE_TYPE=postgresql
# DATABASE_URL=postgresql://...
```

**Expected Result:**
- [ ] DATABASE_TYPE is set to `postgresql`
- [ ] DATABASE_URL points to PostgreSQL database

#### Step 2: Start Application with PostgreSQL
```bash
# Start with PostgreSQL
export DATABASE_TYPE=postgresql
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, monitor startup
sleep 3 && python monitoring/health_check.py --detailed
```

**Expected Result:**
- [ ] Application starts without errors
- [ ] Health check shows PostgreSQL is active
- [ ] Employee count matches migration
- [ ] Connection pool is initialized

#### Step 3: Verify API Endpoints
```bash
# Test key endpoints
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/api/employees | jq '.[] | {id, name}' | head -20
curl -s http://localhost:8000/api/genzai | jq '.[0]'
curl -s http://localhost:8000/api/ukeoi | jq '.[0]'
curl -s http://localhost:8000/api/db-status | jq .
```

**Expected Result:**
- [ ] Health endpoint returns `healthy`
- [ ] Database shows `postgresql`
- [ ] Employees data returns successfully
- [ ] Genzai data returns successfully
- [ ] Ukeoi data returns successfully
- [ ] Row counts match SQLite

---

## 🔍 Post-Deployment Verification

### Functionality Tests
- [ ] Dashboard loads at http://localhost:8000
- [ ] All vacation data displays correctly
- [ ] All genzai employees display
- [ ] All ukeoi employees display
- [ ] Charts render properly
- [ ] Data filtering works (by year, etc.)
- [ ] Download/export functionality works

### Performance Tests
```bash
# Test query performance
time curl -s http://localhost:8000/api/employees | jq . > /dev/null

# Expected: < 500ms response time
```

- [ ] Query response time < 500ms
- [ ] Dashboard loads within 2 seconds
- [ ] No database timeout errors

### Data Integrity Tests
```bash
# Verify encryption
python scripts/verify_migration.py --detailed

# Check specific encrypted fields
psql -U yukyu_user -d yukyu -c \
  "SELECT id, name, birth_date FROM genzai LIMIT 5;"
```

- [ ] Encrypted fields decrypt correctly
- [ ] Birth dates readable in format YYYY-MM-DD
- [ ] No encrypted data corruption
- [ ] All fields present and valid

### Connection Pool Tests
```bash
# Monitor connection usage
python monitoring/health_check.py --postgres-only --detailed

# Load test with concurrent requests
for i in {1..10}; do
  curl -s http://localhost:8000/api/employees &
done
wait
```

- [ ] Connection pool initializes correctly
- [ ] Pool size matches configuration
- [ ] Concurrent requests handled properly
- [ ] No connection exhaustion errors

---

## ⚠️ Rollback Procedure (If Issues Occur)

### Automatic Rollback
```bash
# If critical issues found immediately after migration:
python scripts/rollback_migration.py

# This will:
# 1. Stop the application
# 2. Restore SQLite from backup
# 3. Update .env to use SQLite
# 4. Verify restored database
```

### Manual Rollback
```bash
# If script rollback fails:

# 1. Stop application
pkill -f "uvicorn main:app"

# 2. Restore database
cp yukyu_backup_20251223_120000.db yukyu.db

# 3. Update configuration
echo "DATABASE_TYPE=sqlite" >> .env
echo "DATABASE_URL=sqlite:///./yukyu.db" >> .env

# 4. Start with SQLite
python -m uvicorn main:app --reload
```

### Verification After Rollback
```bash
# Verify rollback successful
python monitoring/health_check.py --detailed

# Check data integrity
python scripts/verify_migration.py
```

---

## 📊 Monitoring & Alerts (Post-Migration)

### Real-Time Monitoring
```bash
# Monitor connection pool
watch -n 2 "python monitoring/health_check.py --postgres-only"

# Monitor application logs
tail -f app.log | grep -E "ERROR|WARNING|CRITICAL"

# Monitor slow queries
psql -U yukyu_user -d yukyu -c "
  SELECT query, calls, mean_exec_time
  FROM pg_stat_statements
  WHERE mean_exec_time > 100
  ORDER BY mean_exec_time DESC
  LIMIT 10;"
```

### Daily Verification
- [ ] Run health checks daily: `python monitoring/health_check.py`
- [ ] Check error logs for issues
- [ ] Monitor database size and growth
- [ ] Verify backups are created
- [ ] Test restore procedure weekly

### Alerts to Configure
- [ ] Connection pool > 80% utilization
- [ ] Query time > 500ms
- [ ] Error rate > 1%
- [ ] Database disk space > 80%
- [ ] Replication lag > 100MB

---

## 📝 Documentation Updates

- [ ] Update README.md with PostgreSQL instructions
- [ ] Update CLAUDE.md with new database setup
- [ ] Update deployment guide with PostgreSQL steps
- [ ] Document connection string format
- [ ] Document environment variables needed
- [ ] Update troubleshooting guide

---

## 🎯 Success Criteria

### Mandatory (Must-Have)
- [ ] ✅ All data migrated to PostgreSQL (100% row count match)
- [ ] ✅ All tests passing (unit, integration, pooling)
- [ ] ✅ Health check passing
- [ ] ✅ Dashboard functional
- [ ] ✅ API endpoints responding correctly
- [ ] ✅ No data corruption

### Highly Recommended
- [ ] ✅ Encrypted fields decrypting correctly
- [ ] ✅ Connection pooling working
- [ ] ✅ Performance improvement (query time)
- [ ] ✅ Backup and rollback tested
- [ ] ✅ Monitoring configured

### Optional (Nice-to-Have)
- [ ] ✅ Full-text search implemented
- [ ] ✅ Read replica configured
- [ ] ✅ PITR backup enabled
- [ ] ✅ Performance benchmarks logged

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue: Cannot connect to PostgreSQL**
```bash
# Solution: Verify connection string
psql -U yukyu_user -h localhost -d yukyu -c "SELECT 1"

# Check .env
cat .env | grep DATABASE_URL
```

**Issue: Row count mismatch after migration**
```bash
# Solution: Re-run load with logging
python scripts/load_json_to_postgresql.py --source data_export.json --verify 2>&1 | tee load.log

# Compare counts
echo "SQLite:" && sqlite3 yukyu_backup.db "SELECT COUNT(*) FROM employees;"
echo "PostgreSQL:" && psql -U yukyu_user -d yukyu -c "SELECT COUNT(*) FROM employees;"
```

**Issue: Connection pool exhaustion**
```bash
# Solution: Check pool size and increase if needed
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=40

# Restart application
pkill -f uvicorn
python -m uvicorn main:app --reload
```

**Issue: Slow queries after migration**
```bash
# Solution: Analyze tables and vacuum
psql -U yukyu_user -d yukyu -c "
  ANALYZE;
  VACUUM ANALYZE;
"

# Check query plans
psql -U yukyu_user -d yukyu -c "
  EXPLAIN ANALYZE SELECT * FROM employees LIMIT 10;
"
```

---

## 🚀 Timeline

| Phase | Task | Duration | Owner |
|-------|------|----------|-------|
| Pre-Migration | Verification | 30 min | DevOps |
| Pre-Migration | Backup & Export | 10 min | DevOps |
| Migration | Application Stop | 1 min | DevOps |
| Migration | Data Load | 2-5 min | System |
| Migration | Verification | 5 min | DevOps |
| Post-Migration | Application Start | 1 min | DevOps |
| Post-Migration | Testing | 15 min | QA |
| Post-Migration | Monitoring Setup | 20 min | DevOps |
| **Total** | **Complete Migration** | **~1 hour** | |

**Downtime Window:** ~5-10 minutes (data load + app restart)

---

## 📋 Sign-Off

- [ ] Pre-deployment verification complete
- [ ] Deployment executed successfully
- [ ] Post-deployment verification complete
- [ ] All tests passing
- [ ] Monitoring configured
- [ ] Rollback procedure tested
- [ ] Team notified of completion

**Deployment Date:** ________________
**Completed By:** ________________
**Verified By:** ________________

---

## Next Steps (Post-Deployment)

1. **Phase 7:** Monitoring & Performance Optimization
   - Configure automated monitoring
   - Set up alerting
   - Optimize slow queries
   - Tune PostgreSQL parameters

2. **Phase 9:** Full-Text Search Implementation
   - Add tsvector columns for employee names
   - Create GIN indexes
   - Implement search API endpoint

3. **Phase 10:** PITR Backup System
   - Configure WAL archiving
   - Set up automated backups
   - Test point-in-time recovery

---

**Status:** ✅ Phase 6 Checklist Ready
**Next Phase:** Phase 7 - Monitoring & Optimization
**Date:** 2025-12-23

🎯 **All Phase 6 components are now in place for PostgreSQL migration deployment!**
