# Plan de Acción - CI/CD y Deployment
**YuKyuDATA-app**
**Versión:** 1.0
**Fecha:** 17 de Enero, 2026

---

## RESUMEN EJECUTIVO

### Estado Actual vs Objetivo

```
MÉTRICA                    ACTUAL    OBJETIVO    GAP
────────────────────────────────────────────────────────
Pipeline Duration           15 min      10 min    -33%
Deployment Automation       20%         100%      +80%
Test Coverage               80%         85%       +5%
Monitoring Active           10%         100%      +90%
Production Ready            40%         100%      +60%
Mean Time to Recovery       30 min      5 min     -83%
Deployment Frequency        Monthly     Weekly    5×
Backup Verification         0%          100%      +100%
```

### Critical Issues

| Issue | Severity | Fix Time |
|-------|----------|----------|
| No real deployment | 🔴 CRITICAL | 3 days |
| Backup not tested | 🔴 CRITICAL | 2 days |
| No health check validation | 🔴 CRITICAL | 1 day |
| Deployment placeholder | 🔴 CRITICAL | 3 days |
| Monitoring offline | 🔴 CRITICAL | 2 days |

---

## FASE 1: FOUNDATION (Semanas 1-2)

### 1.1 Objetivo
Implementar automatización real del deployment para que pueda usarse en producción.

### 1.2 Tareas

#### TAREA 1: Crear Script de Deployment Blue-Green

**Descripción:**
Implementar deployment blue-green sin downtime.

**Files to Create:**
- `scripts/deploy-blue-green.sh`
- `scripts/health-check.sh`
- `.github/workflows/deploy-blue-green.yml`

**Implementation:**
```bash
# scripts/deploy-blue-green.sh

#!/bin/bash
set -e

VERSION="${1:-latest}"
REGISTRY="ghcr.io/jokken79/YuKyuDATA-app1.0v"

# Color selection
CURRENT_COLOR=$(cat /tmp/color.txt 2>/dev/null || echo "blue")
NEW_COLOR=$([[ $CURRENT_COLOR == "blue" ]] && echo "green" || echo "blue")
NEW_PORT=$([[ $NEW_COLOR == "blue" ]] && echo "9000" || echo "9001")

echo "🚀 Deploying $VERSION to $NEW_COLOR (port $NEW_PORT)"

# 1. Pull new image
docker pull "$REGISTRY:$VERSION"

# 2. Stop existing container
docker stop "yukyu-$NEW_COLOR" 2>/dev/null || true
docker rm "yukyu-$NEW_COLOR" 2>/dev/null || true

# 3. Start new container
docker run -d --name "yukyu-$NEW_COLOR" \
  -p "127.0.0.1:$NEW_PORT:8000" \
  -v yukyu-data:/app/data \
  -v yukyu-logs:/app/logs \
  -e DATABASE_URL="postgresql://..." \
  --health-cmd="curl -f http://localhost:8000/health || exit 1" \
  --health-interval=10s \
  --health-timeout=5s \
  --health-retries=3 \
  "$REGISTRY:$VERSION"

echo "⏳ Waiting for health check..."
for i in {1..30}; do
  if docker inspect "yukyu-$NEW_COLOR" | grep -q '"healthy"'; then
    echo "✅ Container is healthy"
    break
  fi
  sleep 2
done

# 4. Run smoke tests
echo "🧪 Running smoke tests..."
bash scripts/smoke-tests.sh "localhost:$NEW_PORT" || {
  echo "❌ Smoke tests failed"
  docker stop "yukyu-$NEW_COLOR"
  exit 1
}

# 5. Update nginx upstream
echo "🔄 Switching traffic..."
docker exec yukyu-nginx bash -c "
cat > /etc/nginx/conf.d/upstream.conf <<EOF
upstream backend {
  server 127.0.0.1:$NEW_PORT;
}
EOF
nginx -s reload
"

# 6. Save color
echo "$NEW_COLOR" > /tmp/color.txt

echo "✅ Deployment complete!"
echo "Old version will be kept for 10 minutes for rollback"

# 7. Cleanup after delay
sleep 600
OLD_COLOR=$([[ $NEW_COLOR == "blue" ]] && echo "green" || echo "blue")
docker stop "yukyu-$OLD_COLOR" 2>/dev/null || true
docker rm "yukyu-$OLD_COLOR" 2>/dev/null || true

echo "🧹 Old version removed"
```

