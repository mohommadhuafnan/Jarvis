@echo off
title JARVIS Windows Startup Setup
cd /d "%~dp0"

echo ======================================================
echo    CONFIGURING JARVIS WINDOWS AUTO-START
echo ======================================================

set PYTHON_CMD=python
if exist "%~dp0.venv\Scripts\python.exe" (
    set PYTHON_CMD="%~dp0.venv\Scripts\python.exe"
)

%PYTHON_CMD% -c "from backend.services.startup_service import startup_service; res = startup_service.enable_startup(); print(res['message'] if res.get('success') else res.get('error'))"

pause
