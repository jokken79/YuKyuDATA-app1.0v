@echo off
chcp 65001 > nul
echo Iniciando en puerto 3000...
cd /d %~dp0..
start /min cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:3000"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 3000
pause
