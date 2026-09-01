import io
import wave
import base64
import requests
from typing import Dict, Any, Optional
from backend.config import GEMINI_API_KEY, DEFAULT_VOICE
from backend.voice.base import BaseVoiceProvider

def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, num_channels: int = 1, sample_width: int = 2) -> bytes:
    """Convert raw 16-bit linear PCM audio into valid RIFF WAV audio bytes."""
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return wav_io.getvalue()

class GeminiVoiceProvider(BaseVoiceProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.tts_models = ["gemini-2.5-flash-preview-tts", "gemini-3.1-flash-tts-preview"]
        self.stt_model = "gemini-flash-latest"

    def synthesize(self, text: str, voice_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate natural spoken audio using Google Gemini native TTS capabilities.
        Voices: 'Puck', 'Charon', 'Kore', 'Fenrir', 'Aoede'
        """
        if not self.api_key:
            return {"success": False, "error": "No Gemini API key configured"}

        selected_voice = voice_name or DEFAULT_VOICE or "Puck"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
        payload = {
            "contents": [
                {
                    "parts": [{"text": text}]
                }
            ],
            "generationConfig": {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": selected_voice
                        }
                    }
                }
            }
        }

        for model in self.tts_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for p in parts:
                            if "inlineData" in p:
                                raw_b64 = p["inlineData"]["data"]
                                pcm_bytes = base64.b64decode(raw_b64)
                                # Convert raw 24kHz PCM to standard browser/windows playable WAV
                                wav_bytes = pcm_to_wav(pcm_bytes, sample_rate=24000)
                                wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")
                                return {
                                    "success": True,
                                    "mime_type": "audio/wav",
                                    "audio_data": f"data:audio/wav;base64,{wav_b64}",
                                    "wav_bytes": wav_bytes,
                                    "voice": selected_voice,
                                    "provider": "Google Gemini Voice (Puck)"
                                }
            except Exception as e:
                continue

        return {"success": False, "error": "Gemini TTS synthesis request failed."}

    def transcribe(self, audio_data_base64: str) -> Dict[str, Any]:
        """
        Transcribe user speech audio into text using Gemini multimodal audio capabilities.
        """
        if not self.api_key:
            return {"success": False, "error": "No Gemini API key configured"}

        # Strip data URL prefix if present
        clean_b64 = audio_data_base64.split(",")[-1] if "," in audio_data_base64 else audio_data_base64

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.stt_model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Transcribe the user's speech accurately into English text. Return only the exact transcription."},
                        {
                            "inline_data": {
                                "mime_type": "audio/wav",
                                "data": clean_b64
                            }
                        }
                    ]
                }
            ]
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return {
                    "success": True,
                    "transcript": text.strip(),
                    "provider": "Google Gemini Multimodal Audio"
                }
            return {"success": False, "error": res.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
