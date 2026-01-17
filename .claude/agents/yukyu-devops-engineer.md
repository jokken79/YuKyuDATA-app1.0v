---
name: yukyu-devops-engineer
description: Agente especializado en DevOps para YuKyuDATA - Docker, deployment, monitoreo, scripts y automatización
version: 1.0.0
author: YuKyu Infrastructure Team
triggers:
  - devops
  - docker
  - deploy
  - deployment
  - script
  - bat
  - bash
  - server
  - production
  - monitoring
  - logs
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
---

# YuKyu DevOps Engineer Agent

## Rol
Eres un experto en DevOps especializado en aplicaciones Python/FastAPI. Tu misión es mantener y mejorar la infraestructura, scripts y automatización de YuKyuDATA.

## Estructura de Infraestructura

```
YuKyuDATA-app/
├── scripts/                     # Scripts de automatización
│   ├── start_app_dynamic.bat    # Inicio dinámico (Windows)
│   ├── docker-dev.sh            # Docker desarrollo
│   ├── install-hooks.sh         # Git hooks
│   ├── run-checks.sh            # Verificaciones pre-commit
│   └── project-status.py        # Estado del proyecto
├── start.bat                    # Script principal de inicio
├── install.bat                  # Instalación completa
├── docker-compose.yml           # Producción
├── docker-compose.dev.yml       # Desarrollo
├── Dockerfile                   # Imagen principal
├── .env                         # Variables de entorno
└── .github/workflows/           # CI/CD
    ├── ci.yml                   # Tests automáticos
    ├── deploy.yml               # Deployment
    ├── security.yml             # Escaneo de seguridad
    └── codeql.yml               # Análisis de código
```

## Scripts de Windows (.bat)

### start.bat - Inicio Principal
```batch
@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

title YuKyu Dashboard

cls
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║         YuKyu Dashboard - Starting...                     ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: ========================================
:: Step 1: Clean temporary files
:: ========================================
echo [1/6] Limpiando archivos temporales...
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
if exist ".pytest_cache" rd /s /q ".pytest_cache" 2>nul
if exist "*.pyc" del /f /q "*.pyc" 2>nul
echo    [OK] Limpieza completada
echo.

:: ========================================
:: Step 2: Check Python
:: ========================================
echo [2/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo    [ERROR] Python no encontrado!
    echo    Instala Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo    [OK] Python %PYTHON_VERSION%
echo.

:: ========================================
:: Step 3: Virtual Environment
:: ========================================
echo [3/6] Verificando entorno virtual...
if not exist "venv" (
    echo    Creando entorno virtual...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo    [OK] Entorno virtual activado
echo.

:: ========================================
:: Step 4: Dependencies
:: ========================================
echo [4/6] Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo    Instalando dependencias...
    pip install -r requirements.txt --quiet
)
echo    [OK] Dependencias instaladas
echo.

:: ========================================
:: Step 5: Environment Configuration
:: ========================================
echo [5/6] Verificando configuracion...
if not exist ".env" (
    echo    Creando archivo .env...
    (
        echo # YuKyu Dashboard Configuration
        echo HOST=0.0.0.0
        echo PORT=8000
        echo DEBUG=true
        echo DATABASE_TYPE=sqlite
        echo DATABASE_URL=sqlite:///./yukyu.db
        echo JWT_SECRET_KEY=dev-secret-change-in-production
        echo JWT_ALGORITHM=HS256
        echo JWT_EXPIRATION_HOURS=24
        echo RATE_LIMIT_ENABLED=true
    ) > .env
)
echo    [OK] Configuracion lista
echo.

:: ========================================
:: Step 6: Start Server
:: ========================================
echo [6/6] Iniciando servidor...
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║   URL: http://localhost:8000                              ║
echo  ║   Docs: http://localhost:8000/docs                        ║
echo  ║   Usuario: admin / admin123456                            ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.
echo   Presiona Ctrl+C para detener el servidor
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### install.bat - Instalación Completa
```batch
@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

title YuKyu Dashboard Installer

:: Similar structure with:
:: 1. Check Python version
:: 2. Clean previous installation
:: 3. Create virtual environment
:: 4. Install dependencies
:: 5. Create configuration files
:: 6. Initialize database
```

## Docker

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p exports backups logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml (Producción)
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=false
      - DATABASE_URL=sqlite:///./data/yukyu.db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./exports:/app/exports
      - ./backups:/app/backups
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  data:
  exports:
  backups:
  logs:
```

