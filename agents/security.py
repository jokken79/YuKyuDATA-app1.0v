"""
Security Agent - Agente de Seguridad y Hardening
=================================================

Experto en seguridad de aplicaciones web:
- Detección de vulnerabilidades OWASP Top 10
- Análisis de configuración de seguridad
- Verificación de autenticación/autorización
- Detección de secretos expuestos
- Análisis de dependencias vulnerables
- Hardening de configuración
- Generación de reportes de seguridad
"""

import logging
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class VulnerabilitySeverity(Enum):
    """Severidad de vulnerabilidades (CVSS-like)."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VulnerabilityCategory(Enum):
    """Categorías OWASP Top 10 2021."""
    A01_BROKEN_ACCESS = "A01:2021-Broken Access Control"
    A02_CRYPTO_FAILURE = "A02:2021-Cryptographic Failures"
    A03_INJECTION = "A03:2021-Injection"
    A04_INSECURE_DESIGN = "A04:2021-Insecure Design"
    A05_MISCONFIG = "A05:2021-Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021-Vulnerable Components"
    A07_AUTH_FAILURE = "A07:2021-Auth Failures"
    A08_INTEGRITY_FAILURE = "A08:2021-Integrity Failures"
    A09_LOGGING_FAILURE = "A09:2021-Logging Failures"
    A10_SSRF = "A10:2021-SSRF"
    OTHER = "Other Security Issue"


@dataclass
class SecurityVulnerability:
    """Representa una vulnerabilidad de seguridad."""
    id: str
    category: VulnerabilityCategory
    severity: VulnerabilitySeverity
    title: str
    description: str
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    cwe_id: Optional[str]
    remediation: str
    references: List[str] = field(default_factory=list)
    false_positive_likelihood: str = "low"
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'category': self.category.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'code_snippet': self.code_snippet,
            'cwe_id': self.cwe_id,
            'remediation': self.remediation,
            'references': self.references
        }


@dataclass
class SecretFinding:
    """Secreto expuesto encontrado."""
    secret_type: str
    file_path: str
    line_number: int
    masked_value: str
    entropy: float
    is_high_risk: bool


@dataclass
class SecurityConfig:
    """Análisis de configuración de seguridad."""
    has_https: bool
    has_cors_config: bool
    cors_allows_all: bool
    has_csrf_protection: bool
    has_rate_limiting: bool
    has_security_headers: bool
    has_input_validation: bool
    has_output_encoding: bool
    has_auth_system: bool
    auth_uses_jwt: bool
    jwt_has_expiry: bool
    passwords_hashed: bool
    issues: List[str]


@dataclass
class SecurityAuditReport:
    """Reporte completo de auditoría de seguridad."""
    timestamp: str
    files_scanned: int
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    vulnerabilities: List[SecurityVulnerability]
    secrets_found: List[SecretFinding]
    security_config: SecurityConfig
    recommendations: List[str]
    security_score: float  # 0-100

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'files_scanned': self.files_scanned,
            'total_vulnerabilities': self.total_vulnerabilities,
            'by_severity': {
                'critical': self.critical_count,
                'high': self.high_count,
                'medium': self.medium_count,
                'low': self.low_count
            },
            'secrets_found': len(self.secrets_found),
            'security_score': self.security_score,
            'recommendations': self.recommendations
        }


class SecurityAgent:
    """
    Agente de Seguridad - Experto en Hardening

    Detecta y reporta vulnerabilidades de seguridad:

    Capacidades:
    - Escaneo OWASP Top 10
    - Detección de secretos expuestos
    - Análisis de SQL Injection
    - Análisis de XSS
    - Verificación de autenticación
    - Análisis de CORS
    - Detección de configuraciones inseguras
    - Hardening recommendations

    Ejemplo de uso:
    ```python
    security = SecurityAgent()

    # Auditoría completa
    report = security.audit_security()

    # Buscar secretos expuestos
    secrets = security.scan_for_secrets()

    # Analizar configuración
    config = security.analyze_security_config()

    # Verificar OWASP Top 10
    vulns = security.scan_owasp_top_10()
    ```
    """

    # Patrones de secretos
    SECRET_PATTERNS = {
        'api_key': [
            r'api[_-]?key\s*[=:]\s*["\']([^"\']{20,})["\']',
            r'apikey\s*[=:]\s*["\']([^"\']{20,})["\']',
        ],
        'password': [
            r'password\s*[=:]\s*["\']([^"\']+)["\']',
            r'passwd\s*[=:]\s*["\']([^"\']+)["\']',
            r'pwd\s*[=:]\s*["\']([^"\']+)["\']',
        ],
        'secret_key': [
            r'secret[_-]?key\s*[=:]\s*["\']([^"\']{16,})["\']',
            r'jwt[_-]?secret\s*[=:]\s*["\']([^"\']+)["\']',
        ],
        'token': [
            r'token\s*[=:]\s*["\']([^"\']{20,})["\']',
            r'bearer\s+([a-zA-Z0-9._-]{20,})',
        ],
        'aws_key': [
            r'AKIA[0-9A-Z]{16}',
            r'aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*["\']([^"\']+)["\']',
        ],
        'private_key': [
            r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----',
        ],
        'database_url': [
            r'(?:mysql|postgresql|mongodb|redis)://[^"\'\s]+',
        ]
    }

    # Patrones de inyección SQL
    SQL_INJECTION_PATTERNS = [
        (r'execute\s*\(\s*f["\']', "f-string en SQL"),
        (r'execute\s*\([^)]*\s*\+\s*', "concatenación en SQL"),
        (r'execute\s*\([^)]*%\s*\(', "formato % en SQL"),
        (r'execute\s*\([^)]*\.format\s*\(', ".format() en SQL"),
        (r'cursor\.execute\s*\(\s*["\'][^?%][^"\']*["\'\s]*\+', "cursor.execute con concatenación"),
    ]

    # Patrones XSS
    XSS_PATTERNS = [
        (r'innerHTML\s*=\s*[^"\']+(?:input|user|data|param)', "innerHTML con datos de usuario"),
        (r'document\.write\s*\([^)]*(?:input|user|data|param)', "document.write con datos de usuario"),
        (r'eval\s*\([^)]*(?:input|user|data|param)', "eval con datos de usuario"),
    ]

    def __init__(self, project_root: str = "."):
        """
        Inicializa el Agente de Seguridad.

        Args:
            project_root: Ruta raíz del proyecto
        """
        self.project_root = Path(project_root)
        self._vuln_counter = 0

    def _generate_vuln_id(self) -> str:
        """Genera un ID único para una vulnerabilidad."""
        self._vuln_counter += 1
        return f"SEC-{datetime.now().strftime('%Y%m%d')}-{self._vuln_counter:04d}"

    def _calculate_entropy(self, s: str) -> float:
        """Calcula la entropía de Shannon de un string."""
        if not s:
            return 0

        from collections import Counter
        import math

        freq = Counter(s)
        length = len(s)
        entropy = 0

        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)

        return entropy

    # ========================================
    # ESCANEO DE SECRETOS
    # ========================================

    def scan_for_secrets(self) -> List[SecretFinding]:
        """
        Escanea el proyecto en busca de secretos expuestos.

        Returns:
            Lista de secretos encontrados
        """
        secrets = []

        # Archivos a escanear
        patterns = ["**/*.py", "**/*.js", "**/*.json", "**/*.yaml", "**/*.yml",
                   "**/*.env", "**/*.config", "**/*.ini", "**/*.xml"]

        # Exclusiones
        excludes = ["node_modules", ".git", "__pycache__", "venv", ".venv"]

        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                # Verificar exclusiones
                if any(excl in str(file_path) for excl in excludes):
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')

                    for secret_type, patterns_list in self.SECRET_PATTERNS.items():
                        for pat in patterns_list:
                            for i, line in enumerate(lines, 1):
                                matches = re.findall(pat, line, re.IGNORECASE)
                                for match in matches:
                                    if isinstance(match, tuple):
                                        match = match[0]

                                    # Filtrar falsos positivos comunes
                                    if self._is_likely_placeholder(match):
                                        continue

                                    entropy = self._calculate_entropy(match)

                                    # Enmascarar el secreto
                                    if len(match) > 8:
                                        masked = match[:4] + '*' * (len(match) - 8) + match[-4:]
                                    else:
                                        masked = '*' * len(match)

                                    secrets.append(SecretFinding(
                                        secret_type=secret_type,
                                        file_path=str(file_path),
                                        line_number=i,
                                        masked_value=masked,
                                        entropy=entropy,
                                        is_high_risk=entropy > 3.5 or secret_type in ['private_key', 'aws_key']
                                    ))

                except Exception as e:
                    logger.warning(f"Error escaneando {file_path}: {e}")

        return secrets

    def _is_likely_placeholder(self, value: str) -> bool:
        """Verifica si un valor es probablemente un placeholder."""
        placeholders = [
            'your_', 'example', 'xxx', 'placeholder', 'change_me',
            'todo', 'fixme', 'secret', 'password123', 'admin123',
            '1234', 'test', 'demo', 'sample'
        ]
        value_lower = value.lower()
        return any(p in value_lower for p in placeholders)

    # ========================================
    # ESCANEO OWASP TOP 10
    # ========================================

    def scan_owasp_top_10(self) -> List[SecurityVulnerability]:
        """
        Escanea el proyecto para vulnerabilidades OWASP Top 10.

        Returns:
            Lista de vulnerabilidades encontradas
        """
        vulnerabilities = []

        py_files = list(self.project_root.glob("**/*.py"))
        js_files = list(self.project_root.glob("**/*.js"))
        html_files = list(self.project_root.glob("**/*.html"))

        # Escanear Python
        for py_file in py_files:
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            vulnerabilities.extend(self._scan_python_file(str(py_file)))

        # Escanear JavaScript
        for js_file in js_files:
            if 'node_modules' in str(js_file):
                continue
            vulnerabilities.extend(self._scan_js_file(str(js_file)))

        # Escanear HTML
        for html_file in html_files:
            vulnerabilities.extend(self._scan_html_file(str(html_file)))

        return vulnerabilities

    def _scan_python_file(self, file_path: str) -> List[SecurityVulnerability]:
        """Escanea un archivo Python."""
        vulns = []
        path = Path(file_path)

        if not path.exists():
            return vulns

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # A03: SQL Injection
            for pattern, desc in self.SQL_INJECTION_PATTERNS:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        vulns.append(SecurityVulnerability(
                            id=self._generate_vuln_id(),
                            category=VulnerabilityCategory.A03_INJECTION,
                            severity=VulnerabilitySeverity.CRITICAL,
                            title=f"SQL Injection: {desc}",
                            description=f"Posible SQL injection detectado: {desc}. "
                                       "La construcción dinámica de queries SQL es peligrosa.",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip()[:100],
                            cwe_id="CWE-89",
                            remediation="Usa queries parametrizadas: cursor.execute('SELECT * FROM t WHERE id=?', (id,)). "
                                        "Considera usar un ORM como SQLAlchemy.",
                            references=["https://owasp.org/www-community/attacks/SQL_Injection"]
                        ))

            # A03: Command Injection
            cmd_patterns = [
                (r'os\.system\s*\([^)]*\+', "os.system con concatenación"),
                (r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True', "subprocess con shell=True"),
                (r'eval\s*\([^)]*(?:input|request|user)', "eval con datos de usuario"),
                (r'exec\s*\([^)]*(?:input|request|user)', "exec con datos de usuario"),
            ]

            for pattern, desc in cmd_patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        vulns.append(SecurityVulnerability(
                            id=self._generate_vuln_id(),
                            category=VulnerabilityCategory.A03_INJECTION,
                            severity=VulnerabilitySeverity.CRITICAL,
                            title=f"Command Injection: {desc}",
                            description="Posible inyección de comandos del sistema.",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip()[:100],
                            cwe_id="CWE-78",
                            remediation="Usa subprocess.run() con lista de argumentos, nunca shell=True. "
                                        "Valida y escapa toda entrada de usuario."
                        ))

            # A02: Cryptographic Failures
            crypto_patterns = [
                (r'md5\s*\(', "MD5 (inseguro para passwords)"),
                (r'sha1\s*\(', "SHA1 (inseguro para passwords)"),
                (r'password.*=.*["\'][^"\']+["\']', "Password hardcodeado"),
            ]

            for pattern, desc in crypto_patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        vulns.append(SecurityVulnerability(
                            id=self._generate_vuln_id(),
                            category=VulnerabilityCategory.A02_CRYPTO_FAILURE,
                            severity=VulnerabilitySeverity.HIGH,
                            title=f"Crypto Failure: {desc}",
                            description="Uso de criptografía débil o secretos hardcodeados.",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip()[:100],
                            cwe_id="CWE-327",
                            remediation="Usa bcrypt o argon2 para passwords. "
                                        "Almacena secretos en variables de entorno."
                        ))

            # A05: Security Misconfiguration
            misconfig_patterns = [
                (r'debug\s*=\s*True', "Debug mode habilitado"),
                (r'verify\s*=\s*False', "Verificación SSL deshabilitada"),
                (r'allow_credentials\s*=\s*True.*allow_origins.*\*', "CORS inseguro"),
            ]

            for pattern, desc in misconfig_patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        vulns.append(SecurityVulnerability(
                            id=self._generate_vuln_id(),
                            category=VulnerabilityCategory.A05_MISCONFIG,
                            severity=VulnerabilitySeverity.HIGH,
                            title=f"Misconfiguration: {desc}",
                            description="Configuración de seguridad insegura detectada.",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip()[:100],
                            cwe_id="CWE-16",
                            remediation="Revisa y corrige la configuración de seguridad. "
                                        "Debug=False en producción, verify=True para SSL."
                        ))

            # A07: Authentication Failures
            auth_patterns = [
                (r'jwt.*algorithm\s*=\s*["\']none["\']', "JWT sin algoritmo"),
                (r'password.*==.*password', "Comparación directa de password"),
            ]

            for pattern, desc in auth_patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        vulns.append(SecurityVulnerability(
                            id=self._generate_vuln_id(),
                            category=VulnerabilityCategory.A07_AUTH_FAILURE,
                            severity=VulnerabilitySeverity.CRITICAL,
                            title=f"Auth Failure: {desc}",
                            description="Problema de autenticación detectado.",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip()[:100],
                            cwe_id="CWE-287",
                            remediation="Usa algoritmos seguros (HS256, RS256) para JWT. "
                                        "Nunca compares passwords en texto plano."
                        ))

        except Exception as e:
            logger.error(f"Error escaneando Python {file_path}: {e}")

        return vulns

    def _scan_js_file(self, file_path: str) -> List[SecurityVulnerability]:
        """Escanea un archivo JavaScript."""
        vulns = []
        path = Path(file_path)

        if not path.exists():
            return vulns

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # XSS
            for pattern, desc in self.XSS_PATTERNS:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        vulns.append(SecurityVulnerability(
                            id=self._generate_vuln_id(),
                            category=VulnerabilityCategory.A03_INJECTION,
                            severity=VulnerabilitySeverity.HIGH,
                            title=f"XSS: {desc}",
                            description="Posible Cross-Site Scripting (XSS).",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip()[:100],
                            cwe_id="CWE-79",
                            remediation="Usa textContent en lugar de innerHTML. "
                                        "Escapa todo contenido de usuario con funciones seguras."
                        ))

            # Prototype Pollution
            proto_pattern = r'\[.*\]\s*=.*(?:input|user|data|param)'
            for i, line in enumerate(lines, 1):
                if re.search(proto_pattern, line, re.IGNORECASE):
                    if '__proto__' in line or 'constructor' in line or 'prototype' in line:
                        vulns.append(SecurityVulnerability(
                            id=self._generate_vuln_id(),
                            category=VulnerabilityCategory.A08_INTEGRITY_FAILURE,
                            severity=VulnerabilitySeverity.HIGH,
                            title="Prototype Pollution",
                            description="Posible prototype pollution con datos de usuario.",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip()[:100],
                            cwe_id="CWE-1321",
                            remediation="Valida keys antes de asignar. "
                                        "Usa Object.create(null) para objetos de datos."
                        ))

        except Exception as e:
            logger.error(f"Error escaneando JS {file_path}: {e}")

        return vulns

    def _scan_html_file(self, file_path: str) -> List[SecurityVulnerability]:
        """Escanea un archivo HTML."""
        vulns = []
        path = Path(file_path)

        if not path.exists():
            return vulns

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Scripts inline (CSP violation)
            if re.search(r'<script[^>]*>[^<]+</script>', content, re.IGNORECASE | re.DOTALL):
                vulns.append(SecurityVulnerability(
                    id=self._generate_vuln_id(),
                    category=VulnerabilityCategory.A05_MISCONFIG,
                    severity=VulnerabilitySeverity.MEDIUM,
                    title="Scripts inline detectados",
                    description="Los scripts inline violan CSP y facilitan XSS.",
                    file_path=file_path,
                    line_number=None,
                    code_snippet=None,
                    cwe_id="CWE-79",
                    remediation="Mueve todos los scripts a archivos externos. "
                               "Implementa Content-Security-Policy sin 'unsafe-inline'."
                ))

            # Forms sin CSRF token
            forms = re.findall(r'<form[^>]*>(.*?)</form>', content, re.DOTALL | re.IGNORECASE)
            for form in forms:
                if 'csrf' not in form.lower() and 'token' not in form.lower():
                    vulns.append(SecurityVulnerability(
                        id=self._generate_vuln_id(),
                        category=VulnerabilityCategory.A01_BROKEN_ACCESS,
                        severity=VulnerabilitySeverity.MEDIUM,
                        title="Formulario sin CSRF token",
                        description="El formulario no tiene protección CSRF visible.",
                        file_path=file_path,
                        line_number=None,
                        code_snippet=None,
                        cwe_id="CWE-352",
                        remediation="Añade un token CSRF a todos los formularios POST. "
                                   "FastAPI: usa CORSMiddleware correctamente."
                    ))

        except Exception as e:
            logger.error(f"Error escaneando HTML {file_path}: {e}")

        return vulns

    # ========================================
    # ANÁLISIS DE CONFIGURACIÓN
    # ========================================

    def analyze_security_config(self) -> SecurityConfig:
        """
        Analiza la configuración de seguridad del proyecto.

        Returns:
            SecurityConfig con el análisis
        """
        issues = []

        # Buscar archivos de configuración
        main_py = self.project_root / "main.py"
        config_files = list(self.project_root.glob("**/config*.py"))

        has_https = False
        has_cors = False
        cors_allows_all = False
        has_csrf = False
        has_rate_limit = False
        has_security_headers = False
        has_validation = False
        has_encoding = False
        has_auth = False
        uses_jwt = False
        jwt_has_expiry = False
        passwords_hashed = False

        files_to_check = [main_py] + config_files

        for file in files_to_check:
            if not file.exists():
                continue

            try:
                content = file.read_text(encoding='utf-8')

                # HTTPS
                if 'https' in content.lower() or 'ssl' in content.lower():
                    has_https = True

                # CORS
                if 'cors' in content.lower():
                    has_cors = True
                    if '"*"' in content or "'*'" in content:
                        cors_allows_all = True
                        issues.append("CORS permite todos los orígenes (*)")

                # CSRF
                if 'csrf' in content.lower():
                    has_csrf = True

                # Rate Limiting
                if 'ratelimit' in content.lower() or 'rate_limit' in content.lower():
                    has_rate_limit = True

                # Security Headers
                if any(h in content.lower() for h in ['x-frame-options', 'x-xss-protection', 'content-security-policy']):
                    has_security_headers = True

                # Validation
                if 'pydantic' in content.lower() or 'validator' in content.lower():
                    has_validation = True

                # Output Encoding
                if 'escape' in content.lower() or 'sanitize' in content.lower():
                    has_encoding = True

                # Auth
                if 'authentication' in content.lower() or 'authorize' in content.lower():
                    has_auth = True

                # JWT
                if 'jwt' in content.lower():
                    uses_jwt = True
                    if 'expir' in content.lower() or 'exp' in content.lower():
                        jwt_has_expiry = True

                # Password Hashing
                if 'bcrypt' in content.lower() or 'argon2' in content.lower() or 'pbkdf2' in content.lower():
                    passwords_hashed = True

            except Exception as e:
                logger.warning(f"Error analizando {file}: {e}")

        # Generar issues
        if not has_https:
            issues.append("No se detectó configuración HTTPS")
        if not has_cors:
            issues.append("No se detectó configuración CORS")
        if not has_csrf:
            issues.append("No se detectó protección CSRF")
        if not has_rate_limit:
            issues.append("No se detectó rate limiting")
        if not has_security_headers:
            issues.append("No se detectaron security headers")
        if not has_validation:
            issues.append("No se detectó validación de entrada (Pydantic)")
        if uses_jwt and not jwt_has_expiry:
            issues.append("JWT configurado pero sin expiración visible")
        if has_auth and not passwords_hashed:
            issues.append("Auth configurado pero sin hash de passwords visible")

        return SecurityConfig(
            has_https=has_https,
            has_cors_config=has_cors,
            cors_allows_all=cors_allows_all,
            has_csrf_protection=has_csrf,
            has_rate_limiting=has_rate_limit,
            has_security_headers=has_security_headers,
            has_input_validation=has_validation,
            has_output_encoding=has_encoding,
            has_auth_system=has_auth,
            auth_uses_jwt=uses_jwt,
            jwt_has_expiry=jwt_has_expiry,
            passwords_hashed=passwords_hashed,
            issues=issues
        )

    # ========================================
    # AUDITORÍA COMPLETA
    # ========================================

    def audit_security(self) -> SecurityAuditReport:
        """
        Realiza una auditoría completa de seguridad.

        Returns:
            SecurityAuditReport con todos los hallazgos
        """
        logger.info("🔒 Iniciando auditoría de seguridad...")

        # Escanear vulnerabilidades
        vulnerabilities = self.scan_owasp_top_10()

        # Escanear secretos
        secrets = self.scan_for_secrets()

        # Añadir vulnerabilidades por secretos
        for secret in secrets:
            if secret.is_high_risk:
                vulnerabilities.append(SecurityVulnerability(
                    id=self._generate_vuln_id(),
                    category=VulnerabilityCategory.A02_CRYPTO_FAILURE,
                    severity=VulnerabilitySeverity.CRITICAL,
                    title=f"Secreto expuesto: {secret.secret_type}",
                    description=f"Se detectó un {secret.secret_type} en el código fuente.",
                    file_path=secret.file_path,
                    line_number=secret.line_number,
                    code_snippet=secret.masked_value,
                    cwe_id="CWE-798",
                    remediation="Elimina el secreto del código y usa variables de entorno. "
                               "Rota las credenciales si fueron comprometidas."
                ))

        # Analizar configuración
        config = self.analyze_security_config()

        # Contar por severidad
        critical = sum(1 for v in vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL)
        high = sum(1 for v in vulnerabilities if v.severity == VulnerabilitySeverity.HIGH)
        medium = sum(1 for v in vulnerabilities if v.severity == VulnerabilitySeverity.MEDIUM)
        low = sum(1 for v in vulnerabilities if v.severity == VulnerabilitySeverity.LOW)

        # Contar archivos escaneados
        files_scanned = len(list(self.project_root.glob("**/*.py")))
        files_scanned += len(list(self.project_root.glob("**/*.js")))
        files_scanned += len(list(self.project_root.glob("**/*.html")))

        # Calcular score
        score = 100
        score -= critical * 25
        score -= high * 10
        score -= medium * 5
        score -= low * 2
        score -= len(secrets) * 5
        score -= len(config.issues) * 3
        score = max(0, score)

        # Generar recomendaciones
        recommendations = self._generate_recommendations(vulnerabilities, secrets, config)

        report = SecurityAuditReport(
            timestamp=datetime.now().isoformat(),
            files_scanned=files_scanned,
            total_vulnerabilities=len(vulnerabilities),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            vulnerabilities=vulnerabilities,
            secrets_found=secrets,
            security_config=config,
            recommendations=recommendations,
            security_score=score
        )

        logger.info(f"✅ Auditoría completada: {len(vulnerabilities)} vulnerabilidades, "
                   f"{len(secrets)} secretos, score: {score}%")

        return report

    def _generate_recommendations(
        self,
        vulns: List[SecurityVulnerability],
        secrets: List[SecretFinding],
        config: SecurityConfig
    ) -> List[str]:
        """Genera recomendaciones de seguridad."""
        recs = []

        # Por categoría más afectada
        category_counts = {}
        for v in vulns:
            cat = v.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        if category_counts:
            top_cat = max(category_counts, key=category_counts.get)
            recs.append(
                f"🎯 Prioridad: {category_counts[top_cat]} vulnerabilidades en '{top_cat}'. "
                "Enfócate en corregir esta categoría primero."
            )

        # Por secretos
        if secrets:
            high_risk = [s for s in secrets if s.is_high_risk]
            recs.append(
                f"🔑 Secretos: {len(secrets)} secretos encontrados ({len(high_risk)} de alto riesgo). "
                "Muévelos a variables de entorno inmediatamente."
            )

        # Por configuración
        if config.cors_allows_all:
            recs.append(
                "⚠️ CORS: Permite todos los orígenes (*). "
                "Restringe a dominios específicos en producción."
            )

        if not config.has_rate_limiting:
            recs.append(
                "🚫 Rate Limiting: No detectado. "
                "Implementa para prevenir ataques de fuerza bruta y DDoS."
            )

        if not config.has_security_headers:
            recs.append(
                "📋 Headers: Faltan security headers. "
                "Añade: X-Frame-Options, X-XSS-Protection, Content-Security-Policy."
            )

        if config.auth_uses_jwt and not config.jwt_has_expiry:
            recs.append(
                "⏰ JWT: Sin expiración visible. "
                "Configura exp claim con tiempo razonable (ej: 24h)."
            )

        # Si está limpio
        if not vulns and not secrets:
            recs.append(
                "✅ ¡Excelente! No se encontraron vulnerabilidades críticas. "
                "Continúa aplicando buenas prácticas de seguridad."
            )

        return recs


# Instancia singleton
_security_instance: Optional[SecurityAgent] = None


def get_security_agent(project_root: str = ".") -> SecurityAgent:
    """Obtiene la instancia global del Agente de Seguridad."""
    global _security_instance
    if _security_instance is None:
        _security_instance = SecurityAgent(project_root)
    return _security_instance
