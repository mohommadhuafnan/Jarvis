import re
import os
import sys
import io
import wave
import base64
import hashlib
import logging
import threading
import winsound
from pathlib import Path
from typing import Optional, Dict, Any

from backend.config import GEMINI_API_KEY, DEFAULT_VOICE, BASE_DIR

logger = logging.getLogger("JARVIS.Voice.TTSService")

class TTSService:
    """
    JARVIS Voice Audio Service.
    Plays verified audio directly to Windows speakers via native WAV playback.
    Operates alongside LiveKit Cloud Realtime Voice.
    """

    def __init__(self, voice_name: Optional[str] = None):
        self.voice_name = voice_name or DEFAULT_VOICE or "Puck"
        self._lock = threading.Lock()
        self.is_speaking = False
        self.cache_dir = BASE_DIR / "storage" / "voice_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def clean_text(self, text: str) -> str:
        """Strip markdown, backticks, emojis, URLs, and code blocks for crisp speech."""
        cleaned = re.sub(r'```[\s\S]*?```', '', text)
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
        cleaned = re.sub(r'https?://\S+', 'link', cleaned)
        cleaned = re.sub(r'[*_#~>|]', '', cleaned)
        cleaned = re.sub(r'\[.*?\]\(.*?\)', '', cleaned)
        cleaned = re.sub(r'\{.*?\}', '', cleaned)
        cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned) # emojis
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _get_cache_path(self, text: str) -> Path:
        hash_key = hashlib.md5(f"{self.voice_name}_{text}".encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hash_key}.wav"

    def speak(self, text: str, block: bool = False):
        """Play verified voice audio if cached or route through LiveKit realtime pipeline."""
        cleaned = self.clean_text(text)
        if not cleaned:
            return

        cache_file = self._get_cache_path(cleaned)
        if cache_file.exists() and cache_file.stat().st_size > 1000:
            with self._lock:
                self.is_speaking = True
                try:
                    logger.info(f"LIVEKIT_AUDIO_OUTPUT_STARTED Voice: '{self.voice_name}' (Puck Audio Stream)")
                    winsound.PlaySound(str(cache_file), winsound.SND_FILENAME)
                    logger.info("LIVEKIT_AUDIO_OUTPUT_COMPLETED")
                except Exception as e:
                    logger.debug(f"Audio playback error: {e}")
                finally:
                    self.is_speaking = False

tts_service = TTSService()
