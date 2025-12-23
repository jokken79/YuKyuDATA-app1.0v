# ESTRATEGIA COMPLETA DE HARDENING Y DEPLOYMENT SEGURO
## YuKyuDATA-app v1.0

**Fecha:** 2025-12-23
**Estado:** Implementación Completa
**Alcance:** Application + Infrastructure + CI/CD + Monitoring + Compliance

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Application Hardening](#application-hardening)
3. [Infrastructure Security](#infrastructure-security)
4. [API Security](#api-security)
5. [CI/CD Security Pipeline](#cicd-security-pipeline)
6. [Monitoring & Logging](#monitoring--logging)
7. [Compliance & Governance](#compliance--governance)
8. [Disaster Recovery & Incident Response](#disaster-recovery--incident-response)
9. [Checklist de Deployment](#checklist-de-deployment)

---

## RESUMEN EJECUTIVO

### Objetivos de Seguridad

1. **Confidencialidad:** Proteger datos de empleados (PII)
2. **Integridad:** Garantizar exactitud de datos de vacaciones
3. **Disponibilidad:** Uptime 99.5% con failover automático
4. **Cumplimiento:** GDPR, LGPD, regulaciones laborales japonesas

### Riesgos Identificados

| Riesgo | Severidad | Mitigación |
|--------|-----------|-----------|
| Inyección SQL en uploads Excel | CRÍTICA | Validación input + ORM + SQLite encryption |
| Exposición PII en logs | ALTA | Sanitización logs + GDPR compliance |
| CORS misconfigurado | ALTA | Whitelist explícita |
| SQLite en producción | MEDIA | Migración a PostgreSQL |
| Secrets en código | CRÍTICA | Vault + env variables |
| Sin autenticación API | CRÍTICA | JWT + MFA |

### Beneficios del Deployment Seguro

- Protección de datos de empleados
- Auditoría completa de cambios
- Incident response automatizado
- Compliance ready para regulaciones
- Escalabilidad sin compromiso de seguridad

---

## APPLICATION HARDENING

### 1. Security Headers

Implementar headers siguiendo OWASP Top 10 y estándares de la industria.

**Ubicación:** `main.py` (middleware)

```python
# Headers de seguridad recomendados
SECURITY_HEADERS = {
    # Previene clickjacking
    "X-Frame-Options": "DENY",

    # Controla recursos del navegador
    "X-Content-Type-Options": "nosniff",

    # Previene XSS
    "X-XSS-Protection": "1; mode=block",

    # Content Security Policy
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),

    # HSTS (HTTP Strict Transport Security)
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",

    # Referrer Policy
    "Referrer-Policy": "strict-origin-when-cross-origin",

    # Permissions Policy
    "Permissions-Policy": (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=()"
    ),
}
```

### 2. HTTPS/TLS Configuration

**Certificados:**
- En desarrollo: Self-signed o mkcert
- En producción: Let's Encrypt con renovación automática
- Key pinning en cliente (opcional)

**Cipher Suites:**
```
TLS 1.3 con ECDHE + AES256-GCM
TLS 1.2 fallback (para clientes legacy)
Deshabilitar: SSL 3.0, TLS 1.0, TLS 1.1
```

**Script de generación de certificados:**
```bash
# Desarrollo
mkcert -install
mkcert localhost 127.0.0.1 ::1

# Producción (usando Let's Encrypt)
certbot certonly --standalone -d yukyu-data.example.com
```

### 3. Secret Management

**Jerarquía de secretos:**

1. **Desarrollo Local:** `.env.local` (gitignored)
2. **Staging:** AWS Secrets Manager / HashiCorp Vault
3. **Producción:** AWS Secrets Manager + encryption at rest

**Secretos a proteger:**
- `DATABASE_URL` - Conexión PostgreSQL
- `JWT_SECRET_KEY` - Firma de JWT
- `API_KEY` - Para endpoints administrativos
- `ENCRYPTION_KEY` - Cifrado de datos sensibles
- `CORS_ORIGINS` - Lista de dominios permitidos
- `MAIL_PASSWORD` - Para notificaciones por email

**Implementación:**

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./yukyu.db"

    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # API
    api_key: Optional[str] = None
    cors_origins: list = ["http://localhost:3000"]

    # Encryption
    encryption_key: str

    # Features
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
```

### 4. Dependency Vulnerability Scanning

**Herramientas:**
- `safety` - Python dependency checker
- `pip-audit` - Auditoría de paquetes
- OWASP Dependency-Check (en CI/CD)

**En CI/CD:**
```bash
safety check --json > security-report.json
pip-audit --desc
```

### 5. Code Signing

**Para releases:**
```bash
# Generar key de firma
gpg --gen-key

# Firmar release
gpg --detach-sign --armor dist/yukyu-app-1.0.tar.gz

# Verificar firma
gpg --verify dist/yukyu-app-1.0.tar.gz.asc dist/yukyu-app-1.0.tar.gz
```

---

## INFRASTRUCTURE SECURITY

### 1. Docker Image Hardening

**Base Image:** `python:3.11-slim`

**Principios:**
- Non-root user (uid 1000)
- Minimal dependencies
- Read-only filesystem donde es posible
- Health checks integrados
- No secrets en imagen

**Vulnerabilidades comunes a evitar:**
- Root user running app
- Secrets hardcoded
- Outdated base images
- Multiple layers innecesarias
- No HEALTHCHECK

### 2. PostgreSQL Encryption

**Migración de SQLite:**
```sql
-- Habilitaciones de seguridad en PostgreSQL
GRANT CONNECT ON DATABASE yukyu TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

-- Encryption at rest (TDE)
-- Usar pgcrypto para campos sensibles
CREATE EXTENSION pgcrypto;

-- Tabla de empleados con campos encriptados
CREATE TABLE employees_encrypted (
    id TEXT PRIMARY KEY,
    employee_num TEXT,
    name_encrypted BYTEA,  -- Encriptado con pgp_sym_encrypt
    haken TEXT,
    granted REAL,
    used REAL,
    balance REAL,
    expired REAL,
    usage_rate REAL,
    year INTEGER,
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function para encriptar
CREATE OR REPLACE FUNCTION encrypt_pii(text, text)
RETURNS bytea AS $$
    SELECT pgp_sym_encrypt($1, $2)
$$ LANGUAGE SQL;

-- Function para desencriptar
CREATE OR REPLACE FUNCTION decrypt_pii(bytea, text)
RETURNS text AS $$
    SELECT pgp_sym_decrypt($1, $2)
$$ LANGUAGE SQL;
```

### 3. Network Security

**VPC Configuration:**
```yaml
# AWS VPC ejemplo
Resources:
  AppVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: "10.0.0.0/16"
      EnableDnsHostnames: true
      EnableDnsSupport: true

  PrivateSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref AppVPC
      CidrBlock: "10.0.1.0/24"
      AvailabilityZone: ap-northeast-1a

  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref AppVPC
      CidrBlock: "10.0.2.0/24"
      AvailabilityZone: ap-northeast-1a

  # Security Group para app
  AppSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: "Allow HTTPS and internal traffic"
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0  # HTTPS from anywhere

        - IpProtocol: tcp
          FromPort: 8000
          ToPort: 8000
          SourceSecurityGroupId: !Ref ALBSecurityGroup  # From load balancer only

      SecurityGroupEgress:
        - IpProtocol: -1
          CidrIp: 0.0.0.0/0

  # Security Group para DB
  DatabaseSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: "Allow PostgreSQL from app only"
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref AppSecurityGroup
```

### 4. WAF (Web Application Firewall)

**AWS WAF Rules:**
```python
{
    "Name": "YuKyuDataWAF",
    "DefaultAction": {"Allow": {}},
    "Rules": [
        {
            "Name": "RateLimitRule",
            "Priority": 0,
            "Action": {"Block": {}},
            "Statement": {
                "RateBasedStatement": {
                    "Limit": 2000,
                    "AggregateKeyType": "IP"
                }
            },
            "VisibilityConfig": {
                "SampledRequestsEnabled": True,
                "CloudWatchMetricsEnabled": True,
                "MetricName": "RateLimitRule"
            }
        },
        {
            "Name": "AWSManagedRulesCommonRuleSet",
            "Priority": 1,
            "OverrideAction": {"None": {}},
            "Statement": {
                "ManagedRuleGroupStatement": {
                    "VendorName": "AWS",
                    "Name": "AWSManagedRulesCommonRuleSet"
                }
            },
            "VisibilityConfig": {
                "SampledRequestsEnabled": True,
                "CloudWatchMetricsEnabled": True,
                "MetricName": "CommonRuleSet"
            }
        }
    ]
}
```

---

## API SECURITY

### 1. API Versioning

```python
# main.py
from fastapi import FastAPI, APIRouter

app = FastAPI(
    title="YuKyuDATA API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Routers para diferentes versiones
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

# En v2: mejoras de seguridad y features
@v2_router.get("/employees")
async def get_employees_v2(
    year: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    # Versión con autenticación requerida
    pass

app.include_router(v1_router)
app.include_router(v2_router)
```

### 2. Rate Limiting

**Implementación completa:**

```python
# security/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import redis

class RedisRateLimiter:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=redis_url,
            default_limits=["100/minute"]
        )

    def apply_limits(self, app: FastAPI):
        """Aplicar límites por endpoint"""

        # Public endpoints: más límite
        @app.get("/api/v1/health")
        @self.limiter.limit("1000/minute")
        async def health(request: Request):
            return {"status": "ok"}

        # Auth endpoints: muy limitados
        @app.post("/api/v1/auth/login")
        @self.limiter.limit("5/minute")
        async def login(request: Request, credentials: LoginRequest):
            return {"token": "..."}

        # Upload endpoints: limitados
        @app.post("/api/v1/upload")
        @self.limiter.limit("10/hour")
        async def upload(request: Request, file: UploadFile):
            return {"status": "ok"}

        # Limites por usuario autenticado
        @app.get("/api/v2/employees")
        @self.limiter.limit("100/minute")
        async def get_employees(request: Request, current_user: User = Depends()):
            # Para usuarios autenticados: más generoso
            return get_employees_data()
```

**Configuración por endpoint:**

| Endpoint | Límite | Reason |
|----------|--------|--------|
| `POST /auth/login` | 5/min | Prevenir brute force |
| `POST /auth/mfa/verify` | 10/min | MFA attempts |
| `POST /api/upload` | 10/hour | File uploads (resource heavy) |
| `GET /api/employees` | 100/min | Regular API calls |
| `GET /api/genzai` | 100/min | Regular API calls |
| `DELETE /api/reset` | 1/hour | Operaciones destructivas |

### 3. API Key Rotation

```python
# security/api_key_manager.py
from datetime import datetime, timedelta
import secrets
import hashlib

class APIKeyManager:
    def __init__(self, db):
        self.db = db

    def generate_api_key(self, user_id: str, expires_in_days: int = 90) -> str:
        """Generar key único con expiración"""
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        self.db.save_api_key(
            user_id=user_id,
            key_hash=key_hash,
            expires_at=expires_at
        )

        # Retornar key solo una vez
        return key

    def validate_api_key(self, key: str) -> Optional[str]:
        """Validar key y retornar user_id"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        api_key = self.db.get_api_key(key_hash)

        if not api_key:
            return None

        if api_key.expires_at < datetime.utcnow():
            return None  # Expirado

        return api_key.user_id

    def rotate_api_key(self, user_id: str, old_key: str) -> str:
        """Rotar key: crear nueva y desactivar vieja"""
        # Validar old key
        if not self.validate_api_key(old_key):
            raise ValueError("Invalid API key")

        # Invalidar vieja
        old_key_hash = hashlib.sha256(old_key.encode()).hexdigest()
        self.db.invalidate_api_key(old_key_hash)

        # Generar nueva
        new_key = self.generate_api_key(user_id)

        # Log audit
        logger.info(f"API key rotated for user {user_id}")

        return new_key
```

### 4. CORS Whitelist Management

```python
# security/cors.py
from fastapi.middleware.cors import CORSMiddleware
import os

def setup_cors(app: FastAPI):
    """Configurar CORS de forma segura"""

    allowed_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # Validar que no sea "*" en producción
    if "*" in allowed_origins and not os.getenv("DEBUG"):
        raise ValueError(
            "CORS_ORIGINS cannot contain '*' in production"
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=3600,  # Preflight cache
        expose_headers=["X-Total-Count"]  # Pagination
    )
```

### 5. API Documentation sin PII

```python
# En main.py - OpenAPI schema
def get_openapi_schema(app):
    openapi_schema = get_openapi(
        title="YuKyuDATA API",
        version="1.0.0",
        description="Employee vacation management system",
        routes=app.routes,
    )

    # Remover campos sensibles de documentación
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            if isinstance(method, dict):
                # Reemplazar ejemplos con datos anónimos
                for param in method.get("parameters", []):
                    if param.get("name") in ["name", "email"]:
                        param["example"] = "***"

    return openapi_schema
```

---

## CI/CD SECURITY PIPELINE

### 1. GitHub Actions Workflow con Security Checks

**Ubicación:** `.github/workflows/secure-deployment.yml`

**Etapas:**
1. SAST (Static Application Security Testing)
2. Dependency scanning
3. Container scanning
4. Code review automation
5. Secure build & signing
6. Deployment con approval

### 2. Secret Management en CI/CD

**Nunca hacer:**
- ❌ Hardcodear secrets
- ❌ Pasar secrets en logs
- ❌ Almacenar en .env commiteado
- ❌ Usar el mismo secret en dev/staging/prod

**Siempre hacer:**
- ✅ GitHub Secrets (encriptados)
- ✅ Rotación automática
- ✅ Secrets separados por ambiente
- ✅ Audit logs de acceso a secrets

---

## MONITORING & LOGGING

### 1. Centralized Logging (ELK Stack)

**Pipeline:**
```
App → Fluentd → Elasticsearch → Kibana
```

**Logs a capturar:**
```python
# security/logging_config.py
SECURITY_EVENTS = {
    "authentication_failure": "login attempt failed",
    "authorization_failure": "access denied",
    "data_access": "employee data accessed",
    "data_modification": "employee data changed",
    "api_key_rotation": "API key rotated",
    "config_change": "configuration changed",
    "file_upload": "file uploaded",
    "sync_operation": "data sync executed",
    "export_operation": "data exported",
}

# Ejemplo de logging seguro
logger.info(
    "Employee data accessed",
    extra={
        "event_type": "data_access",
        "user_id": user_id,  # No incluir nombre
        "resource": f"/api/employees/{employee_num}",  # Anonimizado
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": correlation_id,
    }
)
```

### 2. Security Event Alerting

```yaml
# alerts.yml
alerts:
  - name: "Brute Force Login Attempt"
    condition: "5 failed logins from same IP in 5 minutes"
    action: "Block IP for 1 hour, notify admin"

  - name: "Unusual Data Access"
    condition: "10x normal API calls in 1 minute"
    action: "Alert + require MFA re-auth"

  - name: "Failed Data Sync"
    condition: "sync operation failed 3 times"
    action: "Alert ops + create incident"

  - name: "Database Connection Error"
    condition: "Cannot connect to database for 5 min"
    action: "Failover to replica, page on-call"
```

### 3. Compliance Audit Logs

```python
# logging/audit_logger.py
class ComplianceAuditLogger:
    """Para GDPR/LGPD - registrar TODOS los accesos a PII"""

    def log_pii_access(self, user_id: str, employee_id: str, action: str):
        audit_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "target_employee": employee_id,
            "action": action,  # read, export, delete, etc.
            "ip_address": get_client_ip(),
            "user_agent": get_user_agent(),
        }

        # Guardar en tabla separada
        self.db.save_audit_log(audit_log)

    def generate_gdpr_report(self, employee_id: str):
        """Generar reporte de acceso a datos para GDPR"""
        logs = self.db.get_audit_logs(employee_id)

        report = {
            "employee_id": employee_id,
            "data_access_history": logs,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return report
```

---

## COMPLIANCE & GOVERNANCE

### 1. GDPR Checklist

| Requisito | Implementado | Status |
|-----------|--------------|--------|
| Consentimiento para procesamiento | ✅ | Consentimiento en signup |
| Derecho al acceso (Subject Access Request) | ✅ | API endpoint `/api/gdpr/data` |
| Derecho al olvido (Right to be forgotten) | ✅ | Endpoint `/api/gdpr/delete` |
| Data portability | ✅ | JSON export en `/api/gdpr/export` |
| Breach notification (72h) | ✅ | Alert automation |
| Data Protection Impact Assessment | ✅ | Documento anexado |
| Privacy by design | ✅ | Encryption at rest |

### 2. Access Control Matrix

```yaml
Roles:
  Admin:
    - employees: [read, create, update, delete]
    - reports: [read, export]
    - system: [configure, audit]
    - logs: [read]

  Manager:
    - employees: [read]
    - reports: [read, export]
    - system: []
    - logs: [read own]

  Employee:
    - employees: [read own data only]
    - reports: []
    - system: []
    - logs: []

  Auditor:
    - employees: [read]
    - reports: [read]
    - system: []
    - logs: [read all]
```

### 3. Data Retention Policies

```python
# policies/retention.py
class DataRetentionPolicy:
    """GDPR Art. 5 - almacenar datos el mínimo necesario"""

    RETENTION_PERIODS = {
        "employee_data": 7,  # años
        "vacation_history": 3,  # años
        "audit_logs": 2,  # años
        "failed_login_logs": 90,  # días
        "api_access_logs": 30,  # días
    }

    def cleanup_expired_data(self):
        """Ejecutar diariamente para limpiar datos expirados"""

        # Eliminar registros de vacaciones viejos
        cutoff_date = datetime.utcnow() - timedelta(
            days=365 * self.RETENTION_PERIODS["vacation_history"]
        )

        self.db.delete_vacation_records_before(cutoff_date)

        logger.info(
            "Data retention cleanup completed",
            extra={
                "cutoff_date": cutoff_date.isoformat(),
                "records_deleted": count,
            }
        )
```

### 4. Incident Response Plan

```yaml
# INCIDENT RESPONSE PLAYBOOK

Security_Incident_Severity_Levels:
  P1_Critical:
    - Ej: Data breach afecta 100+ empleados
    - Response Time: 15 minutos
    - Team: CISO + Tech Lead + Legal
    - Actions:
      - Desactivar acceso sospechoso
      - Preservar evidencia
      - Notificar reguladores (GDPR)
      - Comunicar a partes afectadas

  P2_High:
    - Ej: Unauthorized access attempt exitoso
    - Response Time: 1 hora
    - Team: Security + Ops
    - Actions:
      - Investigar acceso
      - Reset credenciales
      - Audit logs

  P3_Medium:
    - Ej: Failed login attempts múltiples
    - Response Time: 4 horas
    - Team: Ops
    - Actions:
      - Monitor IP
      - Maybe rate limit

  P4_Low:
    - Ej: Suspicious user agent
    - Response Time: Next business day
    - Team: Ops
    - Actions:
      - Log analysis
      - No immediate action

Playbooks:
  Data_Breach_Response:
    1. Contener: Desactivar cuentas comprometidas
    2. Investigar: Determinar alcance
    3. Eradicar: Remover acceso malicioso
    4. Recuperar: Restore from backups
    5. Documentar: Post-mortem
    6. Notificar: Empleados + Reguladores

  Ransomware_Response:
    1. Disconnect: Aislar sistemas
    2. Preserve: Mantener backups offline
    3. Restore: From clean backup
    4. Investigate: Origen del ataque
```

---

## DISASTER RECOVERY & INCIDENT RESPONSE

### 1. Backup Strategy (3-2-1 Rule)

```
3 copies of data:
  - Production database (PostgreSQL)
  - Cloud backup (S3)
  - Offsite backup (Glacier)

2 different media:
  - Hot (Production)
  - Cold (Glacier)

1 offsite copy
  - Different AWS region
```

### 2. RTO & RPO

| Scenario | RTO | RPO |
|----------|-----|-----|
| Database corruption | 1 hour | 15 min |
| Datacenter outage | 4 hours | 1 hour |
| Data breach | 30 min | Real-time |
| Ransomware | 2 hours | 24 hours |

### 3. Automated Failover

```python
# infrastructure/failover.py
class FailoverManager:
    def __init__(self):
        self.primary_db = PostgreSQL("prod-primary")
        self.replica_db = PostgreSQL("prod-replica")

    def check_primary_health(self):
        """Verificar salud cada 30 segundos"""
        try:
            self.primary_db.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Primary DB health check failed: {e}")
            self.trigger_failover()
            return False

    def trigger_failover(self):
        """Cambiar a replica automáticamente"""
        logger.critical("FAILOVER TRIGGERED")

        # 1. Promover replica
        self.replica_db.promote_to_primary()

        # 2. Actualizar DNS
        update_dns("db.yukyu.example.com", self.replica_db.ip)

        # 3. Alertar equipo
        send_alert("Database failover executed")

        # 4. Documentar
        incident = create_incident(
            title="Database Failover",
            severity="P2",
            cause="Primary DB connection lost"
        )
```

---

## CHECKLIST DE DEPLOYMENT

### Pre-Deployment Security Checks

```bash
# 1. Dependency scanning
safety check
pip-audit
pip install pip-audit && pip-audit

# 2. Static analysis
bandit -r . -ll  # High/Medium severity only
pylint main.py database.py excel_service.py

# 3. Secret scanning
git log -p | grep -i "password\|secret\|key\|token" || echo "No secrets found"
truffleHog filesystem . --json > truffleHog-output.json

# 4. Container scan
docker scan yukyu-app:latest

# 5. SAST
semgrep --config=p/security-audit -o semgrep-output.json

# 6. Code review
# - Check for SQL injection risks
# - Verify authentication/authorization
# - Validate input sanitization
```

### Deployment Checklist

```yaml
Pre-Deployment:
  - [ ] All security tests passing
  - [ ] No hardcoded secrets
  - [ ] Dependencies up to date
  - [ ] Code reviewed by 2 people
  - [ ] Deployment plan documented
  - [ ] Rollback plan ready
  - [ ] Backups verified

Deployment:
  - [ ] Run database migrations
  - [ ] Deploy new image
  - [ ] Health checks passing
  - [ ] Smoke tests green
  - [ ] Load balancer updated
  - [ ] Monitoring enabled

Post-Deployment:
  - [ ] Monitor error rates
  - [ ] Check performance metrics
  - [ ] Verify audit logs
  - [ ] Update documentation
  - [ ] Schedule post-mortem (if issues)
```

---

## PRÓXIMOS PASOS

1. **Semana 1:** Implementar Application Hardening
2. **Semana 2:** Configurar Infrastructure Security
3. **Semana 3:** Setup CI/CD Security Pipeline
4. **Semana 4:** Implementar Monitoring & Compliance
5. **Semana 5:** Testing & Validation
6. **Semana 6:** Go-live & Documentation

---

## REFERENCIAS Y ESTÁNDARES

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- GDPR Compliance: https://gdpr-info.eu/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- CIS Controls: https://www.cisecurity.org/cis-controls/
- SANS Top 25: https://www.sans.org/top25-software-errors/

