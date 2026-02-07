@echo off
echo Starting YuKyu App (Simple Mode)...
cd /d "%~dp0"

echo Activating venv...
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat

if "%PORT%"=="" set PORT=8000
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=3000
if "%CORS_ORIGINS%"=="" set CORS_ORIGINS=http://localhost:%FRONTEND_PORT%,http://127.0.0.1:%FRONTEND_PORT%,http://localhost:%PORT%,http://127.0.0.1:%PORT%

echo Opening Browser...
start /min cmd /c "timeout /t 5 /nobreak > nul && start http://localhost:%PORT%"

echo Starting Server on port %PORT%...
python -m uvicorn main:app --reload --host 0.0.0.0 --port %PORT%

echo.
echo Server stopped.
pause
