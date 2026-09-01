@echo off
setlocal enabledelayedexpansion

title JARVIS - Disable Windows Auto-Start
echo =====================================================================
echo          JARVIS AI - DISABLE WINDOWS STARTUP & STOP SERVICE
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Disable Windows Startup entry
echo [1/2] Removing JARVIS from Windows Startup...
if exist ".venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe -c "from backend.services.startup_service import startup_service; res = startup_service.disable_startup(); print(res['message'] if res['success'] else res.get('error',''))"
) else (
    set APPDATA_STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
    if exist "!APPDATA_STARTUP!\JARVIS_AutoStart.vbs" del "!APPDATA_STARTUP!\JARVIS_AutoStart.vbs"
    if exist "!APPDATA_STARTUP!\JARVIS_AutoStart.bat" del "!APPDATA_STARTUP!\JARVIS_AutoStart.bat"
    echo [OK] Removed startup shortcut.
)

:: 2. Terminate running background instances
echo.
echo [2/2] Stopping active JARVIS background processes...
taskkill /f /im pythonw.exe >nul 2>&1
if exist "jarvis_instance.lock" del "jarvis_instance.lock" >nul 2>&1
echo [OK] Stopped active background instances.

echo.
echo =====================================================================
echo Auto-start has been disabled and background services stopped.
echo (Your project files and code remain completely intact).
echo.
echo You can restart JARVIS at any time using: start_jarvis.bat
echo or re-enable auto-startup using: install.bat
echo =====================================================================
echo.
pause
