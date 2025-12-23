# Phase 7: Quick Reference Guide

## 🚀 Quick Start

### Initial Setup (First Time)

```bash
# 1. Analyze current performance
python monitoring/performance_monitor.py --detailed

# 2. Create baseline
python monitoring/baseline_collector.py --create

# 3. Get optimization suggestions
python monitoring/query_optimizer.py
```

---

## 📊 Daily Operations

### Check Database Health (2 minutes)

```bash
# All health metrics in one command
python monitoring/health_check.py --detailed
```

**Output includes:**
- SQLite or PostgreSQL status
- Database size
- Row counts per table
- Integrity checks

### Monitor Performance (5 minutes)

```bash
# Real-time performance analysis
python monitoring/performance_monitor.py
```

**Key metrics watched:**
- Slow queries (>100ms)
- Cache hit ratio
- Connection count
- Table bloat

---

## 🔧 Optimization Commands

### Check for Slow Queries

```bash
python monitoring/performance_monitor.py | grep "Analyzing slow"
```

If found:
```bash
# Get detailed suggestions
python monitoring/query_optimizer.py
```

### Suggest Missing Indexes

```bash
python monitoring/query_optimizer.py --suggest-indexes
```

Create recommended indexes:
```bash
psql -U yukyu_user -d yukyu -c "
  CREATE INDEX idx_employees_year ON employees(year);
  CREATE INDEX idx_genzai_status ON genzai(status);
  ANALYZE;
"
```

### Check Table Bloat

```bash
python monitoring/performance_monitor.py | grep "bloat"
```

If bloat > 20%:
```bash
psql -U yukyu_user -d yukyu -c "
  VACUUM ANALYZE employees;
  VACUUM ANALYZE genzai;
"
```

### Analyze Specific Table

```bash
python monitoring/query_optimizer.py --analyze-table employees
```

---

## 📈 Weekly Operations

### Compare Performance Trends

```bash
python monitoring/baseline_collector.py --compare
```

### Create New Baseline

```bash
python monitoring/baseline_collector.py --create
```

### View Baseline History

```bash
python monitoring/baseline_collector.py --show
```

---

## ⚠️ Troubleshooting

### Cache Hit Ratio Too Low

**Problem:** Cache hit ratio < 80%

**Solution:**
```bash
# Check current setting
psql -U postgres -c "SHOW shared_buffers;"

# Increase shared_buffers in postgresql.conf
# shared_buffers = 256MB  (for 1GB+ systems)

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Slow Queries Not Improving

**Problem:** Index created but query still slow

**Solution:**
```bash
# Check query plan again
psql -U yukyu_user -d yukyu -c "
  EXPLAIN ANALYZE SELECT * FROM employees WHERE year = 2025;
"

# If still using Seq Scan:
# 1. Verify index was created
psql -U yukyu_user -d yukyu -c "
  \d employees  -- Shows indexes
"

# 2. Update statistics
psql -U yukyu_user -d yukyu -c "ANALYZE employees;"

# 3. If still not using index, check selectivity
# Column may have low cardinality (few distinct values)
```

### High Dead Rows / Bloat

**Problem:** Table bloat > 20%

**Solution:**
```bash
# Run VACUUM to reclaim space
psql -U yukyu_user -d yukyu -c "VACUUM ANALYZE tablename;"

# If still high bloat after vacuum:
# Table needs FULL VACUUM (locks table)
psql -U yukyu_user -d yukyu -c "VACUUM FULL tablename;"
```

### Too Many Connections

**Problem:** Connection pool nearly full

**Solution:**
```bash
# Check who's connected
psql -U yukyu_user -d yukyu -c "
  SELECT pid, usename, query, state
  FROM pg_stat_activity
  ORDER BY state;
"

# Kill idle connections (if safe)
psql -U postgres -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle' AND query_start < now() - interval '1 hour';
"

# Increase DB_POOL_SIZE environment variable
export DB_POOL_SIZE=20
```

---

## 📋 Common Commands

### Check All Performance Issues

```bash
python monitoring/performance_monitor.py --detailed 2>&1 | grep -E "^  (❌|⚠️|✅)" | head -20
```

### Export Performance Report

```bash
python monitoring/performance_monitor.py > performance_report_$(date +%Y%m%d).txt
```

### Quick Query Analysis

```bash
# Analyze single query
psql -U yukyu_user -d yukyu -c "
  EXPLAIN ANALYZE
  SELECT * FROM employees WHERE year = 2025;
"
```

### Check Database Size

```bash
psql -U yukyu_user -d yukyu -c "
  SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
  FROM pg_database;
"
```

### List All Indexes

```bash
psql -U yukyu_user -d yukyu -c "
  SELECT
    tablename,
    indexname,
    indexdef
  FROM pg_indexes
  WHERE schemaname = 'public';
"
```

### Check Unused Indexes

```bash
psql -U yukyu_user -d yukyu -c "
  SELECT
    tablename,
    indexname,
    idx_scan
  FROM pg_stat_user_indexes
  WHERE idx_scan = 0
  ORDER BY pg_relation_size(indexrelid) DESC;
"
```

---

## 🎯 Daily Checklist

```
☐ Run health check: python monitoring/health_check.py
☐ Check slow queries: python monitoring/performance_monitor.py
☐ No errors in application logs
☐ Cache hit ratio > 90%
☐ No bloat > 20%
☐ All connections healthy
```

## 📊 Weekly Checklist

```
☐ Create baseline: python monitoring/baseline_collector.py --create
☐ Compare with previous: python monitoring/baseline_collector.py --compare
☐ Review slow queries: python monitoring/query_optimizer.py
☐ Check for unused indexes
☐ Verify backups completed
☐ Document any optimizations made
```

---

## 🚨 When to Alert

| Issue | Action |
|-------|--------|
| Cache hit < 70% | Increase shared_buffers |
| Query time > 1s | Add index or optimize |
| Bloat > 30% | Run VACUUM FULL |
| Connections > 90% | Increase pool size |
| Disk > 80% | Archive old data |
| Dead rows > 50% | Emergency VACUUM |

---

## 📞 Performance Contacts

**For PostgreSQL Issues:**
- Documentation: postgresql.org/docs/
- FAQ: postgresql.org/docs/faq.html

**For Application Performance:**
- Check application logs
- Review slow query suggestions
- Run baseline comparison

---

**Last Updated:** 2025-12-23
**Phase 7:** Monitoring & Performance Optimization
