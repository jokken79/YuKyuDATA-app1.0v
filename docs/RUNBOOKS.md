# CI/CD Runbooks - Operational Procedures

## Emergency Procedures

### Incident: Pipeline Red (All Builds Failing)

**Symptoms**: All GitHub Actions workflows are failing

**Diagnosis Steps**:
1. Go to `Actions` tab in GitHub
2. Check latest run of `advanced-pipeline`
3. Click on failed job to see error logs
4. Look for common patterns

**Common Causes & Solutions**:

#### 1. Database Service Unavailable
```bash
# Problem: PostgreSQL service failed to start
# Solution:
docker ps | grep postgres
docker logs <postgres-container>
docker restart <postgres-container>

# Verify:
docker exec <postgres-container> pg_isready
```

#### 2. Cache Corruption
```bash
# Problem: Actions cache is corrupted
# Solution:
# Go to: Settings → Actions → Caches
# Delete all caches for the branch
# Re-run failed workflow

# Local solution:
rm -rf ~/.cache/pip
rm -rf node_modules/
pip install -r requirements.txt
npm install
```

#### 3. Dependency Version Conflict
```bash
# Problem: New version of dependency breaks tests
# Solution:

# Option A: Pin version temporarily
# Edit requirements.txt:
# Change: package>=1.0
# To: package==1.0.5

# Option B: Update constraints
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt

# Then: git commit -m "fix: Update dependencies"
```

#### 4. Secrets Missing or Expired
```bash
# Problem: API keys or tokens expired
# Solution:
# 1. Go to: Settings → Secrets and variables → Actions
# 2. Update the expired secret
# 3. Re-run the workflow

echo "New secret value" | base64
# Copy base64 output to GitHub Secrets
```

**Recovery Steps**:

```bash
# 1. Identify root cause (see logs)
# 2. Fix on local machine:
pytest tests/ -v
npm run test
docker build .

# 3. If it fails locally, fix it
# 4. Commit fix
git commit -m "fix: <description>"
git push

# 5. Monitor GitHub Actions
# 6. Verify all checks pass before merging
```

---

### Incident: Deployment Failed, Need Rollback

**Symptoms**: Production deployment failed or has bugs

**Automatic Rollback**:

The deploy workflow has automatic rollback built-in. If post-deployment verification fails:

```yaml
# Automatically triggers rollback job
# Reverts to previous Docker image
# Restores previous database (if applicable)
```

**Manual Rollback** (if needed):

```bash
# 1. Go to Actions → Deploy workflow
# 2. Click "Run workflow" dropdown
# 3. Select environment and check "Rollback" option
# (Requires custom rollback job setup)

# Alternative: SSH to server
ssh deploy-user@production-server

# Check current image
docker ps --format "{{.Image}}" | grep yukyu

# Get previous image tag
docker images | grep yukyu | head -5

# Stop current
docker stop yukyu-app

# Start previous version
docker run -d --name yukyu-app \
  -p 8000:8000 \
  -v yukyu-data:/app/data \
  --restart unless-stopped \
  ghcr.io/YuKyuDATA-app:previous-tag

# Verify
curl http://localhost:8000/api/health
```

---

### Incident: Security Scan Blocked Merge (False Positive)

**Symptoms**: GitHub shows security alert but code is safe

**Diagnosis**:
1. Go to `Security` tab in GitHub repo
2. Click `Code scanning alerts`
3. Find the alert
4. Review the finding

**Dismiss False Positive**:

```markdown
Method 1: Via GitHub UI
1. Open the alert
2. Click "Dismiss" dropdown
3. Select reason: "False positive" or "Won't fix"
4. Add comment explaining why

Method 2: Via SARIF report
Edit .github/workflows/security-scanning.yml:
Add to skip_check: CKV_AWS_123,CKV_AWS_456

Method 3: Via code change
Fix the issue directly (usually safer)
```

**Common False Positives**:

```python
# ❌ Flagged: "hardcoded password"
config = {
    'test_password': 'hardcoded_test_pass'  # Test data, not real secret
}

# ✅ Solution: Move to test fixtures
# tests/fixtures.py
TEST_PASSWORD = 'hardcoded_test_pass'

# tests/test_something.py
from fixtures import TEST_PASSWORD
```

---

## Regular Maintenance

### Daily Tasks (Automated)

**2 AM UTC**: Advanced CI Pipeline
```bash
# Automatically runs:
- Code quality checks
- Unit tests (3 Python versions)
- Integration tests (4 PostgreSQL versions)
- Frontend tests
- E2E tests
- Security scans
```

**3 AM UTC**: Security Scanning
```bash
# Automatically runs:
- Container vulnerability scan (Trivy)
- IaC security (Checkov)
- SBOM generation
- License compliance
```

**4 AM UTC**: Performance Testing
```bash
# Automatically runs:
- Load testing (Locust)
- Backend benchmarks
- Frontend performance (Lighthouse)
- Database query performance
```

**No action required** - Results available in Actions tab

### Weekly Tasks

#### Review Performance Metrics

