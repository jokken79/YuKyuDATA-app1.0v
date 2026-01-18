@echo off
echo Starting YuKyu App (Simple Mode)...
cd /d "%~dp0"

echo Activating venv...
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat

echo Opening Browser...
start /min cmd /c "timeout /t 5 /nobreak > nul && start http://localhost:8765"

echo Starting Server on port 8765...
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8765

echo.
echo Server stopped.
pause
