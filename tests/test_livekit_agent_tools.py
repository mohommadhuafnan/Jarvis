import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
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
import backend.tools.whatsapp_tools
import backend.tools.knowledge_tools

from backend.voice.livekit_tools import execute_jarvis_tool
from backend.tools.registry import registry

class TestLiveKitAgentTools(unittest.TestCase):
    def test_structured_tool_execution_success(self):
        """Verify tools return structured dictionary with success=True on valid calls."""
        res = execute_jarvis_tool("files.list", {})
        self.assertIsInstance(res, dict)
        self.assertTrue(res.get("success"))
        self.assertIn("result", res)

    def test_structured_tool_execution_time(self):
        """Verify system time tool executes accurately."""
        res = execute_jarvis_tool("system.getTime", {})
        self.assertTrue(res.get("success"))
        self.assertIn("time", res.get("result", {}))

    def test_memory_storage_and_search_tools(self):
        """Verify memory storage and retrieval through livekit tool execution bridge."""
        store_res = execute_jarvis_tool("memory.store", {
            "key": "test_favorite_fruit",
            "value": "Mango",
            "category": "preference"
        })
        self.assertTrue(store_res.get("success"))

        search_res = execute_jarvis_tool("memory.search", {
            "query": "fruit"
        })
        self.assertTrue(search_res.get("success"))

    def test_permission_gated_tool(self):
        """Verify sensitive tools like delete or high-risk actions are properly gated."""
        # Files delete is HIGH_RISK or require confirmation
        defn = registry.get_definition("files.delete")
        if defn:
            res = execute_jarvis_tool("files.delete", {"filename": "test.txt"})
            self.assertFalse(res.get("success"))
            self.assertTrue(res.get("confirmation_required"))

    def test_shutdown_pc_confirmation_gating(self):
        """Verify shutdown requires confirmation before executing."""
        res = execute_jarvis_tool("system.shutdownPC", {"confirm": False})
        self.assertFalse(res.get("success"))
        self.assertTrue(res.get("confirmation_required"))
        self.assertEqual(res.get("risk_level"), "CONFIRM")

        tool_direct = registry.execute("system.shutdownPC", {"confirm": False})
        self.assertFalse(tool_direct.get("result", {}).get("success"))
        self.assertTrue(tool_direct.get("result", {}).get("confirmation_required"))
        self.assertIn("Shutdown will power off your computer", str(tool_direct))

    def test_restart_pc_confirmation_gating(self):
        """Verify restart requires confirmation before executing."""
        res = execute_jarvis_tool("system.restartPC", {"confirm": False})
        self.assertFalse(res.get("success"))
        self.assertTrue(res.get("confirmation_required"))
        self.assertEqual(res.get("risk_level"), "CONFIRM")

        tool_direct = registry.execute("system.restartPC", {"confirm": False})
        self.assertFalse(tool_direct.get("result", {}).get("success"))
        self.assertTrue(tool_direct.get("result", {}).get("confirmation_required"))
        self.assertIn("Restart will reboot your computer", str(tool_direct))

    def test_lock_workstation_tool_registration(self):
        """Verify lock workstation tool is registered."""
        defn = registry.get_definition("system.lockWorkstation")
        self.assertIsNotNone(defn)

    def test_livekit_desktop_client_token(self):
        """Verify LiveKit token generation."""
        from backend.voice.livekit_client import livekit_desktop_client
        token = livekit_desktop_client.generate_token(identity="test-user")
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 50)

if __name__ == "__main__":
    unittest.main()
