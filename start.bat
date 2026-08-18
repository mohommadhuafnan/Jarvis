@echo off
title JARVIS AI — Cyberpunk Command Center
echo ========================================================
echo   JARVIS AI ASSISTANT — CYBERPUNK HUD COMMAND CENTER
echo ========================================================
echo.

echo [1/2] Starting JARVIS AI Core Backend (FastAPI on http://localhost:8000)...
start "JARVIS Backend" cmd /k "python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting JARVIS HUD Frontend (Vite on http://localhost:5173)...
cd frontend
start "JARVIS Frontend" cmd /k "npm run dev"

echo.
echo ========================================================
echo   ALL SYSTEMS OPERATIONAL
echo   HUD Interface: http://localhost:5173
echo   AI API Engine: http://localhost:8000
echo ========================================================
echo.
pause
