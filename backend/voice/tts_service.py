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
from backend.voice.gemini_voice_provider import GeminiVoiceProvider

logger = logging.getLogger("JARVIS.Voice.TTSService")

class TTSService:
    """
    JARVIS Dedicated Voice Output Engine.
    Exclusively powered by Google Gemini Voice API (Voice: Puck).
    Outputs audio directly to Windows speakers via native WAV audio playback.
    Features local voice caching for zero-latency wake and sleep responses.
    """

    def __init__(self, voice_name: Optional[str] = None):
        self.voice_name = voice_name or DEFAULT_VOICE or "Puck"
        self.gemini_voice = GeminiVoiceProvider()
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

    def speak(self, text: str, block: bool = True):
        """Speak the given text aloud using exclusively the native JARVIS Gemini Puck voice."""
        cleaned = self.clean_text(text)
        if not cleaned:
            return

        logger.info(f"GEMINI_PUCK_TTS_STARTED Text: '{cleaned}'")

        if block:
            self._speak_sync(cleaned)
        else:
            threading.Thread(target=self._speak_sync, args=(cleaned,), daemon=True).start()

    def _speak_sync(self, text: str):
        with self._lock:
            self.is_speaking = True
            cache_file = self._get_cache_path(text)
            try:
                # 1. Check local audio cache (instant 0ms Gemini Puck playback)
                if cache_file.exists() and cache_file.stat().st_size > 1000:
                    try:
                        logger.info(f"GEMINI_PUCK_TTS_PLAYING Voice: '{self.voice_name}' Provider: 'Google Gemini Voice (Cached)'")
                        winsound.PlaySound(str(cache_file), winsound.SND_FILENAME)
                        logger.info("GEMINI_PUCK_TTS_COMPLETED")
                        return
                    except Exception as e:
                        logger.debug(f"Cached voice playback error: {e}")

                # 2. Synthesize with Google Gemini Voice Provider (Voice: Puck)
                logger.info(f"GEMINI_PUCK_TTS_SYNTHESIZING Voice: '{self.voice_name}' Model: 'gemini-2.5-flash-preview-tts'")
                res = self.gemini_voice.synthesize(text, voice_name=self.voice_name)
                
                if res.get("success") and "wav_bytes" in res:
                    wav_bytes = res["wav_bytes"]
                    cache_file.write_bytes(wav_bytes)
                    logger.info(f"GEMINI_PUCK_TTS_PLAYING Voice: '{self.voice_name}' Provider: 'Google Gemini Voice'")
                    winsound.PlaySound(str(cache_file), winsound.SND_FILENAME)
                    logger.info("GEMINI_PUCK_TTS_COMPLETED")
                    return
                elif res.get("success") and "audio_data" in res:
                    raw_b64 = res["audio_data"].split(",")[-1]
                    wav_bytes = base64.b64decode(raw_b64)
                    cache_file.write_bytes(wav_bytes)
                    logger.info(f"GEMINI_PUCK_TTS_PLAYING Voice: '{self.voice_name}' Provider: 'Google Gemini Voice'")
                    winsound.PlaySound(str(cache_file), winsound.SND_FILENAME)
                    logger.info("GEMINI_PUCK_TTS_COMPLETED")
                    return
                else:
                    logger.error(f"GEMINI_PUCK_TTS_FAILED Error: {res.get('error')}")

            except Exception as gemini_err:
                logger.error(f"GEMINI_PUCK_TTS_ERROR: {gemini_err}")
            finally:
                self.is_speaking = False

tts_service = TTSService()