```bash
# Monday morning:
# 1. Go to Actions tab
# 2. Click "Performance Testing"
# 3. Click latest run
# 4. Download artifacts:
#    - load-test-results
#    - backend-benchmarks
#    - lighthouse-results

# 5. Check for regressions:
#    - API latency increased?
#    - Database queries slower?
#    - Lighthouse score dropped?
```

#### Review Security Findings

```bash
# Monday 9 AM:
# 1. Go to Security → Code scanning alerts
# 2. Review new alerts since last week
# 3. Triage: fix vs. dismiss vs. document
# 4. For HIGH/CRITICAL: assign to developer
```

#### Check Dependency Updates

```bash
# Dependabot automatically creates PRs for updates
# Review and merge safe updates:

git checkout dependabot/npm_and_yarn/...
npm install
npm test

git checkout dependabot/pip/...
pip install -r requirements.txt
pytest tests/

# If tests pass: merge the PR
```

### Monthly Tasks

#### Cost Review

```bash
# 1st of month:
# Review AWS bills
# Check Infracost estimates for Terraform
# Look for cost anomalies

# If high costs:
- Check for unused resources
- Scale down non-critical environments
- Review database instance sizes
```

#### Dependency Audit

```bash
# pip-audit for Python
pip-audit

# npm audit for JavaScript
npm audit

# Resolve HIGH/CRITICAL vulnerabilities within 2 weeks
```

#### Infrastructure Review

```bash
# 1. Review Terraform state
terraform state list

# 2. Validate current infrastructure matches code
terraform plan
# Should show no changes

# 3. If drift detected:
terraform apply
# Or update .tf files to match actual state
```

#### Certificate/Secret Rotation

```bash
# Check certificate expiry (if using SSL)
openssl s_client -connect yukyu-app.example.com:443 | grep "Not After"

# Rotate secrets if nearing expiry
# Update in GitHub Secrets:
# Settings → Secrets and variables → Actions
```

---

## Deployment Procedures

### Pre-Deployment Checklist

```markdown
Before deploying to production:

✓ Code
  [ ] All commits are reviewed and approved
  [ ] All CI checks pass (green in Actions)
  [ ] No security alerts (or all dismissed)

✓ Testing
  [ ] Unit tests pass (coverage > 80%)
  [ ] Integration tests pass (all DB versions)
  [ ] E2E tests pass
  [ ] Manual smoke testing completed

✓ Release
  [ ] Version number bumped (semantic versioning)
  [ ] CHANGELOG.md updated
  [ ] Release notes prepared
  [ ] Database migrations tested

✓ Infrastructure
  [ ] Terraform plan reviewed
  [ ] Cost estimation acceptable
  [ ] No security warnings
  [ ] Backup plan confirmed
```

### Manual Deployment Steps

```bash
# 1. Ensure on main/master branch
git checkout main
git pull origin main

# 2. Create release tag
git tag v1.2.3
git push origin v1.2.3

# 3. Trigger deployment in GitHub
# Actions → Deploy workflow → Run workflow
# Environment: production
# Skip tests: false
# Version tag: v1.2.3

# 4. Monitor deployment
# Actions tab → Deploy workflow → Latest run
# Check each step completes successfully

# 5. Verify in production
curl https://yukyu-app.example.com/api/health
# Should return 200 with healthy status

# 6. Smoke tests
# Go to app in browser
# Test critical features:
# - Login
# - View employees
# - Create leave request
# - Generate report
```

### Blue-Green Deployment

```bash
# The workflow automatically does blue-green:

# Current (Blue)  | New (Green)
# 100% traffic    | 0% traffic

# 1. Deploy image to Green environment
# 2. Run health checks
# 3. If healthy: switch traffic Blue→Green
# 4. Keep Blue running for quick rollback

# Rollback (if needed):
# 1. Switch traffic Green→Blue
# 2. Keep Blue version available 1 hour
# 3. Then clean up Green
```

### Canary Deployment (if configured)

```bash
# Progressive rollout:
# Hour 1: 10% traffic to new version
# Hour 2: 25% traffic to new version
# Hour 3: 50% traffic to new version
# Hour 4: 100% traffic to new version

# Monitoring:
# - Error rate < 0.1%
# - Latency p95 < 250ms
# - If metrics bad: automatic rollback
```

---

## Scaling Procedures

### Increase Capacity (Traffic Spike)

```bash
# Option 1: AWS Auto Scaling (if using ECS)
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name yukyu-app-prod \
  --desired-capacity 8

# Option 2: Kubernetes (if using K8s)
kubectl scale deployment/yukyu-app --replicas=10 -n production

# Option 3: Manual (Docker on single host)
# Edit docker-compose.yml:
# services:
#   app:
#     deploy:
#       replicas: 5
#
docker-compose up -d
```

### Increase Database Capacity

```bash
# AWS RDS modification
aws rds modify-db-instance \
  --db-instance-identifier yukyu-db \
  --db-instance-class db.r6i.2xlarge \
  --apply-immediately

# PostgreSQL local
# Edit docker-compose.yml:
#   postgres:
#     environment:
#       max_connections: 500
#       shared_buffers: 4GB
#
docker-compose restart postgres
```

