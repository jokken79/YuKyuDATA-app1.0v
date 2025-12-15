@echo off
chcp 65001 > nul
cls
echo ========================================
echo YuKyu Dashboard v5.0 (SQLite Edition)
echo ========================================
echo.

cd /d %~dp0

REM Ask for port number
set /p PORT="Ingrese el puerto (por defecto 8000): "
if "%PORT%"=="" set PORT=8000

echo.
echo Puerto seleccionado: %PORT%
echo Iniciando servidor en http://localhost:%PORT%
echo.
echo Presione Ctrl+C para detener el servidor
echo ========================================
echo.

REM Open browser after 2 seconds
start /min cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:%PORT%"

REM Start server
python -m uvicorn main:app --reload --host 0.0.0.0 --port %PORT%

pause
