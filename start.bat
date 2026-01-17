@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: ========================================
:: YuKyu Dashboard - Smart Startup Script
:: Version: 1.0.0
:: ========================================

title YuKyu Dashboard Launcher

cls
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                                                           ║
echo  ║   ██╗   ██╗██╗   ██╗██╗  ██╗██╗   ██╗██╗   ██╗            ║
echo  ║   ╚██╗ ██╔╝██║   ██║██║ ██╔╝╚██╗ ██╔╝██║   ██║            ║
echo  ║    ╚████╔╝ ██║   ██║█████╔╝  ╚████╔╝ ██║   ██║            ║
echo  ║     ╚██╔╝  ██║   ██║██╔═██╗   ╚██╔╝  ██║   ██║            ║
echo  ║      ██║   ╚██████╔╝██║  ██╗   ██║   ╚██████╔╝            ║
echo  ║      ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝             ║
echo  ║                                                           ║
echo  ║          有給休暇管理システム v5.4                        ║
echo  ║                                                           ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

:: Navigate to project directory
cd /d "%~dp0"

:: ========================================
:: Step 1: Environment Cleanup
:: ========================================
echo [1/6] Limpiando archivos temporales...

:: Clean Python cache
if exist "__pycache__" rd /s /q "__pycache__" 2>nul
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

:: Clean pytest cache
if exist ".pytest_cache" rd /s /q ".pytest_cache" 2>nul

:: Clean coverage files
if exist ".coverage" del /f /q ".coverage" 2>nul
if exist "htmlcov" rd /s /q "htmlcov" 2>nul

:: Clean temp exports
if exist "exports\*.xlsx" del /f /q "exports\*.xlsx" 2>nul
if exist "exports\*.pdf" del /f /q "exports\*.pdf" 2>nul

echo    [OK] Limpieza completada
echo.

:: ========================================
:: Step 2: Check Python Installation
:: ========================================
echo [2/6] Verificando Python...

python --version >nul 2>&1
if errorlevel 1 (
    echo    [ERROR] Python no encontrado!
    echo.
    echo    Por favor instala Python 3.10+ desde:
    echo    https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo    [OK] Python %PYTHON_VERSION% encontrado
echo.

:: ========================================
:: Step 3: Create/Verify Virtual Environment
:: ========================================
echo [3/6] Verificando entorno virtual...

if not exist "venv" (
    echo    Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo    [ERROR] No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo    [OK] Entorno virtual creado
) else (
    echo    [OK] Entorno virtual existente
)

:: Activate virtual environment
call venv\Scripts\activate.bat 2>nul
echo.

:: ========================================
:: Step 4: Install/Update Dependencies
:: ========================================
echo [4/6] Verificando dependencias...

:: Check if requirements.txt exists
if not exist "requirements.txt" (
    echo    [ERROR] requirements.txt no encontrado!
    pause
    exit /b 1
)

:: Upgrade pip first
python -m pip install --upgrade pip --quiet 2>nul

:: Install dependencies
echo    Instalando dependencias (esto puede tardar)...
pip install -r requirements.txt --quiet 2>nul
if errorlevel 1 (
    echo    [WARN] Algunas dependencias pueden tener problemas
    echo    Intentando instalacion sin cache...
    pip install -r requirements.txt --no-cache-dir 2>nul
)

echo    [OK] Dependencias verificadas
echo.

:: ========================================
:: Step 5: Create .env if not exists
:: ========================================
echo [5/6] Verificando configuracion...

if not exist ".env" (
    echo    Creando archivo .env con configuracion por defecto...
    (
        echo # YuKyu Dashboard Configuration
        echo # Generated automatically - Edit as needed
        echo.
        echo # Server Configuration
        echo HOST=0.0.0.0
        echo PORT=8000
        echo DEBUG=true
        echo.
        echo # Database
        echo DATABASE_TYPE=sqlite
        echo DATABASE_URL=sqlite:///./yukyu.db
        echo.
        echo # Security ^(CHANGE IN PRODUCTION!^)
        echo JWT_SECRET_KEY=dev-secret-key-change-in-production-12345
        echo JWT_ALGORITHM=HS256
        echo JWT_EXPIRATION_HOURS=24
        echo.
        echo # Rate Limiting
        echo RATE_LIMIT_ENABLED=true
        echo RATE_LIMIT_REQUESTS=100
        echo RATE_LIMIT_WINDOW=60
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
        echo.
        echo # Excel Files ^(Japanese filenames^)
        echo VACATION_EXCEL=有給休暇管理.xlsm
        echo REGISTRY_EXCEL=【新】社員台帳^(UNS^)T　2022.04.05～.xlsm
    ) > .env
    echo    [OK] Archivo .env creado
) else (
    echo    [OK] Archivo .env existente
)
echo.

:: ========================================
:: Step 6: Initialize Database
:: ========================================
echo [6/6] Verificando base de datos...

if not exist "yukyu.db" (
    echo    Inicializando base de datos...
    python -c "import database; database.init_db()" 2>nul
    if errorlevel 1 (
        echo    [WARN] Base de datos sera creada al iniciar
    ) else (
        echo    [OK] Base de datos inicializada
    )
) else (
    echo    [OK] Base de datos existente
)
echo.

:: ========================================
:: Ready to Start
:: ========================================
echo ════════════════════════════════════════════════════════════
echo.
echo   Configuracion lista!
echo.
echo   Puerto:    8000
echo   URL:       http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Credenciales de desarrollo:
echo   Usuario:   admin
echo   Password:  admin123456
echo.
echo ════════════════════════════════════════════════════════════
echo.

set /p START_NOW="Iniciar servidor ahora? (S/n): "
if /i "%START_NOW%"=="n" (
    echo.
    echo Para iniciar manualmente:
    echo   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
    echo.
    pause
    exit /b 0
)

:: Open browser after delay
start /min cmd /c "timeout /t 3 /nobreak > nul && start http://localhost:8000"

:: Start server
echo.
echo Iniciando servidor...
echo Presiona Ctrl+C para detener
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

:: If server stops
echo.
echo Servidor detenido.
pause
