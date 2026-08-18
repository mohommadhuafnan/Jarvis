# JARVIS — MongoDB Database Architecture & Persistence Layer

## 1. Overview
The JARVIS MongoDB integration establishes an enterprise-grade cloud persistence layer built directly on **MongoDB Atlas** using the official drivers for both Python (`pymongo` with connection pooling) and Node.js (`mongodb` official driver).

MongoDB persists:
- Long-term contextual memory
- Multi-agent autonomous task plans and state transitions
- Chronological conversational dialogues and tool calls
- Comprehensive audit trails and agent execution logs
- User personalization preferences
- Voice session telemetry

```mermaid
flowchart TD
    User([User Voice / Text]) --> VoiceEngine[Voice Engine / Web Speech]
    VoiceEngine --> Gemini[Google Gemini AI Core]
    Gemini --> AgentKernel[Agent Kernel]
    AgentKernel --> PermissionEngine{Permission Engine}
    PermissionEngine -->|Safe / Approved| MultiAgentOrchestrator[Multi-Agent Orchestrator]
    MultiAgentOrchestrator --> SpecializedAgents[Specialized Agents\nComputer | Browser | Gmail | Calendar | Coding | Research]
    SpecializedAgents --> ServiceLayer[Service & Repository Layer]
    ServiceLayer --> MongoPool[(MongoClient Connection Pool)]
    MongoPool --> Atlas[(MongoDB Atlas Cluster: jarvis)]
    
    subgraph Collections [MongoDB Database: jarvis]
        Atlas --> C1[users]
        Atlas --> C2[conversations & messages]
        Atlas --> C3[memories]
        Atlas --> C4[tasks]
        Atlas --> C5[agent_runs & tool_executions]
        Atlas --> C6[voice_sessions]
        Atlas --> C7[preferences]
        Atlas --> C8[audit_logs]
    end
```

---

## 2. Collections & Schema Reference

### 1. `memories`
Stores permanent facts, preferences, and project context.
```json
{
  "id": "mem_a1b2c3d4",
  "userId": "RAVIT",
  "type": "user_preference",
  "key": "main_project",
  "value": "AgriMind AI",
  "source": "conversation",
  "tags": ["user_preference", "main_project"],
  "createdAt": "2026-08-18T10:00:00.000Z",
  "updatedAt": "2026-08-18T10:00:00.000Z"
}
```

### 2. `tasks`
Stores autonomous multi-step task state and allows recovery after restart.
```json
{
  "taskId": "TASK-2026-00123",
  "objective": "Project Testing",
  "description": "Verify autonomous MongoDB persistence",
  "status": "RUNNING",
  "progress": 64,
  "currentStep": "Running tests",
  "agent": "CodingAgent",
  "priority": "high",
  "deadline": "2026-08-25",
  "tags": ["autonomous", "codingagent"],
  "createdAt": "2026-08-18T10:00:00.000Z",
  "updatedAt": "2026-08-18T10:01:00.000Z"
}
```
**Supported States**: `PLANNED`, `RUNNING`, `WAITING_CONFIRMATION`, `PAUSED`, `RECOVERING`, `COMPLETED`, `FAILED`, `CANCELLED`.

### 3. `conversations` & `messages`
Maintains conversational threads and chronological message history.
- `conversations`:
```json
{
  "conversationId": "conv_78a9c0e2",
  "userId": "RAVIT",
  "startedAt": "2026-08-18T10:00:00.000Z",
  "updatedAt": "2026-08-18T10:05:00.000Z",
  "status": "active"
}
```
- `messages`:
```json
{
  "conversationId": "conv_78a9c0e2",
  "role": "user",
  "content": "Jarvis, remember that my main project is AgriMind AI.",
  "timestamp": "2026-08-18T10:00:01.000Z",
  "metadata": {},
  "tool_calls": []
}
```

