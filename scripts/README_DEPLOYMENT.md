# YuKyuDATA Deployment & Performance Scripts

Automatización completa de deployment, testing y monitoreo para YuKyuDATA v6.0.

## Scripts Disponibles

### 1. benchmark-performance.py

Performance benchmarking and SLA validation.

**Usage:**
```bash
# Basic benchmark
python scripts/benchmark-performance.py

# With HTML output
python scripts/benchmark-performance.py --output html

# Compare against baseline
python scripts/benchmark-performance.py --compare benchmarks/baseline.json
```

**Metrics:**
- API response times (P50, P95, P99)
- Bundle load time (simulated 4G)
- Page transition time
- Memory usage
- System health

**Output:**
- JSON report: `benchmarks/benchmark_YYYYMMDD_HHMMSS.json`
- HTML report: `benchmarks/benchmark_YYYYMMDD_HHMMSS.html`

---

### 2. load_test.py

Load testing with Locust for capacity validation.

**Installation:**
```bash
pip install locust
```

**Usage:**
```bash
# Standard load test (50 users, 5 min)
python scripts/load_test.py

# Custom configuration
python scripts/load_test.py --users 100 --spawn-rate 10 --duration 600

# Web UI mode
locust -f scripts/load_test.py --host http://localhost:8000
# Access at http://localhost:8089
```

**What it tests:**
- 50 concurrent users
- 5-minute duration
- 9 critical endpoints
- Mixed read/write operations
- Error rate tracking

**Output:**
- JSON results: `load_test_results/load_test_results_YYYYMMDD_HHMMSS.json`

---

### 3. deploy-production.sh

Blue-green production deployment with automatic rollback.

**Requirements:**
- Docker & Docker Compose
- Network connectivity
- Database backup enabled
- Slack webhook (optional, for notifications)

**Usage:**
```bash
# Standard deployment
bash scripts/deploy-production.sh

# With custom environment
DEPLOY_ENV=production \
SLACK_WEBHOOK_URL="https://hooks.slack.com/..." \
bash scripts/deploy-production.sh

# Dry run (check what would happen)
bash scripts/deploy-production.sh --dry-run
```

**Deployment Flow:**
1. Pre-flight validation (env vars, DB, API)
2. Full database backup
3. Build new Docker image (green)
4. Start on port 8001
5. Health checks
6. Database migrations
7. Smoke tests
8. Switch traffic (port 8001 → 8000)
9. Monitor error rate (30s)
10. Auto-rollback if > 1% errors
11. Stop old version

**Log:**
- `logs/deployment_YYYYMMDD_HHMMSS.log`

**Notifications:**
- Slack channel: #deployments
- Status: success/failure/rollback

---

### 4. smoke-tests.sh

Post-deployment validation tests.

**Usage:**
```bash
# Test against default host
bash scripts/smoke-tests.sh

# Test custom host
bash scripts/smoke-tests.sh http://localhost:8001

# Run from deployment script (automatic)
```

**Tests (10 total):**
1. API Health Check
2. Database Connectivity
3. Core API Endpoints
4. Response Time Validation
5. Static Assets Loading
6. Error Handling (404, 405)
7. Security Headers
8. Pagination Support
9. Content-Type Negotiation
10. Data Integrity

**Success Criteria:**
- All tests passing
- Response time < 1 second
- No 5xx errors

---

### 5. rollback-production.sh

Emergency rollback to previous version.

**Usage:**
```bash
# Rollback to latest backup
bash scripts/rollback-production.sh

# Rollback to specific deployment
bash scripts/rollback-production.sh --deployment-id 20260118_120000
```

**Rollback Process:**
1. Locate backup file
2. Create safety backup of current state
3. Restore database
4. Restart application
5. Health checks
6. Data integrity verification
7. Slack notification

**Important:**
- Always verify backup exists before attempting rollback
- Rollback stops current version gracefully
- Data loss is minimized (uses pre-deployment backup)

---

## Configuration

### Environment Variables

```bash
# Required
export DEPLOY_ENV=production

# Notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export SLACK_WEBHOOK_URL_CRITICAL="https://hooks.slack.com/services/..."

# Database
export DB_BACKUP_PATH="/backups"

# Timing
export DEPLOY_TIMEOUT=300           # seconds
export HEALTH_CHECK_RETRIES=10
export HEALTH_CHECK_INTERVAL=5      # seconds
```

### .env File

Create `.env` in project root:

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Database
DATABASE_URL=sqlite:///./yukyu.db

# Security
JWT_SECRET_KEY=your-256-bit-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=https://...@sentry.io/...
```

---

## Pre-Deployment Checklist

Before running deployment:

```bash
# 1. Run performance benchmark
python scripts/benchmark-performance.py --output html

# 2. Run load test
python scripts/load_test.py --users 50 --duration 300

# 3. Review & sign checklist
cat docs/PRODUCTION_CHECKLIST.md

# 4. Verify all systems
curl http://localhost:8000/api/health
docker ps -a | grep yukyu
sqlite3 yukyu.db "SELECT COUNT(*) FROM employees"

# 5. Create database backup manually (extra safety)
cp yukyu.db backups/manual_backup_$(date +%Y%m%d_%H%M%S).db
```

---

## Post-Deployment Checklist

After deployment:

```bash
# 1. Run smoke tests
bash scripts/smoke-tests.sh http://localhost:8000

