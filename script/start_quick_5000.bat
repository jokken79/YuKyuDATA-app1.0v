@echo off
chcp 65001 > nul
echo Iniciando en puerto 5000...
cd /d %~dp0..
start /min cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:5000"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 5000
pause
