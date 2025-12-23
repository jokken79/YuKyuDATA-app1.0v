# FASE 3 Phase 7: Monitoring & Performance Optimization

## Overview

Phase 7 implements comprehensive monitoring infrastructure and performance optimization for PostgreSQL, enabling real-time visibility into database performance and automated identification of optimization opportunities.

**Status:** In Progress 🟡
**Date Started:** 2025-12-23
**Expected Completion:** 2025-12-23

---

## Phase 7 Components

### 1. Performance Monitoring System 📊

**File:** `monitoring/performance_monitor.py` (250+ lines)

Comprehensive system monitoring that provides:

#### Features
- ✅ **Slow Query Analysis** - Identifies queries exceeding time threshold
- ✅ **Table Statistics** - Size, row counts, dead rows, operations
- ✅ **Index Usage Analysis** - Finds unused indexes
- ✅ **Cache Hit Ratio** - Database cache performance
- ✅ **Connection Pool Monitoring** - Current connections and states
- ✅ **Table Bloat Detection** - Identifies candidates for VACUUM
- ✅ **Query Plan Analysis** - Optimization opportunity detection

#### Key Metrics Tracked

| Metric | Purpose | Alert Threshold |
|--------|---------|-----------------|
| Cache Hit Ratio | Memory efficiency | < 80% |
| Slow Queries | Performance | > 100ms |
| Dead Rows (Bloat) | VACUUM need | > 20% |
| Unused Indexes | Space savings | 0 scans |
| Connections | Pool utilization | > 80% max |

#### Usage

```bash
# Run comprehensive analysis
python monitoring/performance_monitor.py

# Detailed analysis with all metrics
python monitoring/performance_monitor.py --detailed

# Reset statistics for fresh baseline
python monitoring/performance_monitor.py --reset-stats
```

#### Example Output

```
🏥 Starting comprehensive performance analysis...

🔍 Analyzing slow queries (threshold: 100ms)...
  1. SELECT * FROM employees WHERE year = %s LIMIT %s
     Calls: 1250, Mean: 45.23ms, Max: 152.31ms
  2. SELECT * FROM genzai WHERE status = %s
     Calls: 890, Mean: 38.12ms, Max: 89.45ms

📊 Analyzing table statistics...
  employees:
    Size: 125.45 MB, Rows: 145,230
    Dead rows: 2,345, Inserts: 10,000, Updates: 5,000, Deletes: 500
  genzai:
    Size: 89.23 MB, Rows: 52,100
    Dead rows: 1,200, Inserts: 2,000, Updates: 3,200, Deletes: 150

💡 Optimization Recommendations:
  🔧 Run VACUUM on employees (1.6% bloat)
  🔧 Add index on genzai.status (used in 890 queries)
```

---

### 2. Query Optimizer 🔧

**File:** `monitoring/query_optimizer.py` (300+ lines)

Advanced query analysis and optimization suggestions.

#### Features
- ✅ **Slow Query Analysis** - Detailed analysis of expensive queries
- ✅ **Index Suggestions** - Recommends missing indexes
- ✅ **Sequential Scan Detection** - Identifies inefficient table scans
- ✅ **Table Structure Analysis** - Column types and constraints
- ✅ **Query Plan Inspection** - EXPLAIN ANALYZE parsing
- ✅ **Index Effectiveness** - Measures actual vs potential performance

#### Key Functions

**Analyze Query**
```bash
# Analyze specific slow query
# Provides execution plan and suggestions
```

**Suggest Missing Indexes**
```bash
python monitoring/query_optimizer.py --suggest-indexes
```

Identifies columns that should be indexed based on:
- Frequency in WHERE clauses
- Number of distinct values
- Query execution patterns

**Analyze Table Structure**
```bash
python monitoring/query_optimizer.py --analyze-table employees
```

Shows:
- Table size and row count
- Column definitions and types
- Existing indexes and usage
- Bloat percentage

#### Index Creation Examples

```sql
-- Suggested by optimizer
CREATE INDEX idx_employees_year ON employees(year);
CREATE INDEX idx_genzai_status ON genzai(status);
CREATE INDEX idx_genzai_employee_num ON genzai(employee_num);
CREATE INDEX idx_ukeoi_status ON ukeoi(status);
CREATE INDEX idx_leave_requests_employee_num ON leave_requests(employee_num);
```

---

### 3. Baseline Collection 📈

**File:** `monitoring/baseline_collector.py` (250+ lines)

Tracks performance over time for comparison and regression detection.

#### Features
- ✅ **Baseline Creation** - Captures current performance snapshot
- ✅ **Historical Tracking** - Maintains last 10 baselines
- ✅ **Metric Comparison** - Tracks changes over time
- ✅ **Degradation Detection** - Alerts on performance regression
- ✅ **JSON Storage** - Easy integration and analysis

