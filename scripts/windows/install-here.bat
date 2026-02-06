@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================================
:: ANTIGRAVITY QUICK INSTALLER
:: ============================================================================
:: Copia este archivo a cualquier proyecto y ejecutalo.
:: Instalara Antigravity desde C:\Users\kenji\AntigravitiSkillUSN
:: ============================================================================

set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "RESET=[0m"

:: Ruta al ecosistema Antigravity (auto-detecta o edita manualmente)
:: Primero intenta auto-detectar desde la ubicacion de este script
set "SOURCE=%~dp0"
set "SOURCE=%SOURCE:~0,-1%"
if not exist "%SOURCE%\.agent" (
    :: Fallback: ruta fija (edita si es necesario)
    set "SOURCE=C:\Users\kenji\AntigravitiSkillUSN"
)
set "TARGET=%CD%"

echo.
echo %CYAN%============================================================================%RESET%
echo %CYAN%          ANTIGRAVITY QUICK INSTALLER%RESET%
echo %CYAN%============================================================================%RESET%
echo.

:: Verificar que existe el source
if not exist "%SOURCE%\.agent" (
    echo %RED%[ERROR]%RESET% No se encontro AntigravitiSkillUSN en:
    echo         %SOURCE%
    echo.
    echo Edita este archivo y cambia la variable SOURCE a la ruta correcta.
    pause
    exit /b 1
)

echo %CYAN%Fuente:%RESET%  %SOURCE%
echo %CYAN%Destino:%RESET% %TARGET%
echo.

set /p CONFIRM="Instalar Antigravity aqui? (S/n): "
if /i "%CONFIRM%"=="n" (
    echo Cancelado.
    pause
    exit /b 0
)

echo.
echo %GREEN%[1/5]%RESET% Copiando agentes...
if not exist "%TARGET%\.agent\agents" mkdir "%TARGET%\.agent\agents"
xcopy /E /I /Y /Q "%SOURCE%\.agent\agents" "%TARGET%\.agent\agents" >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% Fallo al copiar agentes
) else (
    echo %GREEN%  [OK]%RESET% Agentes copiados
)

echo %GREEN%[2/5]%RESET% Copiando skills...
if not exist "%TARGET%\.agent\skills" mkdir "%TARGET%\.agent\skills"
xcopy /E /I /Y /Q "%SOURCE%\.agent\skills" "%TARGET%\.agent\skills" >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% Fallo al copiar skills
) else (
    echo %GREEN%  [OK]%RESET% Skills copiadas
)

echo %GREEN%[3/5]%RESET% Copiando plugins...
if exist "%SOURCE%\.agent\plugins" (
    if not exist "%TARGET%\.agent\plugins" mkdir "%TARGET%\.agent\plugins"
    xcopy /E /I /Y /Q "%SOURCE%\.agent\plugins" "%TARGET%\.agent\plugins" >nul 2>&1
    echo %GREEN%  [OK]%RESET% Plugins copiados
) else (
    echo %YELLOW%  [SKIP]%RESET% Sin plugins
)

echo %GREEN%[4/5]%RESET% Copiando configuracion...
if exist "%SOURCE%\.agent\workflows" (
    if not exist "%TARGET%\.agent\workflows" mkdir "%TARGET%\.agent\workflows"
    xcopy /E /I /Y /Q "%SOURCE%\.agent\workflows" "%TARGET%\.agent\workflows" >nul 2>&1
)
if exist "%SOURCE%\.antigravity" (
    if not exist "%TARGET%\.antigravity" mkdir "%TARGET%\.antigravity"
    xcopy /E /I /Y /Q "%SOURCE%\.antigravity" "%TARGET%\.antigravity" >nul 2>&1
)
if exist "%SOURCE%\.agent\scripts" (
    if not exist "%TARGET%\.agent\scripts" mkdir "%TARGET%\.agent\scripts"
    xcopy /E /I /Y /Q "%SOURCE%\.agent\scripts" "%TARGET%\.agent\scripts" >nul 2>&1
)
if exist "%SOURCE%\.agent\mcp" (
    if not exist "%TARGET%\.agent\mcp" mkdir "%TARGET%\.agent\mcp"
    xcopy /E /I /Y /Q "%SOURCE%\.agent\mcp" "%TARGET%\.agent\mcp" >nul 2>&1
)
echo %GREEN%  [OK]%RESET% Configuracion copiada