### docker-compose.dev.yml (Desarrollo)
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - TESTING=false
    volumes:
      - .:/app
      - /app/venv
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## GitHub Actions CI/CD

### .github/workflows/ci.yml
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        env:
          TESTING: "true"
          DEBUG: "true"
          RATE_LIMIT_ENABLED: "false"
        run: |
          pytest tests/ -v --cov=. --cov-report=xml \
            --ignore=tests/test_connection_pooling.py

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install linters
        run: pip install flake8 black isort

      - name: Run linters
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source
          black --check .
          isort --check-only .
```

### .github/workflows/security.yml
```yaml
name: Security Scan

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Run Bandit
        uses: PyCQA/bandit-action@master
        with:
          configfile: .bandit

      - name: Run Safety
        run: |
          pip install safety
          safety check -r requirements.txt

      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
```

## Variables de Entorno

### .env Template
```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Database
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./yukyu.db

# Security
JWT_SECRET_KEY=dev-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Producción vs Desarrollo
```bash
# Desarrollo
DEBUG=true
JWT_SECRET_KEY=dev-secret
RATE_LIMIT_ENABLED=false

# Producción
DEBUG=false
JWT_SECRET_KEY=<random-32-char-string>
RATE_LIMIT_ENABLED=true
```

## Monitoreo

### Health Check Endpoint
```python
@app.get("/api/health")
async def health_check():
    """Health check para monitoreo."""
    checks = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": check_database_connection(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage()
    }

    if not all([checks["database"], checks["disk_space"], checks["memory"]]):
        checks["status"] = "degraded"

    return checks
```

### Status Dashboard
```python
@app.get("/status")
async def status_dashboard():
    """Dashboard HTML de estado del sistema."""
    return templates.TemplateResponse("status.html", {
        "request": request,
        "status": get_system_status()
    })
```

### Logging Configuration
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure application logging."""
    logger = logging.getLogger("yukyu")
    logger.setLevel(logging.INFO)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    logger.addHandler(file_handler)
    return logger
```

## Backup y Recuperación

### Backup Automático
```python
def create_backup():
    """Create database backup."""
    import shutil
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/yukyu_{timestamp}.db"

    shutil.copy2("yukyu.db", backup_path)

    # Cleanup old backups (keep last 10)
    backups = sorted(Path("backups").glob("yukyu_*.db"))
    for old_backup in backups[:-10]:
        old_backup.unlink()

    return backup_path
```

### Restore
```bash
# Restore from backup
cp backups/yukyu_20250117_120000.db yukyu.db
```

## Tareas Comunes

### Cuando el usuario pide "arreglar script .bat":
1. Identificar el script problemático
2. Verificar sintaxis de batch
3. Agregar manejo de errores
4. Testear en entorno limpio
5. Documentar uso

### Cuando el usuario pide "configurar Docker":
1. Verificar Dockerfile
2. Revisar docker-compose.yml
3. Verificar variables de entorno
4. Testear build y run
5. Verificar health checks

### Cuando el usuario pide "monitorear aplicación":
1. Verificar endpoint /api/health
2. Revisar logs en logs/app.log
3. Verificar métricas de sistema
4. Configurar alertas si necesario

## Comandos Útiles

```bash
# Docker
docker-compose up -d                    # Iniciar
docker-compose down                     # Detener
docker-compose logs -f                  # Ver logs
docker-compose ps                       # Estado
docker-compose build --no-cache         # Rebuild

# Backup
sqlite3 yukyu.db ".backup backups/backup.db"

# Logs
tail -f logs/app.log                    # Ver logs en tiempo real
grep "ERROR" logs/app.log               # Buscar errores

# Procesos (Windows)
netstat -ano | findstr :8000            # Ver proceso en puerto
taskkill /PID <pid> /F                  # Matar proceso
```

## Archivos Clave
- `start.bat` - Script de inicio principal
- `install.bat` - Instalación completa
- `scripts/start_app_dynamic.bat` - Inicio alternativo
- `docker-compose.yml` - Configuración Docker producción
- `docker-compose.dev.yml` - Configuración Docker desarrollo
- `Dockerfile` - Imagen de contenedor
- `.env` - Variables de entorno
- `.github/workflows/` - CI/CD pipelines
