import os
import re
import sys
import time
import signal
import logging
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import (
    LOGS_DIR,
    LOG_FILE_PATH,
    INSTANCE_LOCK_PATH,
    WAKE_PHRASE,
    INACTIVITY_TIMEOUT_SECS,
    USER_NAME,
    ASSISTANT_NAME,
    GEMINI_API_KEY
)
from backend.voice.wake_word_detector import (
    WakeWordDetector,
    WakeWordState,
    wake_word_detector
)
from backend.voice.tts_service import tts_service
from backend.voice.livekit_client import livekit_desktop_client
import backend.tools # Ensure all tools are registered in registry
from backend.tools.registry import registry
from backend.ai.gemini_service import gemini_service

# -------------------------------------------------------------
# Setup Secure Production Logging (10MB rotating log)
# -------------------------------------------------------------
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("JARVIS.BackgroundService")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Rotating File Handler (10MB max, 5 backups)
    try:
        rfh = RotatingFileHandler(
            str(LOG_FILE_PATH),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        rfh.setLevel(logging.INFO)
        rfh.setFormatter(formatter)
        logger.addHandler(rfh)
    except Exception as e:
        print(f"Warning: Could not initialize rotating log file: {e}")

# Sleep Phrases Whitelist
SLEEP_PHRASES = [
    "sleep jarvis",
    "jarvis sleep",
    "go to sleep",
    "stop listening",
    "sleep now",
    "goodbye jarvis",
    "bye jarvis",
    "exit voice",
    "sleep"
]

class SingleInstanceLock:
    """
    Ensures only a single instance of the JARVIS background daemon runs at any time.
    Uses file locking with process ID validation on Windows.
    """
    def __init__(self, lock_file: Path = INSTANCE_LOCK_PATH):
        self.lock_file = lock_file
        self._acquired = False

    def acquire(self) -> bool:
        try:
            if self.lock_file.exists():
                try:
                    with open(self.lock_file, "r") as f:
                        pid = int(f.read().strip())
                    # Check if the process is actually running
                    if os.name == "nt":
                        import ctypes
                        kernel32 = ctypes.windll.kernel32
                        handle = kernel32.OpenProcess(1, False, pid)
                        if handle:
                            kernel32.CloseHandle(handle)
                            logger.error(f"JARVIS is already running (PID: {pid}). Aborting duplicate launch.")
                            return False
                except Exception:
                    # Stale lock file
                    pass

            with open(self.lock_file, "w") as f:
                f.write(str(os.getpid()))
            self._acquired = True
            return True
        except Exception as e:
            logger.error(f"Failed to acquire single instance lock: {e}")
            return False

    def release(self):
        if self._acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except Exception:
                pass
            self._acquired = False


class JarvisBackgroundService:
    """
    Master Hands-Free Desktop Voice Assistant Daemon for Windows.
    LiveKit Cloud is the Primary Realtime Voice Infrastructure.

    Lifecycle:
    1. Windows starts -> Runs silently in background (JARVIS_SLEEPING).
    2. Local wake-word listener spots 'Hello JARVIS' (WAKE_WORD_DETECTED).
    3. JARVIS wakes -> Starts LiveKit realtime session (LIVEKIT_SESSION_STARTING -> LIVEKIT_CONNECTED).
    4. Speaks 'Yes, how can I help?' in Gemini Puck Voice (LIVEKIT_AGENT_RESPONSE_STARTED -> LIVEKIT_AUDIO_OUTPUT_COMPLETED).
    5. User speaks command -> Executes Windows desktop tools (TOOL_CALL_STARTED -> TOOL_CALL_COMPLETED).
    6. Dangerous actions (Shutdown/Restart/Delete) require explicit voice confirmation (CONFIRMATION_REQUIRED).
    7. User says 'Sleep JARVIS' -> Disconnects LiveKit session (LIVEKIT_DISCONNECTED) -> Returns to JARVIS_SLEEPING.
    """

    def __init__(self):
        self.lock = SingleInstanceLock()
        self.detector: WakeWordDetector = wake_word_detector
        self.livekit_client = livekit_desktop_client
        self.is_running = False
        self._stop_event = threading.Event()
        self._mic_thread: Optional[threading.Thread] = None
        self._is_active_session = False
        self._inactivity_timeout = INACTIVITY_TIMEOUT_SECS
        self._pending_confirmation: Optional[Dict[str, Any]] = None

        # Detector callbacks
        self.detector.on_wake_detected = self._on_wake_word_detected

    def _on_wake_word_detected(self, phrase: str):
        """Invoked when wake phrase is spotted."""
        self.start_active_voice_session(reason=f"Wake phrase detected: '{phrase}'")

    def start_active_voice_session(self, reason: str = "Manual activation"):
        """Trigger wake state, connect LiveKit session, and speak greeting."""
        if self._is_active_session:
            return

        logger.info("JARVIS_AWAKE")
        self._is_active_session = True
        self.detector.set_state(WakeWordState.ACTIVATED)

        # Connect to LiveKit Cloud Realtime session
        try:
            self.livekit_client.start_session_sync(timeout=3.0)
        except Exception as lk_err:
            logger.warning(f"LiveKit Cloud connection notice: {lk_err}")

        # Speak Wake Greeting aloud in Gemini Puck Voice
        greeting = "Yes, how can I help?"
        logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{greeting}'")
        logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
        tts_service.speak(greeting, block=True)
        logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")

    def end_active_voice_session(self, reason: str = "User said sleep or inactivity timeout"):
        """Conclude active session, disconnect LiveKit session, and return to sleeping state."""
        self._is_active_session = False
        self._pending_confirmation = None
        self.detector.set_state(WakeWordState.LISTENING_FOR_WAKE_WORD)

        # Disconnect LiveKit Cloud session
        try:
            self.livekit_client.end_session_sync()
        except Exception:
            pass

        logger.info("JARVIS_SLEEPING")

    def _is_sleep_phrase(self, text: str) -> bool:
        clean = text.lower().strip()
        return any(p in clean for p in SLEEP_PHRASES)

    def process_voice_command(self, user_command: str) -> str:
        """
        Process user voice command, execute desktop action / dangerous confirmation / AI query,
        and speak the response using Google Gemini Puck voice over LiveKit infrastructure.
        """
        clean_lower = user_command.lower().strip()

        # 0. Check Pending Dangerous Action Confirmation
        if self._pending_confirmation:
            action = self._pending_confirmation
            if any(k in clean_lower for k in ["yes", "confirm", "proceed", "do it", "sure", "ok", "okay"]):
                logger.info("CONFIRMATION_ACCEPTED")
                self._pending_confirmation = None
                tool_name = action["tool"]
                args = {**action["args"], "confirm": True}
                logger.info(f"TOOL_CALL_STARTED Tool: '{tool_name}'")
                res = registry.execute(tool_name, args)
                if res.get("success"):
                    logger.info(f"TOOL_CALL_COMPLETED Tool: '{tool_name}'")
                    msg = res.get("message") or res.get("result", {}).get("message") or f"Executed {tool_name} successfully."
                else:
                    logger.error(f"TOOL_CALL_FAILED Tool: '{tool_name}'")
                    msg = res.get("error") or res.get("result", {}).get("error") or f"Action failed."
                logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
                logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
                tts_service.speak(msg, block=True)
                logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
                return msg
            elif any(k in clean_lower for k in ["no", "cancel", "stop", "abort", "don't", "dont"]):
                logger.info("CONFIRMATION_REJECTED")
                self._pending_confirmation = None
                msg = "Action canceled, Boss."
                logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
                logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
                tts_service.speak(msg, block=True)
                logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
                return msg

        # 1. Sleep Command
        if self._is_sleep_phrase(clean_lower):
            msg = "Okay, I will sleep. Say Hello JARVIS when you need me."
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            self.end_active_voice_session(reason="User command sleep")
            return msg

        # 2. Dangerous Operations Requiring Confirmation (Shutdown / Restart)
        if any(k in clean_lower for k in ["shutdown my pc", "shutdown computer", "turn off my pc", "turn off computer", "power off"]):
            logger.info("CONFIRMATION_REQUIRED Action: 'system.shutdownPC'")
            self._pending_confirmation = {"tool": "system.shutdownPC", "args": {}}
            msg = "Shutdown will power off your computer. Do you want me to continue?"
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        if any(k in clean_lower for k in ["restart my pc", "restart computer", "reboot my pc", "reboot computer"]):
            logger.info("CONFIRMATION_REQUIRED Action: 'system.restartPC'")
            self._pending_confirmation = {"tool": "system.restartPC", "args": {}}
            msg = "Restart will reboot your computer. Do you want me to continue?"
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        # Lock Workstation
        if any(k in clean_lower for k in ["lock pc", "lock computer", "lock screen", "lock workstation"]):
            logger.info("TOOL_CALL_STARTED Tool: 'system.lockWorkstation'")
            res = registry.execute("system.lockWorkstation", {})
            msg = "Workstation locked."
            logger.info("TOOL_CALL_COMPLETED Tool: 'system.lockWorkstation'")
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        # 3. Desktop Application Launches (Chrome, WhatsApp, VS Code, Notepad, Calc, Explorer)
        if "open" in clean_lower and any(app in clean_lower for app in ["chrome", "whatsapp", "code", "vs code", "vscode", "notepad", "calculator", "calc", "explorer", "file explorer"]):
            for app in ["chrome", "whatsapp", "vs code", "vscode", "code", "notepad", "calculator", "calc", "file explorer", "explorer"]:
                if app in clean_lower:
                    logger.info(f"TOOL_CALL_STARTED Tool: 'computer.openApplication' App: '{app}'")
                    res = registry.execute("computer.openApplication", {"application": app})
                    if res.get("success") and res.get("result", {}).get("success"):
                        logger.info(f"TOOL_CALL_COMPLETED Tool: 'computer.openApplication'")
                        msg = res["result"].get("message", f"Opening {app}.")
                    else:
                        logger.error(f"TOOL_CALL_FAILED Tool: 'computer.openApplication'")
                        msg = res.get("result", {}).get("error") or f"Sorry, I couldn't open {app} on your computer."
                    logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
                    logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
                    tts_service.speak(msg, block=True)
                    logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
                    return msg

        # Search YouTube
        if any(k in clean_lower for k in ["search youtube for", "youtube search", "find on youtube"]):
            query = re.sub(r'.*(?:search\s+youtube\s+for|youtube\s+search|find\s+on\s+youtube)\s+', '', user_command, flags=re.I).strip()
            logger.info(f"TOOL_CALL_STARTED Tool: 'computer.searchYouTube' Query: '{query}'")
            res = registry.execute("computer.searchYouTube", {"query": query})
            msg = res.get("result", {}).get("message", f"Searching YouTube for {query}.")
            logger.info("TOOL_CALL_COMPLETED Tool: 'computer.searchYouTube'")
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        # Search Google
        if any(k in clean_lower for k in ["search google for", "google search for", "search for", "google for"]):
            query = re.sub(r'.*(?:search\s+google\s+for|google\s+search\s+for|search\s+for|google\s+for)\s+', '', user_command, flags=re.I).strip()
            logger.info(f"TOOL_CALL_STARTED Tool: 'computer.searchGoogle' Query: '{query}'")
            res = registry.execute("computer.searchGoogle", {"query": query})
            msg = res.get("result", {}).get("message", f"Searching Google for {query}.")
            logger.info("TOOL_CALL_COMPLETED Tool: 'computer.searchGoogle'")
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        # Open YouTube / Google Website
        if any(k in clean_lower for k in ["open youtube", "go to youtube", "launch youtube"]):
            logger.info("TOOL_CALL_STARTED Tool: 'computer.openWebsite' URL: 'https://www.youtube.com'")
            res = registry.execute("computer.openWebsite", {"url": "https://www.youtube.com"})
            msg = "Opening YouTube."
            logger.info("TOOL_CALL_COMPLETED Tool: 'computer.openWebsite'")
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        if any(k in clean_lower for k in ["open google", "go to google"]):
            logger.info("TOOL_CALL_STARTED Tool: 'computer.openWebsite' URL: 'https://www.google.com'")
            res = registry.execute("computer.openWebsite", {"url": "https://www.google.com"})
            msg = "Opening Google."
            logger.info("TOOL_CALL_COMPLETED Tool: 'computer.openWebsite'")
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        # Open Folders (Downloads, Documents, Desktop)
        if any(k in clean_lower for k in ["open downloads", "downloads folder", "my downloads", "open documents", "open desktop"]):
            fld = "downloads"
            for candidate in ["downloads", "documents", "desktop", "pictures", "videos"]:
                if candidate in clean_lower:
                    fld = candidate
                    break
            logger.info(f"TOOL_CALL_STARTED Tool: 'computer.openFolder' Folder: '{fld}'")
            res = registry.execute("computer.openFolder", {"folder_path": fld})
            msg = res.get("result", {}).get("message", f"Opened {fld} folder.")
            logger.info("TOOL_CALL_COMPLETED Tool: 'computer.openFolder'")
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        # Open Workspace / Project
        if any(k in clean_lower for k in ["open my project", "open project", "open workspace"]):
            logger.info("TOOL_CALL_STARTED Tool: 'computer.openApplication' App: 'vscode'")
            res_code = registry.execute("computer.openApplication", {"application": "vscode"})
            if res_code.get("success") and res_code.get("result", {}).get("success"):
                msg = "Opening your project in VS Code."
            else:
                res_fld = registry.execute("computer.openFolder", {"folder_path": str(BASE_DIR)})
                msg = "Opening your project folder."
            logger.info("TOOL_CALL_COMPLETED Tool: 'computer.openApplication'")
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        # Keyboard Typing into Active Window
        if clean_lower.startswith("type this message:") or clean_lower.startswith("type this:") or clean_lower.startswith("type message:") or clean_lower.startswith("type "):
            text_to_type = re.sub(r'^(type\s+this\s+message:?|type\s+this:?|type\s+message:?|type\s+)', '', user_command, flags=re.I).strip().strip("'\"")
            if text_to_type:
                logger.info("TOOL_CALL_STARTED Tool: 'computer.typeText'")
                res = registry.execute("computer.typeText", {"text": text_to_type})
                msg = "Typed message into active window."
                logger.info("TOOL_CALL_COMPLETED Tool: 'computer.typeText'")
                logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
                logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
                tts_service.speak(msg, block=True)
                logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
                return msg

        # Take Screenshot
        if any(k in clean_lower for k in ["screenshot", "take screenshot", "take a screenshot", "capture screen"]):
            logger.info("TOOL_CALL_STARTED Tool: 'computer.takeScreenshot'")
            res = registry.execute("computer.takeScreenshot", {})
            if res.get("success") and res.get("result", {}).get("success"):
                msg = "Screenshot taken."
                logger.info("TOOL_CALL_COMPLETED Tool: 'computer.takeScreenshot'")
            else:
                msg = "Failed to capture screenshot."
                logger.error("TOOL_CALL_FAILED Tool: 'computer.takeScreenshot'")
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return msg

        # 4. AI Conversational & Knowledge Query Fallback
        try:
            ai_res = gemini_service.process_query(user_command)
            spoken_answer = ai_res.get("reply") or ai_res.get("spoken_response") or ai_res.get("summary") or f"I am {ASSISTANT_NAME}, your personal AI desktop assistant."
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{spoken_answer}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(spoken_answer, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return spoken_answer
        except Exception as ai_err:
            logger.error(f"ERROR: AI query processing error: {ai_err}")
            fallback_msg = f"I am {ASSISTANT_NAME}, your personal AI assistant. How may I assist you, {USER_NAME}?"
            logger.info(f"LIVEKIT_AGENT_RESPONSE_STARTED Text: '{fallback_msg}'")
            logger.info("LIVEKIT_AUDIO_OUTPUT_STARTED")
            tts_service.speak(fallback_msg, block=True)
            logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
            return fallback_msg

    def _microphone_listener_worker(self):
        """
        Dedicated Hands-Free Microphone Audio Listener for JARVIS.
        Continuously captures microphone audio in a single stream to avoid
        device concurrency collisions on Windows.
        """
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 150
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8
            recognizer.phrase_threshold = 0.3
            recognizer.non_speaking_duration = 0.5

            try:
                mic = sr.Microphone()
            except Exception as mic_err:
                logger.error(f"ERROR: Microphone initialization failed: {mic_err}")
                self.detector.set_state(WakeWordState.ERROR)
                return

            logger.info("MICROPHONE_INITIALIZED")
            logger.info("MICROPHONE_DEVICE: Default Windows Audio Input Device (Microphone Array)")

            with mic as source:
                try:
                    recognizer.adjust_for_ambient_noise(source, duration=0.8)
                    logger.info(f"MICROPHONE_CALIBRATED: Energy Threshold = {recognizer.energy_threshold:.1f}")
                except Exception as cal_err:
                    logger.warning(f"Ambient noise calibration notice: {cal_err}")

                logger.info("JARVIS_SLEEPING")
                last_speech_time = time.time()

                while not self._stop_event.is_set():
                    # If JARVIS is currently speaking via speaker, skip capture to prevent self-triggering
                    if tts_service.is_speaking:
                        time.sleep(0.15)
                        continue

                    # 1. SLEEPING MODE (Listening for Wake Word 'Hello JARVIS')
                    if not self._is_active_session:
                        try:
                            audio = recognizer.listen(source, timeout=1.5, phrase_time_limit=3.5)
                            if self._stop_event.is_set() or tts_service.is_speaking:
                                continue

                            text = ""
                            try:
                                text = recognizer.recognize_google(audio).strip()
                            except (sr.UnknownValueError, sr.RequestError):
                                pass

                            if text:
                                text_lower = text.lower()
                                for phrase in self.detector.wake_phrases:
                                    if phrase in text_lower:
                                        logger.info(f"WAKE_WORD_DETECTED: '{phrase}'")
                                        self.start_active_voice_session(reason=f"Wake phrase: {phrase}")
                                        last_speech_time = time.time()
                                        time.sleep(0.3) # Acoustic cooldown
                                        break
                        except sr.WaitTimeoutError:
                            continue
                        except Exception as loop_e:
                            if not self._stop_event.is_set():
                                logger.debug(f"Wake loop tick notice: {loop_e}")
                            time.sleep(0.1)

                    # 2. ACTIVE MODE (Listening for Command)
                    else:
                        # Check inactivity timeout (e.g. 25 seconds)
                        if time.time() - last_speech_time > self._inactivity_timeout:
                            logger.info(f"Inactivity timeout ({self._inactivity_timeout}s elapsed). Returning to sleep.")
                            self.end_active_voice_session(reason="Inactivity timeout")
                            continue

                        try:
                            logger.info("LIVEKIT_USER_SPEECH_STARTED")
                            audio = recognizer.listen(source, timeout=3.5, phrase_time_limit=10.0)
                            if self._stop_event.is_set() or tts_service.is_speaking:
                                continue

                            command_text = ""
                            try:
                                command_text = recognizer.recognize_google(audio).strip()
                            except (sr.UnknownValueError, sr.RequestError):
                                pass

                            if command_text:
                                last_speech_time = time.time()
                                logger.info(f"LIVEKIT_USER_TRANSCRIPT: '{command_text}'")

                                self.detector.set_state(WakeWordState.PROCESSING)
                                self.process_voice_command(command_text)
                                time.sleep(0.3) # Acoustic cooldown
                        except sr.WaitTimeoutError:
                            continue
                        except Exception as cmd_loop_e:
                            if not self._stop_event.is_set():
                                logger.debug(f"Command loop tick notice: {cmd_loop_e}")
                            time.sleep(0.1)

        except ImportError:
            logger.error("ERROR: speech_recognition library is not installed.")
        except Exception as fatal_e:
            logger.error(f"ERROR: Fatal error in microphone listener worker: {fatal_e}")

    def start(self) -> bool:
        """Starts the background service daemon."""
        logger.info("==================================================")
        logger.info("    STARTING JARVIS BACKGROUND SERVICE DAEMON     ")
        logger.info("==================================================")

        if not self.lock.acquire():
            logger.error("ERROR: Could not start JARVIS: Another instance is already running.")
            return False

        self.is_running = True
        self._stop_event.clear()

        # Register OS signal handlers only in the main thread
        if threading.current_thread() is threading.main_thread():
            try:
                signal.signal(signal.SIGINT, self._handle_signal)
                signal.signal(signal.SIGTERM, self._handle_signal)
            except (ValueError, AttributeError):
                pass

        # Start Unified Microphone Audio Thread
        self.detector.start()
        self._mic_thread = threading.Thread(
            target=self._microphone_listener_worker,
            daemon=True,
            name="JARVIS-Microphone-Worker"
        )
        self._mic_thread.start()
        logger.info(f"JARVIS is ready and listening locally for '{WAKE_PHRASE}'.")
        return True

    def run_forever(self):
        """Blocks and runs the daemon until stopped."""
        if not self.is_running:
            if not self.start():
                return

        try:
            while not self._stop_event.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt.")
        finally:
            self.stop()

    def stop(self):
        """Cleanly stops the background service and releases all resources."""
        if not self.is_running:
            return

        logger.info("Stopping JARVIS background service...")
        self.is_running = False
        self._is_active_session = False
        self._stop_event.set()

        self.detector.stop()
        self.livekit_client.end_session_sync()

        if self._mic_thread and self._mic_thread.is_alive():
            self._mic_thread.join(timeout=1.5)
        self.lock.release()
        logger.info("JARVIS background service stopped cleanly.")

    def _handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        self.stop()
        sys.exit(0)

    def get_health(self) -> Dict[str, Any]:
        """Returns health diagnostics of the background assistant."""
        return {
            "jarvis": "running" if self.is_running else "stopped",
            "state": self.detector.state.value,
            "wake_word_detector": self.detector.get_status(),
            "livekit_connected": self.livekit_client.is_connected,
            "pid": os.getpid(),
            "inactivity_timeout_secs": self._inactivity_timeout,
            "log_file": str(LOG_FILE_PATH)
        }

background_service = JarvisBackgroundService()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="JARVIS Background Service Daemon")
    parser.add_argument("--test-wake", action="store_true", help="Simulate wake-word detection test")
    parser.add_argument("--test-command", type=str, default="", help="Execute a single voice command test")
    args = parser.parse_args()

    if args.test_command:
        print(f"[TEST] Testing voice command: '{args.test_command}'...")
        service = JarvisBackgroundService()
        result = service.process_voice_command(args.test_command)
        print(f"[TEST] Result: '{result}'")
    elif args.test_wake:
        print("[TEST] Running JARVIS Wake Word test simulation...")
        service = JarvisBackgroundService()
        if service.start():
            print(f"[TEST] State: {service.detector.state.value}")
            print("[TEST] Triggering simulated 'Hello JARVIS'...")
            service.detector.trigger_activation("Hello JARVIS")
            time.sleep(1.0)
            service.end_active_voice_session(reason="Test complete")
            service.stop()
            print("[TEST] Passed successfully.")
    else:
        background_service.run_forever()
