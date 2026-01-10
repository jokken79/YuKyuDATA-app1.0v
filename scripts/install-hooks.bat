@echo off
REM =============================================================================
REM install-hooks.bat - Install pre-commit hooks for YuKyuDATA-app (Windows)
REM =============================================================================

echo ==============================================
echo   YuKyuDATA-app Pre-commit Hooks Installer
echo ==============================================
echo.

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

cd /d "%PROJECT_ROOT%"

REM Check if we're in a git repository
if not exist ".git" (
    echo ERROR: Not a git repository. Please run from project root.
    exit /b 1
)

REM Check Python availability
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    exit /b 1
)

echo [1/4] Checking pre-commit installation...

REM Install pre-commit if not available
where pre-commit >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo       Installing pre-commit...
    pip install pre-commit
) else (
    echo       pre-commit already installed
)

echo [2/4] Installing git hooks...
call pre-commit install
call pre-commit install --hook-type post-commit

echo [3/4] Creating hook scripts...
REM Windows doesn't need chmod, scripts will work via python/bash

echo [4/4] Running initial check...
call pre-commit run --all-files

echo.
echo ==============================================
echo   Installation complete!
echo ==============================================
echo.
echo Hooks installed:
echo   - pre-commit: Runs before each commit
echo   - post-commit: Updates CLAUDE_MEMORY.md
echo.
echo Commands:
echo   pre-commit run --all-files  # Run all checks
echo   pre-commit run ^<hook-id^>    # Run specific hook
echo   git commit --no-verify      # Skip hooks (use sparingly)
echo.

pause
