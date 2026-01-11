@echo off
REM docker-dev.bat - Start YuKyuDATA Development Environment (Windows)
REM
REM Usage:
REM   scripts\docker-dev.bat              Start with build
REM   scripts\docker-dev.bat --no-build   Start without build
REM   scripts\docker-dev.bat --rebuild    Force rebuild
REM   scripts\docker-dev.bat --stop       Stop containers
REM   scripts\docker-dev.bat --logs       View logs
REM   scripts\docker-dev.bat --test       Run tests in container
REM   scripts\docker-dev.bat --shell      Open shell in container

setlocal enabledelayedexpansion

REM ============================================
REM CONFIGURATION
REM ============================================
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "COMPOSE_FILE=%PROJECT_DIR%\docker-compose.dev.yml"
set "CONTAINER_NAME=yukyu-dev"

REM ============================================
REM FUNCTIONS
REM ============================================

:print_header
echo.
echo ============================================
echo   YuKyuDATA Docker Development Environment
echo ============================================
echo.
goto :eof

:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running. Please start Docker Desktop.
    exit /b 1
)

echo [OK] Docker is available
goto :eof

:check_env_file
if not exist "%PROJECT_DIR%\.env" (
    if exist "%PROJECT_DIR%\.env.example" (
        echo [WARNING] .env file not found. Creating from .env.example...
        copy "%PROJECT_DIR%\.env.example" "%PROJECT_DIR%\.env" >nul
        echo [OK] Created .env file. Please review and update secrets.
    ) else (
        echo [WARNING] .env file not found. Using default environment variables.
    )
) else (
    echo [OK] .env file found
)
goto :eof

:start_dev
call :print_header
call :check_docker
call :check_env_file

echo.
echo [INFO] Starting development environment...
echo.

cd /d "%PROJECT_DIR%"

if "%~1"=="--rebuild" (
    echo [INFO] Forcing rebuild...
    docker compose -f "%COMPOSE_FILE%" build --no-cache
)

if "%~1"=="--no-build" (
    docker compose -f "%COMPOSE_FILE%" up
) else (
    docker compose -f "%COMPOSE_FILE%" up --build
)
goto :eof

:stop_dev
call :print_header
echo [INFO] Stopping development environment...
cd /d "%PROJECT_DIR%"
docker compose -f "%COMPOSE_FILE%" down
echo [OK] Development environment stopped
goto :eof

:show_logs
cd /d "%PROJECT_DIR%"
docker compose -f "%COMPOSE_FILE%" logs -f
goto :eof

:run_tests
call :print_header
echo [INFO] Running tests inside container...
cd /d "%PROJECT_DIR%"
docker compose -f "%COMPOSE_FILE%" exec app pytest tests/ -v
goto :eof

:open_shell
echo [INFO] Opening shell in container...
cd /d "%PROJECT_DIR%"
docker compose -f "%COMPOSE_FILE%" exec app /bin/bash
goto :eof

:show_status
cd /d "%PROJECT_DIR%"
echo.
echo [INFO] Container status:
docker compose -f "%COMPOSE_FILE%" ps
echo.
goto :eof

:show_help
echo Usage: %~nx0 [OPTION]
echo.
echo Options:
echo   (none)       Start development environment with build
echo   --no-build   Start without rebuilding the image
echo   --rebuild    Force rebuild the image (no cache)
echo   --stop       Stop the development environment
echo   --logs       View container logs
echo   --test       Run pytest inside the container
echo   --shell      Open bash shell in the container
echo   --status     Show container status
echo   --help       Show this help message
echo.
echo Examples:
echo   %~nx0                    Start with build
echo   %~nx0 --no-build         Start without build
echo   %~nx0 --stop             Stop containers
echo.
echo Access the application at: http://localhost:8000
goto :eof

REM ============================================
REM MAIN
REM ============================================

if "%~1"=="" goto :default_start
if "%~1"=="--no-build" goto :no_build
if "%~1"=="--rebuild" goto :rebuild
if "%~1"=="--stop" goto :stop
if "%~1"=="--logs" goto :logs
if "%~1"=="--test" goto :test
if "%~1"=="--shell" goto :shell
if "%~1"=="--status" goto :status
if "%~1"=="--help" goto :help
if "%~1"=="-h" goto :help

echo [ERROR] Unknown option: %~1
call :show_help
exit /b 1

:default_start
call :start_dev --build
goto :end

:no_build
call :start_dev --no-build
goto :end

:rebuild
call :start_dev --rebuild
goto :end

:stop
call :stop_dev
goto :end

:logs
call :show_logs
goto :end

:test
call :run_tests
goto :end

:shell
call :open_shell
goto :end

:status
call :show_status
goto :end

:help
call :show_help
goto :end

:end
endlocal
