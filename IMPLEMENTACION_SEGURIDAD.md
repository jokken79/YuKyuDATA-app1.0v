# GUÍA DE IMPLEMENTACIÓN - Hardening y Deployment Seguro
## YuKyuDATA-app v1.0

**Fecha:** 2025-12-23
**Responsable:** DevOps/Security Team
**Timeline:** 6 semanas

---

## TABLA DE CONTENIDOS

1. [Semana 1: Preparación](#semana-1-preparación)
2. [Semana 2: Application Hardening](#semana-2-application-hardening)
3. [Semana 3: Infrastructure Setup](#semana-3-infrastructure-setup)
4. [Semana 4: CI/CD Pipeline](#semana-4-cicd-pipeline)
5. [Semana 5: Monitoring & Compliance](#semana-5-monitoring--compliance)
6. [Semana 6: Testing & Go-Live](#semana-6-testing--go-live)

---

## SEMANA 1: PREPARACIÓN

### 1.1 Setup del Ambiente de Desarrollo

```bash
# Clonar repositorio
git clone https://github.com/your-org/yukyu-app.git
cd yukyu-app

# Crear rama para security implementation
git checkout -b feat/security-hardening

# Crear estructura de directorios
mkdir -p .github/workflows
mkdir -p nginx/{ssl,conf.d}
mkdir -p security/
mkdir -p monitoring/{rules,dashboards}
mkdir -p scripts/{backup,migrate}
mkdir -p tests/security

# Instalar herramientas de seguridad
pip install -r requirements-security.txt
```

### 1.2 Configuración de Secrets

```bash
# Generar secretos seguros
python scripts/generate_secrets.py > .env.production

# Verificar contenido (no commitear!)
cat .env.production

# Copiar a location segura
# En producción: AWS Secrets Manager o HashiCorp Vault
```

### 1.3 Instalación de Herramientas de Testing

```bash
# SAST/DAST
pip install bandit semgrep pylint mypy

# Dependency scanning
pip install safety pip-audit

# Container scanning
curl -fsSL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# Docker
# Asegurarse de tener Docker 20.10+ y Docker Compose 1.29+

# Git hooks para pre-commit
pip install pre-commit
pre-commit install
```

### 1.4 Documentación Inicial

- Revisar `SEGURIDAD_DEPLOYMENT.md` (ya creado)
- Actualizar `README.md` con security guidelines
- Crear `SECURITY.md` con contact info para security reports

---

## SEMANA 2: APPLICATION HARDENING

### 2.1 Implementar Security Headers

**Archivo:** `main.py` (modificar existing code)

```python
from fastapi import FastAPI
from config.security import settings, security_headers

app = FastAPI(title="YuKyuDATA API", version="1.0.0")

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Agregar security headers
    for header, value in security_headers.items():
        response.headers[header] = value

    # Agregar request ID para tracing
    response.headers["X-Request-ID"] = request.headers.get("x-request-id", str(uuid4()))

    return response
```

### 2.2 Implementar Rate Limiting

**Ubicación:** `main.py`

```python
from security.rate_limiter import rate_limit_manager, EndpointRateLimiter

# En endpoints
@app.post("/api/v1/auth/login")
async def login(request: Request, credentials: LoginRequest):
    allowed, info = rate_limit_manager.is_allowed(
        request,
        max_requests=5,
        window_seconds=60
    )

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"},
            headers={"Retry-After": str(info["reset_at"].second)}
        )

    # Process login
    pass
```

### 2.3 Configurar CORS Seguro

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware
from config.security import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
    expose_headers=["X-Total-Count"]
)
```

### 2.4 Implementar Logging Seguro

```python
# logging_config.py
import logging
import json
from datetime import datetime

class SecurityAwareFormatter(logging.Formatter):
    """Formatter que sanitiza PII en logs"""

    SENSITIVE_FIELDS = [
        'password', 'token', 'api_key', 'secret',
        'email', 'phone', 'ssn'
    ]

    def format(self, record):
        # Sanitizar valores sensibles
        if hasattr(record, '__dict__'):
            for field in self.SENSITIVE_FIELDS:
                if field in record.__dict__:
                    record.__dict__[field] = '***REDACTED***'

        return super().format(record)

# Usar en handlers
handler = logging.FileHandler('app.log')
handler.setFormatter(SecurityAwareFormatter())
```

### 2.5 Actualizar requirements.txt

```text
# requirements-security.txt
fastapi==0.104.0
uvicorn==0.24.0
pydantic-settings==2.0.0

# Security
cryptography==41.0.0
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.0
PyJWT==2.8.0
slowapi==0.1.9
redis==5.0.0

# Data validation
pydantic==2.4.0

# Database
sqlalchemy==2.0.0
psycopg2-binary==2.9.0

# Monitoring
sentry-sdk==1.38.0
prometheus-client==0.19.0
python-json-logger==2.0.7

# Testing
pytest==7.4.0
pytest-cov==4.1.0
pytest-asyncio==0.21.0

# Security scanning
bandit==1.7.5
semgrep==1.42.0
```

### 2.6 Testing Inicial

```bash
# SAST scanning
bandit -r . -ll
semgrep --config=p/security-audit

# Dependency check
safety check
pip-audit

# Unit tests
pytest tests/security/ -v
```

**Milestone:** ✓ Application hardening basado completado

---

## SEMANA 3: INFRASTRUCTURE SETUP

### 3.1 Docker Image Hardening

**Crear Dockerfile.secure** (ya creado)

**Build y test:**
```bash
docker build -f Dockerfile.secure -t yukyu-app:latest .

# Verificar que corre como non-root
docker run --rm yukyu-app:latest id
# Output debe ser: uid=1000(appuser)

# Scan image
docker scan yukyu-app:latest
trivy image yukyu-app:latest
```

### 3.2 PostgreSQL Setup

**Crear scripts/db-init.sql:**

```sql
-- Crear usuario app
CREATE USER yukyu_app WITH PASSWORD 'strong-password';

-- Crear database
CREATE DATABASE yukyu_production OWNER yukyu_app;

-- Habilitar extensiones de seguridad
\c yukyu_production
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Crear schema
CREATE SCHEMA IF NOT EXISTS public AUTHORIZATION yukyu_app;

-- Permisos mínimos
GRANT CONNECT ON DATABASE yukyu_production TO yukyu_app;
GRANT USAGE ON SCHEMA public TO yukyu_app;
GRANT CREATE ON SCHEMA public TO yukyu_app;

-- Encryption para PII (ejemplo)
CREATE OR REPLACE FUNCTION encrypt_pii(text)
RETURNS bytea AS $$
    SELECT pgp_sym_encrypt($1, current_setting('app.encryption_key'))
$$ LANGUAGE SQL;
```

### 3.3 Docker Compose Setup

**Crear docker-compose.secure.yml** (ya creado)

**Validar configuración:**
```bash
docker-compose -f docker-compose.secure.yml config

# Verificar volúmenes
docker-compose -f docker-compose.secure.yml images

# Pre-flight checks
docker-compose -f docker-compose.secure.yml --env-file .env.production config | grep -i password
# Output: must be empty!
```

### 3.4 Nginx Reverse Proxy

**Crear nginx/nginx.conf** (ya creado)

**Generar certificados SSL:**

```bash
# Desarrollo (self-signed)
mkcert -install
mkcert -cert-file nginx/ssl/cert.pem -key-file nginx/ssl/key.pem localhost 127.0.0.1

# Producción (Let's Encrypt)
certbot certonly --standalone \
  -d yukyu-data.example.com \
  --email admin@example.com \
  --agree-tos

# Copiar certs
cp /etc/letsencrypt/live/yukyu-data.example.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/yukyu-data.example.com/privkey.pem nginx/ssl/key.pem

# DH parameters para PFS
openssl dhparam -out nginx/ssl/dhparam.pem 2048
```

### 3.5 Testing Infrastructure

```bash
# Levantar stack local
docker-compose -f docker-compose.secure.yml up -d

# Verificar servicios
docker-compose -f docker-compose.secure.yml ps

# Health checks
curl -k https://localhost/health
curl http://localhost:9090/targets  # Prometheus

# Verificar logs
docker-compose -f docker-compose.secure.yml logs -f app
```

**Milestone:** ✓ Infrastructure lista en local

---

## SEMANA 4: CI/CD PIPELINE

### 4.1 GitHub Actions Setup

**Crear .github/workflows/secure-deployment.yml** (ya creado)

**Agregar GitHub Secrets:**
```bash
# En https://github.com/your-org/yukyu-app/settings/secrets

REGISTRY_USERNAME=<github-username>
REGISTRY_PASSWORD=<github-token>
DOCKER_BUILDKIT=1

ARGOCD_SERVER=<argocd-server-url>
ARGOCD_AUTH_TOKEN=<argocd-token>

SLACK_WEBHOOK_URL=<slack-webhook>
GITGUARDIAN_API_KEY=<gitguardian-token>

AWS_ACCESS_KEY_ID=<aws-key>
AWS_SECRET_ACCESS_KEY=<aws-secret>
```

### 4.2 Pre-commit Hooks

**Crear .pre-commit-config.yaml:**

```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-ll]

  - repo: https://github.com/returntocorp/semgrep
    rev: 1.42.0
    hooks:
      - id: semgrep
        args: [--config=p/security-audit]

  - repo: https://github.com/PyCQA/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
      - id: check-case-conflict
      - id: check-merge-conflict
      - id: detect-private-key
      - id: trailing-whitespace
      - id: end-of-file-fixer
```

### 4.3 Testing CI/CD Workflow

```bash
# Triggear workflow
git add .github/workflows/secure-deployment.yml
git commit -m "ci: add secure deployment pipeline"
git push origin feat/security-hardening

# Monitorear en GitHub Actions
# https://github.com/your-org/yukyu-app/actions

# Verificar que todos los checks pasan
# - SAST
# - Dependency scanning
# - Container scanning
# - Security tests
```

**Milestone:** ✓ CI/CD pipeline operacional

---

## SEMANA 5: MONITORING & COMPLIANCE

### 5.1 Prometheus Setup

**Crear monitoring/prometheus.yml** (ya creado)

**Crear rules:**
```bash
mkdir -p monitoring/rules
# monitoring/alerts.yml ya creado
```

### 5.2 Grafana Dashboards

**Crear dashboards JSON:**
```bash
# Crear dashboards en https://grafana.example.com/dashboards
# - Application Health
# - Security Events
# - Infrastructure Metrics
# - Deployment Status

# Exportar como JSON a grafana/dashboards/
```

### 5.3 Elasticsearch & Kibana

**Setup logs:**
```bash
# En docker-compose, Elasticsearch y Kibana ya están configurados

# Crear index pattern en Kibana
# http://localhost:5601/app/dev_tools#/console

PUT _index_template/yukyu
{
  "index_patterns": ["yukyu-logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1
    },
    "mappings": {
      "properties": {
        "timestamp": {"type": "date"},
        "severity": {"type": "keyword"},
        "event_type": {"type": "keyword"},
        "user_id": {"type": "keyword"},
        "message": {"type": "text"}
      }
    }
  }
}
```

### 5.4 Compliance Configuration

**GDPR Compliance:**
```python
# scripts/compliance.py
from datetime import datetime, timedelta
from database import db

def generate_gdpr_report(employee_id: str):
    """Generar SAR (Subject Access Request)"""

    # Obtener todos los datos
    employee = db.get_employee(employee_id)
    access_logs = db.get_audit_logs(employee_id)

    report = {
        "employee_id": employee_id,
        "personal_data": employee,
        "access_history": access_logs,
        "generated_at": datetime.utcnow().isoformat(),
    }

    return report

def delete_employee_data(employee_id: str):
    """Ejercer derecho al olvido"""

    # Soft delete (para auditoría)
    db.soft_delete_employee(employee_id)

    # Log audit
    log_event(f"Employee {employee_id} data deleted (GDPR)")
```

### 5.5 Testing Compliance

```bash
# Verificar GDPR endpoints
curl -X GET http://localhost:8000/api/v1/gdpr/data \
  -H "Authorization: Bearer <token>" \
  -H "X-Employee-ID: <employee_id>"

# Exportar datos
curl -X GET http://localhost:8000/api/v1/gdpr/export \
  -H "Authorization: Bearer <token>" > employee_data.json

# Solicitar eliminación
curl -X POST http://localhost:8000/api/v1/gdpr/delete \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"reason": "employee left company"}'
```

**Milestone:** ✓ Monitoring y compliance operacional

---

## SEMANA 6: TESTING & GO-LIVE

### 6.1 Security Testing

```bash
# Penetration testing (local)
# Tools: OWASP ZAP, Burp Suite Community

# OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://app:8000/

# Manual testing
# - SQL Injection: ' OR '1'='1
# - XSS: <script>alert('xss')</script>
# - CSRF: Verificar tokens CSRF
# - Authentication bypass
```

### 6.2 Load Testing

```bash
# Instalar k6
brew install k6

# Crear test script
cat > tests/load.js << 'EOF'
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 100,        // 100 usuarios virtuales
  duration: '30s', // 30 segundos
};

export default function() {
  let res = http.get('http://localhost:8000/api/v1/employees');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
EOF

# Ejecutar test
k6 run tests/load.js
```

### 6.3 Backup & Disaster Recovery Testing

```bash
# Test backup
docker-compose exec db pg_dump -U yukyu_app -d yukyu_production > /tmp/backup.sql

# Test restore
# 1. Stop app
# 2. Restore from backup
# 3. Verify data integrity
# 4. Start app
# 5. Run smoke tests
```

### 6.4 Failover Testing

```bash
# En producción con replicas:
# 1. Desconectar primary database
# 2. Verificar que app falla over a replica
# 3. Verificar que aplicación sigue funcionando
# 4. Verificar que datos están sincronizados
# 5. Reconectar primary
```

### 6.5 Deployment Rehearsal

```bash
# Ejecutar deployment script en staging
./scripts/deploy.sh staging v1.0.0

# Verificar todos los checks
# - Health checks OK
# - Smoke tests OK
# - Logs limpios
# - Metrics esperados

# Si todo OK, proceder a producción
./scripts/deploy.sh production v1.0.0
```

### 6.6 Documentation & Training

```bash
# Crear runbooks para operaciones
# - Deployment procedure
# - Rollback procedure
# - Incident response
# - Backup & recovery
# - Security incident handling

# Capacitar al equipo
# - Security best practices
# - Incident response
# - Log analysis
# - Monitoring interpretation
```

**Milestone:** ✓ Sistema ready para producción

---

## CHECKLIST PRE-DEPLOYMENT

### Funcional
- [ ] Todos los endpoints trabajando
- [ ] Database migrations pasadas
- [ ] API documentation actualizada
- [ ] No broken links en docs

### Security
- [ ] No secrets en git history
- [ ] SAST checks passing
- [ ] Dependency scanning clean
- [ ] Container image scan clean
- [ ] Security headers habilitados
- [ ] HTTPS/TLS configurado
- [ ] Rate limiting activo
- [ ] CORS configurado correctamente
- [ ] Input validation implementado
- [ ] SQL injection prevención

### Infrastructure
- [ ] Docker image builds successfully
- [ ] Docker Compose levanta todos los servicios
- [ ] Health checks configurados y funcionando
- [ ] Resource limits definidos
- [ ] Network policies configuradas
- [ ] Backups funcionando
- [ ] Reverse proxy TLS terminada
- [ ] Database encrypted at rest

### Monitoring & Logging
- [ ] Prometheus metrics exposed
- [ ] Elasticsearch recibiendo logs
- [ ] Grafana dashboards setup
- [ ] Alert rules configuradas
- [ ] Audit logging enabled
- [ ] Security event logging enabled

### Compliance
- [ ] GDPR endpoints implemented
- [ ] Data retention policies configured
- [ ] LGPD compliance checklist passed
- [ ] Security training completed
- [ ] Incident response plan documented
- [ ] Privacy policy updated
- [ ] Legal review completed

### Operations
- [ ] Runbooks documented
- [ ] Team training completed
- [ ] On-call rotation established
- [ ] Escalation procedures defined
- [ ] Communication channels ready
- [ ] Incident post-mortem template ready

---

## POST-DEPLOYMENT MONITORING

### Primeras 24 horas
- Monitorear error rates
- Verificar performance metrics
- Revisar security logs
- Confirmar backups running
- Check database replication lag

### Primera semana
- Daily security log review
- Performance baseline establishment
- Capacity planning review
- Team feedback collection
- Documentation updates

### Primeros 30 días
- Full security audit
- Performance optimization
- Vulnerability reassessment
- Compliance audit
- Incident response drills

---

## PRÓXIMOS PASOS POST-DEPLOYMENT

1. **Hardening Avanzado:**
   - Web Application Firewall (WAF)
   - DDoS protection
   - Advanced threat detection

2. **Escalabilidad:**
   - Kubernetes migration
   - Auto-scaling policies
   - Global distribution

3. **Compliance:**
   - SOC 2 certification
   - Penetration testing (tercero)
   - Security certification

4. **Modernización:**
   - Zero-trust security model
   - Service mesh (Istio)
   - Advanced observability

---

## SOPORTE Y REFERENCIAS

**En caso de problemas:**
1. Revisar logs: `docker-compose logs -f service_name`
2. Verificar health checks: `/health` endpoint
3. Contactar al equipo de seguridad
4. Crear issue en GitHub

**Documentación:**
- SEGURIDAD_DEPLOYMENT.md - Estrategia general
- Este archivo - Implementación paso a paso
- Dockerfile.secure - Hardened Docker image
- docker-compose.secure.yml - Stack de servicios
- .github/workflows/secure-deployment.yml - CI/CD pipeline

**Contactos:**
- Security Team: security@example.com
- DevOps Team: devops@example.com
- On-call: [Slack channel]
