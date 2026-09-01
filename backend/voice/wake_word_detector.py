import time
import logging
import threading
from enum import Enum
from typing import Callable, Optional, List, Dict, Any

logger = logging.getLogger("JARVIS.Voice.WakeWordDetector")

class WakeWordState(str, Enum):
    IDLE = "IDLE"
    LISTENING_FOR_WAKE_WORD = "LISTENING_FOR_WAKE_WORD"
    ACTIVATED = "ACTIVATED"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"

class WakeWordDetector:
    """
    Wake-Word State and Pattern Detection Manager for JARVIS.
    Maintains wake phrases, debouncing, and state transitions.
    """

    def __init__(
        self,
        wake_phrases: Optional[List[str]] = None,
        debounce_seconds: float = 2.0,
        on_wake_detected: Optional[Callable[[str], None]] = None,
        on_state_change: Optional[Callable[[WakeWordState, WakeWordState], None]] = None
    ):
        self.wake_phrases = [p.lower().strip() for p in (wake_phrases or ["hello jarvis", "hey jarvis", "jarvis", "ok jarvis"])]
        self.debounce_seconds = debounce_seconds
        self.on_wake_detected = on_wake_detected
        self.on_state_change = on_state_change

        self._state: WakeWordState = WakeWordState.IDLE
        self._state_lock = threading.Lock()
        self._is_running = False
        self._is_paused = False
        self._last_trigger_time: float = 0.0
        self._stop_event = threading.Event()
        self._last_error: Optional[str] = None

    @property
    def state(self) -> WakeWordState:
        with self._state_lock:
            return self._state

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def set_state(self, new_state: WakeWordState):
        """Safely transition state and trigger callback if provided."""
        old_state = self._state
        with self._state_lock:
            if self._state == new_state:
                return
            self._state = new_state

        logger.info(f"[STATE_TRANSITION] {old_state.value} -> {new_state.value}")
        if self.on_state_change:
            try:
                self.on_state_change(new_state, old_state)
            except Exception as e:
                logger.error(f"Error in on_state_change callback: {e}")

    def trigger_activation(self, phrase: str = "Hello JARVIS") -> bool:
        """
        Trigger activation manually or from detected audio.
        Applies debounce filter to prevent duplicate activations.
        """
        now = time.time()
        if now - self._last_trigger_time < self.debounce_seconds:
            logger.warning(f"WakeWordDetector: Suppressed duplicate wake word trigger ({now - self._last_trigger_time:.2f}s < {self.debounce_seconds}s)")
            return False

        self._last_trigger_time = now
        logger.info(f"WAKE_WORD_DETECTED: '{phrase}'")
        self.set_state(WakeWordState.ACTIVATED)

        if self.on_wake_detected:
            try:
                self.on_wake_detected(phrase)
            except Exception as e:
                logger.error(f"Error in on_wake_detected callback: {e}")

        return True

    def start(self):
        """Start local wake word detector."""
        self._stop_event.clear()
        self._is_running = True
        self._is_paused = False
        self.set_state(WakeWordState.LISTENING_FOR_WAKE_WORD)

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False
        self.set_state(WakeWordState.LISTENING_FOR_WAKE_WORD)

    def stop(self):
        """Cleanly stop the detector."""
        self._is_running = False
        self._stop_event.set()
        self.set_state(WakeWordState.IDLE)

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "is_running": self._is_running,
            "is_paused": self._is_paused,
            "wake_phrases": self.wake_phrases,
            "debounce_seconds": self.debounce_seconds,
            "last_error": self._last_error
        }

wake_word_detector = WakeWordDetector()
