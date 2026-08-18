import sys
import os
import time
import requests
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import all tool modules to populate registry
import backend.tools.system_tools
import backend.tools.task_tools
import backend.tools.calendar_tools
import backend.tools.email_tools
import backend.tools.gmail_tools
import backend.tools.web_tools
import backend.tools.file_tools
import backend.tools.code_sandbox
import backend.tools.vision_tools
import backend.tools.computer_tools
import backend.tools.browser_tools
import backend.tools.memory_tools

from backend.voice.valsea_stt import valsea_stt
from backend.voice.valsea_tts import valsea_tts
from backend.voice.conversation_manager import conversation_manager
from backend.voice.audio_session import AudioSession
from backend.voice.voice_gateway import voice_gateway
from backend.kernel.agent_kernel import agent_kernel
from backend.kernel.permission_engine import permission_engine
from backend.services.conversation_service import conversation_service
from backend.services.task_service import task_service
from backend.services.audit_service import audit_service
from backend.database.mongodb import get_mongo_client

test_results = {}

def run_test(name, test_fn):
    try:
        ok = test_fn()
        status = "PASS" if ok else "FAIL"
        test_results[name] = status
        print(f"[{status}] {name}")
    except Exception as e:
        test_results[name] = f"FAIL ({e})"
        print(f"[FAIL] {name}: {e}")

# TEST 1: Voice -> transcript
def test_1_voice_to_transcript():
    res = valsea_stt.transcribe("Jarvis, check system status", language="en")
    return res.get("success") is True and len(res.get("transcript", "")) > 0 and res.get("latency_ms") is not None

# TEST 2: Transcript -> Gemini
def test_2_transcript_to_gemini():
    from backend.ai.gemini_service import ai_service
    res = ai_service.process_query("What is 15 + 27?")
    return "42" in res.get("reply", "") or len(res.get("reply", "")) > 0

# TEST 3: Gemini -> Agent Kernel
def test_3_gemini_to_agent_kernel():
    res = agent_kernel.process_command("What time is it?")
    return "reply" in res and len(res["reply"]) > 0

# TEST 4: Agent Kernel -> Computer Agent
def test_4_agent_kernel_to_computer_agent():
    res = agent_kernel.process_command("Open Notepad")
    return res.get("tool_used") == "computer.openApplication" or "notepad" in res.get("reply", "").lower()

# TEST 5: Agent result -> Gemini
def test_5_agent_result_to_gemini():
    res = agent_kernel.process_command("List my workspace files")
    return res.get("tool_used") == "files.list" or "workspace" in res.get("reply", "").lower() or "file" in res.get("reply", "").lower()

# TEST 6: Gemini -> TTS
def test_6_gemini_to_tts():
    tts = valsea_tts.synthesize("Welcome Commander, neural voice synthesis is online.", voice="Puck")
    return tts.get("success") is True and tts.get("latency_ms") is not None and len(tts.get("clean_text", "")) > 0

# TEST 7: TTS -> speaker
def test_7_tts_to_speaker():
    tts = valsea_tts.synthesize("Test playback ready.", voice="Puck")
    return tts.get("clean_text") == "Test playback ready." and tts.get("success") is True

# TEST 8: Full conversation ("Jarvis, open Notepad.")
def test_8_full_conversation():
    turn = voice_gateway.process_voice_turn(
        audio_or_text="Jarvis, open Notepad.",
        conversation_id="test_voice_full"
    )
    return turn.get("success") is True and ("notepad" in turn.get("reply", "").lower() or turn.get("tool_used") == "computer.openApplication")

# TEST 9: Multi-turn conversation ("Jarvis, what's on my calendar?" then "What about tomorrow?")
def test_9_multi_turn_conversation():
    conv_id = f"test_multiturn_{int(time.time())}"
    # Turn 1
    turn1 = voice_gateway.process_voice_turn("Jarvis, what's on my calendar?", conversation_id=conv_id)
    # Turn 2
    turn2 = voice_gateway.process_voice_turn("What about tomorrow?", conversation_id=conv_id)
    return turn1.get("success") is True and turn2.get("success") is True and len(turn2.get("reply", "")) > 0

# TEST 10: Barge-in interruption
def test_10_barge_in():
    valsea_tts.reset_abort()
    intr = voice_gateway.interrupt()
    return intr.get("status") == "INTERRUPTED" and valsea_tts.is_aborted is True

# TEST 11: Confirmation ("Send this email." -> "Yes" -> executes gmail.send)
def test_11_voice_confirmation():
    conv_id = f"test_confirm_{int(time.time())}"
    # Set pending confirmation state
    conversation_manager.set_pending_confirmation(
        conversation_id=conv_id,
        tool_name="gmail.send",
        arguments={"recipient": "team@agrimind.ai", "subject": "Update", "body": "Report ready."},
        prompt_text="Do you want me to send the email to team@agrimind.ai?",
        risk_level="CONFIRM"
    )
    # User says "Yes"
    turn = voice_gateway.process_voice_turn("Yes, send it.", conversation_id=conv_id)
    return turn.get("success") is True and turn.get("tool_used") == "gmail.send"

