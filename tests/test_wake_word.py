import time
import unittest
from pathlib import Path

from backend.voice.wake_word_detector import WakeWordDetector, WakeWordState
from backend.background_service import SingleInstanceLock, JarvisBackgroundService

class TestWakeWordAndBackground(unittest.TestCase):
    """
    Unit test suite for Phase 1: Local Wake Word Engine and Background Service.
    """

    def setUp(self):
        self.detector = WakeWordDetector(
            wake_phrases=["hello jarvis", "jarvis"],
            debounce_seconds=0.5
        )

    def tearDown(self):
        if self.detector.is_running:
            self.detector.stop()

    def test_01_initial_state(self):
        """Verify initial state is IDLE."""
        self.assertEqual(self.detector.state, WakeWordState.IDLE)
        self.assertFalse(self.detector.is_running)
        self.assertFalse(self.detector.is_paused)

    def test_02_state_transitions(self):
        """Verify state machine transitions cleanly."""
        state_history = []

        def on_change(new_s, old_s):
            state_history.append((old_s, new_s))

        self.detector.on_state_change = on_change

        self.detector.set_state(WakeWordState.LISTENING_FOR_WAKE_WORD)
        self.assertEqual(self.detector.state, WakeWordState.LISTENING_FOR_WAKE_WORD)

        self.detector.set_state(WakeWordState.ACTIVATED)
        self.assertEqual(self.detector.state, WakeWordState.ACTIVATED)

        self.detector.set_state(WakeWordState.PROCESSING)
        self.assertEqual(self.detector.state, WakeWordState.PROCESSING)

        self.detector.set_state(WakeWordState.SPEAKING)
        self.assertEqual(self.detector.state, WakeWordState.SPEAKING)

        self.detector.set_state(WakeWordState.IDLE)
        self.assertEqual(self.detector.state, WakeWordState.IDLE)

        self.assertEqual(len(state_history), 5)
        self.assertEqual(state_history[0], (WakeWordState.IDLE, WakeWordState.LISTENING_FOR_WAKE_WORD))

    def test_03_trigger_activation_and_debouncing(self):
        """Verify trigger activation works and rapid duplicate triggers are debounced."""
        triggered = []

        def on_wake(phrase):
            triggered.append(phrase)

        self.detector.on_wake_detected = on_wake

        # First trigger should succeed
        res1 = self.detector.trigger_activation("Hello JARVIS")
        self.assertTrue(res1)
        self.assertEqual(self.detector.state, WakeWordState.ACTIVATED)
        self.assertEqual(len(triggered), 1)

        # Immediate second trigger within debounce window should be suppressed
        res2 = self.detector.trigger_activation("Hello JARVIS")
        self.assertFalse(res2)
        self.assertEqual(len(triggered), 1)

        # Wait past debounce window
        time.sleep(0.6)
        res3 = self.detector.trigger_activation("Hello JARVIS")
        self.assertTrue(res3)
        self.assertEqual(len(triggered), 2)

    def test_04_microphone_lifecycle_pause_resume(self):
        """Verify microphone ownership lifecycle can pause and resume."""
        self.detector.start()
        self.assertTrue(self.detector.is_running)
        self.assertFalse(self.detector.is_paused)
        self.assertEqual(self.detector.state, WakeWordState.LISTENING_FOR_WAKE_WORD)

        # Pause detector when active voice session starts
        self.detector.pause()
        self.assertTrue(self.detector.is_paused)

        # Resume detector when active voice session ends
        self.detector.resume()
        self.assertFalse(self.detector.is_paused)
        self.assertEqual(self.detector.state, WakeWordState.LISTENING_FOR_WAKE_WORD)

        self.detector.stop()
        self.assertFalse(self.detector.is_running)
        self.assertEqual(self.detector.state, WakeWordState.IDLE)

    def test_05_single_instance_lock(self):
        """Verify single instance lock prevents multiple concurrent daemons."""
        test_lock_file = Path("test_jarvis.lock")
        if test_lock_file.exists():
            test_lock_file.unlink()

        lock1 = SingleInstanceLock(lock_file=test_lock_file)
        self.assertTrue(lock1.acquire())

        # Second lock on same file should fail
        lock2 = SingleInstanceLock(lock_file=test_lock_file)
        self.assertFalse(lock2.acquire())

        # Release first lock
        lock1.release()
        self.assertFalse(test_lock_file.exists())

    def test_06_background_service_health_diagnostics(self):
        """Verify background service health status returns structured data."""
        srv = JarvisBackgroundService()
        health = srv.get_health()
        self.assertIn("jarvis", health)
        self.assertIn("state", health)
        self.assertIn("wake_word_detector", health)
        self.assertIn("pid", health)

if __name__ == "__main__":
    unittest.main()
