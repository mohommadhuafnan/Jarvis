@echo off
title Stopping JARVIS...
echo Stopping active JARVIS background service...
taskkill /f /im pythonw.exe >nul 2>&1
if exist "jarvis_instance.lock" del /f /q "jarvis_instance.lock" >nul 2>&1
echo [OK] JARVIS background process stopped.
exit /b 0
