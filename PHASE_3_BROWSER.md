# JARVIS — Browser Agent & Playwright Automation (Step 4/6)

## 1. Overview

The **JARVIS Browser Agent** provides programmatic, DOM-based web automation using **Playwright**. Rather than relying on fragile mouse coordinates, it directly inspects and interacts with the browser's Document Object Model (DOM), accessibility trees, and JavaScript execution runtime.

```
                           USER (Voice / Command)
                                     │
                                     ▼
                           ┌───────────────────┐
                           │   AGENT KERNEL    │
                           │(Planner & Router) │
                           └─────────┬─────────┘
                                     │
                                     ▼
                           ┌───────────────────┐
                           │   TOOL REGISTRY   │
                           │  (browser.* tools)│
                           └─────────┬─────────┘
                                     │
                                     ▼
                           ┌───────────────────┐
                           │ PERMISSION ENGINE │ (READ_ONLY / LOW_RISK / CONFIRM / HIGH_RISK)
                           └─────────┬─────────┘
                                     │
                                     ▼
                           ┌───────────────────┐
                           │   BROWSER AGENT   │
                           │(Playwright Engine)│
                           └─────────┬─────────┘
                                     │
                                     ▼
                           ┌───────────────────┐
                           │ Chromium Browser  │ (Tabs, DOM, History, Screenshots)
                           └───────────────────┘
```

---

## 2. Browser Tools Reference

| Tool Name | Risk Level | Description |
| :--- | :--- | :--- |
| `browser.open(url)` | `LOW_RISK` | Launch browser and navigate to a URL. |
| `browser.navigate(url)` | `LOW_RISK` | Navigate active page to a new URL. |
| `browser.newTab(url)` | `LOW_RISK` | Open a new browser tab with optional URL. |
| `browser.closeTab(index)` | `LOW_RISK` | Close the active or indexed tab. |
| `browser.getTabs()` | `READ_ONLY` | Query all open tabs and active states. |
| `browser.getCurrentUrl()` | `READ_ONLY` | Return active URL and page title. |
| `browser.getPageTitle()` | `READ_ONLY` | Return title of current page. |
| `browser.readPage()` | `READ_ONLY` | Extract structured `{title, url, text, links, buttons, inputs}` without raw HTML bloat. |
| `browser.findText(text)` | `READ_ONLY` | Search for keyword/deadline snippet on page. |
| `browser.clickElement(selector)` | `CONFIRM` | Click a DOM element by role, label, text, or CSS selector. |
| `browser.typeIntoField(selector, text)` | `CONFIRM` | Fill text into an input or textarea. |
| `browser.selectOption(selector, value)` | `CONFIRM` | Select option from dropdown menu. |
| `browser.scroll(direction)` | `READ_ONLY` | Scroll page viewport up or down. |
| `browser.goBack()` | `LOW_RISK` | Go to previous page in navigation history. |
| `browser.goForward()` | `LOW_RISK` | Go forward in navigation history. |
| `browser.refresh()` | `LOW_RISK` | Reload active page. |
| `browser.screenshot()` | `READ_ONLY` | Capture base64 screenshot of browser view. |
| `browser.submitForm(selector)` | `CONFIRM` | Submit a form (gated with user confirmation). |

---

## 3. Safety & Permission Policies

1. **Passive Operations (`READ_ONLY`)**: `readPage`, `findText`, `search`, `getCurrentUrl`, `screenshot` execute immediately without confirmation.
2. **Standard Navigation (`LOW_RISK`)**: `open`, `navigate`, `newTab`, `closeTab`, `scroll`, `goBack`, `goForward` execute with auto-approval.
3. **Interactive Side-Effects (`CONFIRM`)**: `typeIntoField`, `clickElement`, `submitForm` require explicit confirmation if interacting with sensitive forms or external actions.
4. **High-Risk Guardrails (`HIGH_RISK`)**: Financial transactions, credential changes, file uploads, and account modifications require explicit double-check confirmation.
5. **No Password Storage**: Passwords and private credentials are NEVER sent to the LLM or persisted in memory.

---

## 4. Emergency Stop Integration

Calling `POST /api/kernel/stop` or speaking *"Jarvis, stop"* immediately triggers `browser_mgr.close_all()`, closing all active Playwright pages, browser contexts, and cancelling any background operations.
