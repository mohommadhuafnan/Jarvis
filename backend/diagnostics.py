import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import (
    mask_secret,
    LIVEKIT_URL,
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    GOOGLE_API_KEY,
    GEMINI_API_KEY,
    is_livekit_configured,
    is_gemini_configured,
    WAKE_PHRASE
)

def run_diagnostics():
    print("=" * 60)
    print("        JARVIS SYSTEM HARDWARE & SERVICE DIAGNOSTICS      ")
    print("=" * 60)

    checks = []

    # 1. Python Environment
    py_ver = sys.version.split()[0]
    is_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    checks.append(("Python Version", f"{py_ver} ({'Virtualenv .venv' if is_venv else 'Global Python'})", is_venv))

    # 2. Key Package Imports
    packages = [
        ("FastAPI & Uvicorn", "fastapi", True),
        ("Python Multipart", "multipart", True),
        ("LiveKit Agents SDK", "livekit.agents", True),
        ("LiveKit Google Plugin", "livekit.plugins.google", True),
        ("LiveKit Silero VAD", "livekit.plugins.silero", True),
        ("Audio Input (SoundDevice)", "sounddevice", True),
        ("PyAudio Engine", "pyaudio", True),
        ("SpeechRecognition (Wake Word)", "speech_recognition", True),
        ("Windows Automation (PyAutoGUI)", "pyautogui", True),
        ("Playwright DOM Engine", "playwright", True),
        ("System Tray (pystray)", "pystray", True),
        ("MongoDB Driver (pymongo)", "pymongo", True),
    ]

    for label, pkg_name, required in packages:
        try:
            __import__(pkg_name)
            checks.append((f"Package: {label}", "INSTALLED (OK)", True))
        except ImportError as e:
            checks.append((f"Package: {label}", f"NOT INSTALLED ({e})", not required))

    # 3. Environment Credentials (Masked)
    livekit_ok = is_livekit_configured()
    gemini_ok = is_gemini_configured()

    checks.append(("LiveKit URL", LIVEKIT_URL or "<not-set>", bool(LIVEKIT_URL)))
    checks.append(("LiveKit API Key", mask_secret(LIVEKIT_API_KEY), bool(LIVEKIT_API_KEY)))
    checks.append(("LiveKit API Secret", mask_secret(LIVEKIT_API_SECRET), bool(LIVEKIT_API_SECRET)))
    checks.append(("Google / Gemini API Key", mask_secret(GOOGLE_API_KEY or GEMINI_API_KEY), gemini_ok))
    
    from backend.config import DEFAULT_MODEL, LIVE_MODEL
    checks.append(("General AI Model", DEFAULT_MODEL, bool(DEFAULT_MODEL)))
    checks.append(("Gemini Live Voice Model", LIVE_MODEL, bool(LIVE_MODEL)))

    # 4. Audio Input Device Check
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
        has_mic = len(input_devices) > 0
        mic_name = input_devices[0]['name'] if has_mic else "No Input Device Found"
        checks.append(("Microphone Device", f"{mic_name} ({len(input_devices)} found)", has_mic))
    except Exception as e:
        checks.append(("Microphone Device", f"Check failed: {e}", False))

    # 5. Local Wake-Word Engine
    try:
        from backend.voice.wake_word_detector import wake_word_detector
        detector_ok = wake_word_detector is not None
        checks.append(("Local Wake-Word Engine", f"Ready for '{WAKE_PHRASE}'", detector_ok))
    except Exception as e:
        checks.append(("Local Wake-Word Engine", f"Init failed: {e}", False))

    # 6. Windows Startup Service
    try:
        from backend.services.startup_service import startup_service
        startup_st = startup_service.get_status()
        checks.append(("Windows Auto-Start", f"Configured: {startup_st['startup_enabled']}", True))
    except Exception as e:
        checks.append(("Windows Auto-Start", f"Check failed: {e}", False))

    # Print Results
    print(f"{'SUBSYSTEM':<35} {'STATUS / VALUE':<25}")
    print("-" * 60)
    all_passed = True
    for label, val, passed in checks:
        status_marker = "[OK]" if passed else "[WARN/FAIL]"
        if not passed:
            all_passed = False
        print(f"{label:<35} {val:<25}")

    print("=" * 60)
    if all_passed:
        print(">> ALL SYSTEMS OPERATIONAL AND READY FOR VOICE INTERACTION <<")
    else:
        print(">> ATTENTION: SOME SUBSYSTEMS REQUIRE CONFIGURATION <<")
    print("=" * 60)

    return all_passed

if __name__ == "__main__":
    run_diagnostics()
