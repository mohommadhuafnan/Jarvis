# 🤖 JARVIS — Personal AI Computer Assistant & Autonomous Operating System

JARVIS is a futuristic, local-first personal AI computer assistant powered by **LiveKit Cloud Realtime WebRTC**, **Google Gemini Live Voice AI**, **Native Windows Automation**, **Playwright DOM Browser Automation**, **Google OAuth (Gmail & Calendar)**, and **Multi-Agent Task Orchestration**.

---

## ⚡ LiveKit Cloud + Gemini Realtime Voice Integration

JARVIS v3.0 features high-fidelity, ultra-low latency, bidirectional speech-to-speech intelligence powered by **LiveKit Cloud** and **Gemini Live API**:

1. **LiveKit Cloud WebRTC Streaming**: Direct bi-directional audio transport between the browser and LiveKit Cloud (`wss://jarvis-33vlibgi.livekit.cloud`).
2. **Gemini Live Realtime Voice Model**: Instant speech reasoning with natural vocal inflections, sub-second latency, and natural turn-taking.
3. **Hardware-Accelerated Voice Activity Detection (VAD) & Barge-In**: Instant interruption support—when the user speaks, JARVIS immediately ceases speaking and processes the new instruction.
4. **Autonomous Function Tools Bridge**: LiveKit Agent executes local computer tools, browser navigation, calendar scheduling, Gmail, code sandbox, and memory retrieval with strict permission gating (`READ_ONLY`, `LOW_RISK`, `CONFIRM`, `HIGH_RISK`).
5. **Secure Server-Side Token Generation**: Frontend connects via short-lived JWT tokens minted by `/api/livekit/token` without exposing API secrets or keys to client bundles.

---

## 🎨 Cyberpunk Red HUD Architecture

* **Obsidian & Crimson Red Palette**: High-contrast cyberpunk hacker aesthetic.
* **Central Reactor Core (HUD Orb)**: Canvas-rendered multi-ring HUD reactor with targeting reticles and real-time audio-reactive amplitude expansion driven directly by WebRTC stream frequencies.
* **Telemetry Bar**: Live CPU, RAM, Disk, System uptime, active `Gemini Flash` model, and real-time digital clock.
* **Task Workspace**: `CURRENT TASK` progress checklist (`0% -> 100%`) with live multi-step execution tracking and timestamped `ACTIVITY FEED`.
* **Voice Pipeline**: Always-ready hands-free LiveKit WebRTC channel with fallback to local STT/TTS engine.

---

## 🛡️ Realtime Voice & Multi-Agent Architecture

```
                 USER (Mic Audio & WebRTC Stream)
                                │
                                ▼
                   ┌─────────────────────────┐
                   │  FRONTEND CYBERPUNK HUD │ (React 19 + LiveKit Client)
                   └────────────┬────────────┘
                                │  WebRTC Audio (Opus)
                                ▼
                   ┌─────────────────────────┐
                   │   LIVEKIT CLOUD ROOM    │ (wss://jarvis-33vlibgi.livekit.cloud)
                   └────────────┬────────────┘
                                │  Bi-directional Realtime Audio Stream
                                ▼
                   ┌─────────────────────────┐
                   │   JARVIS VOICE AGENT    │ (backend/agent.py)
                   │  google.realtime.Model  │ (Gemini 2.5 Flash / Voice: Puck)
                   └────────────┬────────────┘
                                │
                                ▼
                   ┌─────────────────────────┐
                   │   LIVEKIT TOOLS BRIDGE  │ (backend/voice/livekit_tools.py)
                   └────────────┬────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
   ┌───────────┐          ┌───────────┐          ┌───────────┐
   │ Computer  │          │  Browser  │          │  Google   │
   │   Agent   │          │   Agent   │          │   Agent   │
   │ • App Win │          │•Playwright│          │•Gmail API │
   │ • Mouse/KB│          │•DOM scrape│          │•Calendar  │
   └─────┬─────┘          └─────┬─────┘          └─────┬─────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  PERMISSION ENGINE  │ (READ_ONLY / LOW / CONFIRM / HIGH_RISK)
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │   TOOL EXECUTION    │ (Structured { success, result, error })
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  MONGODB AUDIT LOG  │ (MongoDB Atlas Telemetry)
                     └─────────────────────┘
```

---

## 🚀 Quick Start

### 1. Configure Environment Variables
Copy `.env.example` to `.env` and configure your API keys:
```bash
# LiveKit Cloud Credentials
LIVEKIT_URL=wss://jarvis-33vlibgi.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 2. Launch JARVIS Command Center (One-Click)
Run `start.bat` to launch all 3 subsystems simultaneously:
```cmd
start.bat
```
This automatically boots:
1. **JARVIS AI Core Backend** on `http://localhost:8000`
2. **JARVIS LiveKit Voice Agent** connected to LiveKit Cloud WebRTC
3. **JARVIS Cyberpunk HUD Frontend** on `http://localhost:5173`

### 3. Or Launch Subsystems Individually

#### Start AI FastAPI Backend:
```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

#### Start LiveKit Agent Worker:
```bash
python backend/agent.py dev
```

#### Start Frontend HUD:
```bash
npm --prefix frontend run dev
```

---

## 🧪 Testing & Verification

Run automated test suites:
```bash
# Test LiveKit token generation and agent tool execution bridge
npm run test:livekit

# Or run full unit test suite
python -m unittest tests/test_livekit_token.py tests/test_livekit_agent_tools.py tests/test_personal_assistant.py tests/test_personal_knowledge_vault.py tests/test_critical_rebuild.py
```

---

## 🔒 Security & Safe Execution Rules

1. **Structured Tool Returns**: Every tool executed by Gemini Live returns `{"success": true/false, "result": ..., "error": ...}`. Gemini never hallucinates tool success.
2. **Permission Engine**: Sensitive actions (`HIGH_RISK` / `CONFIRM` like deleting files or sending external messages) require explicit confirmation.
3. **Secret Protection**: `LIVEKIT_API_SECRET`, `GOOGLE_API_KEY`, and OAuth tokens are strictly processed server-side and never exposed to the frontend.
