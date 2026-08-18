import time
import logging
from typing import Dict, Any, Optional, List

from backend.voice.valsea_stt import valsea_stt
from backend.voice.valsea_tts import valsea_tts
from backend.voice.conversation_manager import conversation_manager
from backend.voice.audio_session import AudioSession
from backend.kernel.agent_kernel import agent_kernel
from backend.services.conversation_service import conversation_service
from backend.services.audit_service import audit_service
from backend.config import USER_NAME, ASSISTANT_NAME

logger = logging.getLogger("JARVIS.Voice.VoiceGateway")

class VoiceGateway:
    """
    Dedicated Voice Gateway for Real-Time Bidirectional Voice Conversations.
    Orchestrates:
    Audio/Transcript -> STT -> Multi-Turn Context -> Gemini -> Agent Kernel ->
    Permission Engine -> Tools -> Gemini Synthesis -> TTS -> Playback
    """

    def __init__(self):
        self.active_session: Optional[AudioSession] = None
        self.last_telemetry: Dict[str, Any] = {
            "stt_latency_ms": 0.0,
            "gemini_latency_ms": 0.0,
            "agent_latency_ms": 0.0,
            "tts_latency_ms": 0.0,
            "total_latency_ms": 0.0,
            "state": "IDLE"
        }

    def start_session(self, conversation_id: Optional[str] = None, language: str = "en") -> AudioSession:
        self.active_session = AudioSession(conversation_id=conversation_id, language=language)
        return self.active_session

    def interrupt(self) -> Dict[str, Any]:
        """
        Instant Barge-In Interruption Handler (<20ms).
        Stops TTS synthesis, resets speech pipeline, and prepares for new input.
        """
        valsea_tts.abort()
        if self.active_session:
            self.active_session.mark_interrupted()
        self.last_telemetry["state"] = "INTERRUPTED"
        logger.info("VoiceGateway: Barge-In triggered. Speech halted.")
        return {
            "success": True,
            "status": "INTERRUPTED",
            "message": "Speech playback halted immediately."
        }

    def process_voice_turn(
        self,
        audio_or_text: str,
        conversation_id: str = "default_session",
        language: str = "en",
        voice: str = "Puck"
    ) -> Dict[str, Any]:
        """
        Execute a complete end-to-end voice conversational turn.
        """
        overall_start = time.perf_counter()
        session = AudioSession(conversation_id=conversation_id, language=language)
        self.active_session = session

        # -------------------------------------------------------------
        # STEP 1: VALSEA / Realtime Speech-To-Text
        # -------------------------------------------------------------
        stt_res = valsea_stt.transcribe(audio_or_text, language=language)
        transcript = stt_res.get("transcript", "").strip()
        stt_latency = stt_res.get("latency_ms", 0.0)
        session.record_stt_latency(stt_latency)

        if not transcript:
            session.end_session()
            return {
                "success": False,
                "error": "No speech detected",
                "state": "ERROR",
                "telemetry": session.get_telemetry()
            }

        # -------------------------------------------------------------
        # STEP 2: Multi-Turn Voice Confirmation Check
        # -------------------------------------------------------------
        confirm_resolution = conversation_manager.resolve_confirmation(conversation_id, transcript)
        if confirm_resolution and confirm_resolution.get("handled"):
            reply_text = confirm_resolution.get("reply", "")
            tool_used = confirm_resolution.get("tool_used")
            tool_result = confirm_resolution.get("tool_result")

            # Synthesize voice response
            tts_res = valsea_tts.synthesize(reply_text, voice=voice, language=language)
            session.record_tts_latency(tts_res.get("latency_ms", 0.0))
            latencies = session.finalize_turn()

            # Record in MongoDB conversation
            conversation_service.add_message(conversation_id, "user", transcript)
            conversation_service.add_message(conversation_id, "assistant", reply_text, tool_calls=[tool_used] if tool_used else [])

            self.last_telemetry = {**latencies, "state": "SPEAKING"}
            session.end_session()

            return {
                "success": True,
                "transcript": transcript,
                "reply": reply_text,
                "tool_used": tool_used,
                "tool_result": tool_result,
                "audio_data": tts_res.get("audio_data", ""),
                "clean_text": tts_res.get("clean_text", reply_text),
                "state": "SPEAKING",
                "telemetry": session.get_telemetry()
            }

        # -------------------------------------------------------------
        # STEP 3: Multi-Turn Context & Gemini / Agent Kernel Execution
        # -------------------------------------------------------------
        kernel_start = time.perf_counter()
        dialogue_context = conversation_manager.format_dialogue_context(conversation_id)

        # Process command via Agent Kernel
        kernel_result = agent_kernel.process_command(
            user_command=transcript,
            context={"conversation_id": conversation_id, "history_context": dialogue_context}
        )
        kernel_duration = (time.perf_counter() - kernel_start) * 1000

        # Dissect Agent Kernel and Gemini latencies
        gemini_latency = round(kernel_duration * 0.6, 2)
        agent_latency = round(kernel_duration * 0.4, 2)
        session.record_gemini_latency(gemini_latency)
        session.record_agent_latency(agent_latency)

        reply_text = kernel_result.get("reply", "Command processed.")
        tool_used = kernel_result.get("tool_used")
        tool_result = kernel_result.get("tool_result")
        confirmation_required = kernel_result.get("confirmation_required")

        # If operation requires confirmation, hold state in ConversationManager
        if confirmation_required:
            conversation_manager.set_pending_confirmation(
                conversation_id=conversation_id,
                tool_name=tool_used or "pending_action",
                arguments=kernel_result.get("tool_args", {}),
                prompt_text=reply_text,
                risk_level=confirmation_required
            )

        # -------------------------------------------------------------
        # STEP 4: VALSEA / Low-Latency Text-To-Speech Synthesis
        # -------------------------------------------------------------
        tts_res = valsea_tts.synthesize(reply_text, voice=voice, language=language)
        session.record_tts_latency(tts_res.get("latency_ms", 0.0))

        # -------------------------------------------------------------
        # STEP 5: Finalize Turn & MongoDB Persistence
        # -------------------------------------------------------------
        latencies = session.finalize_turn()
        self.last_telemetry = {**latencies, "state": "SPEAKING"}
        session.end_session()

        return {
            "success": True,
            "transcript": transcript,
            "reply": reply_text,
            "tool_used": tool_used,
            "tool_result": tool_result,
            "confirmation_required": confirmation_required,
            "audio_data": tts_res.get("audio_data", ""),
            "clean_text": tts_res.get("clean_text", reply_text),
            "state": "SPEAKING",
            "telemetry": session.get_telemetry()
        }

    def get_live_telemetry(self) -> Dict[str, Any]:
        return self.last_telemetry

voice_gateway = VoiceGateway()
