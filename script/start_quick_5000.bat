@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
echo Iniciando en puerto 5000...
cd /d %~dp0..
set PORT=5000
set FRONTEND_PORT=5000
set CORS_ORIGINS=http://localhost:%FRONTEND_PORT%,http://127.0.0.1:%FRONTEND_PORT%,http://localhost:%PORT%,http://127.0.0.1:%PORT%
start /min cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:5000"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 5000
pause
