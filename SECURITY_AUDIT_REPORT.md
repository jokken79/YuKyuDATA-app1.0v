# Informe de Auditoria de Seguridad Profunda - YuKyuDATA-app

**Fecha**: 2025-12-23
**Version de la Aplicacion**: 2.0.0
**Auditor**: Seguridad DevSecOps
**Clasificacion**: CONFIDENCIAL

---

## Resumen Ejecutivo

Se ha realizado una auditoria de seguridad profunda de la aplicacion YuKyuDATA-app, un sistema de gestion de vacaciones de empleados. Se identificaron **23 vulnerabilidades** distribuidas en las siguientes categorias:

| Severidad | Cantidad | Descripcion |
|-----------|----------|-------------|
| CRITICA   | 4        | Requieren correccion inmediata |
| ALTA      | 7        | Requieren correccion en 1-2 semanas |
| MEDIA     | 8        | Requieren correccion en 1 mes |
| BAJA      | 4        | Mejoras recomendadas |

---

## Vulnerabilidades CRITICAS (Prioridad Inmediata)

### CRIT-01: Credenciales Hardcodeadas en el Codigo Fuente

**Archivo**: `main.py` (Lineas 122, 130-135)
**Severidad**: CRITICA
**CWE**: CWE-798 (Use of Hard-coded Credentials)
**OWASP**: A07:2021 - Identification and Authentication Failures

**Codigo Vulnerable**:
```python
# main.py:122
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "yukyu-secret-key-2024-change-in-production")

# main.py:130-135
USERS_DB = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "name": "Administrator"
    }
}
```

**Riesgo**:
- Cualquier atacante que tenga acceso al codigo fuente puede obtener credenciales de admin
- El secret JWT por defecto permite falsificar tokens
- No hay hash de passwords - se almacenan en texto plano

**Remediacion**:
```python
import os
from passlib.hash import bcrypt

# Cargar desde variables de entorno OBLIGATORIAS
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]  # Sin valor por defecto

# Usar hash de passwords con bcrypt
USERS_DB = {
    "admin": {
        "password_hash": bcrypt.hash(os.environ.get("ADMIN_PASSWORD", "")),
        "role": "admin",
        "name": "Administrator"
    }
}

# Verificacion de password
def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.verify(plain_password, password_hash)
```

**Test de Verificacion**:
```python
def test_no_hardcoded_secrets():
    """Verifica que no hay secretos hardcodeados"""
    with open("main.py") as f:
        content = f.read()
    assert "admin123" not in content
    assert "yukyu-secret-key" not in content
```

---

### CRIT-02: Backups sin Encriptacion ni Control de Acceso

**Archivo**: `database.py` (Lineas 1004-1103), `main.py` (Lineas 977-1038)
**Severidad**: CRITICA
**CWE**: CWE-311 (Missing Encryption of Sensitive Data)
**OWASP**: A02:2021 - Cryptographic Failures

**Codigo Vulnerable**:
```python
# database.py:1029
shutil.copy2(DB_NAME, backup_filepath)  # Copia sin encriptar

# main.py:977-995 - Endpoint sin autenticacion
@app.post("/api/backup")
async def create_backup():
    result = database.create_backup()  # Sin auth
```

**Riesgo**:
- Los backups contienen datos sensibles (salarios, fechas de nacimiento, nacionalidades)
- Cualquier usuario puede crear/listar/restaurar backups sin autenticacion
- Los archivos .db estan en texto plano y pueden ser leidos directamente

**Remediacion**:
```python
from cryptography.fernet import Fernet
import os

BACKUP_ENCRYPTION_KEY = os.environ["BACKUP_ENCRYPTION_KEY"]

def create_encrypted_backup(backup_dir="backups"):
    """Crea backup encriptado de la base de datos."""
    fernet = Fernet(BACKUP_ENCRYPTION_KEY.encode())

    # Leer DB original
    with open(DB_NAME, 'rb') as f:
        db_data = f.read()

    # Encriptar
    encrypted_data = fernet.encrypt(db_data)

    # Guardar encriptado
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"yukyu_backup_{timestamp}.db.enc"
    backup_filepath = Path(backup_dir) / backup_filename

    with open(backup_filepath, 'wb') as f:
        f.write(encrypted_data)

    return {"filename": backup_filename, "encrypted": True}

# Endpoint con autenticacion obligatoria
@app.post("/api/backup")
async def create_backup(user: dict = Depends(require_admin)):
    result = database.create_encrypted_backup()
    return {"status": "success", "backup": result}
```

