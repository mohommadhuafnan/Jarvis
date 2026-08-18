# 🤖 JARVIS — Personal AI Computer Assistant & Autonomous Operating System

JARVIS is a futuristic, local-first personal AI computer assistant powered by **Google Gemini AI**, **Native Windows Automation**, **Playwright DOM Browser Automation**, **Google OAuth (Gmail & Calendar)**, and **Multi-Agent Task Orchestration**.

---

## 🎨 Cyberpunk Red HUD Architecture

* **Obsidian & Crimson Red Palette**: High-contrast cyberpunk hacker aesthetic.
* **Central Reactor Core (HUD Orb)**: Canvas-rendered multi-ring HUD reactor with targeting reticles and audio-reactive amplitude expansion.
* **Telemetry Bar**: Live CPU, RAM, Disk, System uptime, active `Gemini Flash` model, and real-time digital clock.
* **Task Workspace**: `CURRENT TASK` progress checklist (`0% -> 100%`) with live multi-step execution tracking and timestamped `ACTIVITY FEED`.
* **Voice Pipeline**: Local wake-word keyword detector (*"Jarvis"*, *"Nova"*, *"Friday"*, *"Athena"*, *"Computer"*), Web Speech API, and **100% Google Gemini Voice Core** with instant **Barge-In voice interruption**.

---

## 🛡️ Multi-Agent Architecture & Tool Registry

```
                         USER (Voice / Text)
                                  │
                                  ▼
                         🎤 VOICE PIPELINE
                   (Wake Word / Gemini Audio)
                                  │
                                  ▼
                        🧠 GEMINI AI BRAIN
                      (gemini-flash-latest)
                                  │
                                  ▼
                        ┌──────────────────┐
                        │   AGENT KERNEL   │
                        │ Multi-Step Router│
                        └─────────┬────────┘
                                  │
         ┌────────────────┬───────┴────────┬────────────────┬────────────────┐
         ▼                ▼                ▼                ▼                ▼
   ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
   │ Computer  │    │  Browser  │    │  Google   │    │  Coding   │    │  Files &  │
   │   Agent   │    │   Agent   │    │   Agent   │    │   Agent   │    │  Memory   │
   │ • App Win │    │•Playwright│    │•Gmail API │    │ • Sandbox │    │ • FS Gate │
   │ • Mouse/KB│    │•DOM scrape│    │•Calendar  │    │ • Test/Py │    │ • Vault   │
   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
         │                │                │                │                │
         └────────────────┴───────┬────────┴────────────────┴────────────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │  PERMISSION ENGINE  │ (READ_ONLY / LOW / CONFIRM / HIGH_RISK)
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │   TOOL EXECUTION    │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │  VOICE RESPONSE     │ (Gemini Live Audio Synthesis)
                       └─────────────────────┘
```

---

## 🛠️ Specialized Agents & Tools

### 1. Computer Control Agent (`computer_tools.py`)
- `computer.openApplication(application)`: Launch whitelisted system applications.
- `computer.closeApplication(application)`: Close running applications.
- `computer.focusApplication(window_title)`: Bring target window to the front.
- `computer.minimizeWindow()` & `computer.maximizeWindow()`: Window viewport controls.
- `computer.moveMouse(x, y)`, `computer.click()`, `computer.typeText(text)`, `computer.pressKey(key)`, `computer.hotkey(keys)`, `computer.scroll(clicks)`: PyAutoGUI hardware simulation.
- `computer.takeScreenshot()`: Captures display framebuffer.
- `computer.analyzeScreen(prompt)`: Multimodal visual grounding via **Google Gemini Vision**.

### 2. Browser Agent (`browser_tools.py`)
- Powered by **Playwright DOM Automation**:
  - `browser.open(url)`: Navigate to web pages.
  - `browser.search(query)`: Search web and extract top result URLs.
  - `browser.readPage()`: Extract readable text and title from the active DOM.
  - `browser.findText(text)`: Search for keywords and deadlines on active pages.
  - `browser.clickElement(selector)`: Click buttons or links by text/selector.
  - `browser.typeIntoField(selector, text)`: Fill input forms.
  - `browser.scroll(direction)`: Scroll viewport up/down.

### 3. Google Services Agent (`email_tools.py` & `calendar_tools.py`)
- **OAuth 2.0 Project**: `argon-system-505908-p2`
- **Gmail Tools**: `email.read`, `email.draft`, `email.send` (gated with confirmation).
- **Calendar Tools**: `calendar.getEvents`, `calendar.createEvent`, `calendar.updateEvent`, `calendar.deleteEvent`.

### 4. Coding & Sandbox Agent (`code_sandbox.py`)
- Isolated Python and Node.js code runner with **5-second hard execution timeout**, capturing stdout, stderr, and return codes.

### 5. Memory & Cloud Persistence Layer (`mongodb.py` & `memory_service.py`)
- **MongoDB Atlas Cloud Database**: Enterprise-grade persistence layer supporting 10 core collections (`users`, `conversations`, `messages`, `memories`, `tasks`, `agent_runs`, `tool_executions`, `voice_sessions`, `preferences`, `audit_logs`).
- **Autonomous Task State Recovery**: Recovers and continues interrupted task plans across server restarts.
- **Audit Trails & Security Redaction**: Full telemetry logging with automated masking of credentials, tokens, and keys.
- **Dual-Driver Architecture**: Native support for Python (`pymongo`) and Node.js (`mongodb` official driver).


---

## 🚀 Quick Launch

### Run on Windows
Double-click `start.bat` in `c:\Users\PC\Desktop\JARVIS`.

### Or Run via Terminal
```bash
# Terminal 1: Backend
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open your browser at: **`http://localhost:5173/`**