echo %GREEN%[5/5]%RESET% Creando alias .claude/agents...
if not exist "%TARGET%\.claude\agents" mkdir "%TARGET%\.claude\agents"
for /D %%A in ("%TARGET%\.agent\agents\*") do (
    set "AGENT_NAME=%%~nxA"
    if not "!AGENT_NAME!"=="_planned" (
        if not exist "%TARGET%\.claude\agents\!AGENT_NAME!" mkdir "%TARGET%\.claude\agents\!AGENT_NAME!" 2>nul
        if exist "%%A\IDENTITY.md" (
            copy /Y "%%A\IDENTITY.md" "%TARGET%\.claude\agents\!AGENT_NAME!\!AGENT_NAME!.md" >nul 2>&1
        )
    )
)
echo %GREEN%  [OK]%RESET% Alias creados

echo %GREEN%[6/6]%RESET% Creando configuracion MCP multi-IDE...

:: .mcp.json para Claude Code
(
    echo {
    echo   "mcpServers": {
    echo     "antigravity-agents": {
    echo       "command": "python",
    echo       "args": [".agent/mcp/agents-server-v2.py"],
    echo       "description": "96 agentes autonomos Antigravity como herramientas MCP"
    echo     }
    echo   }
    echo }
) > "%TARGET%\.mcp.json"
echo   %GREEN%[OK]%RESET% .mcp.json ^(Claude Code^)

:: .cursor/mcp.json para Cursor
if not exist "%TARGET%\.cursor" mkdir "%TARGET%\.cursor"
(
    echo {
    echo   "mcpServers": {
    echo     "antigravity-agents": {
    echo       "command": "python",
    echo       "args": [".agent/mcp/agents-server-v2.py"],
    echo       "description": "96 agentes autonomos Antigravity como herramientas MCP"
    echo     }
    echo   }
    echo }
) > "%TARGET%\.cursor\mcp.json"
echo   %GREEN%[OK]%RESET% .cursor/mcp.json ^(Cursor^)

:: .windsurf/mcp.json para Windsurf
if not exist "%TARGET%\.windsurf" mkdir "%TARGET%\.windsurf"
(
    echo {
    echo   "mcpServers": {
    echo     "antigravity-agents": {
    echo       "command": "python",
    echo       "args": [".agent/mcp/agents-server-v2.py"],
    echo       "description": "96 agentes autonomos Antigravity como herramientas MCP"
    echo     }
    echo   }
    echo }
) > "%TARGET%\.windsurf\mcp.json"
echo   %GREEN%[OK]%RESET% .windsurf/mcp.json ^(Windsurf^)

:: .zed/settings.json para Zed
if not exist "%TARGET%\.zed" mkdir "%TARGET%\.zed"
(
    echo {
    echo   "context_servers": {
    echo     "antigravity-agents": {
    echo       "command": {
    echo         "path": "python",
    echo         "args": [".agent/mcp/agents-server-v2.py"]
    echo       },
    echo       "settings": {}
    echo     }
    echo   }
    echo }
) > "%TARGET%\.zed\settings.json"
echo   %GREEN%[OK]%RESET% .zed/settings.json ^(Zed^)

echo.
echo %GREEN%============================================================================%RESET%
echo %GREEN%                    INSTALACION COMPLETADA%RESET%
echo %GREEN%============================================================================%RESET%
echo.
echo Agentes instalados en: %TARGET%\.agent\agents\
echo Skills instaladas en:  %TARGET%\.agent\skills\
echo MCP configurado para:  Claude Code, Cursor, Windsurf, Zed
echo.
pause