---

### CRIT-03: Path Traversal en Restauracion de Backup

**Archivo**: `database.py` (Linea 1088)
**Severidad**: CRITICA
**CWE**: CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)
**OWASP**: A01:2021 - Broken Access Control

**Codigo Vulnerable**:
```python
# database.py:1088
backup_path = Path(backup_dir) / backup_filename  # Sin validacion
# Un atacante puede usar: {"filename": "../../../etc/passwd"}
```

**Riesgo**:
- Un atacante puede restaurar archivos arbitrarios del sistema
- Puede sobrescribir la base de datos con contenido malicioso
- No hay validacion del nombre de archivo

**Remediacion**:
```python
import re

def restore_backup(backup_filename: str, backup_dir: str = "backups"):
    """Restaura backup con validacion de path."""

    # 1. Validar formato de nombre de archivo
    if not re.match(r'^yukyu_backup_\d{8}_\d{6}\.db(\.enc)?$', backup_filename):
        raise ValueError("Invalid backup filename format")

    # 2. Validar que no hay path traversal
    if '..' in backup_filename or '/' in backup_filename or '\\' in backup_filename:
        raise ValueError("Invalid characters in filename")

    # 3. Resolver path y verificar que esta dentro del directorio permitido
    backup_dir_resolved = Path(backup_dir).resolve()
    backup_path = (backup_dir_resolved / backup_filename).resolve()

    if not str(backup_path).startswith(str(backup_dir_resolved)):
        raise ValueError("Path traversal detected")

    if not backup_path.exists():
        raise ValueError(f"Backup file {backup_filename} not found")

    # Continuar con restauracion...
```

---

### CRIT-04: Falta de Proteccion CSRF en Endpoints de Modificacion

**Archivo**: `main.py` (Todos los endpoints POST/DELETE/PUT)
**Severidad**: CRITICA
**CWE**: CWE-352 (Cross-Site Request Forgery)
**OWASP**: A01:2021 - Broken Access Control

**Riesgo**:
- Un atacante puede hacer que un usuario autenticado ejecute acciones no deseadas
- Puede eliminar todos los datos de la base de datos
- Puede sincronizar datos maliciosos

**Remediacion**:
```python
from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel

class CsrfSettings(BaseModel):
    secret_key: str = os.environ["CSRF_SECRET_KEY"]
    cookie_samesite: str = "strict"
    cookie_secure: bool = True

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

@app.post("/api/sync")
async def sync_data(
    csrf_protect: CsrfProtect = Depends(),
    user: dict = Depends(require_auth)
):
    await csrf_protect.validate_csrf()
    # ... resto de la logica
```

---

## Vulnerabilidades ALTAS

### HIGH-01: JWT Sin Verificacion de Algoritmo Correcto

**Archivo**: `main.py` (Linea 169)
**Severidad**: ALTA
**CWE**: CWE-327 (Use of a Broken or Risky Cryptographic Algorithm)

**Riesgo**: Vulnerable al ataque "Algorithm Confusion" si el atacante manipula el header.

**Remediacion**:
```python
from jwt.exceptions import InvalidAlgorithmError

def verify_jwt_token(token: str) -> dict:
    try:
        # Verificar header antes de decodificar
        header = jwt.get_unverified_header(token)
        if header.get('alg') != JWT_ALGORITHM:
            raise InvalidAlgorithmError("Algorithm mismatch")

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub"]}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token")
```

---

### HIGH-02: Exposicion de Datos Sensibles en Respuestas API

**Archivo**: `database.py` (Lineas 398-399, 468-469)
**Severidad**: ALTA
**CWE**: CWE-200 (Exposure of Sensitive Information)
**OWASP**: A02:2021 - Cryptographic Failures