#### Tracked Metrics

```
- Database size (total)
- Table sizes and row counts
- Index count
- Cache hit ratio
- Connection count
- Date/timestamp
```

#### Usage

**Create Baseline (Before Optimization)**
```bash
python monitoring/baseline_collector.py --create
# Saves: monitoring/baselines.json
```

**Compare Current vs Baseline (After Optimization)**
```bash
python monitoring/baseline_collector.py --compare
```

**View Baseline History**
```bash
python monitoring/baseline_collector.py --show
```

#### Example Comparison Output

```
📊 Comparing metrics with baseline...
  Baseline: 2025-12-23 12:00:00

Database Size:
  Baseline: 2450.34 MB
  Current:  2451.45 MB
  Change:   +1.11 MB (+0.0%)

Cache Hit Ratio:
  Baseline: 92.34%
  Current:  94.12%
  Change:   +1.78%  ✅
```

---

## Implementation Strategy

### Phase 7a: Monitoring Infrastructure ✅ (This Session)

**Components Created:**
1. `monitoring/performance_monitor.py` - Real-time performance metrics
2. `monitoring/query_optimizer.py` - Query analysis and suggestions
3. `monitoring/baseline_collector.py` - Performance baseline tracking

**What's Tracked:**
- Slow queries (>100ms)
- Table statistics (size, rows, bloat)
- Index usage and effectiveness
- Cache hit ratios
- Connection pool status
- Dead rows percentage

---

### Phase 7b: Automated Monitoring (Next)

Will implement:
- Cron jobs for regular metric collection
- Email alerts for threshold violations
- Dashboard visualization
- Historical trend analysis

---

### Phase 7c: Performance Tuning (Next)

Will implement:
- PostgreSQL configuration optimization
- Index creation and maintenance
- Query rewriting suggestions
- Connection pool sizing

---

## How to Use Phase 7

### Initial Setup

**1. Create Performance Baseline (Before Any Changes)**
```bash
# Capture current performance
python monitoring/baseline_collector.py --create

# View baseline
python monitoring/baseline_collector.py --show
```

**2. Run Initial Performance Analysis**
```bash
# Comprehensive analysis
python monitoring/performance_monitor.py --detailed

# Save output for reference
python monitoring/performance_monitor.py > /tmp/initial_analysis.log
```

**3. Identify Optimization Opportunities**
```bash
# Suggest missing indexes
python monitoring/query_optimizer.py --suggest-indexes

# Analyze specific table
python monitoring/query_optimizer.py --analyze-table employees

# Full optimization report
python monitoring/query_optimizer.py
```

### Daily Operations

**Daily Health Check**
```bash
# Check performance metrics
python monitoring/performance_monitor.py

# Check for new slow queries
python monitoring/query_optimizer.py
```

**Weekly Optimization**
```bash
# Compare with baseline
python monitoring/baseline_collector.py --compare

# Identify new optimization opportunities
python monitoring/query_optimizer.py --suggest-indexes
```

---

## PostgreSQL Configuration Tuning

### Recommended Settings for Large Datasets (>100k rows)

**File: `postgresql.conf`**

```ini
# Memory Settings
shared_buffers = 256MB              # 25% of system RAM
effective_cache_size = 1GB          # 75% of system RAM
work_mem = 16MB                     # RAM per operation
maintenance_work_mem = 64MB         # For VACUUM/ANALYZE

# Query Planning
random_page_cost = 1.1              # For SSD (lower = more index use)
effective_io_concurrency = 200      # For SSD parallelism

# Parallelization
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4

# Connection Management
max_connections = 200
connection_limit = 5               # Per role

# Logging for Performance Analysis
log_statement = 'all'              # Or 'mod' for modifications only
log_min_duration_statement = 100   # Log queries > 100ms
log_duration = on
log_connections = on
log_disconnections = on

# Checkpoints and WAL
checkpoint_timeout = '15min'
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Lock Management
deadlock_timeout = '1s'
lock_timeout = '30s'
```

### Performance Tuning Steps

**1. Analyze Current Performance**
```bash
python monitoring/performance_monitor.py --detailed
```

**2. Create Baseline**
```bash
python monitoring/baseline_collector.py --create
```

**3. Apply Optimizations**

```bash
# Run VACUUM on tables with bloat
psql -U yukyu_user -d yukyu -c "VACUUM ANALYZE employees;"
psql -U yukyu_user -d yukyu -c "VACUUM ANALYZE genzai;"

# Create suggested indexes
psql -U yukyu_user -d yukyu -c "
  CREATE INDEX idx_employees_year ON employees(year);
  CREATE INDEX idx_genzai_status ON genzai(status);
"

# Refresh statistics
psql -U yukyu_user -d yukyu -c "ANALYZE;"
```