---

## Database Operations

### Backup Procedures

```bash
# Automatic backups (daily at 5 AM UTC)
# Stored in AWS Backup vault
# Retention: 30 days

# Manual backup
docker exec yukyu-postgres pg_dump -U yukyu_user yukyu_db > backup.sql

# Verify backup
ls -lh backup.sql
file backup.sql
```

### Restore from Backup

```bash
# Find backup
aws backup describe-recovery-point-by-backup-vault \
  --backup-vault-name yukyu-backups-primary

# Restore to new DB
aws backup restore-db-from-db-backup \
  --recovery-point-arn arn:aws:backup:...
  --target-db-instance-identifier yukyu-db-restored

# Or local restore:
docker exec -i yukyu-postgres psql -U yukyu_user yukyu_db < backup.sql
```

### Database Migration

```bash
# Alembic (if using for migrations)
alembic revision --autogenerate -m "Add new column"
alembic upgrade head

# Verify migration
psql -U yukyu_user -d yukyu_db -c "\d employees"
```

---

## Monitoring & Alerts

### Metrics to Monitor

```
Dashboard: Grafana or CloudWatch

Application Metrics:
- Request latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Throughput (requests/second)
- Active connections

Database Metrics:
- Query latency
- Connections used
- Replication lag
- Cache hit rate

Infrastructure Metrics:
- CPU utilization
- Memory usage
- Disk I/O
- Network throughput
```

### Alert Thresholds

```yaml
Critical (immediate action):
  - Error rate > 5%
  - API latency p99 > 5s
  - Database replication lag > 10s
  - Disk usage > 85%

Warning (investigate):
  - Error rate > 1%
  - API latency p95 > 500ms
  - Database replication lag > 5s
  - Disk usage > 70%
```

### Slack Notifications

```yaml
# Configure in GitHub Secrets:
SLACK_WEBHOOK_URL: https://hooks.slack.com/services/...

# Automatically notified on:
- Deployment started/completed/failed
- Security alert found
- Performance regression detected
- Cost threshold exceeded
```

---

## Troubleshooting Guide

### Issue: Tests Pass Locally, Fail in CI

```bash
# Cause: Environment differences

# Solution:
# 1. Run in Docker (same as CI)
docker-compose -f docker-compose.dev.yml up
docker-compose exec app pytest tests/ -v

# 2. Check environment variables
echo $DATABASE_URL
echo $DEBUG

# 3. Check Python version
python --version  # Should match CI matrix

# 4. Check database state
docker-compose exec postgres psql -U yukyu_user yukyu_db
SELECT COUNT(*) FROM employees;
```

### Issue: Docker Build Fails in CI

```bash
# Cause: Missing dependencies or changed APIs

# Solution:
# 1. Build locally
docker build -t yukyu-app:test .

# 2. If it fails locally, fix it
# Review Dockerfile changes
git diff Dockerfile

# 3. Test the build
docker run -it yukyu-app:test /bin/bash
python -c "import main; print('OK')"

# 4. Commit fix
git push
```

### Issue: Performance Regression Detected

```bash
# Cause: Code change degraded performance

# Solution:
# 1. Identify the commit
git log --oneline -10

# 2. Check the changes
git show <commit>

# 3. Profile the code
# Add timing logs
import time
start = time.time()
# ... code ...
print(f"Took {time.time() - start}s")

# 4. Optimize
# - Add caching
# - Use database indexes
# - Parallelize operations

# 5. Verify improvement
pytest tests/ --benchmark-only
```

---

## Cost Optimization

### Identify Cost Drivers

```bash
# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-02-01 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE

# Top services (usually):
# - RDS (database): 40%
# - EC2/ECS (compute): 35%
# - S3 (storage): 15%
# - Data transfer: 10%
```

### Reduce Costs

```bash
# Database
- Use reserved instances (1-year discount: 30%)
- Reduce backup retention (7 days instead of 30)
- Use Aurora instead of RDS (25% cheaper)

# Compute
- Use spot instances (70% discount)
- Scale down non-production environments
- Use containers instead of VMs

# Storage
- Lifecycle policies (old data → glacier)
- Compression (S3-IDA)
- Delete unused snapshots
```

---

## On-Call Guide

### During On-Call Shift

```
Responsibilities:
- Monitor alerts
- Respond to production issues
- Maintain system uptime
- Escalate if needed

Escalation Path:
1. Try to fix (< 5 min)
2. Call team lead
3. Call engineering manager
4. Call CTO (if critical)
```

### Incident Response

```bash
# 1. Acknowledge alert
# 2. Check dashboard/logs
# 3. Assess severity
# 4. Take action
# 5. Document resolution
# 6. Post-mortem (if severe)

# Critical (P0): Immediate action
# High (P1): Fix within 1 hour
# Medium (P2): Fix within business day
# Low (P3): Fix within week
```

---

## References

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Terraform Docs](https://www.terraform.io/docs)
- [AWS Documentation](https://docs.aws.amazon.com)
- [PostgreSQL Docs](https://www.postgresql.org/docs)
- [Docker Docs](https://docs.docker.com)
