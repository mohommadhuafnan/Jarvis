@echo off
title JARVIS AI — Cyberpunk Command Center
cd /d "%~dp0"

echo ========================================================
echo   JARVIS AI ASSISTANT — CYBERPUNK HUD COMMAND CENTER
echo   LIVEKIT CLOUD + GEMINI REALTIME VOICE POWERED
echo ========================================================
echo.

set PYTHON_CMD=python
if exist "%~dp0.venv\Scripts\python.exe" (
    set PYTHON_CMD="%~dp0.venv\Scripts\python.exe"
)

echo [1/4] Starting JARVIS AI Core Backend (FastAPI on http://localhost:8000)...
start "JARVIS Backend" cmd /k "%PYTHON_CMD% -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload"

echo [2/4] Starting JARVIS LiveKit Realtime Agent (WebRTC Worker)...
start "JARVIS LiveKit Agent" cmd /k "%PYTHON_CMD% backend\agent.py dev"

echo [3/4] Starting JARVIS Windows Background Wake Word & System Tray...
start "JARVIS System Tray" cmd /k "%PYTHON_CMD% backend\tray.py"

echo [4/4] Starting JARVIS HUD Frontend (Vite on http://localhost:5173)...
cd "%~dp0frontend"
start "JARVIS Frontend" cmd /k "npm run dev"

echo.
echo ========================================================
echo   ALL SYSTEMS OPERATIONAL
echo   HUD Interface: http://localhost:5173
echo   AI API Engine: http://localhost:8000
echo   LiveKit Cloud: wss://jarvis-33vlibgi.livekit.cloud
echo   System Tray: Active with "Hello JARVIS" Wake Word
echo ========================================================
echo.
pause
