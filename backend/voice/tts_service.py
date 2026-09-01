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
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from backend.config import GEMINI_API_KEY, DEFAULT_VOICE, BASE_DIR
from backend.voice.gemini_voice_provider import GeminiVoiceProvider

logger = logging.getLogger("JARVIS.Voice.TTSService")

class TTSService:
    """
    JARVIS Primary Voice Output Engine.
    Uses Google Gemini Voice API (Voice: Puck) for natural, expressive speech.
    Features local voice caching for zero-latency wake/sleep responses,
    and automatic offline fallback.
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
        """Speak the given text aloud using the native JARVIS Gemini Puck voice."""
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
                # 1. Check local audio cache first (instant 0ms playback)
                if cache_file.exists():
                    try:
                        logger.info("GEMINI_PUCK_TTS_PLAYING")
                        winsound.PlaySound(str(cache_file), winsound.SND_FILENAME)
                        logger.info("GEMINI_PUCK_TTS_COMPLETED")
                        return
                    except Exception as e:
                        logger.debug(f"Cache playback failed: {e}")

                # 2. Synthesize with Google Gemini Voice Provider (Voice: Puck)
                try:
                    res = self.gemini_voice.synthesize(text, voice_name=self.voice_name)
                    if res.get("success") and "wav_bytes" in res:
                        wav_bytes = res["wav_bytes"]
                        cache_file.write_bytes(wav_bytes)
                        logger.info("GEMINI_PUCK_TTS_PLAYING")
                        winsound.PlaySound(str(cache_file), winsound.SND_FILENAME)
                        logger.info("GEMINI_PUCK_TTS_COMPLETED")
                        return
                    elif res.get("success") and "audio_data" in res:
                        raw_b64 = res["audio_data"].split(",")[-1]
                        wav_bytes = base64.b64decode(raw_b64)
                        cache_file.write_bytes(wav_bytes)
                        logger.info("GEMINI_PUCK_TTS_PLAYING")
                        winsound.PlaySound(str(cache_file), winsound.SND_FILENAME)
                        logger.info("GEMINI_PUCK_TTS_COMPLETED")
                        return
                except Exception as gemini_err:
                    logger.warning(f"Gemini Voice synthesis notice: {gemini_err}. Attempting local speech fallback.")

                # 3. Local Offline Fallback (pyttsx3 / PowerShell) if network/API unavailable
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 185)
                    voices = engine.getProperty('voices')
                    for v in voices:
                        if 'david' in v.name.lower() or 'puck' in v.name.lower():
                            engine.setProperty('voice', v.id)
                            break
                    logger.info("GEMINI_PUCK_TTS_PLAYING (Fallback)")
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                    logger.info("GEMINI_PUCK_TTS_COMPLETED")
                    return
                except Exception:
                    pass

                try:
                    ps_text = text.replace("'", "''")
                    cmd = [
                        "powershell.exe",
                        "-NoProfile",
                        "-Command",
                        f"Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Rate = 1; $synth.Speak('{ps_text}')"
                    ]
                    logger.info("GEMINI_PUCK_TTS_PLAYING (PS Fallback)")
                    subprocess.run(cmd, capture_output=True, timeout=8)
                    logger.info("GEMINI_PUCK_TTS_COMPLETED")
                except Exception as ps_err:
                    logger.error(f"Speech playback fallback failed: {ps_err}")
            finally:
                self.is_speaking = False

tts_service = TTSService()
