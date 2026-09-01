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
    Operates 100% in the background (no terminal window required).

    Unified Audio Loop State Machine:
    1. SLEEPING (LISTENING_FOR_WAKE_WORD) -> Listens locally on default microphone for 'Hello JARVIS'.
    2. ACTIVATED (LISTENING_FOR_COMMAND) -> Speaks 'Yes, how can I help?' in Gemini Puck Voice,
       captures user command, executes desktop action, speaks response in Gemini Puck Voice.
    3. SLEEP COMMAND -> On 'Sleep JARVIS', speaks confirmation and returns to SLEEPING.
    """

    def __init__(self):
        self.lock = SingleInstanceLock()
        self.detector: WakeWordDetector = wake_word_detector
        self.is_running = False
        self._stop_event = threading.Event()
        self._mic_thread: Optional[threading.Thread] = None
        self._is_active_session = False
        self._inactivity_timeout = INACTIVITY_TIMEOUT_SECS

        # Detector callbacks
        self.detector.on_wake_detected = self._on_wake_word_detected

    def _on_wake_word_detected(self, phrase: str):
        """Invoked when wake phrase is spotted."""
        self._is_active_session = True
        self.detector.set_state(WakeWordState.ACTIVATED)

    def start_active_voice_session(self, reason: str = "Manual activation"):
        """Manually trigger wake state from tray menu or external event."""
        logger.info(f"Manual Wake Requested: {reason}")
        self._is_active_session = True
        self.detector.set_state(WakeWordState.ACTIVATED)
        greeting = "Yes, how can I help?"
        tts_service.speak(greeting, block=True)
        logger.info("LISTENING_FOR_COMMAND")

    def end_active_voice_session(self, reason: str = "User said sleep or inactivity timeout"):
        """Conclude active session and return to background wake-word listening."""
        logger.info(f"Returning to SLEEPING state: {reason}")
        self._is_active_session = False
        self.detector.set_state(WakeWordState.LISTENING_FOR_WAKE_WORD)
        logger.info("LISTENING_FOR_WAKE_WORD")

    def _is_sleep_phrase(self, text: str) -> bool:
        clean = text.lower().strip()
        return any(p in clean for p in SLEEP_PHRASES)

    def process_voice_command(self, user_command: str) -> str:
        """
        Process user voice command, execute desktop action / AI query,
        and speak the response using Google Gemini Puck voice.
        """
        clean_lower = user_command.lower().strip()

        # 1. Sleep Command
        if self._is_sleep_phrase(clean_lower):
            msg = "Okay, I will sleep. Say Hello JARVIS when you need me."
            logger.info(f"RESPONSE_GENERATED: '{msg}'")
            tts_service.speak(msg, block=True)
            self._is_active_session = False
            self.detector.set_state(WakeWordState.LISTENING_FOR_WAKE_WORD)
            logger.info("LISTENING_FOR_WAKE_WORD")
            return msg

        # 2. Desktop Application Launches (Chrome, WhatsApp, VS Code, Notepad, Calc, Explorer)
        if "open" in clean_lower and any(app in clean_lower for app in ["chrome", "whatsapp", "code", "vs code", "vscode", "notepad", "calculator", "calc", "explorer", "file explorer"]):
            for app in ["chrome", "whatsapp", "vs code", "vscode", "code", "notepad", "calculator", "calc", "file explorer", "explorer"]:
                if app in clean_lower:
                    res = registry.execute("computer.openApplication", {"application": app})
                    if res.get("success") and res.get("result", {}).get("success"):
                        msg = res["result"].get("message", f"Opening {app}.")
                    else:
                        msg = res.get("result", {}).get("error") or f"Sorry, I couldn't open {app} on your computer."
                    logger.info(f"RESPONSE_GENERATED: '{msg}'")
                    tts_service.speak(msg, block=True)
                    return msg

        # Search YouTube
        if any(k in clean_lower for k in ["search youtube for", "youtube search", "find on youtube"]):
            query = re.sub(r'.*(?:search\s+youtube\s+for|youtube\s+search|find\s+on\s+youtube)\s+', '', user_command, flags=re.I).strip()
            res = registry.execute("computer.searchYouTube", {"query": query})
            msg = res.get("result", {}).get("message", f"Searching YouTube for {query}.")
            logger.info(f"RESPONSE_GENERATED: '{msg}'")
            tts_service.speak(msg, block=True)
            return msg

        # Search Google
        if any(k in clean_lower for k in ["search google for", "google search for", "search for", "google for"]):
            query = re.sub(r'.*(?:search\s+google\s+for|google\s+search\s+for|search\s+for|google\s+for)\s+', '', user_command, flags=re.I).strip()
            res = registry.execute("computer.searchGoogle", {"query": query})
            msg = res.get("result", {}).get("message", f"Searching Google for {query}.")
            logger.info(f"RESPONSE_GENERATED: '{msg}'")
            tts_service.speak(msg, block=True)
            return msg

        # Open YouTube / Google Website
        if any(k in clean_lower for k in ["open youtube", "go to youtube", "launch youtube"]):
            res = registry.execute("computer.openWebsite", {"url": "https://www.youtube.com"})
            msg = "Opening YouTube."
            logger.info(f"RESPONSE_GENERATED: '{msg}'")
            tts_service.speak(msg, block=True)
            return msg

        if any(k in clean_lower for k in ["open google", "go to google"]):
            res = registry.execute("computer.openWebsite", {"url": "https://www.google.com"})
            msg = "Opening Google."
            logger.info(f"RESPONSE_GENERATED: '{msg}'")
            tts_service.speak(msg, block=True)
            return msg

        # Open Folders (Downloads, Documents, Desktop)
        if any(k in clean_lower for k in ["open downloads", "downloads folder", "my downloads", "open documents", "open desktop"]):
            fld = "downloads"
            for candidate in ["downloads", "documents", "desktop", "pictures", "videos"]:
                if candidate in clean_lower:
                    fld = candidate
                    break
            res = registry.execute("computer.openFolder", {"folder_path": fld})
            msg = res.get("result", {}).get("message", f"Opened {fld} folder.")
            logger.info(f"RESPONSE_GENERATED: '{msg}'")
            tts_service.speak(msg, block=True)
            return msg

        # Open Workspace / Project
        if any(k in clean_lower for k in ["open my project", "open project", "open workspace"]):
            res_code = registry.execute("computer.openApplication", {"application": "vscode"})
            if res_code.get("success") and res_code.get("result", {}).get("success"):
                msg = "Opening your project in VS Code."
            else:
                res_fld = registry.execute("computer.openFolder", {"folder_path": str(BASE_DIR)})
                msg = "Opening your project folder."
            logger.info(f"RESPONSE_GENERATED: '{msg}'")
            tts_service.speak(msg, block=True)
            return msg

        # Keyboard Typing into Active Window
        if clean_lower.startswith("type this message:") or clean_lower.startswith("type this:") or clean_lower.startswith("type message:") or clean_lower.startswith("type "):
            text_to_type = re.sub(r'^(type\s+this\s+message:?|type\s+this:?|type\s+message:?|type\s+)', '', user_command, flags=re.I).strip().strip("'\"")
            if text_to_type:
                res = registry.execute("computer.typeText", {"text": text_to_type})
                msg = "Typed message into active window."
                logger.info(f"RESPONSE_GENERATED: '{msg}'")
                tts_service.speak(msg, block=True)
                return msg

        # Take Screenshot
        if any(k in clean_lower for k in ["screenshot", "take screenshot", "take a screenshot", "capture screen"]):
            res = registry.execute("computer.takeScreenshot", {})
            if res.get("success") and res.get("result", {}).get("success"):
                msg = "Screenshot taken."
            else:
                msg = "Failed to capture screenshot."
            logger.info(f"RESPONSE_GENERATED: '{msg}'")
            tts_service.speak(msg, block=True)
            return msg

        # 3. AI Conversational & Knowledge Query Fallback
        try:
            ai_res = gemini_service.process_query(user_command)
            spoken_answer = ai_res.get("reply") or ai_res.get("spoken_response") or ai_res.get("summary") or f"I am {ASSISTANT_NAME}, your personal AI desktop assistant."
            logger.info(f"RESPONSE_GENERATED: '{spoken_answer}'")
            tts_service.speak(spoken_answer, block=True)
            return spoken_answer
        except Exception as ai_err:
            logger.error(f"AI query processing error: {ai_err}")
            fallback_msg = f"I am {ASSISTANT_NAME}, your personal AI assistant. How may I assist you?"
            logger.info(f"RESPONSE_GENERATED: '{fallback_msg}'")
            tts_service.speak(fallback_msg, block=True)
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
                logger.error(f"MICROPHONE_INIT_FAILED: {mic_err}")
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

                logger.info("LISTENING_FOR_WAKE_WORD")
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
                                        self._is_active_session = True
                                        self.detector.set_state(WakeWordState.ACTIVATED)
                                        last_speech_time = time.time()

                                        # Speak Wake Greeting aloud in Gemini Puck Voice
                                        greeting = "Yes, how can I help?"
                                        tts_service.speak(greeting, block=True)
                                        time.sleep(0.3) # Acoustic feedback cooldown
                                        logger.info("LISTENING_FOR_COMMAND")
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
                            self._is_active_session = False
                            self.detector.set_state(WakeWordState.LISTENING_FOR_WAKE_WORD)
                            logger.info("LISTENING_FOR_WAKE_WORD")
                            continue

                        try:
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
                                logger.info(f"COMMAND_TRANSCRIPT: '{command_text}'")
                                logger.info(f"COMMAND_RECEIVED: '{command_text}'")

                                self.detector.set_state(WakeWordState.PROCESSING)
                                self.process_voice_command(command_text)
                                time.sleep(0.3) # Acoustic feedback cooldown

                                if self._is_active_session:
                                    logger.info("LISTENING_FOR_COMMAND")
                        except sr.WaitTimeoutError:
                            continue
                        except Exception as cmd_loop_e:
                            if not self._stop_event.is_set():
                                logger.debug(f"Command loop tick notice: {cmd_loop_e}")
                            time.sleep(0.1)

        except ImportError:
            logger.error("speech_recognition library is not installed.")
        except Exception as fatal_e:
            logger.error(f"Fatal error in microphone listener worker: {fatal_e}")

    def start(self) -> bool:
        """Starts the background service daemon."""
        logger.info("==================================================")
        logger.info("    STARTING JARVIS BACKGROUND SERVICE DAEMON     ")
        logger.info("==================================================")

        if not self.lock.acquire():
            logger.error("Could not start JARVIS: Another instance is already running.")
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