### 4. `agent_runs` & `tool_executions`
Logs each agent action with inputs, execution status, and results (with automated secret sanitization).
```json
{
  "runId": "run_9f8e7d6c",
  "taskId": "TASK-2026-00123",
  "agent": "ComputerAgent",
  "tool": "computer.openApplication",
  "argumentsSummary": { "application": "terminal" },
  "status": "COMPLETED",
  "startedAt": "2026-08-18T10:00:00.000Z",
  "completedAt": "2026-08-18T10:00:02.000Z",
  "resultSummary": { "success": true }
}
```

### 5. `audit_logs`
Records security and risk-level permission checks.
```json
{
  "timestamp": "2026-08-18T10:00:00.000Z",
  "taskId": "TASK-2026-00123",
  "agent": "GmailAgent",
  "tool": "gmail.send",
  "riskLevel": "CONFIRM",
  "permissionDecision": "APPROVED",
  "status": "success",
  "details": { "recipient": "commander@jarvis.ai" }
}
```

### 6. `preferences`
Stores key-value user personalization attributes.
```json
{
  "userId": "RAVIT",
  "key": "preferredLanguage",
  "value": "English",
  "updatedAt": "2026-08-18T10:00:00.000Z"
}
```

### 7. `voice_sessions`
Captures voice interaction metadata without storing raw audio recordings.
```json
{
  "sessionId": "vsession_1234abcd",
  "conversationId": "conv_78a9c0e2",
  "startedAt": "2026-08-18T10:00:00.000Z",
  "endedAt": "2026-08-18T10:03:00.000Z",
  "language": "en",
  "provider": "Google Gemini Live Audio",
  "status": "completed"
}
```

---

## 3. Indexes Reference

| Collection | Indexed Fields | Options |
|---|---|---|
| `conversations` | `conversationId` (ASC), `userId` (ASC), `updatedAt` (DESC) | `unique: true, sparse: true` on `conversationId` |
| `messages` | `(conversationId, timestamp)` (ASC), `timestamp` (DESC) | Compound index for rapid chronological retrieval |
| `memories` | `(userId, key)` (ASC), `type` (ASC), `updatedAt` (DESC) | Search & entity lookup acceleration |
| `tasks` | `taskId` (ASC), `status` (ASC), `updatedAt` (DESC) | `unique: true, sparse: true` on `taskId` |
| `agent_runs` | `taskId` (ASC), `startedAt` (DESC), `runId` (ASC) | Telemetry sorting |
| `audit_logs` | `taskId` (ASC), `timestamp` (DESC), `riskLevel` (ASC) | Security audit trail index |
| `preferences` | `(userId, key)` (ASC) | `unique: true` constraint |
| `voice_sessions`| `sessionId` (ASC), `startedAt` (DESC) | `unique: true, sparse: true` on `sessionId` |
| `users` | `userId` (ASC) | `unique: true, sparse: true` |

---

## 4. Connection Pooling & Performance

1. **Singleton Client**: `get_mongo_client()` instantiates a single `MongoClient` pool (`maxPoolSize=50`, `minPoolSize=5`) that persists throughout application lifecycle.
2. **DNS Fallback Resolution**: Configured with `8.8.8.8` / `1.1.1.1` fallback resolvers to ensure instantaneous SRV resolution across all platforms.
3. **Health Check Endpoint**:
   - `GET /api/health/database`
   - Executes real `{ "ping": 1 }` against admin database and returns latency:
   ```json
   {
     "database": "mongodb",
     "status": "connected",
     "latency_ms": 124.5,
     "database_name": "jarvis"
   }
   ```

---

## 5. Security & Secret Redaction

- **Zero-Exposure Policy**: Sensitive tokens (`MONGODB_URI`, passwords, OAuth secrets, API keys) are masked before printing or logging.
- **`sanitize_payload()`**: Recursively scrubs credentials before writing to `agent_runs` or `audit_logs`.
- **Permission Matrix**: All database operations route strictly through `PermissionEngine.check_permission()`.
