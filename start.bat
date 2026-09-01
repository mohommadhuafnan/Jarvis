@echo off
title JARVIS AI — Cyberpunk Command Center
echo ========================================================
echo   JARVIS AI ASSISTANT — CYBERPUNK HUD COMMAND CENTER
echo   LIVEKIT CLOUD + GEMINI REALTIME VOICE POWERED
echo ========================================================
echo.

echo [1/3] Starting JARVIS AI Core Backend (FastAPI on http://localhost:8000)...
start "JARVIS Backend" cmd /k "python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting JARVIS LiveKit Realtime Agent (WebRTC Worker)...
start "JARVIS LiveKit Agent" cmd /k "python backend\agent.py dev"

echo [3/3] Starting JARVIS HUD Frontend (Vite on http://localhost:5173)...
cd frontend
start "JARVIS Frontend" cmd /k "npm run dev"

echo.
echo ========================================================
echo   ALL SYSTEMS OPERATIONAL
echo   HUD Interface: http://localhost:5173
echo   AI API Engine: http://localhost:8000
echo   LiveKit Cloud: wss://jarvis-33vlibgi.livekit.cloud
echo ========================================================
echo.
pause
