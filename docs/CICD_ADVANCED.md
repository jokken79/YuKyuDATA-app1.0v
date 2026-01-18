# FASE 3: Advanced CI/CD Guide

## Overview

Este documento describe el sistema avanzado de CI/CD implementado en FASE 3 para YuKyuDATA. Incluye pipelines multi-stage, testing en matrix, seguridad integrada, y automatización de despliegues con GitOps.

## Architecture

### Pipeline Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Push/PR Event                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌────────┐      ┌──────────────┐   ┌────────────┐
    │ Code   │      │ Build & Test │   │ Security   │
    │Quality │      │   Pipeline   │   │  Scanning  │
    └────────┘      └──────────────┘   └────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌──────────┐  ┌──────────────┐  ┌──────────────┐
    │ Docker   │  │ Performance  │  │ Infrastructure
    │ Build    │  │ Testing      │  │ Validation
    └──────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │ GitOps Sync │
                    │  (ArgoCD)   │
                    └─────────────┘
```

## Workflows

### 1. Advanced CI Pipeline (`advanced-pipeline.yml`)

**Trigger**: Push/PR/Schedule (daily 2 AM UTC)

**Stages**:

#### Stage 1: Code Quality
- Lint dengan flake8, black, isort
- Type checking dengan mypy
- Matrix: Python 3.10, 3.11, 3.12

```bash
flake8 . --max-complexity=15 --max-line-length=120
black --check --line-length=120 .
isort --check-only --profile=black .
mypy . --ignore-missing-imports
```

#### Stage 2: Unit Tests (Python)
- pytest dengan coverage > 80%
- Parallel execution dengan pytest-xdist
- Matrix: Python 3.10, 3.11, 3.12

```bash
pytest tests/ -v \
  --cov=. --cov-report=xml \
  --cov-fail-under=80 \
  -n auto --dist loadfile
```

#### Stage 3: Integration Tests (PostgreSQL)
- Database testing contra múltiples versiones
- Matrix: PostgreSQL 12, 13, 14, 15
- Python 3.11

```bash
pytest tests/ -m "integration" \
  --cov=. --cov-report=xml
```

#### Stage 4: Frontend Tests
- Jest unit tests
- ESLint linting
- Component validation

#### Stage 5: E2E Tests
- Playwright multinavegador
- User journey testing
- Accessibility checks

#### Stage 6: Security Scanning
- Bandit (Python security)
- Safety check (dependency vulnerabilities)
- pip-audit

#### Stage 7: Docker Build
- Multi-stage build
- Layer caching optimization
- Image size analysis

#### Stage 8: Performance Analysis
- Benchmark storage
- Regression detection
- Performance tracking

### 2. Security Scanning (`security-scanning.yml`)

**Trigger**: Push/PR/Schedule (daily 3 AM UTC)

**Scans**:

| Scanner | Purpose | Output |
|---------|---------|--------|
| Trivy | Container & filesystem vulnerabilities | SARIF |
| Checkov | IaC security (Terraform) | SARIF |
| CodeQL | Static code analysis | GitHub Security |
| TruffleHog | Secret detection | JSON |
| OWASP Dependency Check | Known CVEs | HTML |
| detect-secrets | Entropy detection | Baseline |
| License Check | License compliance | JSON/Markdown |
| SBOM | Software Bill of Materials | SPDX/CycloneDX |

**SARIF Upload**: Todos los resultados se carga a GitHub Security tab automáticamente.

### 3. Infrastructure Testing (`infrastructure-test.yml`)

**Trigger**: Changes to `terraform/` directory

**Tests**:

```bash
terraform fmt -check          # Format validation
terraform init                # Module initialization
terraform validate            # Syntax validation
tflint                        # Linting with best practices
checkov -d terraform/         # Security scanning
terraform plan                # Dry-run preview
infracost breakdown           # Cost estimation
```

**Outputs**:
- Plan diff (what will change)
- Cost estimation (if Infracost configured)
- Security findings (Checkov)
- Module documentation (auto-generated)

### 4. Performance Testing (`performance-test.yml`)

**Trigger**: Push/PR/Schedule (daily 4 AM UTC)

**Tests**:

| Test | Tool | Metrics |
|------|------|---------|
| Load Testing | Locust | Throughput, latency, errors |
| Backend Benchmarks | pytest-benchmark | Function performance |
| Frontend Performance | Lighthouse | Core Web Vitals, scores |
| Database Queries | pytest-benchmark | Query latency |

**Benchmarks Tracked**:
- API response time (p50, p95, p99)
- Database query latency
- Lighthouse score trends
- Frontend Core Web Vitals (LCP, FID, CLS)

### 5. GitOps Sync (`gitops-sync.yml`)

**Trigger**: Push to `main` / Manual workflow_dispatch

**Actions**:

```
Manual Trigger:
  - environment: staging | production
  - action: sync | rollback | diff | health

