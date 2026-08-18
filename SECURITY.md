# JARVIS AI — Security & Privacy Architecture

## 1. Safety Principles

JARVIS treats the Large Language Model as an **untrusted planner**. The AI model can propose tool names and argument payloads, but the **Agent Kernel and Safety Layer** determine whether an action is permitted and whether user confirmation is required.

---

## 2. Tool Risk Classification Matrix

| Permission Level | Description | Confirmation Required | Example Tools |
| :--- | :--- | :--- | :--- |
| **READ_ONLY** | Passive data retrieval without system state change | No | `system.getTime`, `tasks.list`, `calendar.getEvents`, `email.read`, `web.search`, `computer.takeScreenshot` |
| **LOW_RISK** | Benign workspace modifications | No | `tasks.create`, `memory.store`, `files.read`, `files.create` (in `/workspace`) |
| **CONFIRM** | External communications or state modifications | **Yes (Voice or UI Click)** | `email.send`, `calendar.createEvent`, `files.move`, `computer.openApplication` |
| **HIGH_RISK** | Destructive actions, arbitrary execution, shell commands | **Strict Confirmation + Audit Log** | `files.delete`, `code.run`, `terminal.runCommand`, `system.config` |

---

## 3. Sandboxing & Isolation

1. **Filesystem Sandbox**: All file modifications are restricted to the local workspace root (`/workspace`). Path traversal sequences (`../`, `..\\`) are resolved and rejected.
2. **Code Execution Sandbox**: Python and Node.js code runs in isolated subprocesses with a **5-second hard execution timeout**, memory limits, and isolated current working directories.
3. **Computer Control Whitelist**: Application launching is strictly restricted to an approved whitelist of executables.
4. **Credential Isolation**: Secrets (`GEMINI_API_KEY`, `GOOGLE_CLIENT_SECRET`, `MONGODB_URI`, OAuth tokens) are stored exclusively in server-side `.env` and local encrypted stores, never exposed to the frontend client or raw logs.
5. **MongoDB Payload Sanitization (`sanitize_payload`)**: All data written to `agent_runs` and `audit_logs` is recursively scrubbed to mask connection URIs, API keys, passwords, and tokens.
6. **Restricted Database Access**: The LLM is never given direct arbitrary query access or `db.runCommand()`. All database interactions strictly route through validated service layer functions (`MemoryService`, `TaskService`, `ConversationService`, `AuditService`).


---

## 4. Emergency Stop & Voice Interrupt

- **Voice Barge-In**: Speaking at any moment halts active TTS output and triggers `LISTENING` mode.
- **Cancel Commands**: Speaking *"Jarvis, stop"*, *"Cancel"*, or *"Abort"* immediately cancels running tasks.