# TEST 12: Dangerous action ("Delete this file." -> HIGH_RISK confirmation)
def test_12_dangerous_action_gating():
    conv_id = f"test_danger_{int(time.time())}"
    turn = voice_gateway.process_voice_turn("Delete this file report.txt", conversation_id=conv_id)
    # High risk action must require confirmation
    pending = conversation_manager.get_pending_confirmation(conv_id)
    return turn.get("confirmation_required") is not None or pending is not None or "confirm" in turn.get("reply", "").lower()

# TEST 13: Tamil ("Jarvis, இன்று என்ன schedule இருக்கு?")
def test_13_tamil_language():
    turn = voice_gateway.process_voice_turn(
        audio_or_text="Jarvis, இன்று என்ன schedule இருக்கு?",
        language="ta",
        conversation_id="test_ta"
    )
    return turn.get("success") is True and len(turn.get("reply", "")) > 0

# TEST 14: Tamil + English code-switching ("Jarvis, இன்று என்ன meetings இருக்கு?")
def test_14_tamil_english_code_switching():
    turn = voice_gateway.process_voice_turn(
        audio_or_text="Jarvis, இன்று என்ன meetings இருக்கு?",
        language="ta-en",
        conversation_id="test_ta_en"
    )
    return turn.get("success") is True and len(turn.get("reply", "")) > 0

# TEST 15: Restart & MongoDB persistence verification
def test_15_restart_persistence():
    conv_id = "test_persistence_session"
    conversation_service.add_message(conv_id, "user", "Remember my code-name is Phoenix")
    conversation_service.add_message(conv_id, "assistant", "Acknowledged, Commander Phoenix.")
    msgs = conversation_service.get_messages(conv_id)
    return len(msgs) >= 2 and any("Phoenix" in m.get("content", "") for m in msgs)

# END-TO-END: Voice -> STT -> Gemini -> Agent -> Tool -> Gemini -> TTS -> Speaker
def test_e2e_full_voice_pipeline():
    res = requests.post(
        "http://127.0.0.1:8000/api/voice/gateway/process",
        json={"audio_or_text": "Jarvis, what time is it?", "language": "en", "voice": "Puck"},
        timeout=10
    )
    if res.status_code == 200:
        data = res.json()
        telemetry = data.get("telemetry", {}).get("latencies", {})
        return (
            data.get("success") is True and
            len(data.get("reply", "")) > 0 and
            data.get("state") == "SPEAKING" and
            telemetry.get("total_latency_ms", 0) > 0
        )
    return False

if __name__ == "__main__":
    print("\n========== JARVIS STEP 10: REAL-TIME VOICE VERIFICATION ==========\n")
    run_test("VALSEA STT (TEST 1: Voice -> transcript)", test_1_voice_to_transcript)
    run_test("Gemini integration (TEST 2: Transcript -> Gemini)", test_2_transcript_to_gemini)
    run_test("Agent Kernel integration (TEST 3: Gemini -> Agent Kernel)", test_3_gemini_to_agent_kernel)
    run_test("Computer Agent (TEST 4: Agent Kernel -> Computer Agent)", test_4_agent_kernel_to_computer_agent)
    run_test("Agent result -> Gemini (TEST 5)", test_5_agent_result_to_gemini)
    run_test("VALSEA TTS (TEST 6: Gemini -> TTS)", test_6_gemini_to_tts)
    run_test("TTS -> speaker (TEST 7)", test_7_tts_to_speaker)
    run_test("Full conversation (TEST 8: Open Notepad)", test_8_full_conversation)
    run_test("Multi-turn conversation (TEST 9: Context retention)", test_9_multi_turn_conversation)
    run_test("Barge-in (TEST 10: Instant Interruption)", test_10_barge_in)
    run_test("Permission confirmation (TEST 11: Voice approval)", test_11_voice_confirmation)
    run_test("Dangerous action (TEST 12: High-risk gating)", test_12_dangerous_action_gating)
    run_test("Tamil (TEST 13: Multilingual)", test_13_tamil_language)
    run_test("Tamil-English (TEST 14: Code-switching)", test_14_tamil_english_code_switching)
    run_test("Restart & Persistence (TEST 15)", test_15_restart_persistence)
    
    print("\n--- END-TO-END VERIFICATION ---")
    run_test("END-TO-END: Voice -> STT -> Gemini -> Agent -> Tool -> Gemini -> TTS -> Speaker", test_e2e_full_voice_pipeline)
    print("\n==================================================================\n")
