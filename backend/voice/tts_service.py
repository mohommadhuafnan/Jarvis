import re
import os
import sys
import logging
import threading
import subprocess
from typing import Optional

logger = logging.getLogger("JARVIS.Voice.TTSService")

class TTSService:
    """
    High-Reliability Windows Text-to-Speech Engine for JARVIS.
    Uses native SAPI5 voices (pyttsx3) with PowerShell System.Speech fallback.
    Runs speech safely without COM threading issues.
    """

    def __init__(self, voice_gender: str = "male", rate: int = 185):
        self.voice_gender = voice_gender
        self.rate = rate
        self._lock = threading.Lock()

    def clean_text(self, text: str) -> str:
        """Strip markdown, backticks, emojis, URLs, and code blocks."""
        cleaned = re.sub(r'```[\s\S]*?```', '', text)
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
        cleaned = re.sub(r'https?://\S+', 'link', cleaned)
        cleaned = re.sub(r'[*_#~>|]', '', cleaned)
        cleaned = re.sub(r'\[.*?\]\(.*?\)', '', cleaned)
        cleaned = re.sub(r'\{.*?\}', '', cleaned)
        cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned) # emojis
        # Clean extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def speak(self, text: str, block: bool = True):
        """Speak the given text aloud. If block=False, runs in background thread."""
        cleaned = self.clean_text(text)
        if not cleaned:
            return

        logger.info(f"[SPEAK] '{cleaned}'")

        if block:
            self._speak_sync(cleaned)
        else:
            threading.Thread(target=self._speak_sync, args=(cleaned,), daemon=True).start()

    def _speak_sync(self, text: str):
        with self._lock:
            # 1. Try pyttsx3
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', self.rate)
                voices = engine.getProperty('voices')
                # Pick David for male JARVIS tone, or Zira for female
                preferred = "david" if self.voice_gender == "male" else "zira"
                selected_voice = None
                for v in voices:
                    if preferred in v.name.lower():
                        selected_voice = v.id
                        break
                if selected_voice:
                    engine.setProperty('voice', selected_voice)

                engine.say(text)
                engine.runAndWait()
                engine.stop()
                return
            except Exception as e:
                logger.warning(f"pyttsx3 speech failed: {e}. Attempting PowerShell Speech fallback.")

            # 2. Native Windows PowerShell System.Speech Fallback
            try:
                # Escape single quotes for PowerShell
                ps_text = text.replace("'", "''")
                cmd = [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    f"Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Rate = 1; $synth.Speak('{ps_text}')"
                ]
                subprocess.run(cmd, capture_output=True, timeout=10)
            except Exception as ps_err:
                logger.error(f"PowerShell speech fallback failed: {ps_err}")

tts_service = TTSService()
