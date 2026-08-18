# JARVIS — Advanced Multi-Agent Orchestrator & Agent Registry (Step 9)

## 1. Overview

The **JARVIS Multi-Agent Orchestrator** transforms JARVIS from a single-command assistant into an **autonomous multi-agent operating system**. It parses high-level user directives, plans sequential multi-step task workflows, dispatches sub-tasks to 7 specialized agents, validates intermediary tool results, and handles runtime failures with dynamic fallback recovery.

```
                           USER (Voice / Text)
                                    │
                                    ▼
                           ┌──────────────────┐
                           │   GEMINI BRAIN   │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │   AGENT KERNEL   │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │   ORCHESTRATOR   │
                           │  (Task Planner)  │
                           └────────┬─────────┘
                                    │
         ┌───────────────┬──────────┴─────┬───────────────┬───────────────┐
         ▼               ▼                ▼               ▼               ▼
   ┌───────────┐   ┌───────────┐    ┌───────────┐   ┌───────────┐   ┌───────────┐
   │ Computer  │   │  Browser  │    │   Gmail   │   │ Calendar  │   │  Coding/  │
   │   Agent   │   │   Agent   │    │   Agent   │   │   Agent   │   │   File    │
   │(Win32/GUI)│   │(Playwright│    │  (OAuth)  │   │  (OAuth)  │   │ (Sandbox) │
   └─────┬─────┘   └─────┬─────┘    └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
         │               │                │               │               │
         └───────────────┴──────────┬─────┴───────────────┴───────────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │PERMISSION ENGINE │ (READ_ONLY / LOW / CONFIRM / HIGH_RISK)
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │  TOOL EXECUTION  │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │RESULT VALIDATION │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │ VOICE & HUD CORE │
                           └──────────────────┘
```

---

## 2. Centralized Agent Registry (`agent_registry.py`)

| Agent Name | Category | Tool Count | Capabilities | Health Status |
| :--- | :--- | :--- | :--- | :--- |
| **`ComputerAgent`** | `computer` | 13 | App launch/close, window management, PyAutoGUI mouse/keyboard simulation, Gemini Multimodal Screen Vision | **HEALTHY** |
| **`BrowserAgent`** | `browser` | 19 | Playwright DOM navigation, multi-tab sessions, text search, form filling, web scraping | **HEALTHY** |
| **`GmailAgent`** | `google` | 8 | OAuth inbox scanning, thread-safe replies, drafting, prompt-injection defense | **HEALTHY** |
| **`CalendarAgent`** | `google` | 9 | Google Calendar event management, conflict matrix, availability, free-time windows | **HEALTHY** |
| **`FileAgent`** | `files` | 6 | Local workspace file reading/writing, persistent semantic memory vault in SQLite | **HEALTHY** |
| **`CodingAgent`** | `coding` | 2 | Isolated subprocess code execution sandbox (Python/JS) with hard 5s timeout | **HEALTHY** |
| **`ResearchAgent`** | `research` | 2 | Web indexing, multi-source verification, knowledge synthesis | **HEALTHY** |

---

## 3. Orchestration Lifecycle

1. **Directive Parsing**: User voice command is parsed and tokenized.
2. **Multi-Agent Task Planning**: Intent classifier generates an ordered list of `TaskStep` definitions.
3. **Pre-Execution Permission Gating**: Before executing any tool, `permission_engine.check_permission` evaluates risk levels (`READ_ONLY`, `LOW_RISK`, `CONFIRM`, `HIGH_RISK`). If user confirmation is required, execution pauses and emits `confirmation_required: true`.
4. **Step-by-Step Execution**: Specialized tools are invoked with structured argument validation.
5. **Dynamic Fallback Recovery**: If a tool fails (e.g. network timeout or DOM selector mismatch), the orchestrator catches the exception, logs diagnostic details, and selects an alternative strategy.
6. **Unified Synthesis**: Multi-agent outputs are aggregated into a single natural language briefing and synthesized via Google Gemini Voice.
