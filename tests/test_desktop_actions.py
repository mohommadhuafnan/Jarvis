import unittest
from unittest.mock import patch, MagicMock
import backend.tools.computer_tools
from backend.tools.registry import registry
from backend.tools.computer_tools import (
    resolve_application_executable,
    open_application,
    open_website,
    search_google,
    search_youtube,
    open_folder
)
from backend.voice.tts_service import tts_service
from backend.background_service import background_service
from backend.services.startup_service import startup_service

class TestDesktopActions(unittest.TestCase):

    def test_resolve_known_applications(self):
        # Chrome resolution
        res_chrome = resolve_application_executable("chrome")
        self.assertIn(res_chrome["type"], ["exe", "exe_fallback"])
        self.assertEqual(res_chrome["name"], "Google Chrome")

        # Notepad resolution
        res_notepad = resolve_application_executable("notepad")
        self.assertEqual(res_notepad["type"], "exe")
        self.assertEqual(res_notepad["name"], "Notepad")

        # Calculator resolution
        res_calc = resolve_application_executable("calculator")
        self.assertIn(res_calc["type"], ["exe", "uri"])
        self.assertEqual(res_calc["name"], "Calculator")

        # Explorer resolution
        res_exp = resolve_application_executable("explorer")
        self.assertEqual(res_exp["type"], "exe")
        self.assertEqual(res_exp["name"], "File Explorer")

        # WhatsApp resolution
        res_wa = resolve_application_executable("whatsapp")
        self.assertIn(res_wa["type"], ["exe", "uri", "web"])

    def test_nonexistent_application_reporting(self):
        # Must report honest failure, never fake success
        res = open_application("completely_fake_application_xyz987")
        self.assertFalse(res["success"])
        self.assertIn("couldn't find", res["error"])

    def test_tool_registry_open_application_dual_kwargs(self):
        with patch("subprocess.Popen", return_value=MagicMock()):
            # Test with 'application' kwarg
            res1 = registry.execute("computer.openApplication", {"application": "notepad"})
            self.assertTrue(res1["success"])
            self.assertTrue(res1["result"]["success"])

            # Test with 'app_name' kwarg
            res2 = registry.execute("computer.openApplication", {"app_name": "notepad"})
            self.assertTrue(res2["success"])
            self.assertTrue(res2["result"]["success"])

    def test_website_and_search_tools(self):
        with patch("webbrowser.open", return_value=True) as mock_wb:
            # Open website
            res_web = open_website("https://youtube.com")
            self.assertTrue(res_web["success"])
            mock_wb.assert_called_with("https://youtube.com")

            # Search Google
            res_goog = search_google("React tutorials")
            self.assertTrue(res_goog["success"])
            self.assertIn("React+tutorials", res_goog["search_url"])

            # Search YouTube
            res_yt = search_youtube("Python tutorials")
            self.assertTrue(res_yt["success"])
            self.assertIn("Python+tutorials", res_yt["search_url"])

    def test_open_folder_resolution(self):
        with patch("os.startfile", return_value=None) as mock_sf:
            res = open_folder("downloads")
            self.assertTrue(res["success"])
            self.assertIn("Downloads", res["path"])

    def test_tts_text_cleaner(self):
        raw = "```python\nprint(1)\n```\nHere is a **bold** item with `code` and [link](http://test.com) 🚀"
        cleaned = tts_service.clean_text(raw)
        self.assertNotIn("```", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertIn("bold", cleaned)
        self.assertIn("code", cleaned)

    def test_sleep_phrases_recognition(self):
        self.assertTrue(background_service._is_sleep_phrase("Sleep JARVIS"))
        self.assertTrue(background_service._is_sleep_phrase("jarvis sleep"))
        self.assertTrue(background_service._is_sleep_phrase("go to sleep"))
        self.assertTrue(background_service._is_sleep_phrase("stop listening"))
        self.assertFalse(background_service._is_sleep_phrase("open chrome"))

    def test_startup_service_status(self):
        status = startup_service.get_status()
        self.assertIn("startup_enabled", status)
        self.assertIn("startup_path", status)

if __name__ == "__main__":
    unittest.main()
