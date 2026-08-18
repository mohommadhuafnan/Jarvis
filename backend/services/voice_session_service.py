import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.database.collections import get_voice_sessions_col

logger = logging.getLogger("JARVIS.Services.VoiceSession")

class VoiceSessionService:
    """
    Manages audio and voice interaction session records in MongoDB.
    Stores metadata, language, latency, and provider without capturing raw audio stream blobs.
    """

    def create_session(
        self,
        conversation_id: Optional[str] = None,
        language: str = "en",
        provider: str = "Google Gemini Live Audio"
    ) -> Dict[str, Any]:
        col = get_voice_sessions_col()
        sid = f"vsession_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        doc = {
            "sessionId": sid,
            "conversationId": conversation_id or f"conv_{uuid.uuid4().hex[:8]}",
            "startedAt": now,
            "endedAt": None,
            "language": language,
            "provider": provider,
            "status": "active"
        }

        if col is not None:
            try:
                col.insert_one(doc)
            except Exception as e:
                logger.error(f"Error recording voice session: {e}")

        return {k: v for k, v in doc.items() if k != "_id"}

    def end_session(self, session_id: str) -> bool:
        col = get_voice_sessions_col()
        if col is None:
            return False

        try:
            res = col.update_one(
                {"sessionId": session_id},
                {"$set": {"endedAt": datetime.now().isoformat(), "status": "completed"}}
            )
            return res.modified_count > 0
        except Exception as e:
            logger.error(f"Error ending voice session '{session_id}': {e}")
            return False

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        col = get_voice_sessions_col()
        if col is None:
            return []

        try:
            cursor = col.find({}, {"_id": 0}).sort("startedAt", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error listing voice sessions: {e}")
            return []

voice_session_service = VoiceSessionService()
