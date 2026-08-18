import re
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class TaskStep(BaseModel):
    id: int
    description: str
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = {}
    completed: bool = False

class TaskPlan(BaseModel):
    title: str
    agent_category: str
    is_multi_step: bool
    steps: List[TaskStep]
    estimated_duration_seconds: float = 1.0

class TaskPlanner:
    def __init__(self):
        pass

    def plan_task(self, user_command: str) -> TaskPlan:
        lower = user_command.lower().strip()
        clean_lower = re.sub(r'[^\w\s]', '', lower).strip()

        # 0. Emergency Stop Intent
        if clean_lower in ["stop", "jarvis stop", "stop jarvis", "halt", "emergency stop", "abort"] or clean_lower.endswith(" stop"):
            steps = [
                TaskStep(id=1, description="Triggering system emergency stop", tool_name="system.getDiagnostics", arguments={})
            ]
            return TaskPlan(title="Emergency Stop", agent_category="system", is_multi_step=False, steps=steps)

        # 0.4. WhatsApp Intent
        if "whatsapp" in lower:
            if any(w in lower for w in ["send", "message", "tell", "text"]):
                # Extract recipient and message text
                recip = "Contact"
                msg_text = "Hello"
                m = re.search(r'(?:to|contact)\s+([a-zA-Z0-9_\+]+)\s+(?:saying|that|with message|message)\s+(.*)', user_command, flags=re.I)
                if m:
                    recip = m.group(1).strip()
                    msg_text = m.group(2).strip().strip("'\"")
                elif " to " in lower:
                    parts = user_command.split(" to ", 1)[1].split(" ", 1)
                    recip = parts[0].strip()
                    msg_text = parts[1].strip() if len(parts) > 1 else "Hello"

                steps = [
                    TaskStep(id=1, description=f"Preparing WhatsApp message for {recip}", tool_name=None),
                    TaskStep(id=2, description=f"Requesting confirmation to send WhatsApp message to {recip} [CONFIRM]", tool_name="whatsapp.send_message", arguments={"recipient": recip, "message": msg_text}),
                    TaskStep(id=3, description="Dispatching via WhatsApp gateway", tool_name=None)
                ]
                return TaskPlan(title=f"WhatsApp: Send Message to {recip} [CONFIRM]", agent_category="computer", is_multi_step=False, steps=steps)
            else:
                steps = [
                    TaskStep(id=1, description="Launching WhatsApp Desktop application", tool_name="whatsapp.open", arguments={})
                ]
                return TaskPlan(title="WhatsApp: Launch Desktop App", agent_category="computer", is_multi_step=False, steps=steps)

        # 0.5. Memory Store Intent ("Remember that...", "Remember my...")
        if lower.startswith("remember") or "remember that" in lower:
            clean = re.sub(r'^(jarvis\s*,?\s*)?remember(\s+that)?\s+', '', user_command, flags=re.I).strip()
            key = "fact"
            value = clean
            category = "preferences"

            if " is " in clean:
                parts = clean.split(" is ", 1)
                key = re.sub(r'^(my\s+|the\s+)', '', parts[0], flags=re.I).strip().replace(' ', '_')
                value = parts[1].strip()
                if "project" in key.lower():
                    category = "projects"
            elif " are " in clean:
                parts = clean.split(" are ", 1)
                key = re.sub(r'^(my\s+|the\s+)', '', parts[0], flags=re.I).strip().replace(' ', '_')
                value = parts[1].strip()

            steps = [
                TaskStep(id=1, description=f"Storing '{key}' in long-term memory vault", tool_name="memory.store", arguments={"key": key, "value": value, "category": category}),
                TaskStep(id=2, description="Synchronizing with MongoDB vault", tool_name=None)
            ]
            return TaskPlan(title=f"Memory: Store '{key}'", agent_category="system", is_multi_step=False, steps=steps)

        # 0.6. Memory Recall Intent ("What is my...", "What's my...", "Who is my...")
        if any(w in lower for w in ["what is my", "what's my", "who is my", "recall my", "what project", "tell me about my project", "what did i ask"]):
            query = re.sub(r'^(what\s+is\s+my|what\'s\s+my|who\s+is\s+my|recall\s+my|tell\s+me\s+about\s+my)\s+', '', lower).strip()
            steps = [
                TaskStep(id=1, description=f"Querying memory vault for '{query}'", tool_name="memory.search", arguments={"query": query or "project"}),
                TaskStep(id=2, description="Formatting memory recall for voice synthesis", tool_name=None)
            ]
            return TaskPlan(title=f"Memory: Recall '{query}'", agent_category="system", is_multi_step=False, steps=steps)

        # 0.7. Reminders Intent ("Remind me at 8 PM to work on AgriMind", "Set a reminder...")
        if lower.startswith("remind") or "remind me" in lower or "set a reminder" in lower:
            time_match = re.search(r'(?:at|for|by)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\d{1,2}\s*(?:am|pm)|tomorrow|tonight)', user_command, flags=re.I)
            remind_time = time_match.group(1).strip() if time_match else "later today"
            
            clean_remind = re.sub(r'^(jarvis\s*,?\s*)?(remind\s+me|set\s+a\s+reminder)\s+(to\s+|at\s+[^\s]+\s+to\s+|for\s+)', '', user_command, flags=re.I).strip()
            # Remove the time part from reminder text if captured
            if time_match:
                clean_remind = clean_remind.replace(time_match.group(0), "").strip()

            steps = [
                TaskStep(id=1, description=f"Scheduling reminder for {remind_time}", tool_name="tasks.create_reminder", arguments={"reminder_text": clean_remind or "Follow up task", "reminder_time": remind_time}),
                TaskStep(id=2, description="Persisting reminder to MongoDB task scheduler", tool_name=None)
            ]
            return TaskPlan(title=f"Reminder: {clean_remind} ({remind_time})", agent_category="system", is_multi_step=False, steps=steps)

        # 1. Multi-Step Check: E.g., "Check calendar and email me the details"
        if ("calendar" in lower or "meeting" in lower) and ("email" in lower or "inbox" in lower):
            steps = [
                TaskStep(id=1, description="Inspecting scheduled calendar events for meeting details", tool_name="calendar.listEvents", arguments={"days_ahead": 2}),
                TaskStep(id=2, description="Searching Gmail inbox for threads matching meeting context", tool_name="gmail.searchEmails", arguments={"query": "Meeting OR AgriMind"}),
                TaskStep(id=3, description="Correlating meeting briefing with sender details", tool_name=None)
            ]
            return TaskPlan(title="Cross-Agent: Calendar & Gmail Intelligence Correlation", agent_category="google", is_multi_step=True, steps=steps)

        # 2. Browser Tab & Navigation Intents
        if any(w in lower for w in ["new tab", "open another tab", "another tab", "open tab"]):
            steps = [
                TaskStep(id=1, description="Allocating new browser page in context", tool_name="browser.newTab", arguments={}),
                TaskStep(id=2, description="Synchronizing active viewport", tool_name=None)
            ]
            return TaskPlan(title="Browser: Open New Tab", agent_category="browser", is_multi_step=False, steps=steps)

        if any(w in lower for w in ["go back", "previous page", "browser back"]):
            steps = [
                TaskStep(id=1, description="Navigating to previous history entry", tool_name="browser.goBack", arguments={}),
                TaskStep(id=2, description="Waiting for DOM refresh", tool_name=None)
            ]
            return TaskPlan(title="Browser: Go Back", agent_category="browser", is_multi_step=False, steps=steps)

        if any(w in lower for w in ["read page", "read this page", "read the page"]):
            steps = [
                TaskStep(id=1, description="Extracting DOM elements and text from active page", tool_name="browser.readPage", arguments={}),
                TaskStep(id=2, description="Formatting content summary with AI Core", tool_name=None)
            ]
            return TaskPlan(title="Browser: Read Active Web Page", agent_category="browser", is_multi_step=False, steps=steps)

        if any(w in lower for w in ["http://", "https://", ".com", ".org", ".edu", "open website", "open google", "open browser"]):
            raw_url = re.search(r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(com|org|io|net|edu)', user_command)
            target_url = raw_url.group(0) if raw_url else ("google.com" if "google" in lower else "google.com")
            steps = [
                TaskStep(id=1, description=f"Launching Playwright browser engine", tool_name=None),
                TaskStep(id=2, description=f"Navigating to {target_url}", tool_name="browser.open", arguments={"url": target_url}),
                TaskStep(id=3, description="Waiting for DOM load event", tool_name=None)
            ]
            return TaskPlan(title=f"Browser: Navigate to {target_url}", agent_category="browser", is_multi_step=False, steps=steps)

        # 3. Screen Vision Intent
        if any(w in lower for w in ["screenshot", "take a screenshot", "capture screen"]):
            steps = [
                TaskStep(id=1, description="Capturing full-resolution display framebuffer", tool_name="computer.takeScreenshot", arguments={})
            ]
            return TaskPlan(title="Computer: Take Screenshot", agent_category="computer", is_multi_step=False, steps=steps)

        if any(w in lower for w in ["screen", "camera", "what's on my screen", "what is on my screen", "read screen", "look at my screen"]):
            steps = [
                TaskStep(id=1, description="Capturing display framebuffer for multimodal inspection", tool_name="computer.takeScreenshot", arguments={}),
                TaskStep(id=2, description="Passing image tensor to Gemini Multimodal Vision", tool_name="computer.analyzeScreen", arguments={"prompt": user_command}),
                TaskStep(id=3, description="Synthesizing visual grounding report", tool_name=None)
            ]
            return TaskPlan(title="Screen Vision Analysis", agent_category="computer", is_multi_step=False, steps=steps)

        # 4. OS Keyboard & Mouse Automation
        if any(w in lower for w in ["press enter", "press key", "press space", "press tab", "press escape", "press esc"]):
            key_to_press = "enter"
            for k in ["enter", "space", "tab", "esc", "escape", "backspace", "up", "down", "left", "right"]:
                if k in lower:
                    key_to_press = "esc" if k == "escape" else k
                    break
            steps = [
                TaskStep(id=1, description=f"Sending keyboard event '{key_to_press}'", tool_name="computer.pressKey", arguments={"key": key_to_press})
            ]
            return TaskPlan(title=f"Computer: Press {key_to_press.upper()}", agent_category="computer", is_multi_step=False, steps=steps)

        if any(w in lower for w in ["scroll down", "scroll up", "scroll"]):
            amount = -400 if "down" in lower else 400
            steps = [
                TaskStep(id=1, description=f"Scrolling viewport {'down' if amount < 0 else 'up'}", tool_name="computer.scroll", arguments={"clicks": amount})
            ]
            return TaskPlan(title="Computer: Scroll Viewport", agent_category="computer", is_multi_step=False, steps=steps)

        if "click" in lower:
            steps = [
                TaskStep(id=1, description="Executing mouse click at active coordinates", tool_name="computer.click", arguments={})
            ]
            return TaskPlan(title="Computer: Mouse Click", agent_category="computer", is_multi_step=False, steps=steps)

        if lower.startswith("type ") or "type this" in lower:
            typed_text = re.sub(r'^(type\s+(this\s+into\s+the\s+current\s+window\s*:?|this\s*:?|text\s*:?|)|type\s+)', '', user_command, flags=re.I).strip().strip("'\"")
            steps = [
                TaskStep(id=1, description=f"Typing text into focused window: '{typed_text}'", tool_name="computer.typeText", arguments={"text": typed_text})
            ]
            return TaskPlan(title="Computer: Type Text", agent_category="computer", is_multi_step=False, steps=steps)

        # 5. Computer Desktop Applications & Windows Control
        if any(w in lower for w in ["open", "close", "minimize", "maximize", "switch to", "focus", "launch"]):
            target_app = None
            for app in ["chrome", "vs code", "vscode", "code", "notepad", "calculator", "calc", "file explorer", "explorer", "terminal", "powershell", "cmd", "edge"]:
                if app in lower:
                    target_app = app
                    break

            if target_app:
                if "close" in lower:
                    tool = "computer.closeApplication"
                    desc = f"Closing application '{target_app}'"
                    args = {"application": target_app}
                elif "minimize" in lower:
                    tool = "computer.minimizeWindow"
                    desc = f"Minimizing '{target_app}' window"
                    args = {"window_title": target_app}
                elif "maximize" in lower:
                    tool = "computer.maximizeWindow"
                    desc = f"Maximizing '{target_app}' window"
                    args = {"window_title": target_app}
                elif "switch" in lower or "focus" in lower:
                    tool = "computer.focusApplication"
                    desc = f"Focusing '{target_app}' window"
                    args = {"window_title": target_app}
                else:
                    tool = "computer.openApplication"
                    desc = f"Launching desktop application '{target_app}'"
                    args = {"application": target_app}

                steps = [
                    TaskStep(id=1, description=f"Validating '{target_app}' in application matrix", tool_name=None),
                    TaskStep(id=2, description=desc, tool_name=tool, arguments=args),
                    TaskStep(id=3, description="Verifying execution status", tool_name=None)
                ]
                return TaskPlan(title=f"Computer Control: {desc}", agent_category="computer", is_multi_step=False, steps=steps)

        # 6. Gmail Agent Intents
        if any(w in lower for w in ["draft a reply", "draft reply", "reply saying", "draft an email", "draft email", "prepare email"]):
            reply_body = re.sub(r'.*(reply\s+saying|draft\s+a\s+reply\s+saying|draft\s+reply)\s+', '', user_command, flags=re.I).strip() or "I will attend the meeting as scheduled."
            steps = [
                TaskStep(id=1, description="Synthesizing email body with Gemini AI", tool_name=None),
                TaskStep(id=2, description="Generating Gmail draft buffer", tool_name="gmail.createDraft", arguments={"recipient": "recipient@domain.com", "subject": "Re: Update", "body": reply_body}),
                TaskStep(id=3, description="Storing draft in Gmail without sending", tool_name=None)
            ]
            return TaskPlan(title="Gmail: Create Draft Reply", agent_category="google", is_multi_step=False, steps=steps)

        if any(w in lower for w in ["send the draft", "send it", "send email", "send this email"]):
            steps = [
                TaskStep(id=1, description="Validating recipient address and message body", tool_name=None),
                TaskStep(id=2, description="Requesting explicit user authorization [CONFIRM]", tool_name="gmail.send", arguments={"recipient": "contact@domain.com", "subject": "Re: Update", "body": "I will attend as discussed."}),
                TaskStep(id=3, description="Dispatching email via Google API gateway", tool_name=None)
            ]
            return TaskPlan(title="Gmail: Send Email [CONFIRM]", agent_category="google", is_multi_step=False, steps=steps)

        if any(w in lower for w in ["read latest email", "read my latest email", "read the latest", "read this email", "read email", "read the first one"]):
            steps = [
                TaskStep(id=1, description="Querying latest message from Gmail inbox", tool_name="gmail.getEmail", arguments={"message_id": "latest"}),
                TaskStep(id=2, description="Delimiting untrusted email body securely", tool_name=None),
                TaskStep(id=3, description="Synthesizing executive summary with Gemini", tool_name=None)
            ]
            return TaskPlan(title="Gmail: Read & Summarize Latest Email", agent_category="google", is_multi_step=False, steps=steps)

        if "find email" in lower or "search email" in lower or "from my university" in lower or "from university" in lower or "about tomorrow" in lower:
            q = "from:university" if "university" in lower else ("tomorrow" if "tomorrow" in lower else "meeting")
            steps = [
                TaskStep(id=1, description=f"Executing Gmail search query '{q}'", tool_name="gmail.searchEmails", arguments={"query": q}),
                TaskStep(id=2, description="Aggregating matched message threads", tool_name=None),
                TaskStep(id=3, description="Presenting search results", tool_name=None)
            ]
            return TaskPlan(title=f"Gmail: Search Emails '{q}'", agent_category="google", is_multi_step=False, steps=steps)

        if any(w in lower for w in ["unread", "check my unread", "check my email", "check my emails", "check email", "inbox", "mail", "anything important in my inbox"]):
            steps = [
                TaskStep(id=1, description="Connecting to Google Gmail OAuth Gateway", tool_name=None),
                TaskStep(id=2, description="Querying unread messages and priority headers", tool_name="gmail.getUnreadEmails", arguments={"max_results": 5}),
                TaskStep(id=3, description="Compiling executive inbox briefing", tool_name=None)
            ]
            return TaskPlan(title="Gmail: Check Unread Emails", agent_category="google", is_multi_step=False, steps=steps)

        # 7. Calendar Specific Intents
        if any(w in lower for w in ["schedule a", "schedule meeting", "create event", "create a meeting", "add meeting", "book something"]):
            title_text = "Meeting"
            if "with " in lower:
                title_text = f"Meeting with {user_command.split('with ')[1].split(' ')[0]}"
            target_start = "Tomorrow 15:00" if ("tomorrow" in lower or "3 pm" in lower or "afternoon" in lower) else "Tomorrow 10:00"
            steps = [
                TaskStep(id=1, description="Validating meeting parameters and attendee addresses", tool_name=None),
                TaskStep(id=2, description=f"Requesting user confirmation to schedule {title_text} [CONFIRM]", tool_name="calendar.createEvent", arguments={"title": title_text, "start_time": target_start, "end_time": "Tomorrow 16:00"}),
                TaskStep(id=3, description="Dispatching event to Google Calendar store", tool_name=None)
            ]
            return TaskPlan(title=f"Calendar: Schedule {title_text} [CONFIRM]", agent_category="google", is_multi_step=False, steps=steps)

        if any(w in lower for w in ["what is on my calendar", "what's on my calendar", "what's happening on my calendar", "calendar today", "next meeting", "do i have anything"]):
            steps = [
                TaskStep(id=1, description="Accessing Google Calendar store", tool_name=None),
                TaskStep(id=2, description="Fetching today's schedule and evaluating conflicts", tool_name="calendar.listEvents", arguments={"days_ahead": 1}),
                TaskStep(id=3, description="Formatting schedule briefing", tool_name=None)
            ]
            return TaskPlan(title="Calendar Schedule Briefing", agent_category="google", is_multi_step=False, steps=steps)

        # 8. Web Search Intent
        if any(w in lower for w in ["search for", "google for", "search google", "lookup"]):
            query = re.sub(r'^(search\s+google\s+for\s+|search\s+for\s+|google\s+for\s+|lookup\s+)', '', user_command, flags=re.I).strip() or "latest news"
            steps = [
                TaskStep(id=1, description=f"Querying search engine for '{query}'", tool_name="browser.search", arguments={"query": query}),
                TaskStep(id=2, description="Synthesizing structured answer", tool_name=None)
            ]
            return TaskPlan(title=f"Web Search: {query}", agent_category="browser", is_multi_step=False, steps=steps)

        # Default: General Intelligence Query
        steps = [
            TaskStep(id=1, description="Parsing natural language semantics", tool_name=None),
            TaskStep(id=2, description="Direct Gemini neural reasoning", tool_name=None),
            TaskStep(id=3, description="Synthesizing voice response", tool_name=None)
        ]
        return TaskPlan(title="Neural Inference", agent_category="system", is_multi_step=False, steps=steps)

planner = TaskPlanner()
