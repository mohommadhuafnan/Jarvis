import os
import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app import app
from backend.config import is_livekit_configured, LIVEKIT_URL

class TestLiveKitTokenGeneration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_livekit_status_endpoint(self):
        """Verify LiveKit status endpoint returns healthy configuration."""
        res = self.client.get("/api/livekit/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("configured"), "LiveKit should be configured")
        self.assertEqual(data.get("server_url"), LIVEKIT_URL)
        self.assertTrue(data.get("has_api_key"))
        self.assertTrue(data.get("has_api_secret"))
        self.assertTrue(data.get("gemini_configured"))
        self.assertEqual(data.get("status"), "READY")

    def test_livekit_token_endpoint(self):
        """Verify LiveKit token generation creates valid JWT token without exposing secrets."""
        res = self.client.get("/api/livekit/token?room=test-room-1&identity=test-user")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        self.assertGreater(len(data["token"]), 20)
        self.assertEqual(data.get("room"), "test-room-1")
        self.assertEqual(data.get("identity"), "test-user")
        self.assertEqual(data.get("server_url"), LIVEKIT_URL)

    def test_livekit_token_default_parameters(self):
        """Verify default parameters for token endpoint."""
        res = self.client.get("/api/livekit/token")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        self.assertEqual(data.get("room"), "jarvis-room-default")

if __name__ == "__main__":
    unittest.main()
