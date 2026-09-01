import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import USER_NAME
from backend.database.collections import get_conversations_col, get_messages_col

logger = logging.getLogger("JARVIS.Services.Conversation")

class ConversationService:
    """
    Manages conversational threads, dialogue sessions, and chronological message history in MongoDB.
    """

    def __init__(self):
        self.default_user = USER_NAME or "default_user"

    def get_or_create_conversation(self, conversation_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve an existing active conversation or create a new one.
        """
        col = get_conversations_col()
        uid = user_id or self.default_user
        cid = conversation_id or f"conv_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()

        if col is not None:
            try:
                existing = col.find_one({"conversationId": cid}, {"_id": 0})
                if existing:
                    return existing

                doc = {
                    "conversationId": cid,
                    "userId": uid,
                    "startedAt": now,
                    "updatedAt": now,
                    "status": "active",
                    "title": "Interactive Session"
                }
                col.insert_one(doc)
                return {k: v for k, v in doc.items() if k != "_id"}
            except Exception as e:
                logger.error(f"Error creating conversation '{cid}': {e}")

        return {
            "conversationId": cid,
            "userId": uid,
            "startedAt": now,
            "updatedAt": now,
            "status": "active"
        }

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Append a message to a conversation thread.
        Roles: 'user', 'assistant', 'system', 'tool'
        """
        msg_col = get_messages_col()
        conv_col = get_conversations_col()
        now = datetime.now().isoformat()

        clean_meta = {}
        if metadata:
            # Filter out sensitive fields
            clean_meta = {k: v for k, v in metadata.items() if "token" not in k.lower() and "secret" not in k.lower() and "key" not in k.lower()}

        doc = {
            "conversationId": conversation_id,
            "role": role,
            "content": content,
            "timestamp": now,
            "metadata": clean_meta,
            "tool_calls": tool_calls or []
        }

        if msg_col is not None:
            try:
                msg_col.insert_one(doc)
            except Exception as e:
                logger.error(f"Error inserting message to conversation '{conversation_id}': {e}")

        if conv_col is not None:
            try:
                conv_col.update_one(
                    {"conversationId": conversation_id},
                    {"$set": {"updatedAt": now}}
                )
            except Exception as e:
                logger.error(f"Error updating conversation timestamp: {e}")

        return {k: v for k, v in doc.items() if k != "_id"}

    def get_messages(self, conversation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve messages for a given conversation sorted chronologically.
        """
        msg_col = get_messages_col()
        if msg_col is None:
            return []

        try:
            cursor = msg_col.find(
                {"conversationId": conversation_id},
                {"_id": 0}
            ).sort("timestamp", 1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error fetching messages for '{conversation_id}': {e}")
            return []

    def list_conversations(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List active and recent conversations.
        """
        conv_col = get_conversations_col()
        uid = user_id or self.default_user
        if conv_col is None:
            return []

        try:
            cursor = conv_col.find(
                {"userId": uid},
                {"_id": 0}
            ).sort("updatedAt", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []

conversation_service = ConversationService()
