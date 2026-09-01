import os
import re
import json
import time
import requests
from typing import Dict, Any, List, Optional
from backend.config import GEMINI_API_KEY, ASSISTANT_NAME, USER_NAME
from backend.tools.registry import registry, RiskLevel
from backend.kernel.planner import planner, TaskPlan
from backend.kernel.permission_engine import permission_engine
from backend.services.memory_service import memory_service
from backend.services.task_service import task_service, TaskStatus
from backend.services.conversation_service import conversation_service
from backend.services.audit_service import audit_service

# Import all tool modules to populate Tool Registry
import backend.tools.system_tools
import backend.tools.task_tools
import backend.tools.calendar_tools
import backend.tools.gmail_tools
import backend.tools.web_tools
import backend.tools.file_tools
import backend.tools.code_sandbox
import backend.tools.vision_tools
import backend.tools.computer_tools
import backend.tools.browser_tools
import backend.tools.memory_tools
import backend.tools.whatsapp_tools
import backend.tools.knowledge_tools


class AgentKernel:
    """
    Central JARVIS Agent Kernel with MongoDB integration:
    1. Parse incoming user intent (Voice or Text).
    2. Formulate multi-step task execution plan.
    3. Route sub-tasks to specialized agents.
    4. Check safety & permission levels via Permission Engine.
    5. Execute tools and capture structured results.
    6. Retrieve and persist long-term memories in MongoDB.
    7. Track autonomous tasks and recover state across restarts.
    8. Record audit trails and agent execution logs in MongoDB.
    """

    def __init__(self):
        self.active_tasks: Dict[str, Any] = {}
        self.emergency_stop_triggered = False

    def trigger_emergency_stop(self) -> Dict[str, Any]:
        """Global emergency abort."""
        self.emergency_stop_triggered = True
        try:
            from backend.tools.browser_tools import browser_mgr
            browser_mgr.close_all()
        except Exception:
            pass
        audit_service.log_audit(
            task_id="EMERGENCY_STOP",
            agent="Kernel",
            tool="emergency.stop",
            risk_level="HIGH_RISK",
            permission_decision="APPROVED",
            status="STOPPED",
            details="Emergency Stop activated."
        )
        return {
            "success": True,
            "status": "STOPPED",
            "message": "Emergency Stop activated. All active browser automation and background tasks halted."
        }

    def reset_stop(self):
        self.emergency_stop_triggered = False

    def process_command(self, user_command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main execution pipeline of the Agent Kernel.
        """
        if self.emergency_stop_triggered:
            self.reset_stop()

        user_clean = user_command.strip()
        lower = user_clean.lower()
        conv_id = (context or {}).get("conversation_id", "default_session")

        # Record user message in MongoDB conversation
        conversation_service.get_or_create_conversation(conversation_id=conv_id)
        conversation_service.add_message(
            conversation_id=conv_id,
            role="user",
            content=user_clean
        )

        # 1. Direct Memory Recall / Working On Check
        relevant_memories = []
        if any(w in lower for w in ["what is my", "what's my", "who is", "remember", "project", "working on", "preference", "what did you do", "continue"]):
            # Search memory vault
            query_terms = re.sub(r'^(what\s+is\s+my|what\'s\s+my|who\s+is|tell\s+me\s+about)\s+', '', lower).strip()
            relevant_memories = memory_service.search_memory(query=query_terms or "project")

        # 2. Check for "What did you do?" -> Audit Log Summary
        if "what did you do" in lower or "recent actions" in lower or "audit" in lower:
            recent_logs = audit_service.get_audit_logs(limit=5)
            log_summary = "\n".join([f"- {l.get('agent', 'Agent')}: {l.get('tool', 'Action')} ({l.get('status', 'done')})" for l in recent_logs])
            reply = f"Here is a summary of recent operations, Commander:\n{log_summary}" if recent_logs else "No recent operations recorded in the audit logs, Commander."
            conversation_service.add_message(conversation_id=conv_id, role="assistant", content=reply)
            return {
                "reply": reply,
                "tool_used": "audit.getLogs",
                "tool_result": {"recent_logs": recent_logs},
                "action_plan": ["Queried MongoDB audit_logs", "Generated summary"],
                "state": "SPEAKING",
                "model": "JARVIS Kernel (MongoDB Audit)"
            }

        # 3. Check for "Continue my previous task" -> Task State Recovery
        if "continue" in lower and ("task" in lower or "previous" in lower):
            tasks = task_service.list_tasks(limit=5)
            in_prog = [t for t in tasks if t.get("status") in [TaskStatus.RUNNING, TaskStatus.RECOVERING, TaskStatus.PLANNED]]
            if in_prog:
                target_task = in_prog[0]
                reply = f"Resuming previous task '{target_task.get('objective')}' (Status: {target_task.get('status')}, Progress: {target_task.get('progress')}%)."
                task_service.update_task(task_id=target_task["taskId"], status=TaskStatus.RUNNING, current_step="Resuming autonomous execution")
                conversation_service.add_message(conversation_id=conv_id, role="assistant", content=reply)
                return {
                    "reply": reply,
                    "tool_used": "tasks.recover",
                    "tool_result": {"task": target_task},
                    "action_plan": ["Retrieved persisted task from MongoDB", "Resumed execution"],
                    "state": "SPEAKING",
                    "model": "JARVIS Task Recovery"
                }

        # 4. Formulate Task Plan
        plan = planner.plan_task(user_clean)
        action_steps = [s.description for s in plan.steps]

        tool_executed = None
        tool_result = None
        pending_confirmation = None

        # 5. Sequential Step Execution
        for step in plan.steps:
            if self.emergency_stop_triggered:
                return {
                    "reply": "Execution halted by Emergency Stop.",
                    "tool_used": None,
                    "tool_result": None,
                    "action_plan": ["Emergency Stop Triggered", "Halted"],
                    "state": "IDLE",
                    "plan": plan.dict()
                }

            if step.tool_name:
                # Permission Check
                allowed, reason, risk = permission_engine.check_permission(step.tool_name, step.arguments)
                if not allowed:
                    pending_confirmation = {
                        "tool": step.tool_name,
                        "arguments": step.arguments,
                        "risk_level": risk.value if hasattr(risk, "value") else str(risk),
                        "reason": reason,
                        "message": f"Commander, confirmation required to execute {step.tool_name}."
                    }
                    tool_executed = step.tool_name
                    tool_result = {"status": "CONFIRMATION_REQUIRED", "details": pending_confirmation}
                    audit_service.log_audit(
                        task_id=step.id,
                        agent=plan.agent_category,
                        tool=step.tool_name,
                        risk_level=str(risk),
                        permission_decision="PENDING_CONFIRMATION",
                        status="CONFIRMATION_REQUIRED",
                        details=step.arguments
                    )
                    break

                # Execute Tool
                t_start = time.strftime("%Y-%m-%dT%H:%M:%S")
                tool_res = registry.execute(step.tool_name, step.arguments)
                t_end = time.strftime("%Y-%m-%dT%H:%M:%S")
                tool_executed = step.tool_name
                tool_result = tool_res
                step.completed = True

                # Persist Agent Run & Audit Record in MongoDB
                audit_service.log_agent_run(
                    task_id=step.id,
                    agent=plan.agent_category,
                    tool=step.tool_name,
                    arguments_summary=step.arguments,
                    status="COMPLETED",
                    started_at=t_start,
                    completed_at=t_end,
                    result_summary=tool_res
                )
                audit_service.log_audit(
                    task_id=step.id,
                    agent=plan.agent_category,
                    tool=step.tool_name,
                    risk_level=str(risk),
                    permission_decision="APPROVED",
                    status="success",
                    details=step.arguments
                )

        # 6. Direct Gemini Inference with Tool Context & Memory Context
        prompt = f"""You are {ASSISTANT_NAME}, an advanced personal AI computer assistant and command center.
Commander name: {USER_NAME}.
User instruction: "{user_clean}"
Active Plan: {plan.title} (Category: {plan.agent_category})
"""
        if relevant_memories:
            prompt += f"\nRelevant Persistent Long-Term Memories from MongoDB:\n{json.dumps(relevant_memories, default=str)}\n"

        if tool_executed:
            prompt += f"\nExecuted Tool: {tool_executed}\nTool Result Payload:\n{json.dumps(tool_result, default=str)}\n"
            prompt += "\nProvide a concise, direct, voice-friendly response to the commander based on the result."
        else:
            prompt += "\nRespond directly, smartly, and concisely to the commander. If recalling a remembered project or preference from memory, state it clearly."

        reply_text = self._call_gemini(prompt, user_clean, tool_executed, tool_result, relevant_memories)

        # Record assistant reply in MongoDB conversation
        conversation_service.add_message(
            conversation_id=conv_id,
            role="assistant",
            content=reply_text,
            metadata={"tool_used": tool_executed}
        )

        return {
            "reply": reply_text,
            "tool_used": tool_executed,
            "tool_result": tool_result,
            "action_plan": action_steps,
            "state": "SPEAKING",
            "model": "Gemini Flash (Agent Kernel)",
            "plan": plan.dict(),
            "confirmation_required": pending_confirmation
        }

    def _call_gemini(
        self,
        prompt: str,
        user_command: str,
        tool_used: Optional[str],
        tool_result: Any,
        relevant_memories: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        system_instruction = (
            f"You are JARVIS, personal AI voice assistant to Boss (Commander {USER_NAME or 'Ravit'}). "
            "Speak naturally, concisely, and conversationally in 1-2 clear sentences. "
            "Address the user as 'Boss'. Never give vague or generic responses. "
            "State outcomes clearly (e.g. 'Chrome is open, Boss.', 'Your email has been sent, Boss.')."
        )
        full_prompt = f"{system_instruction}\n\nContext & Tool Execution:\n{prompt}"

        if GEMINI_API_KEY:
            for model in ["gemini-flash-lite-latest", "gemini-flash-latest"]:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                    headers = {"Content-Type": "application/json", "X-goog-api-key": GEMINI_API_KEY}
                    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
                    res = requests.post(url, headers=headers, json=payload, timeout=6)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                except Exception:
                    continue

        # Truthful Heuristic / Structured Tool Response
        lower = user_command.lower().strip()

        if lower in ["stop", "jarvis stop", "stop jarvis", "halt", "emergency stop", "abort"]:
            return "Stopped, Boss. I'm ready."

        if "hello" in lower or "wake" in lower or lower == "jarvis" or lower == "hey jarvis":
            return "Hello, Boss. How can I help you?"

        if tool_used == "whatsapp.open":
            return "WhatsApp is open, Boss."

        if tool_used == "whatsapp.send_message":
            return "Done, Boss. The WhatsApp message has been sent."

        if tool_used == "knowledge.get_today_lectures":
            if isinstance(tool_result, dict) and tool_result.get("spoken_summary"):
                return tool_result["spoken_summary"]
            return "You have no lectures scheduled for that day on your active timetable, Boss."

        if tool_used == "knowledge.get_next_class":
            if isinstance(tool_result, dict) and tool_result.get("spoken_summary"):
                return tool_result["spoken_summary"]
            return "You don't have any upcoming classes scheduled for today, Boss."

        if tool_used == "knowledge.get_timetable":
            if isinstance(tool_result, dict):
                count = tool_result.get("total_classes", 0)
                doc = tool_result.get("active_document", "your active document")
                return f"You have {count} total classes in your active timetable from {doc}, Boss."
            return "No active timetable is currently loaded in your vault, Boss."

        if tool_used == "knowledge.get_profile":
            if isinstance(tool_result, dict):
                prof = tool_result.get("profile", {})
                deg = prof.get("degree", "BICT")
                yr = prof.get("year", "2nd Year")
                proj = prof.get("primary_project", "AgriMind AI")
                if "project" in lower:
                    return f"Your primary project is {proj}, Boss."
                return f"According to your personal profile, Boss: you are studying {deg} in your {yr}, and your main project is {proj}."

        if tool_used == "knowledge.forget":
            if isinstance(tool_result, dict) and tool_result.get("message"):
                return tool_result["message"]
            return "Knowledge records updated, Boss."

        if tool_used == "knowledge.search_vault":
            if isinstance(tool_result, dict):
                results = tool_result.get("results", [])
                if results:
                    top = results[0]
                    return f"According to your knowledge vault, your {top.get('key')} is {top.get('value')}, Boss."
                return "I don't have that information in your knowledge vault yet, Boss."


        if tool_used in ["gmail.getUnreadEmails", "email.read", "gmail.searchEmails", "gmail.getEmail", "gmail.createDraft", "gmail.send", "gmail.reply"]:
            if isinstance(tool_result, dict):
                if tool_result.get("connected") is False:
                    return "Boss, your Gmail account isn't connected yet."
                if tool_result.get("summary"):
                    return tool_result["summary"]
                if tool_result.get("snippet"):
                    sender = tool_result.get("from", "Unknown").split("<")[0].strip()
                    return f"The latest email is from {sender} regarding '{tool_result.get('subject')}': {tool_result.get('snippet')}"
                if tool_result.get("message"):
                    return tool_result["message"]

        if tool_used in ["calendar.listEvents", "calendar.getEvents", "calendar.createEvent"]:
            if isinstance(tool_result, dict):
                if tool_result.get("connected") is False:
                    return "Boss, your Google Calendar isn't connected yet."
                if tool_result.get("verified") is True:
                    return f"Done, Boss. Your meeting '{tool_result.get('title', 'Meeting')}' is scheduled and verified on Google Calendar."
                if tool_result.get("verified") is False and "failed" in tool_result.get("message", "").lower():
                    return "I couldn't confirm that the meeting was created on Google Calendar, Boss."
                if tool_result.get("summary"):
                    return tool_result["summary"]
                if tool_result.get("message"):
                    return tool_result["message"]

        if tool_used == "memory.search":
            if isinstance(tool_result, dict):
                memories = tool_result.get("memories", [])
                if memories:
                    top = memories[0]
                    return f"You told me that your {top.get('key', 'item')} is {top.get('value', '')}, Boss."
                return "I don't have that stored in memory yet, Boss."
            if relevant_memories:
                top = relevant_memories[0]
                return f"You told me that your {top.get('key', 'item')} is {top.get('value', '')}, Boss."
            return "I couldn't find that in your memories, Boss."

        if tool_used == "memory.store":
            if isinstance(tool_result, dict) and tool_result.get("key"):
                return f"I've remembered that your {tool_result.get('key')} is {tool_result.get('value')}, Boss."
            return "I've remembered that for you, Boss."

        if tool_used in ["tasks.create", "tasks.create_reminder"]:
            if isinstance(tool_result, dict) and tool_result.get("reminder_time"):
                return f"I've set your reminder for {tool_result.get('reminder_time')}, Boss."
            return "Reminder created and armed in background scheduler, Boss."

        if tool_used == "computer.openApplication":
            app = ""
            if isinstance(tool_result, dict):
                app = tool_result.get("application") or tool_result.get("result", {}).get("application", "")
            if not app:
                for a in ["chrome", "vs code", "vscode", "code", "notepad", "calculator", "explorer", "whatsapp"]:
                    if a in lower:
                        app = a
                        break
            app_title = "VS Code" if app in ["vs code", "vscode", "code"] else (app.capitalize() if app else "Application")
            return f"{app_title} is open, Boss."

        if tool_used == "computer.closeApplication":
            return "Application closed, Boss."

        if tool_used == "computer.minimizeWindow":
            return "Window minimized, Boss."

        if tool_used == "computer.maximizeWindow":
            return "Window maximized, Boss."

        if tool_used == "computer.typeText":
            return "Text typed into active window, Boss."

        if tool_used == "computer.pressKey":
            return "Key pressed, Boss."

        if tool_used == "computer.click":
            return "Click executed, Boss."

        if tool_used == "computer.scroll":
            return "Scrolled, Boss."

        if tool_used in ["computer.analyzeScreen", "computer.takeScreenshot"]:
            return "Screenshot captured, Boss."

        if isinstance(tool_result, dict) and tool_result.get("summary"):
            return tool_result["summary"]
        if isinstance(tool_result, dict) and tool_result.get("message"):
            return tool_result["message"]

        return "Done, Boss."

agent_kernel = AgentKernel()
