# 🤖 JARVIS — Windows Desktop AI Voice Assistant & Computer Control

JARVIS is a hands-free, native Windows personal AI voice assistant powered by **Local Wake Word Detection ("Hello JARVIS")**, **Google Gemini AI**, **Native Windows Computer Automation**, and **Offline Windows SAPI5 Speech Synthesis**.

After installation, **JARVIS runs quietly in the Windows background**. You do **NOT** need to open PowerShell, Command Prompt, VS Code, or a browser website. Simply speak to your laptop.

---

## ⚡ Target Experience

```text
Turn ON laptop
       ↓
JARVIS starts automatically in background (no terminal window)
       ↓
You say: "Hello JARVIS"
       ↓
JARVIS wakes up and responds: "Yes, how can I help?"
       ↓
You say: "Open Chrome" / "Open WhatsApp" / "Search Google for React tutorials"
       ↓
JARVIS executes the action on Windows & confirms aloud
       ↓
You say: "Sleep JARVIS"
       ↓
JARVIS goes back to sleep mode
```

---

## 🚀 One-Click Installation & Setup

### 1. Configure `.env`
Ensure your `.env` file contains your Gemini API key:
```env
GEMINI_API_KEY=your_google_gemini_api_key
```

### 2. Run the Installer
Double-click **`install.bat`** (or run in CMD):
```cmd
install.bat
```

The installer will:
1. Check Python 3.10+.
2. Set up the virtual environment (`.venv`).
3. Install all required dependencies (`pip install -r backend/requirements.txt`).
4. Enable **Windows Auto-Start on Login** silently via user Startup folder (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\JARVIS_AutoStart.vbs`).
5. Launch JARVIS silently in the background.

---

## 🎙️ Voice Commands Guide

| Voice Command | Action Executed on Windows | Spoken Response |
| :--- | :--- | :--- |
| **"Hello JARVIS"** / **"Hey JARVIS"** | Wakes JARVIS from background sleeping state | *"Yes, how can I help?"* |
| **"Open Chrome"** | Launches `chrome.exe` on your desktop | *"Opening Chrome."* |
| **"Open WhatsApp"** | Launches WhatsApp Desktop (UWP Store app or web fallback) | *"Opening WhatsApp."* |
| **"Open YouTube"** | Opens `https://www.youtube.com` in default browser | *"Opening YouTube."* |
| **"Search Google for [query]"** | Opens browser and performs Google search | *"Searching Google for [query]."* |
| **"Search YouTube for [query]"** | Opens browser and performs YouTube video search | *"Searching YouTube for [query]."* |
| **"Open Downloads"** / **"Open Documents"** | Opens Windows File Explorer at that folder | *"Opened downloads folder."* |
| **"Take a screenshot"** | Captures active display screenshot | *"Screenshot captured."* |
| **"Who are you?"** / **General Questions** | Generates Gemini AI answer | Speaks answer aloud via TTS |
| **"Sleep JARVIS"** / **"Go to sleep"** | Returns to background sleeping mode | *"Okay, I'll sleep. Say Hello JARVIS when you need me."* |

---

## 🎛️ Windows Control Scripts

* **`install.bat`**: Full setup, dependency installation, and Windows startup activation.
* **`start_jarvis.bat`**: Starts JARVIS silently in the background (using `pythonw.exe`).
* **`stop_jarvis.bat`**: Terminates active background JARVIS processes.
* **`uninstall.bat`**: Disables Windows Auto-Start and stops background services (preserves code).

---

## 🖥️ System Tray Controls

When JARVIS is running, a glowing **Red Reactor Orb** appears in your Windows System Tray (taskbar bottom-right).

**Right-Click Menu Options:**
* **Status**: Displays `Ready` / `Listening` / `Activated`.
* **Start Listening**: Manually activates voice listening.
* **Pause Listening**: Temporarily pauses wake-word detector.
* **View Logs**: Opens `logs/jarvis.log` directly.
* **Open Dashboard (HUD)**: Opens the optional React Cyberpunk HUD if desired.
* **Exit JARVIS**: Cleanly terminates background daemon and releases audio devices.

---

## 🧪 Automated Testing

Run the full 62-test regression suite:
```cmd
.\.venv\Scripts\python.exe -m unittest tests/test_desktop_actions.py tests/test_wake_word.py tests/test_livekit_token.py tests/test_livekit_agent_tools.py tests/test_personal_assistant.py tests/test_personal_knowledge_vault.py tests/test_critical_rebuild.py tests/test_phase_integration.py
```

---

## 🔒 Security & Confirmation

* **Low-Risk Actions** (e.g. opening apps, searches, taking screenshots, reading info): Auto-approved and executed immediately.
* **High-Risk Actions** (e.g. deleting files, formatting, killing unknown processes): Prompt for voice/user confirmation before executing.
* **Privacy**: Local wake-word listener runs 100% locally on your machine without continuously transmitting audio to external clouds.
