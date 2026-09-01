@echo off
title JARVIS Windows Startup Setup
cd /d "%~dp0"

echo ======================================================
echo    CONFIGURING JARVIS WINDOWS AUTO-START
echo ======================================================

python -c "from backend.services.startup_service import startup_service; res = startup_service.enable_startup(); print(res['message'] if res.get('success') else res.get('error'))"

pause