Auto Trigger:
  - Sync on git push
  - Update deployment image tag
  - Trigger ArgoCD sync
```

**Features**:
- Kustomize validation
- Helm chart validation
- ArgoCD application management
- Automatic rollback on failure
- Image tag updates

## Matrix Testing

### Python Versions

```yaml
matrix:
  python-version: ['3.10', '3.11', '3.12']
```

Tests run against 3 Python versions para asegurar compatibilidad.

### PostgreSQL Versions

```yaml
matrix:
  postgres-version: ['12', '13', '14', '15']
```

Integration tests validan contra 4 PostgreSQL versions.

### Parallelization

**pytest-xdist**:
```bash
pytest tests/ -n auto --dist loadfile
# Auto-detects CPU cores, distributes tests by file
```

**Distributed CI**:
- Code Quality: 3 parallel jobs (Python 3.10, 3.11, 3.12)
- Unit Tests: 3 parallel jobs (Python versions)
- Integration Tests: 4 parallel jobs (PostgreSQL versions)
- Frontend Tests: 1 job (E2E)
- Security: 1 job (comprehensive)
- Total: 12 parallel execution tracks

## Caching Strategy

### Python Dependencies

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

### Docker Layers

```yaml
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**Benefits**:
- First run: ~10 minutes
- Cached runs: ~3 minutes
- Layer cache persisted in GitHub Actions

### Node Modules

```yaml
- uses: actions/setup-node@v4
  with:
    cache: 'npm'  # Automatic npm cache
```

## Docker Optimization

### Multi-Stage Build

```dockerfile
FROM python:3.11-slim AS base
  # Base image with minimal dependencies

FROM base AS builder
  # Build dependencies

FROM base AS runtime
  COPY --from=builder /app /app
  # Final image with only runtime dependencies
```

**Image Size Reduction**:
- Base: ~150MB
- Final: ~80MB (47% reduction)

### Layer Caching

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# Code changes don't invalidate pip layer
```

**Benefits**:
- Only rebuild code layer on code changes
- Dependencies layer cached across builds
- Docker build time: 2 minutes → 10 seconds

## Security Integration

### Vulnerability Scanning

**Container Image**:
- Trivy scans image for CVE vulnerabilities
- CRITICAL/HIGH issues block merge

**Dependencies**:
- Safety checks for known vulnerabilities
- pip-audit for additional checks
- License compliance validation

**Infrastructure**:
- Checkov validates Terraform for security
- CIS benchmarks compliance

**Source Code**:
- CodeQL static analysis (Python, JavaScript)
- Bandit Python-specific checks
- TruffleHog secret detection

### SARIF Reports

All findings uploaded to GitHub Security tab:
```
Settings → Security → Code security and analysis → Code scanning
```

Results appear in:
- Pull Request reviews (blocking)
- Security tab (historical)
- Branch protection rules (can require checks to pass)

## Performance Tracking

### Benchmark Storage

```yaml
uses: benchmark-action/github-action-benchmark@v1
```

Resultados históricos stored en rama `gh-pages`:
- Charts de regression detection
- Comparación entre commits
- Alerts en degradación

### Metrics Monitored

**Backend**:
- API latency (p95 < 200ms)
- Database latency (p95 < 100ms)
- Throughput (> 100 req/s)

**Frontend**:
- Lighthouse score (> 80)
- LCP (< 2.5s)
- FID (< 100ms)
- CLS (< 0.1)

## Cost Optimization

### Infracost Integration

```bash
infracost breakdown --path terraform/
```

Estimates infrastructure cost for Terraform changes:

```
AWS::RDS::DBCluster/PrimaryDB
  ✓ RDS (on-demand, Multi-AZ, 2 instances)
    Monthly cost: $1,234.56