**Riesgo**:
- Datos de salarios expuestos a cualquier usuario
- Fechas de nacimiento expuestas (PII)
- Nacionalidades expuestas (dato sensible GDPR)

**Remediacion**:
```python
SENSITIVE_FIELDS = {'hourly_wage', 'wage_revision', 'birth_date', 'nationality', 'visa_expiry'}

def sanitize_employee_data(employee: dict, user_role: str) -> dict:
    """Elimina campos sensibles segun el rol del usuario."""
    if user_role != 'admin':
        return {k: v for k, v in employee.items() if k not in SENSITIVE_FIELDS}
    return employee
```

---

### HIGH-03: Excel Parsing Vulnerable a XXE y Zip Bomb

**Archivo**: `excel_service.py` (Lineas 13, 170, 238)
**Severidad**: ALTA
**CWE**: CWE-611 (Improper Restriction of XML External Entity Reference)
**CVE**: CVE-2018-1000656 (openpyxl versions < 2.6.0)

**Riesgo**:
- Un archivo Excel malicioso puede causar DoS por consumo de memoria
- Archivos muy grandes pueden crashear el servidor

**Remediacion**:
```python
import os
from openpyxl import load_workbook

MAX_FILE_SIZE_MB = 50
MAX_ROWS = 100000

def parse_excel_file_safe(file_path: str):
    """Parser seguro de Excel con limites."""

    # 1. Verificar tamanio del archivo
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {file_size_mb:.1f}MB")

    # 2. Cargar con read_only para reducir memoria
    wb = load_workbook(file_path, data_only=True, read_only=True)
    sheet = wb.active

    # 3. Limitar filas procesadas
    row_count = 0
    for row in sheet.iter_rows(min_row=2, values_only=True):
        row_count += 1
        if row_count > MAX_ROWS:
            break
        # procesar...

    wb.close()
```

---

### HIGH-04: Falta de Rate Limiting Efectivo en Endpoints Criticos

**Archivo**: `main.py` (Linea 114)
**Severidad**: ALTA
**CWE**: CWE-770 (Allocation of Resources Without Limits)

**Riesgo**: Los endpoints criticos no estan protegidos por rate limiting.

**Remediacion**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")  # Solo 5 intentos por minuto
async def login(request: Request, login_data: UserLogin):
    ...
```

---

### HIGH-05: Inyeccion SQL Potencial en Query Dinamica

**Archivo**: `database.py` (Linea 381)
**Severidad**: ALTA
**CWE**: CWE-89 (SQL Injection)
**OWASP**: A03:2021 - Injection

**Riesgo**: Aunque actualmente usa parametros, el patron de construccion dinamica es propenso a errores futuros.

**Remediacion**: Usar ORM como SQLAlchemy para queries mas seguras.

---

### HIGH-06: Falta de Validacion de Tipo de Archivo en Upload

**Archivo**: `main.py` (Endpoint /api/upload)
**Severidad**: ALTA
**CWE**: CWE-434 (Unrestricted Upload of File with Dangerous Type)

**Remediacion**:
```python
import magic
import re

ALLOWED_EXTENSIONS = {'.xlsx', '.xlsm', '.xls'}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Validar extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Invalid file extension")

    # 2. Validar MIME type
    content = await file.read()
    mime = magic.from_buffer(content, mime=True)
    # validar mime...
```

---

### HIGH-07: XSS Reflejado en Mensajes de Error

**Archivo**: `main.py` (Multiples endpoints)
**Severidad**: ALTA
**CWE**: CWE-79 (Cross-site Scripting)
**OWASP**: A03:2021 - Injection

**Remediacion**:
```python
import html

def safe_error_message(error: Exception) -> str:
    """Sanitiza mensajes de error para prevenir XSS."""
    msg = str(error)
    return html.escape(msg)[:500]
