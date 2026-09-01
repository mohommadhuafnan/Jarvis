import re
import json
import logging
from typing import Dict, Any, List, Optional
from backend.services.conversation_service import conversation_service
from backend.services.audit_service import audit_service
from backend.tools.registry import registry

logger = logging.getLogger("JARVIS.Voice.ConversationManager")

class ConversationManager:
    """
    Manages multi-turn conversational context, dialogue memory,
    and voice-driven permission confirmation states.
    """

    def __init__(self):
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}
        self.last_conversation_id: str = "default_session"

    def set_pending_confirmation(self, conversation_id: str, tool_name: str, arguments: Dict[str, Any], prompt_text: str, risk_level: str):
        """
        Hold a tool execution awaiting explicit user confirmation (e.g. 'Yes', 'Confirm').
        """
        self.pending_confirmations[conversation_id] = {
            "tool_name": tool_name,
            "arguments": arguments,
            "prompt_text": prompt_text,
            "risk_level": risk_level
        }
        logger.info(f"Held pending confirmation for {conversation_id}: {tool_name}")

    def get_pending_confirmation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return self.pending_confirmations.get(conversation_id)

    def clear_pending_confirmation(self, conversation_id: str):
        if conversation_id in self.pending_confirmations:
            del self.pending_confirmations[conversation_id]

    def is_confirmation_response(self, text: str) -> bool:
        """Check if user utterance is an affirmative confirmation."""
        clean = text.lower().strip().rstrip(".!?,")
        affirmative_patterns = [
            "yes", "yeah", "yep", "sure", "confirm", "proceed", "go ahead", "send it", "do it",
            "yes please", "approved", "ok", "okay", "execute", "ஆமாம்", "சரி", "ஆம்", "ow", "hari"
        ]
        return any(clean == p or clean.startswith(p + " ") or clean.endswith(" " + p) for p in affirmative_patterns)

    def is_rejection_response(self, text: str) -> bool:
        """Check if user utterance is a cancellation/rejection."""
        clean = text.lower().strip().rstrip(".!?,")
        rejection_patterns = [
            "no", "nope", "cancel", "stop", "abort", "don't", "dont", "nevermind", "இல்லை", "வேண்டாம்", "naha", "epa"
        ]
        return any(clean == p or clean.startswith(p + " ") or clean.endswith(" " + p) for p in rejection_patterns)

    def resolve_confirmation(self, conversation_id: str, user_text: str) -> Optional[Dict[str, Any]]:
        """
        If a confirmation is pending, check user response and execute if approved.
        """
        pending = self.get_pending_confirmation(conversation_id)
        if not pending:
            return None

        if self.is_confirmation_response(user_text):
            tool_name = pending["tool_name"]
            arguments = pending["arguments"]
            risk_level = pending["risk_level"]
            self.clear_pending_confirmation(conversation_id)

            logger.info(f"User confirmed execution of {tool_name} via voice.")
            tool_res = registry.execute(tool_name, arguments)

            audit_service.log_audit(
                task_id=f"voice_confirm_{conversation_id}",
                agent="ConversationManager",
                tool=tool_name,
                risk_level=risk_level,
                permission_decision="APPROVED_BY_VOICE",
                status="success" if tool_res.get("success") else "error",
                details=arguments
            )

            return {
                "handled": True,
                "approved": True,
                "tool_used": tool_name,
                "tool_result": tool_res,
                "reply": f"Confirmed. I have executed {tool_name} successfully."
            }

        elif self.is_rejection_response(user_text):
            tool_name = pending["tool_name"]
            self.clear_pending_confirmation(conversation_id)
            logger.info(f"User cancelled execution of {tool_name} via voice.")
            return {
                "handled": True,
                "approved": False,
                "tool_used": tool_name,
                "tool_result": {"status": "CANCELLED_BY_USER"},
                "reply": f"Understood. Operation {tool_name} cancelled."
            }

        return None

    def get_conversation_history(self, conversation_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Fetch recent dialogue turns from MongoDB to provide multi-turn context.
        """
        return conversation_service.get_messages(conversation_id=conversation_id, limit=limit)

    def format_dialogue_context(self, conversation_id: str) -> str:
        """
        Compile recent dialogue history into a structured prompt context.
        """
        msgs = self.get_conversation_history(conversation_id, limit=6)
        if not msgs:
            return ""

        context_lines = ["Recent Conversation Context:"]
        for m in msgs:
            role = m.get("role", "user").capitalize()
            content = m.get("content", "")
            context_lines.append(f"- {role}: {content}")

        return "\n".join(context_lines)

conversation_manager = ConversationManager()
