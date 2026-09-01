@echo off
title JARVIS Background Daemon
cd /d "%~dp0"

echo ======================================================
echo    STARTING JARVIS HEADLESS BACKGROUND DAEMON
echo ======================================================

python backend/background_service.py