**4. Collect New Baseline**
```bash
python monitoring/baseline_collector.py --create
```

**5. Compare Results**
```bash
python monitoring/baseline_collector.py --compare
```

---

## Monitoring & Alerting Setup

### Cron Schedule (Recommended)

```bash
# Daily performance analysis (2 AM)
0 2 * * * /usr/bin/python3 /path/to/monitoring/performance_monitor.py >> /var/log/performance.log 2>&1

# Weekly baseline comparison (Sunday 3 AM)
0 3 * * 0 /usr/bin/python3 /path/to/monitoring/baseline_collector.py --compare >> /var/log/baseline.log 2>&1

# Query optimization check (Wednesday 2 AM)
0 2 * * 3 /usr/bin/python3 /path/to/monitoring/query_optimizer.py >> /var/log/optimizer.log 2>&1
```

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Cache Hit < 80% | 75% | 50% | Increase shared_buffers |
| Query Time > 500ms | Yes | Yes | Add index or rewrite |
| Bloat > 20% | Yes | Yes | Run VACUUM |
| Connections > 80% | Yes | Yes | Increase pool size |
| Dead Rows > 10% | Yes | Yes | Run VACUUM ANALYZE |

---

## Performance Optimization Checklist

### Pre-Optimization
- [ ] Create performance baseline
- [ ] Document current metrics
- [ ] Identify bottlenecks (slow queries, missing indexes)
- [ ] Notify stakeholders

### Optimization Phase
- [ ] Apply PostgreSQL configuration tuning
- [ ] Create recommended indexes
- [ ] Run VACUUM ANALYZE
- [ ] Rewrite slow queries
- [ ] Analyze query plans

### Post-Optimization
- [ ] Create new baseline
- [ ] Compare with pre-optimization metrics
- [ ] Verify improvements
- [ ] Document changes made
- [ ] Monitor for regressions

### Success Criteria
- [ ] Cache hit ratio > 90%
- [ ] Query time < 100ms (95th percentile)
- [ ] Bloat < 5%
- [ ] All indexes used regularly
- [ ] No performance regression

---

## Example: Optimizing Slow Employee Query

### 1. Identify Problem

```bash
python monitoring/performance_monitor.py --detailed
# Output shows: SELECT * FROM employees WHERE year = %s (mean: 152ms)
```

### 2. Analyze Query

```bash
psql -U yukyu_user -d yukyu -c "
  EXPLAIN ANALYZE SELECT * FROM employees WHERE year = 2025 LIMIT 20;
"
# Output shows: Seq Scan on employees (slow - no index)
```

### 3. Create Index

```bash
psql -U yukyu_user -d yukyu -c "
  CREATE INDEX idx_employees_year ON employees(year);
  ANALYZE employees;
"
```

### 4. Verify Improvement

```bash
psql -U yukyu_user -d yukyu -c "
  EXPLAIN ANALYZE SELECT * FROM employees WHERE year = 2025 LIMIT 20;
"
# Output shows: Index Scan using idx_employees_year (fast - uses index)
```

### 5. Document Results

```bash
python monitoring/baseline_collector.py --create
python monitoring/baseline_collector.py --compare
# Output shows: Query time improved from 152ms to 18ms (88% faster!)
```

---

## Next Steps (Phase 7 Continuation)

### Phase 7b: Automated Monitoring
- Dashboard for real-time metrics
- Automated alerting system
- Email notifications for threshold violations
- Historical trend visualization

### Phase 7c: Advanced Optimization
- Automatic index creation recommendations
- Query rewriting suggestions
- Connection pool auto-tuning
- Workload analysis and projection

### Phase 7d: Documentation
- Comprehensive optimization guide
- Best practices document
- Troubleshooting guide
- Case studies and examples

---

## Resources

### PostgreSQL Tuning Documentation
- [PostgreSQL Configuration](https://www.postgresql.org/docs/15/runtime-config.html)
- [Query Planning](https://www.postgresql.org/docs/15/using-explain.html)
- [Index Types](https://www.postgresql.org/docs/15/indexes-types.html)

### Monitoring Tools
- `pg_stat_statements` - Query statistics
- `pg_stat_activity` - Active connections
- `pg_stat_user_tables` - Table statistics
- `EXPLAIN/EXPLAIN ANALYZE` - Query planning

---

## Files Created

```
monitoring/
├── performance_monitor.py       (250+ lines) - Real-time metrics
├── query_optimizer.py           (300+ lines) - Query optimization
├── baseline_collector.py        (250+ lines) - Baseline tracking
└── baselines.json              (created on first --create)

Documentation:
└── FASE3_PHASE7_MONITORING.md  (this file)
```

---

**Phase 7 Status:** In Progress 🟡
**Next Phase:** Phase 7b - Automated Monitoring & Alerting
**Date:** 2025-12-23