# 2. Monitor for 30 minutes
# - Check Prometheus: http://localhost:9090
# - Check AlertManager: http://localhost:9093
# - Watch logs: docker-compose logs -f app

# 3. Verify key functionality
# - Login to application
# - Create test leave request
# - Check notifications
# - Review analytics

# 4. Declare success
# - All smoke tests passing
# - No critical alerts
# - Error rate < 0.1%
# - Response time normal
```

---

## Troubleshooting

### Deployment Fails on Health Check

```bash
# Check application logs
docker-compose logs -f app

# Check database
sqlite3 yukyu.db "PRAGMA integrity_check"

# Manual health check
curl -v http://localhost:8001/api/health

# If still failing, rollback
bash scripts/rollback-production.sh
```

### High Error Rate After Deployment

```bash
# Check recent errors
docker-compose logs -f app | grep ERROR

# Review migrations
python -m alembic current

# Check database state
docker-compose exec postgres psql -U yukyu -c "SELECT version()"

# Auto-rollback if > 1% errors (deployment script handles this)
# Manual rollback:
bash scripts/rollback-production.sh
```

### Smoke Tests Failing

```bash
# Test individual endpoint
curl -v http://localhost:8000/api/health

# Check if service is running
docker ps -a | grep app

# Restart if needed
docker-compose restart app

# Re-run smoke tests
bash scripts/smoke-tests.sh http://localhost:8000
```

### Cannot Connect to Database

```bash
# Check database exists
ls -la yukyu.db

# Restore from backup
cp backups/yukyu_pre_deploy_*.db yukyu.db

# Verify database integrity
sqlite3 yukyu.db ".tables"

# Restart application
docker-compose restart app
```

---

## Monitoring During Deployment

### Real-time Monitoring

```bash
# Terminal 1: Watch logs
tail -f logs/deployment_*.log

# Terminal 2: Monitor error rate
watch -n 2 'curl -s http://localhost:8000/api/health/detailed'

# Terminal 3: Check Docker status
docker stats

# Terminal 4: Database activity
sqlite3 yukyu.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
```

### Prometheus Queries

Access http://localhost:9090 and run:

```promql
# API request rate
rate(api_requests_total[5m])

# Error rate
rate(api_errors_total[5m])

# Response time P95
histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))

# Database connections
database_connections_in_use
```

---

## Performance Targets (SLA)

| Metric | Target | Alert Level |
|--------|--------|-------------|
| API P95 Response | < 200ms | > 250ms |
| API Error Rate | < 0.1% | > 1% |
| Memory Usage | < 50MB | > 100MB |
| CPU Usage | < 80% | > 90% |
| Disk Usage | < 80% | > 90% |
| DB Connections | > 5 available | < 2 available |
| Throughput (POST) | > 50 req/s | < 40 req/s |

---

## Emergency Procedures

### Critical Alert: Service Down

```bash
# 1. Immediate action
bash scripts/rollback-production.sh

# 2. Verify restoration
bash scripts/smoke-tests.sh

# 3. Notify team
# Slack notification sent automatically

# 4. Post-incident
# - Review logs for root cause
# - Document incident
# - Schedule postmortem
```

### Critical Alert: High Error Rate

```bash
# 1. Check recent changes
git log --oneline -5

# 2. Review error logs
docker-compose logs -f app | grep ERROR

# 3. If caused by recent deployment
bash scripts/rollback-production.sh

# 4. Investigate root cause offline
```

### Data Corruption Detected

```bash
# 1. Restore from clean backup
bash scripts/rollback-production.sh

# 2. Verify data integrity
sqlite3 yukyu.db "PRAGMA integrity_check"

# 3. Run database diagnostics
python scripts/validate-migration.py

# 4. Contact database team
```

---

## Best Practices

1. **Always test in staging first**
   - Run full test suite
   - Load test with realistic data
   - Verify backup/restore

2. **Schedule deployments carefully**
   - Off-peak hours preferred
   - Have rollback plan ready
   - Notify stakeholders

3. **Monitor during deployment**
   - Watch error rates
   - Monitor resource usage
   - Check application logs

4. **Keep backups clean**
   - Daily retention: 7 days
   - Weekly retention: 4 weeks
   - Monthly retention: 1 year

5. **Document incidents**
   - What went wrong
   - How it was fixed
   - Prevention measures

---

## Support & Help

### Documentation
- Performance Baseline: `docs/FASE_5b_PERFORMANCE_AND_DEPLOYMENT.md`
- Production Checklist: `docs/PRODUCTION_CHECKLIST.md`
- Incident Response: `docs/INCIDENT_RESPONSE_PLAN.md`

### Useful Commands

```bash
# See deployment logs
tail -n 100 logs/deployment_*.log

# Check Prometheus metrics
curl http://localhost:9090/api/v1/targets

# List available backups
ls -la backups/ | grep "pre_deploy"

# Manual health check
curl -s http://localhost:8000/api/health/detailed | jq .
```

### Escalation

- **DevOps Team:** devops@example.com
- **On-call:** oncall@example.com
- **Emergency:** +1-555-YUKYU-911

---

**Last Updated:** 2026-01-18
**Version:** v6.0
**Status:** Production Ready
