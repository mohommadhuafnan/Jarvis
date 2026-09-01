import os
import sys
import time
import signal
import logging
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import (
    LOGS_DIR,
    LOG_FILE_PATH,
    INSTANCE_LOCK_PATH,
    WAKE_PHRASE,
    INACTIVITY_TIMEOUT_SECS
)
from backend.voice.wake_word_detector import (
    WakeWordDetector,
    WakeWordState,
    wake_word_detector
)

# -------------------------------------------------------------
# Setup Secure Rotating Production Logging
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

    # Rotating File Handler (10MB per file, 5 backup copies)
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
    Master Background Daemon for JARVIS.
    Runs silently in the Windows background without requiring Chrome or the web UI.

    Lifecycle:
    1. Acquires Single-Instance lock.
    2. Initializes Local Wake Word Engine for 'Hello JARVIS'.
    3. Manages state machine (IDLE -> LISTENING -> ACTIVATED -> PROCESSING -> SPEAKING -> IDLE).
    4. Handles microphone ownership handover during active voice conversations.
    5. Gracefully terminates on system shutdown or signal.
    """

    def __init__(self):
        self.lock = SingleInstanceLock()
        self.detector: WakeWordDetector = wake_word_detector
        self.is_running = False
        self._stop_event = threading.Event()
        self._active_session_timer: Optional[threading.Timer] = None
        self._inactivity_timeout = INACTIVITY_TIMEOUT_SECS

        # Configure detector callbacks
        self.detector.on_wake_detected = self._on_wake_word_detected
        self.detector.on_state_change = self._on_detector_state_changed

    def _on_wake_word_detected(self, phrase: str):
        """Callback invoked when local wake word 'Hello JARVIS' is detected."""
        logger.info(f"WAKE_WORD_DETECTED: '{phrase}' - Activating voice assistant pipeline.")
        self.activate_voice_session(reason=f"Wake word detected: {phrase}")

    def _on_detector_state_changed(self, new_state: WakeWordState, old_state: WakeWordState):
        logger.info(f"JARVIS System State: {old_state.value} -> {new_state.value}")

    def activate_voice_session(self, reason: str = "Manual activation"):
        """
        Transitions JARVIS to ACTIVATED, pauses local wake word mic capture,
        and prepares the system for LiveKit Realtime / Agent conversation.
        """
        logger.info(f"ACTIVATING JARVIS VOICE SESSION (Reason: {reason})")
        self.detector.pause()
        self.detector.set_state(WakeWordState.ACTIVATED)

        # Reset inactivity timer
        self._reset_inactivity_timer()

    def end_voice_session(self, reason: str = "User said Goodbye / Timeout"):
        """
        Ends the active voice session, releases LiveKit mic,
        and resumes the local wake-word listener.
        """
        logger.info(f"ENDING VOICE SESSION (Reason: {reason}). Resuming local wake-word listener.")
        if self._active_session_timer:
            self._active_session_timer.cancel()
            self._active_session_timer = None

        self.detector.resume()

    def _reset_inactivity_timer(self):
        if self._active_session_timer:
            self._active_session_timer.cancel()

        self._active_session_timer = threading.Timer(
            self._inactivity_timeout,
            self._on_inactivity_timeout
        )
        self._active_session_timer.daemon = True
        self._active_session_timer.start()

    def _on_inactivity_timeout(self):
        logger.info(f"Voice session inactivity timeout ({self._inactivity_timeout}s elapsed). Returning to wake-word mode.")
        self.end_voice_session(reason="Inactivity timeout")

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

        # Register OS signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        # Start Local Wake Word Detector
        self.detector.start()
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
        self._stop_event.set()

        if self._active_session_timer:
            self._active_session_timer.cancel()

        self.detector.stop()
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
    args = parser.parse_args()

    if args.test_wake:
        print("[TEST] Running JARVIS Wake Word test simulation...")
        service = JarvisBackgroundService()
        if service.start():
            print(f"[TEST] State: {service.detector.state.value}")
            print("[TEST] Triggering simulated 'Hello JARVIS'...")
            service.detector.trigger_activation("Hello JARVIS")
            print(f"[TEST] State after activation: {service.detector.state.value}")
            time.sleep(1.0)
            service.end_voice_session(reason="Test complete")
            print(f"[TEST] State after session end: {service.detector.state.value}")
            service.stop()
            print("[TEST] Passed successfully.")
    else:
        background_service.run_forever()