**Acceptance Criteria:**
- ✅ Script completes without errors
- ✅ New container becomes healthy
- ✅ Smoke tests pass
- ✅ Traffic switches to new version
- ✅ Old version removed after 10 minutes
- ✅ Rollback possible during 10-minute window

**Estimated Time:** 6-8 hours

---

#### TAREA 2: Crear Smoke Tests

**Description:**
Automated tests que corren post-deployment para validar que la aplicación funciona.

**File:** `scripts/smoke-tests.sh`

```bash
#!/bin/bash

HOST="${1:-localhost:8000}"
FAILED=0

test_endpoint() {
  local name="$1"
  local url="$2"
  local expected_code="${3:-200}"

  echo -n "Testing $name... "
  status=$(curl -s -o /dev/null -w "%{http_code}" "$url")

  if [ "$status" == "$expected_code" ]; then
    echo "✅"
  else
    echo "❌ (got $status, expected $expected_code)"
    FAILED=$((FAILED + 1))
  fi
}

echo "Running smoke tests against $HOST"
echo "================================"

# Health check
test_endpoint "Health" "http://$HOST/api/health" 200

# API endpoints
test_endpoint "Employees" "http://$HOST/api/employees?year=2025" 200
test_endpoint "Dashboard" "http://$HOST/" 200
test_endpoint "Docs" "http://$HOST/docs" 200

# Database connectivity
test_endpoint "DB Status" "http://$HOST/api/db-status" 200

# Verify data integrity
echo -n "Checking employee count... "
count=$(curl -s "http://$HOST/api/employees?year=2025" | jq '.meta.total // 0')
if [ "$count" -gt 0 ]; then
  echo "✅ (found $count employees)"
else
  echo "❌ (no employees found)"
  FAILED=$((FAILED + 1))
fi

echo "================================"
if [ $FAILED -eq 0 ]; then
  echo "✅ All smoke tests passed"
  exit 0
else
  echo "❌ $FAILED tests failed"
  exit 1
fi
```

**Acceptance Criteria:**
- ✅ 6+ endpoint tests
- ✅ Health check validation
- ✅ Data integrity check
- ✅ Fails if any test fails

**Estimated Time:** 4 hours

---

#### TAREA 3: Automatizar Database Migrations

**Description:**
Ejecutar migrations automáticamente en el deployment.

**Modification:** `.github/workflows/deploy.yml`

```yaml
jobs:
  deploy:
    steps:
      - name: Run database migrations
        if: ${{ always() && needs.preflight.result == 'success' }}
        run: |
          # Create temporary container for migrations
          docker run --rm \
            -e DATABASE_URL="postgresql://..." \
            -v /tmp/migrations:/migrations \
            "$REGISTRY/$IMAGE_NAME:$VERSION" \
            alembic upgrade head

      - name: Backup before migration
        run: |
          # Create backup before applying migrations
          pg_dump -U $DB_USER $DB_NAME > /backups/pre-migration-$(date +%s).sql

          # Keep last 5 backups
          ls -t /backups/pre-migration-*.sql | tail -n +6 | xargs rm -f
```

**Acceptance Criteria:**
- ✅ Migrations run before deployment
- ✅ Backup created before migrations
- ✅ Rollback possible if migration fails
- ✅ Migration status logged

**Estimated Time:** 3 hours

---

#### TAREA 4: Implement Rollback Procedure

**Description:**
Automated rollback si health check falla.

**File:** `scripts/rollback.sh`

```bash
#!/bin/bash

CURRENT_COLOR=$(cat /tmp/color.txt)
TARGET_COLOR=$([[ $CURRENT_COLOR == "blue" ]] && echo "green" || echo "blue")

echo "🔄 Rolling back from $CURRENT_COLOR to $TARGET_COLOR"

# Get target container
TARGET_CONTAINER="yukyu-$TARGET_COLOR"

# Check if target is still running
if ! docker inspect "$TARGET_CONTAINER" &>/dev/null; then
  echo "❌ Target container $TARGET_CONTAINER not found"
  exit 1
fi

# Switch traffic back
docker exec yukyu-nginx bash -c "
cat > /etc/nginx/conf.d/upstream.conf <<EOF
upstream backend {
  server 127.0.0.1:$([[ $TARGET_COLOR == "blue" ]] && echo "9000" || echo "9001");
}
EOF
nginx -s reload
"

# Stop current
docker stop "yukyu-$CURRENT_COLOR"

# Save rolled-back color
echo "$TARGET_COLOR" > /tmp/color.txt

echo "✅ Rollback complete"
```

