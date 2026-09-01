@echo off
title Stopping JARVIS...
echo Stopping active JARVIS background service...
taskkill /f /im pythonw.exe >nul 2>&1
if exist "jarvis_instance.lock" del "jarvis_instance.lock" >nul 2>&1
echo [OK] JARVIS background process stopped.
timeout /t 2 >nul
exit
