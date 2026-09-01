@echo off
title JARVIS Background Daemon
cd /d "%~dp0"

echo ======================================================
echo    STARTING JARVIS HEADLESS BACKGROUND DAEMON
echo ======================================================

set PYTHON_CMD=python
if exist "%~dp0.venv\Scripts\python.exe" (
    set PYTHON_CMD="%~dp0.venv\Scripts\python.exe"
)

%PYTHON_CMD% backend\background_service.py
