# config.security.py
# Configuración centralizada de seguridad para YuKyuDATA

from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Tuple, ClassVar
import os
from datetime import timedelta

class SecuritySettings(BaseSettings):
    """
    Configuración de seguridad
    Las variables se cargan de environment variables con prefijo YUKYU_
    """

    # ============================================
    # DATABASE SECURITY
    # ============================================
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./yukyu.db"
    )

    # Encryption para PII en base de datos
    database_encryption_key: Optional[str] = os.getenv("DATABASE_ENCRYPTION_KEY")
    database_pool_size: int = 5
    database_pool_max_overflow: int = 10

    # ============================================
    # JWT & AUTHENTICATION
    # ============================================
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "change-me-in-production"
    )

    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15  # Access token: 15 minutos (v5.17)
    jwt_expiration_hours: int = 24    # Legacy - deprecated, use jwt_expiration_minutes
    jwt_refresh_expiration_days: int = 7  # Refresh token: 7 dias (v5.17)

    # MFA Settings
    mfa_enabled: bool = os.getenv("MFA_ENABLED", "false").lower() == "true"
    mfa_issuer: str = "YuKyuDATA"
    totp_window_size: int = 1  # Tolerancia de ventanas TOTP

    # ============================================
    # API SECURITY
    # ============================================
    api_key: Optional[str] = os.getenv("API_KEY")
    api_key_rotation_days: int = 90

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Rate limits por endpoint
    rate_limits: ClassVar[Dict[str, Tuple[str, str]]] = {
        "login": ("5/minute", "Prevenir brute force"),
        "mfa_verify": ("10/minute", "MFA attempts"),
        "upload": ("10/hour", "File uploads"),
        "export": ("20/hour", "Data exports"),
        "sync": ("5/hour", "Sync operations"),
        "get_employees": ("100/minute", "API read"),
        "delete": ("1/hour", "Destructive operations"),
    }

    # ============================================
    # CORS & HTTP
    # ============================================
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # Parse from env if provided
    def __init__(self, **data):
        super().__init__(**data)
        if os.getenv("CORS_ORIGINS"):
            self.cors_origins = os.getenv("CORS_ORIGINS").split(",")

    # Allowed methods
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_credentials: bool = True
    cors_max_age: int = 3600

    # ============================================
    # ENCRYPTION
    # ============================================
    encryption_key: str = os.getenv(
        "ENCRYPTION_KEY",
        "0" * 64  # 32 bytes en hex
    )

    # Cipher to use for PII encryption
    encryption_cipher: str = "AES-256-GCM"

    # ============================================
    # SSL/TLS
    # ============================================
    ssl_enabled: bool = not os.getenv("DEBUG", "false").lower() == "true"
    ssl_certfile: Optional[str] = os.getenv("SSL_CERT_FILE")
    ssl_keyfile: Optional[str] = os.getenv("SSL_KEY_FILE")

    # Cipher suites (en orden de preferencia)
    tls_cipher_suites: List[str] = [
        "TLS_AES_256_GCM_SHA384",      # TLS 1.3
        "TLS_AES_128_GCM_SHA256",      # TLS 1.3
        "TLS_CHACHA20_POLY1305_SHA256",  # TLS 1.3
        "ECDHE-RSA-AES256-GCM-SHA384",  # TLS 1.2
        "ECDHE-RSA-AES128-GCM-SHA256",  # TLS 1.2
    ]

    tls_min_version: str = "TLSv1.2"  # Never lower

    # ============================================
    # SECURITY HEADERS
    # ============================================
    security_headers: ClassVar[Dict[str, str]] = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": (
            "default-src 'self'; "
            # Allow CDN scripts for ApexCharts, Chart.js, GSAP, Flatpickr
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            # Styles need inline for dynamic theming + CDN for Animate.css, Flatpickr
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "img-src 'self' data: blob:; "
            # Allow Google Fonts
            "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=()"
        ),
    }

    # ============================================
    # LOGGING & AUDITING
    # ============================================
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "json"  # JSON para parsing fácil

    # Logging sensitive
    log_sql_queries: bool = False  # NEVER en producción
    log_request_headers: bool = False  # Contiene credenciales
    log_response_body: bool = False  # Contiene PII

    # Sanitización de logs
    sensitive_fields: List[str] = [
        "password",
        "token",
        "secret",
        "api_key",
        "credit_card",
        "ssn",
        "email",
        "phone",
    ]

    # ============================================
    # COMPLIANCE
    # ============================================
    # GDPR
    gdpr_enabled: bool = True
    gdpr_data_retention_days: int = 90 * 365  # 90 años
    gdpr_audit_retention_days: int = 3 * 365  # 3 años

    # LGPD (Brasil)
    lgpd_enabled: bool = True

    # Datos de empleados
    pii_encryption_required: bool = True
    pii_fields: List[str] = [
        "name",
        "email",
        "phone",
        "birth_date",
        "employee_num",
        "kana",
        "nationality",
    ]

    # ============================================
    # MONITORING & ALERTING
    # ============================================
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN")
    sentry_environment: str = os.getenv("ENVIRONMENT", "development")

    # Elasticsearch
    elasticsearch_enabled: bool = True
    elasticsearch_host: str = os.getenv("ELASTICSEARCH_HOST", "localhost:9200")
    elasticsearch_user: str = os.getenv("ELASTICSEARCH_USER", "elastic")
    elasticsearch_password: str = os.getenv("ELASTICSEARCH_PASSWORD", "")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")

    # ============================================
    # SECRETS MANAGER
    # ============================================
    # AWS Secrets Manager
    aws_secrets_manager_enabled: bool = os.getenv("AWS_SECRETS_MANAGER_ENABLED", "false").lower() == "true"
    aws_region: str = os.getenv("AWS_REGION", "ap-northeast-1")
    aws_secrets_prefix: str = "yukyu"

    # HashiCorp Vault
    vault_enabled: bool = os.getenv("VAULT_ENABLED", "false").lower() == "true"
    vault_addr: Optional[str] = os.getenv("VAULT_ADDR")
    vault_token: Optional[str] = os.getenv("VAULT_TOKEN")
    vault_path: str = "secret/data/yukyu"

    # ============================================
    # DEBUGGING & DEVELOPMENT
    # ============================================
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    testing: bool = os.getenv("TESTING", "false").lower() == "true"

    # IMPORTANT: Never set these to True in production!
    allow_cors_all: bool = False
    allow_http_in_production: bool = False
    expose_database_errors: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class APISecurityConfig:
    """Configuración de seguridad de API endpoints"""

    # Versioning
    API_VERSION = "1.0.0"
    API_ENDPOINTS = {
        # Public endpoints (sin autenticación requerida)
        "public": [
            "/health",
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ],

        # Protected endpoints (requieren API key)
        "protected": [
            "/api/v1/employees",
            "/api/v1/genzai",
            "/api/v1/ukeoi",
        ],

        # Admin only endpoints
        "admin": [
            "/api/v1/sync",
            "/api/v1/sync-genzai",
            "/api/v1/sync-ukeoi",
            "/api/v1/upload",
            "/api/v1/reset",
            "/api/v1/reset-genzai",
            "/api/v1/reset-ukeoi",
            "/api/v1/admin/users",
            "/api/v1/admin/logs",
            "/api/v1/admin/settings",
        ],
    }

    # Response formats
    RESPONSE_HEADERS = {
        "X-API-Version": API_VERSION,
        "X-Content-Type-Options": "application/json",
    }

    # Error responses (sin PII)
    ERROR_RESPONSES = {
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid credentials",
                        "error_code": "UNAUTHORIZED",
                    }
                }
            },
        },
        403: {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient permissions",
                        "error_code": "FORBIDDEN",
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Too many requests",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "retry_after": 60,
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error",
                        "error_code": "INTERNAL_ERROR",
                        "request_id": "uuid",
                    }
                }
            },
        },
    }


# Instanciar configuración global
settings = SecuritySettings()
api_config = APISecurityConfig()


def validate_security_config() -> List[str]:
    """Validar que la configuración de seguridad es correcta"""

    issues = []

    # En producción
    if not settings.debug:
        if settings.jwt_secret_key == "change-me-in-production":
            issues.append("JWT_SECRET_KEY must be changed in production")

        if not settings.ssl_enabled:
            issues.append("SSL must be enabled in production")

        if "*" in settings.cors_origins:
            issues.append("CORS origins cannot be '*' in production")

        if settings.database_url == "sqlite:///./yukyu.db":
            issues.append("Must use PostgreSQL in production, not SQLite")

    return issues


# Validar al iniciar
_config_issues = validate_security_config()
if _config_issues:
    import sys
    print("SECURITY CONFIGURATION ISSUES:")
    for issue in _config_issues:
        print(f"  - {issue}")

    # Solo salir en producción (no debug y no testing)
    if not settings.debug and not settings.testing:
        # En desarrollo local, solo mostrar warning
        if os.getenv("FORCE_EXIT_ON_SECURITY_ISSUES", "false").lower() == "true":
            sys.exit(1)
