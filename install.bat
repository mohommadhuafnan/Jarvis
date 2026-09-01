@echo off
setlocal enabledelayedexpansion

title JARVIS Windows Desktop Assistant - Installation
echo =====================================================================
echo          JARVIS AI - WINDOWS DESKTOP ASSISTANT INSTALLER
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python Installation
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in PATH.
    echo Please install Python 3.10+ from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do set PY_VER=%%v
echo [OK] Detected %PY_VER%

:: 2. Check / Create Virtual Environment
echo.
echo [2/6] Setting up virtual environment (.venv)...
if not exist ".venv" (
    echo Creating new virtual environment...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)
echo [OK] Virtual environment ready.

:: 3. Upgrade pip and install dependencies
echo.
echo [3/6] Installing required dependencies...
call .\.venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
call .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some dependencies had warnings during install, proceeding...
) else (
    echo [OK] Dependencies installed successfully.
)

:: 4. Validate .env file
echo.
echo [4/6] Validating environment configuration (.env)...
if not exist ".env" (
    if exist ".env.example" (
        echo Copying .env.example to .env...
        copy .env.example .env >nul
        echo [NOTICE] Created .env file. Please ensure your GEMINI_API_KEY is configured.
    ) else (
        echo [WARNING] No .env found. Please create one with your API keys.
    )
) else (
    echo [OK] .env configuration file found.
)

:: 5. Configure Windows Startup
echo.
echo [5/6] Configuring Windows Startup (Silent Auto-Start on Login)...
.\.venv\Scripts\python.exe -c "from backend.services.startup_service import startup_service; res = startup_service.enable_startup(); print(res['message'] if res['success'] else res['error'])"

:: 6. Launch JARVIS in Background
echo.
echo [6/6] Launching JARVIS in background...
start "" /b ".\.venv\Scripts\pythonw.exe" "backend\tray.py"

echo.
echo =====================================================================
echo                  INSTALLATION COMPLETE!
echo =====================================================================
echo.
echo JARVIS is now running silently in your Windows background!
echo Look for the red reactor orb in your System Tray (taskbar bottom-right).
echo.
echo HOW TO USE:
echo 1. Say: "Hello JARVIS"
echo 2. JARVIS will respond: "Yes, how can I help?"
echo 3. Say any command:
echo    - "Open Chrome"
echo    - "Open WhatsApp"
echo    - "Open YouTube"
echo    - "Search Google for React tutorials"
echo    - "Search YouTube for Python tutorials"
echo    - "Open Downloads"
echo    - "Who are you?"
echo 4. Say: "Sleep JARVIS" to return to sleep mode.
echo.
echo Auto-start is enabled. JARVIS will start automatically every time
echo you turn on or log into your laptop.
echo.
echo To manage JARVIS, right-click the tray icon or run uninstall.bat.
echo =====================================================================
echo.
pause
