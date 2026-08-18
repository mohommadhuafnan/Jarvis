# JARVIS AI — System Architecture & Multi-Agent Specifications

## 1. System Overview

JARVIS is designed as a **voice-first personal computer assistant and autonomous agent system**. It enables natural language computer control, screen perception, multi-step task execution, tool orchestration, and service integration while preserving local control and safety.

```
                                      🎤 USER (Voice / Keyboard)
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │   Speech Recognition  │ (Web Speech / Whisper)
                                     └───────────┬───────────┘
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │  JARVIS AI CORE BRAIN │ (Google Gemini Flash / Pro)
                                     └───────────┬───────────┘
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │     AGENT KERNEL      │ (Multi-Agent Planner & Router)
                                     └───────────┬───────────┘
                                                 │
         ┌───────────────────┬───────────────────┼───────────────────┬───────────────────┐
         ▼                   ▼                   ▼                   ▼                   ▼
 ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
 │ Computer Agent│   │ Research Agent│   │ Coding Agent  │   │  Files Agent  │   │ Comms Agent   │
 │ • App Launch  │   │ • Web Search  │   │ • Sandbox Run │   │ • Directory   │   │ • Gmail API   │
 │ • Mouse/Key   │   │ • Page Scrape │   │ • Node / Py   │   │ • Read/Write  │   │ • Calendar API│
 │ • Window HUD  │   │ • Summaries   │   │ • Git CLI     │   │ • Delete Gate │   │ • OAuth Sync  │
 │ • Screenshot  │   │ • Citations   │   │ • Stderr/out  │   │ • Transcode   │   │ • Draft Gates │
 └───────┬───────┘   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
         │                   │                   │                   │                   │
         └───────────────────┴───────────────────┼───────────────────┴───────────────────┘
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │     SAFETY LAYER      │ (READ_ONLY / LOW / CONFIRM / HIGH_RISK)
                                     └───────────┬───────────┘
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │  Execution Runtime    │ (Native Win32 / Subprocess / REST)
                                     └───────────────────────┘
```

---

## 2. Multi-Agent Hierarchy

1. **Master Orchestrator (JARVIS Brain)**: Evaluates user intent, breaks down complex instructions into sequential sub-plans, and delegates to specialized sub-agents.
2. **Computer Control Agent**:
   - Manages native desktop applications (`Chrome`, `VS Code`, `Notepad`, `Explorer`).
   - Simulates keyboard shortcuts, mouse clicks, scrolls, and window states (`minimize`, `maximize`, `focus`).
   - Captures screen frames for visual comprehension.
3. **Research Agent**:
   - Executes web queries via live search and DuckDuckGo/Google endpoints.
   - Extracts page snippets, validates sources, and formats concise answers.
4. **Coding & Terminal Agent**:
   - Executes scripts within an isolated subprocess sandbox.
   - Captures stdout/stderr, return codes, and execution durations.
   - Classifies commands into Safe, Confirm, and Dangerous tiers.
5. **Filesystem Agent**:
   - Manages workspace directory `/workspace` with safe path resolution preventing traversal attacks.
6. **Communication Agent**:
   - Handles Google OAuth token lifecycle.
   - Interacts with Gmail API and Google Calendar API.
   - Enforces confirmation gates before sending drafts or deleting calendar events.

---

## 3. Realtime Audio & Voice Pipeline

- **Wake Word Detection**: Client-side continuous keyword listener (*"Jarvis"*, *"Nova"*, *"Friday"*, *"Athena"*, *"Computer"*).
- **Speech-to-Text**: Streaming interim transcript updates shown in real-time.
- **Audio Feedback**: Procedural Web Audio API oscillator-based futuristic chimes and HUD sound FX.
- **Barge-In**: If the user begins speaking while JARVIS is speaking via TTS, speech synthesis immediately halts and transitions to `LISTENING`.

---

## 4. MongoDB Database & Persistence Architecture

The central persistence backbone is **MongoDB Atlas**, supporting 10 distinct collections:
- `users`: User identity and profile settings.
- `conversations` & `messages`: Threaded conversational state with role, timestamps, and tool metadata.
- `memories`: Long-term memory vault with semantic search and user preference tagging.
- `tasks`: Autonomous multi-step task lifecycle (`PLANNED`, `RUNNING`, `WAITING_CONFIRMATION`, `PAUSED`, `RECOVERING`, `COMPLETED`, `FAILED`, `CANCELLED`).
- `agent_runs` & `tool_executions`: Full agent run logs, arguments, and execution telemetry.
- `voice_sessions`: Session duration, language, and provider metrics without storing audio recordings.
- `preferences`: Key-value user configuration store.
- `audit_logs`: Gated security decisions, permission trails, and action history.

