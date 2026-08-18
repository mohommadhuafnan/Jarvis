import time
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from backend.services.voice_session_service import voice_session_service

logger = logging.getLogger("JARVIS.Voice.AudioSession")

class AudioSession:
    """
    Manages an active real-time voice interaction session,
    tracking turn-by-turn latencies, provider metadata, and interruption events.
    """

    def __init__(self, session_id: Optional[str] = None, conversation_id: Optional[str] = None, language: str = "en"):
        self.session_id = session_id or f"vsession_{uuid.uuid4().hex[:8]}"
        self.conversation_id = conversation_id or f"conv_{uuid.uuid4().hex[:8]}"
        self.language = language
        self.provider = "VALSEA / Google Gemini Live Audio"
        self.started_at = time.time()
        self.is_active = True
        self.interrupted = False
        
        # Telemetry metrics in milliseconds
        self.latencies: Dict[str, float] = {
            "stt_latency_ms": 0.0,
            "gemini_latency_ms": 0.0,
            "agent_latency_ms": 0.0,
            "tts_latency_ms": 0.0,
            "total_latency_ms": 0.0
        }

        # Initialize session in MongoDB
        try:
            voice_session_service.create_session(
                conversation_id=self.conversation_id,
                language=self.language,
                provider=self.provider
            )
        except Exception as e:
            logger.warning(f"Failed to record session in MongoDB: {e}")

    def record_stt_latency(self, duration_ms: float):
        self.latencies["stt_latency_ms"] = round(duration_ms, 2)

    def record_gemini_latency(self, duration_ms: float):
        self.latencies["gemini_latency_ms"] = round(duration_ms, 2)

    def record_agent_latency(self, duration_ms: float):
        self.latencies["agent_latency_ms"] = round(duration_ms, 2)

    def record_tts_latency(self, duration_ms: float):
        self.latencies["tts_latency_ms"] = round(duration_ms, 2)

    def finalize_turn(self) -> Dict[str, float]:
        self.latencies["total_latency_ms"] = round(
            self.latencies["stt_latency_ms"] +
            self.latencies["gemini_latency_ms"] +
            self.latencies["agent_latency_ms"] +
            self.latencies["tts_latency_ms"],
            2
        )
        return self.latencies

    def mark_interrupted(self):
        self.interrupted = True
        logger.info(f"AudioSession {self.session_id} marked as INTERRUPTED (Barge-In).")

    def end_session(self):
        self.is_active = False
        try:
            voice_session_service.end_session(self.session_id)
        except Exception:
            pass

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "language": self.language,
            "provider": self.provider,
            "interrupted": self.interrupted,
            "latencies": self.latencies
        }