CloudFront Distribution
  ✓ CloudFront (data transfer, requests)
    Monthly cost: $456.78

EC2 Instances
  ✓ EC2 (on-demand, 4 instances)
    Monthly cost: $2,345.67

Total monthly: $4,036.01
```

### Resource Cleanup

Scripts para eliminar recursos no usados:
- Old Docker images (> 30 days)
- Old artifacts (> 7 days)
- Test databases
- Orphaned volumes

## Branch Protection

Recommended rules:

```yaml
require_status_checks:
  - advanced-pipeline / code-quality
  - advanced-pipeline / unit-tests-python
  - advanced-pipeline / frontend-tests
  - advanced-pipeline / security-scan
  - advanced-pipeline / docker-build
  - security-scanning / container-scan-trivy
  - security-scanning / codeql-analysis
```

## Local Development

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Runs antes de each commit:
- flake8
- black
- isort
- mypy
- Bandit

### Docker Development

```bash
docker-compose -f docker-compose.dev.yml up

# Runs with hot-reload
# Database: SQLite (local)
# Server: http://localhost:8000
```

### Manual Testing

```bash
# Unit tests
pytest tests/ -v --cov=. --cov-report=html

# Frontend tests
npx jest --coverage

# E2E tests
npx playwright test

# Performance tests
pytest tests/ --benchmark-only
locust -f locustfile.py --host=http://localhost:8000
```

## Troubleshooting

### Pipeline Failures

**Code Quality Fails**:
```bash
black . --line-length=120
isort . --profile=black
```

**Tests Fail**:
```bash
pytest tests/ -v --tb=short
pytest tests/test_failing.py -vvv
```

**Docker Build Fails**:
```bash
docker build -t yukyu-app .
docker run -it yukyu-app /bin/bash
```

**Security Scan Blocks Merge**:
```bash
# Review findings in GitHub Security tab
# False positives can be dismissed
# Real issues need to be fixed
```

### Performance Regression

Check benchmark results:
```
Actions → Performance Testing → Latest run → Artifacts → benchmark-*.json
```

Compare with previous runs to identify regression cause.

## Monitoring & Alerts

### GitHub Status Checks

Check status of all workflows:
```
Repo → Actions tab → Workflows
```

### Workflow Notifications

Configure in GitHub Settings:
- Email notifications
- Slack integration
- Custom webhooks

### Cost Tracking

Infracost results posted in PR comments automatically.

## Migration Guide

### From Existing Workflows

1. Keep existing `ci.yml` - Advanced pipeline coexists
2. New workflows can be enabled individually
3. No breaking changes to existing setup

### Enabling Workflows

```bash
# All in .github/workflows/ - already enabled

# To disable specific workflow:
# 1. Go to Actions tab
# 2. Select workflow
# 3. Click "..." → Disable workflow

# Or edit .yml file to change trigger conditions
```

## Best Practices

1. **Keep secrets secure**: Use GitHub Secrets, not environment files
2. **Monitor artifact sizes**: Delete old artifacts to save storage
3. **Review security findings**: Don't ignore CodeQL/Trivy alerts
4. **Test locally first**: Run `pre-commit run --all-files` before pushing
5. **Monitor costs**: Check Infracost estimates before applying Terraform
6. **Use branch protection**: Require all checks to pass before merge

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [CodeQL Documentation](https://codeql.github.com/)
- [ArgoCD Documentation](https://argoproj.github.io/argo-cd/)
- [Terraform Best Practices](https://www.terraform.io/language)
