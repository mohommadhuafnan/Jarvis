@echo off
cd /d "%~dp0"
title Starting JARVIS...

echo Starting JARVIS in background...
start "" /b ".\.venv\Scripts\pythonw.exe" "backend\tray.py"

echo.
echo JARVIS is now running in the background!
echo Say "Hello JARVIS" to activate.
timeout /t 3 >nul
exit
