# JARVIS — Google Calendar Agent & OAuth Integration (Step 8)

## 1. Overview

The **JARVIS Google Calendar Agent** provides secure, voice- and text-driven calendar orchestration powered by the **Google Calendar API** and **OAuth 2.0 Project `argon-system-505908-p2`** using scope `https://www.googleapis.com/auth/calendar`.

```
                           USER (Voice / Text)
                                    │
                                    ▼
                           ┌──────────────────┐
                           │   AGENT KERNEL   │
                           │(Planner & Router)│
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │  TOOL REGISTRY   │
                           │(calendar.* tools)│
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │PERMISSION ENGINE │ (READ_ONLY / CONFIRM / HIGH_RISK)
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │  CALENDAR AGENT  │
                           │ (OAuth Gateway)  │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │Google Calendar AP│ (argon-system-505908-p2)
                           └──────────────────┘
```

---

## 2. Google OAuth Configuration

* **Project ID**: `argon-system-505908-p2`
* **Client ID**: `715850947465-ktgkms9h9bta4ojuugh9n2or3c5h87go.apps.googleusercontent.com`
* **Authorized Scopes**: `https://www.googleapis.com/auth/calendar` + `https://www.googleapis.com/auth/gmail.modify`
* **Unified OAuth Gateway**: Shared token storage in SQLite `oauth_tokens` table.

---

## 3. Registered Calendar Tools

| Tool Name | Permission Level | Description |
| :--- | :--- | :--- |
| `calendar.listCalendars()` | `READ_ONLY` | Lists user's primary and secondary calendars with timezones. |
| `calendar.listEvents(days_ahead, date)` | `READ_ONLY` | Fetches schedule and detects timing conflicts. |
| `calendar.getEvents(days_ahead)` | `READ_ONLY` | Compatibility alias for retrieving upcoming events. |
| `calendar.getEvent(event_id)` | `READ_ONLY` | Retrieves full metadata for a specific event. |
| `calendar.checkAvailability(time_query)` | `READ_ONLY` | Evaluates schedule matrix for a specific time (e.g. 5 PM). |
| `calendar.findFreeTime(date)` | `READ_ONLY` | Computes open windows and meeting slots. |
| `calendar.createEvent(title, start_time, ...)` | `CONFIRM` | Schedules a new event (requires explicit user confirmation). |
| `calendar.updateEvent(event_id, title, ...)` | `CONFIRM` | Reschedules/moves an existing event (requires confirmation). |
| `calendar.deleteEvent(event_id)` | `HIGH_RISK` | Cancels/deletes an event (requires HIGH_RISK confirmation dialog). |

---

## 4. Multi-Agent & Cross-Agent Coordination

1. **Calendar + Gmail Workflows**: Multi-step plans extract meeting subjects/attendees and query relevant Gmail threads automatically without human intervention.
2. **Natural Language Timezone Engine**: Interprets relative expressions (*"today"*, *"tomorrow 3 PM"*, *"in two hours"*) against the user's local timezone (`Asia/Kolkata`).
3. **Emergency Stop & Security**: All operations adhere to Kernel-level aborts (`POST /api/kernel/stop`) and never persist credentials into AI memory or prompt templates.