**Acceptance Criteria:**
- ✅ Rollback completes in < 30 seconds
- ✅ Old version remains healthy
- ✅ Traffic switched back
- ✅ Can verify rollback succeeded

**Estimated Time:** 2 hours

---

#### TAREA 5: Test Backup Restoration

**Description:**
Automated backup verification procedure.

**File:** `.github/workflows/backup-verify.yml`

```yaml
name: Backup Verification

on:
  schedule:
    - cron: '0 4 * * *'  # Daily at 4 AM
  workflow_dispatch:

jobs:
  verify-backup:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Download latest backup
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          aws s3 cp s3://yukyu-backups/latest.sql.gz ./backup.sql.gz
          gunzip backup.sql.gz

      - name: Start test database
        run: |
          docker run -d --name test-db \
            -e POSTGRES_PASSWORD=test \
            -e POSTGRES_DB=test \
            postgres:15-alpine
          sleep 10

      - name: Restore backup
        run: |
          docker exec test-db psql -U postgres -d test -f backup.sql

      - name: Verify integrity
        run: |
          # Count tables
          table_count=$(docker exec test-db psql -U postgres -d test -c \
            "SELECT COUNT(*) FROM information_schema.tables" | head -3 | tail -1)

          if [ "$table_count" -lt 5 ]; then
            echo "❌ Not enough tables: $table_count"
            exit 1
          fi

          # Check critical table
          employee_count=$(docker exec test-db psql -U postgres -d test -c \
            "SELECT COUNT(*) FROM employees")

          echo "✅ Backup verification passed"

      - name: Cleanup
        if: always()
        run: docker stop test-db && docker rm test-db

      - name: Alert on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: '{"text":"⚠️ Backup verification failed"}'
```

**Acceptance Criteria:**
- ✅ Backup downloads successfully
- ✅ Restore completes in < 5 minutes
- ✅ Integrity checks pass
- ✅ Alerts on failure

**Estimated Time:** 4 hours

---

### 1.3 Summary - Week 1

| Task | Time | Priority |
|------|------|----------|
| Blue-green script | 6h | P0 |
| Smoke tests | 4h | P0 |
| DB migrations | 3h | P0 |
| Rollback procedure | 2h | P1 |
| Backup verification | 4h | P0 |
| **Total** | **19h** | |

**Responsible:** DevOps/Platform Engineer

---

## FASE 2: AUTOMATION (Semanas 3-4)

### 2.1 Test Parallelization

**Goal:** Reduce CI time from 15 min → 5 min

**Implementation:**
```yaml
test:
  strategy:
    matrix:
      shard: [1, 2, 3, 4]

  steps:
    - run: |
        pytest tests/ \
          --splits 4 \
          --group ${{ matrix.shard }} \
          -x  # fail fast
```

**Estimated Speedup:** 4× faster (15 min → 4 min)
**Estimated Time to Implement:** 2 hours

---

### 2.2 Infrastructure as Code (Terraform)

**Goal:** Make infrastructure reproducible and versionable

**Files to Create:**
- `terraform/main.tf` - Main configuration
- `terraform/variables.tf` - Input variables
- `terraform/outputs.tf` - Outputs
- `terraform/docker.tf` - Docker provider config

**Implementation Plan:**
1. Translate docker-compose.secure.yml to Terraform
2. Add AWS / GCP provider
3. Create CI/CD step for `terraform plan`
4. Store state in S3/GCS

**Estimated Time:** 16 hours (depends on cloud provider)

---

### 2.3 Monitoring Activation

**Goal:** Get Prometheus + Grafana + Alerting working

**Steps:**
1. Deploy docker-compose.secure.yml (or subset)
2. Create Grafana datasource (Prometheus)
3. Create dashboards:
   - Application metrics
   - Database metrics
   - Request latency
   - Error rates
4. Configure AlertManager rules

**Estimated Time:** 8 hours

---

## FASE 3: HARDENING (Semanas 5-6)

### 3.1 Security Improvements

| Item | Effort | Priority |
|------|--------|----------|
| WAF (ModSecurity) | 4h | P2 |
| Rate limiting | 3h | P1 |
| JWT rotation | 2h | P1 |
| Secret rotation | 3h | P1 |
| Security headers | 1h | P0 |

---

### 3.2 Incident Response

**Runbooks to Create:**
1. Database down
2. High CPU
3. Disk full
4. Security breach
5. Deployment rollback

**Estimated Time:** 8 hours

---

## FASE 4: OPTIMIZATION (Semanas 7-8)

### 4.1 Performance Baselines

