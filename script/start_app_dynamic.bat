@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cls
echo ========================================
echo YuKyu Dashboard v5.0 (Dynamic Port)
echo ========================================
echo.

:AskPort
set /p PORT="Ingrese el puerto para la APP (backend) [default=8000]: "
if "%PORT%"=="" set PORT=8000

set /p FRONTEND_PORT="Ingrese el puerto para Frontend/CORS [default=3000]: "
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=3000

echo.
echo ========================================
echo Configuracion Seleccionada:
echo ----------------------------------------
echo Backend Port (API):       %PORT%
echo Frontend Port (Browser):  %FRONTEND_PORT%
echo ========================================
echo.
echo Si esto es correcto, el navegador se abrira en http://localhost:%PORT%
echo (CORS permitido para frontend %FRONTEND_PORT%)
echo.
pause

cd /d %~dp0..

REM Set Environment Variables for Python
set PORT=%PORT%
set FRONTEND_PORT=%FRONTEND_PORT%
set CORS_ORIGINS=http://localhost:%FRONTEND_PORT%,http://127.0.0.1:%FRONTEND_PORT%,http://localhost:%PORT%,http://127.0.0.1:%PORT%

REM Open browser after 2 seconds
start /min cmd /c "timeout /t 3 /nobreak > nul && start http://localhost:%PORT%"

REM Start server
echo Iniciando servidor uvicorn en puerto %PORT%...
python -m uvicorn main:app --reload --host 0.0.0.0 --port %PORT%

pause
