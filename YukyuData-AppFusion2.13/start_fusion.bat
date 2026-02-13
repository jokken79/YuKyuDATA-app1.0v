@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   YuKyu Fusion 2.13 Launcher
echo ========================================================
echo.

:: Check for Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b
)

:: Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://python.org/
    pause
    exit /b
)

:: Backend Setup
echo [Backend] Checking setup...
if not exist "backend\venv" (
    echo [Backend] Creating virtual environment...
    cd backend
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b
    )
    echo [Backend] Installing dependencies...
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
)

:: Frontend Setup
echo [Frontend] Checking setup...
if not exist "frontend\node_modules" (
    echo [Frontend] Installing dependencies...
    cd frontend
    call npm install
    cd ..
)

:: Start Servers
echo.
echo ========================================================
echo   Starting Services...
echo ========================================================
echo.

start "YuKyu Backend (Port 8000)" cmd /k "cd backend && call venv\Scripts\activate && uvicorn main:app --reload --port 8000"
timeout /t 2 /nobreak >nul
start "YuKyu Frontend (Port 3000)" cmd /k "cd frontend && npm run dev"

echo.
echo   - Backend: http://localhost:8000
echo   - Frontend: http://localhost:3000
echo.
echo   Servers are running in separate windows.
echo   Press any key to exit this launcher (servers will keep running).
pause