```yaml
# Add to CI
performance-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Load test
      run: |
        # 100 concurrent users, 5 min duration
        ab -n 5000 -c 100 http://localhost:8000/
```

**Estimated Time:** 3 hours

---

### 4.2 Cost Optimization

- Right-sizing resources
- Scheduled scaling
- Spot instances (if cloud)

**Estimated Time:** 4 hours

---

## IMPLEMENTATION TIMELINE

```
WEEK 1      WEEK 2      WEEK 3      WEEK 4      WEEK 5-6    WEEK 7-8
├─────────┼──────────┼──────────┼──────────┼────────────┼─────────┤
│ Phase 1 │ Phase 1  │ Phase 2  │ Phase 2  │ Phase 3    │ Phase 4 │
│ Found.. │ Testing  │ Automation  │ IaC   │ Hardening  │ Optimize│
└─────────┴──────────┴──────────┴──────────┴────────────┴─────────┘

Critical Path:
1. Blue-green deploy (Week 1)
2. Smoke tests (Week 1)
3. DB migrations (Week 1)
4. Test + verify (Week 2)
5. IaC + Monitoring (Week 3-4)
```

---

## RESOURCE REQUIREMENTS

### Team Composition
- 1x Senior DevOps Engineer (40h/week)
- 1x Backend Engineer (for DB migrations) (16h/week)
- 1x Platform Engineer (optional, 8h/week)

### Tools Required
```
Infrastructure:
  - Container registry: Already have (GHCR) ✅
  - Database: Already have (PostgreSQL) ✅
  - Message queue: Optional
  - Cache: Already have (Redis) ✅

Monitoring:
  - Prometheus: Ready to deploy ✅
  - Grafana: Ready to deploy ✅
  - AlertManager: Ready to deploy ✅
  - ELK Stack: Ready to deploy ✅

CI/CD:
  - GitHub Actions: Already have ✅
  - Docker: Already have ✅

Cloud (if needed):
  - S3 for backups: ~$10/month
  - CloudWatch: ~$0/month (if AWS)
```

---

## SUCCESS CRITERIA

### Phase 1 (Foundation)
- ✅ Deploy script works (blue-green)
- ✅ Smoke tests automated
- ✅ DB migrations automated
- ✅ Rollback procedure tested
- ✅ Backup verification working

### Phase 2 (Automation)
- ✅ CI time < 5 minutes
- ✅ Infrastructure as code (Terraform)
- ✅ Monitoring dashboard active
- ✅ Alert rules configured

### Phase 3 (Hardening)
- ✅ WAF enabled
- ✅ Rate limiting working
- ✅ JWT rotation automated
- ✅ Security audit passed

### Phase 4 (Optimization)
- ✅ Performance baselines established
- ✅ Cost tracking implemented
- ✅ Incident runbooks complete
- ✅ Team training done

---

## RISK MITIGATION

### Risk: Deployment Fails in Production
**Mitigation:**
- Test on staging first
- Keep old version running (10 min window)
- Automated rollback
- Smoke tests before traffic shift

### Risk: Data Loss During Migration
**Mitigation:**
- Backup before migration
- Test migrations on copy
- Rollback plan documented
- Verify backup restore works

### Risk: Performance Regression
**Mitigation:**
- Load test before deploy
- Monitor metrics during deploy
- Canary release to subset
- Auto-rollback if error rate > 1%

---

## NEXT STEPS

### Immediate (Next 48 hours)
1. ✅ Review this plan with team
2. ✅ Assign resources
3. ✅ Create GitHub issues for each task
4. ✅ Set up project board (GitHub Projects)

### This Week
1. Start implementing Phase 1 tasks
2. Create test environment (staging)
3. Document current procedures

### Weekly Sync
- Monday 9:00 AM: Planning (30 min)
- Wednesday 3:00 PM: Progress check (30 min)
- Friday 4:00 PM: Demo + retrospective (1 hour)

---

## MONITORING SUCCESS

### Key Metrics

```
Metric                   Current    Target    Timeline
─────────────────────────────────────────────────────
Deployment Time          30 min     5 min     Week 2
Deployment Frequency     Monthly    Weekly    Week 4
CI Pipeline Time         15 min     5 min     Week 3
Test Coverage            80%        85%       Week 2
Mean Time to Recovery    30 min     5 min     Week 2
Backup Restore Time      Unknown    <5 min    Week 1
Uptime                   95%        99.9%     Week 6
```

---

**Document prepared by:** Claude Code Agent
**Date:** January 17, 2026
**Version:** 1.0
**Status:** Ready for Implementation
