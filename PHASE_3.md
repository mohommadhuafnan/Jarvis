# JARVIS — Phase 3 Multi-Agent Personal AI Specification

## 1. Phase 3 Overview

Phase 3 elevates JARVIS into a **multi-agent personal operating system**, orchestrating specialized sub-agents with centralized permissions, DOM browser automation via Playwright, live Gmail and Google Calendar integration, task planning, and emergency stop mechanisms.

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

## 2. Permission Levels

1. **`READ_ONLY`**: Zero confirmation required (`read_screen`, `read_email`, `search_web`, `list_events`, `read_file`).
2. **`LOW_RISK`**: Benign modifications (`open_application`, `create_task`, `store_memory`, `open_browser`).
3. **`CONFIRM`**: User confirmation required via Voice or HUD button (`send_email`, `create_event`, `form_submit`, `git_push`).
4. **`HIGH_RISK`**: Strict confirmation + double-check (`delete_file`, `delete_event`, `run_destructive_command`).

---

## 3. Specialized Agents

* **Computer Agent**: Native desktop app launches, window states, mouse/keyboard simulation, and screen frame perception.
* **Browser Agent**: DOM-based web navigation, page reading, element clicking, text extraction using Playwright.
* **Google Agent**: OAuth2 token lifecycle, Gmail reading/drafting/sending, Google Calendar events.
* **Coding Agent**: Isolated code runner with 5-second hard execution timeout and stdout/stderr capture.
* **Research Agent**: Web search, content scraping, and verified summaries.
* **File Agent**: Sandboxed workspace file operations with traversal attack prevention.
