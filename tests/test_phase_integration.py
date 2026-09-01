import os
import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import mask_secret, LOG_FILE_PATH, is_livekit_configured, is_gemini_configured
from backend.voice.wake_word_detector import WakeWordDetector, WakeWordState
from backend.background_service import JarvisBackgroundService
from backend.services.startup_service import startup_service
from backend.services.memory_service import memory_service
from backend.kernel.planner import task_planner
from backend.kernel.permission_engine import permission_engine, RiskLevel
from backend.voice.livekit_tools import execute_jarvis_tool
from backend.tools.computer_tools import take_screenshot
from backend.tools.system_tools import get_diagnostics

class TestJarvisPhaseIntegration(unittest.TestCase):
    """
    Comprehensive Integration Test Suite for Phases 1 through 8.
    """

    # --- PHASE 1: LOCAL WAKE WORD & BACKGROUND SERVICE ---
    def test_phase1_wake_word_and_daemon(self):
        detector = WakeWordDetector(debounce_seconds=0.2)
        self.assertEqual(detector.state, WakeWordState.IDLE)

        # Trigger activation
        activated = detector.trigger_activation("Hello JARVIS")
        self.assertTrue(activated)
        self.assertEqual(detector.state, WakeWordState.ACTIVATED)

        # Pause and resume
        detector.pause()
        self.assertTrue(detector.is_paused)
        detector.resume()
        self.assertFalse(detector.is_paused)
        self.assertEqual(detector.state, WakeWordState.LISTENING_FOR_WAKE_WORD)

    # --- PHASE 2: LIVEKIT REALTIME CONFIG & TOOL BRIDGE ---
    def test_phase2_livekit_and_tools_contract(self):
        self.assertTrue(is_livekit_configured())
        self.assertTrue(is_gemini_configured())

        # Test tool contract returns structured {"success": bool, "result": ..., "error": ...}
        res = execute_jarvis_tool("system.getDiagnostics", {})
        self.assertIn("success", res)
        self.assertTrue(res["success"])
        self.assertIn("cpu_usage", res["result"])

    # --- PHASE 3: COMPUTER CONTROL & PERMISSIONS ---
    def test_phase3_computer_tools_and_permissions(self):
        # Open app is LOW_RISK
        allowed, reason, level = permission_engine.check_permission("computer.openApplication", {"application": "notepad"})
        self.assertEqual(level, RiskLevel.LOW_RISK)
        self.assertTrue(allowed)

        # Destructive tool check
        allowed_d, reason_d, level_d = permission_engine.check_permission("nonexistent.tool", {})
        self.assertFalse(allowed_d)

    # --- PHASE 4: SCREEN UNDERSTANDING & SCREENSHOT ---
    def test_phase4_screenshot_capture(self):
        res = take_screenshot()
        self.assertIn("data_url", res)
        self.assertEqual(res.get("status"), "SCREENSHOT_CAPTURED")

    # --- PHASE 5: MULTI-STEP TASK PLANNER & RECOVERY ---
    def test_phase5_multistep_planner(self):
        plan = task_planner.plan("Open Chrome and search for Python tutorials")
        self.assertIsNotNone(plan)
        self.assertTrue(len(plan.steps) >= 1)
        self.assertIn(plan.agent_category, ["computer", "browser"])

    # --- PHASE 6: WINDOWS SYSTEM STARTUP & HEALTH ---
    def test_phase6_startup_service_and_health(self):
        status = startup_service.get_status()
        self.assertIn("startup_enabled", status)
        self.assertIn("startup_path", status)

        bg = JarvisBackgroundService()
        health = bg.get_health()
        self.assertIn("jarvis", health)
        self.assertIn("wake_word_detector", health)

    # --- PHASE 7: MEMORY VAULT & CONTEXT ---
    def test_phase7_memory_vault_lifecycle(self):
        # Store memory
        store_res = memory_service.store_memory(
            key="preferred_code_editor",
            value="VS Code"
        )
        self.assertTrue(store_res.get("success", False))

        # Search memory
        memories = memory_service.search_memory(query="preferred_code_editor")
        self.assertTrue(any("VS Code" in str(m.get("value")) for m in memories))

        # Forget memory
        del_res = memory_service.delete_memory("preferred_code_editor")
        self.assertTrue(del_res)

    # --- PHASE 8: PRODUCTION HARDENING & SECURITY REDACTION ---
    def test_phase8_production_hardening_and_redaction(self):
        # Secret masking test with safe synthetic token
        masked = mask_secret("test_secret_token_abcdef123456_xyz", show_chars=4)
        self.assertTrue(masked.startswith("test..."))
        self.assertTrue(masked.endswith("_xyz"))
        self.assertNotIn("abcdef123456", masked)

        # Log directory exists
        self.assertTrue(LOG_FILE_PATH.parent.exists())

if __name__ == "__main__":
    unittest.main()