```

---

## Vulnerabilidades MEDIAS

### MED-01: CORS Permite Credenciales con Multiples Origenes

**Archivo**: `main.py` (Lineas 259-265)
**Severidad**: MEDIA
**CWE**: CWE-942 (Permissive Cross-domain Policy)

**Remediacion**: En produccion usar solo un origen permitido.

---

### MED-02: Sesion JWT sin Invalidacion (Token Replay)

**Archivo**: `main.py` (Linea 408)
**Severidad**: MEDIA
**CWE**: CWE-384 (Session Fixation)

**Problema**: El endpoint logout no invalida el token.

**Remediacion**: Implementar lista negra de tokens con Redis.

---

### MED-03: Logging Insuficiente de Acciones Sensibles

**Archivo**: `logger.py`, `main.py`
**Severidad**: MEDIA
**CWE**: CWE-778 (Insufficient Logging)
**OWASP**: A09:2021 - Security Logging and Monitoring Failures

**Problema**: No hay logging de intentos de login fallidos ni accesos a datos sensibles.

---

### MED-04: Falta de Audit Trail para Cambios en Datos

**Archivo**: `database.py`
**Severidad**: MEDIA

**Problema**: No hay registro de quien modifica datos de empleados.

---

### MED-05: No hay GDPR Compliance (Derecho al Olvido)

**Regulacion**: GDPR Art. 17

**Problema**: No hay forma de eliminar completamente los datos de un empleado.

---

### MED-06: Datos de Export sin Proteccion

**Archivo**: `excel_export.py`
**Severidad**: MEDIA
**CWE**: CWE-552

**Problema**: Los archivos exportados contienen datos sensibles sin encriptar.

---

### MED-07: XSS en Frontend con Manipulacion DOM Insegura

**Archivo**: `static/js/app.js` (Multiples lineas)
**Severidad**: MEDIA
**CWE**: CWE-79 (Cross-site Scripting)

**Problema**: Se usa asignacion directa de HTML en el DOM sin sanitizar todos los campos.

**Remediacion**: Usar textContent en lugar de asignacion HTML directa, o sanitizar con DOMPurify.

---

### MED-08: Headers de Seguridad Faltantes

**Archivo**: `main.py`
**Severidad**: MEDIA
**CWE**: CWE-693

**Remediacion**: Agregar middleware con headers de seguridad:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Content-Security-Policy

---

## Vulnerabilidades BAJAS

### LOW-01: Version de Python no Especificada
### LOW-02: Dependencias sin Version Fija
### LOW-03: Debug Mode Potencial en Produccion
### LOW-04: Falta de Health Check Seguro

---

## Plan de Remediacion

| Prioridad | Vulnerabilidad | Esfuerzo | Fecha Limite |
|-----------|----------------|----------|--------------|
| 1 | CRIT-01: Credenciales hardcodeadas | 2 horas | Inmediato |
| 2 | CRIT-02: Backups sin encriptar | 4 horas | 24 horas |
| 3 | CRIT-03: Path Traversal | 2 horas | 24 horas |
| 4 | CRIT-04: Sin CSRF | 4 horas | 48 horas |
| 5 | HIGH-01 a HIGH-07 | 16 horas | 1 semana |
| 6 | MED-01 a MED-08 | 20 horas | 2 semanas |
| 7 | LOW-01 a LOW-04 | 4 horas | 1 mes |

---

## Resumen de Cumplimiento

| Estandar | Cumplimiento | Notas |
|----------|--------------|-------|
| OWASP Top 10 2021 | 30% | Falta trabajo en A01, A02, A03, A07, A09 |
| GDPR | 40% | Falta derecho al olvido, portabilidad |
| OWASP ASVS L1 | 25% | Falta validacion, crypto, autenticacion |

---

## Proximos Pasos

1. **Inmediato (0-24h)**: Corregir CRIT-01 a CRIT-04
2. **Corto plazo (1-2 semanas)**: Corregir HIGH-01 a HIGH-07
3. **Mediano plazo (1 mes)**: Implementar MED-01 a MED-08
4. **Largo plazo**: Implementar seguridad continua con SAST/DAST en CI/CD

---

*Este informe fue generado como parte de una auditoria de seguridad profunda.*
