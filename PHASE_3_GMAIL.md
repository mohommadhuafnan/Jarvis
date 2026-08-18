# JARVIS — Gmail Agent & Google OAuth Integration (Step 7)

## 1. Overview

The **JARVIS Gmail Agent** enables secure, voice- and command-controlled email management powered by the **Google Gmail API** and **OAuth 2.0 Project `argon-system-505908-p2`**. 

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
                           │ (gmail.* tools)  │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │PERMISSION ENGINE │ (READ_ONLY / LOW_RISK / CONFIRM)
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │   GMAIL AGENT    │
                           │(OAuth Gateway)   │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │ Google Gmail API │ (argon-system-505908-p2)
                           └──────────────────┘
```

---

## 2. Google OAuth Configuration

* **Project ID**: `argon-system-505908-p2`
* **Client ID**: `715850947465-ktgkms9h9bta4ojuugh9n2or3c5h87go.apps.googleusercontent.com`
* **Authorized Scope**: `https://www.googleapis.com/auth/gmail.modify`
* **Server-Side Token Storage**: SQLite `oauth_tokens` table. Credentials and access tokens are strictly server-side and never exposed to the frontend or sent inside LLM prompts.

---

## 3. Registered Gmail Tools

| Tool Name | Permission Level | Description |
| :--- | :--- | :--- |
| `gmail.getUnreadEmails(max_results)` | `READ_ONLY` | Retrieves unread messages with headers and snippets. |
| `gmail.searchEmails(query)` | `READ_ONLY` | Searches inbox using queries (`is:unread`, `from:...`, `subject:...`). |
| `gmail.getEmail(message_id)` | `READ_ONLY` | Extracts sanitized email body with attachment metadata. |
| `gmail.createDraft(recipient, subject, body)` | `LOW_RISK` | Creates and saves a draft without sending. |
| `gmail.reply(recipient, body, thread_id)` | `CONFIRM` | Prepares a reply preserving message thread relationship. |
| `gmail.send(recipient, subject, body)` | `CONFIRM` | Sends an email (Mandatory user confirmation required). |
| `gmail.archive(message_id)` | `LOW_RISK` | Archives an email message. |
| `gmail.addLabel(message_id, label)` | `LOW_RISK` | Applies a label tag to an email. |

---

## 4. Security & Prompt Injection Protection

1. **Untrusted Data Delimitation**: All email body content is automatically wrapped in `<untrusted_email_data>...</untrusted_email_data>` tags before reasoning. The LLM treats email text strictly as data, neutralizing any embedded prompt-injection instructions.
2. **Mandatory Confirmation on Send**: `gmail.send` and `gmail.reply` cannot execute without explicit confirmation from the user (via the HUD confirmation dialog or voice confirmation).
3. **No Automatic Attachment Execution**: Attachments are represented purely by metadata (`filename`, `mimeType`, `size`).
4. **Token Isolation**: No refresh tokens or OAuth secrets enter logs, memory graphs, or external requests.
