import io
import os
import sys
import wave
import base64
import logging
import traceback
import requests
from typing import Dict, Any, Optional, List

from backend.config import GEMINI_API_KEY, GOOGLE_API_KEY, DEFAULT_VOICE
from backend.voice.base import BaseVoiceProvider

logger = logging.getLogger("JARVIS.Voice.GeminiVoiceProvider")

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
    """
    Google Gemini Native TTS & STT Voice Provider.
    Primary voice: 'Puck' (Prebuilt neural voice from Google Gemini).
    Implements dual synthesis pipelines:
    1. Official google.genai Python SDK
    2. Direct Generative Language REST API
    Includes structured diagnostic telemetry with safe credential handling.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY or GOOGLE_API_KEY or ""
        self.api_key_var_name = "GEMINI_API_KEY" if GEMINI_API_KEY else "GOOGLE_API_KEY"
        self.tts_models = [
            "gemini-2.5-flash-preview-tts",
            "gemini-3.1-flash-tts-preview",
            "gemini-2.5-pro-preview-tts"
        ]
        self.stt_model = "gemini-flash-latest"
        self.timeout = 10

    def synthesize(self, text: str, voice_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate natural spoken audio using Google Gemini native TTS capabilities.
        Voices: 'Puck', 'Charon', 'Kore', 'Fenrir', 'Aoede'
        """
        key_exists = bool(self.api_key)
        selected_voice = voice_name or DEFAULT_VOICE or "Puck"
        cleaned_text = text.strip()

        if not key_exists:
            err_msg = f"No Gemini API key found in environment variable '{self.api_key_var_name}'"
            logger.error(f"GEMINI_PUCK_TTS_ERROR: {err_msg}")
            return {
                "success": False,
                "error": err_msg,
                "error_type": "MissingAPIKeyError",
                "http_status": None,
                "model": self.tts_models[0],
                "voice": selected_voice,
                "api_key_configured": False
            }

        logger.info(f"GEMINI_PUCK_TTS_STARTED Text: '{cleaned_text[:60]}...'")

        last_error_info: Dict[str, Any] = {}

        # Pipeline 1: Try official google.genai SDK
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            for model in self.tts_models:
                logger.info(
                    f"GEMINI_PUCK_TTS_REQUEST SDK: 'google.genai' Model: '{model}' Voice: '{selected_voice}' "
                    f"APIKeyVar: '{self.api_key_var_name}' Configured: {key_exists} Timeout: {self.timeout}s"
                )
                try:
                    config = types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=selected_voice
                                )
                            )
                        )
                    )
                    response = client.models.generate_content(
                        model=model,
                        contents=cleaned_text,
                        config=config
                    )

                    if response.candidates and response.candidates[0].content:
                        parts = response.candidates[0].content.parts
                        for p in parts:
                            if hasattr(p, 'inline_data') and p.inline_data:
                                pcm_bytes = p.inline_data.data
                                wav_bytes = pcm_to_wav(pcm_bytes, sample_rate=24000)
                                wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")
                                logger.info(
                                    f"GEMINI_PUCK_TTS_RESPONSE Status: 200 SDK: 'google.genai' Model: '{model}' "
                                    f"PCMBytes: {len(pcm_bytes)} WAVBytes: {len(wav_bytes)}"
                                )
                                return {
                                    "success": True,
                                    "mime_type": "audio/wav",
                                    "audio_data": f"data:audio/wav;base64,{wav_b64}",
                                    "wav_bytes": wav_bytes,
                                    "voice": selected_voice,
                                    "model": model,
                                    "provider": f"Google Gemini Voice ({selected_voice})"
                                }
                except Exception as sdk_err:
                    err_type = type(sdk_err).__name__
                    err_str = str(sdk_err)
                    http_status = None
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        http_status = 429
                    elif "400" in err_str or "INVALID_ARGUMENT" in err_str:
                        http_status = 400
                    elif "403" in err_str or "PERMISSION_DENIED" in err_str:
                        http_status = 403
                    elif "404" in err_str or "NOT_FOUND" in err_str:
                        http_status = 404

                    last_error_info = {
                        "error_type": err_type,
                        "http_status": http_status,
                        "model": model,
                        "voice": selected_voice,
                        "details": err_str[:300],
                        "api_key_configured": True
                    }
                    logger.warning(
                        f"GEMINI_PUCK_TTS_ERROR SDK: 'google.genai' Model: '{model}' "
                        f"HTTP_STATUS: {http_status} ErrorType: {err_type} Details: {err_str[:200]}"
                    )
        except Exception as import_err:
            logger.debug(f"google.genai SDK import notice: {import_err}")

        # Pipeline 2: Direct REST Generative Language API
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
        payload = {
            "contents": [{"parts": [{"text": cleaned_text}]}],
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
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            url_with_key = f"{endpoint}?key={self.api_key}"
            logger.info(
                f"GEMINI_PUCK_TTS_REQUEST REST Model: '{model}' Voice: '{selected_voice}' "
                f"Endpoint: '{endpoint}' APIKeyVar: '{self.api_key_var_name}' Configured: {key_exists} Timeout: {self.timeout}s"
            )
            try:
                res = requests.post(url_with_key, headers=headers, json=payload, timeout=self.timeout)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for p in parts:
                            if "inlineData" in p:
                                raw_b64 = p["inlineData"]["data"]
                                pcm_bytes = base64.b64decode(raw_b64)
                                wav_bytes = pcm_to_wav(pcm_bytes, sample_rate=24000)
                                wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")
                                logger.info(
                                    f"GEMINI_PUCK_TTS_RESPONSE Status: 200 REST Model: '{model}' "
                                    f"PCMBytes: {len(pcm_bytes)} WAVBytes: {len(wav_bytes)}"
                                )
                                return {
                                    "success": True,
                                    "mime_type": "audio/wav",
                                    "audio_data": f"data:audio/wav;base64,{wav_b64}",
                                    "wav_bytes": wav_bytes,
                                    "voice": selected_voice,
                                    "model": model,
                                    "provider": f"Google Gemini Voice ({selected_voice})"
                                }
                else:
                    err_details = res.text[:300]
                    last_error_info = {
                        "error_type": "HTTPError",
                        "http_status": res.status_code,
                        "model": model,
                        "voice": selected_voice,
                        "details": err_details,
                        "api_key_configured": True
                    }
                    logger.warning(
                        f"GEMINI_PUCK_TTS_ERROR REST Model: '{model}' HTTP_STATUS: {res.status_code} "
                        f"Details: {err_details[:200]}"
                    )
            except Exception as rest_err:
                err_type = type(rest_err).__name__
                last_error_info = {
                    "error_type": err_type,
                    "http_status": None,
                    "model": model,
                    "voice": selected_voice,
                    "details": str(rest_err)[:300],
                    "api_key_configured": True
                }
                logger.warning(
                    f"GEMINI_PUCK_TTS_ERROR REST Model: '{model}' ErrorType: {err_type} Details: {str(rest_err)[:200]}"
                )

        error_message = (
            f"Google Gemini TTS synthesis failed across all models {self.tts_models}. "
            f"HTTP_STATUS: {last_error_info.get('http_status')}, "
            f"ErrorType: {last_error_info.get('error_type')}, "
            f"Details: {last_error_info.get('details')}"
        )
        logger.error(f"GEMINI_PUCK_TTS_FAILED Error: {error_message}")
        return {
            "success": False,
            "error": error_message,
            **last_error_info
        }

    def transcribe(self, audio_data_base64: str) -> Dict[str, Any]:
        """
        Transcribe user speech audio into text using Gemini multimodal audio capabilities.
        """
        if not self.api_key:
            return {"success": False, "error": "No Gemini API key configured"}

        clean_b64 = audio_data_base64.split(",")[-1] if "," in audio_data_base64 else audio_data_base64

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.stt_model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Accurately transcribe the spoken English audio into plain text. Return ONLY the transcribed text."},
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
            res = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return {
                            "success": True,
                            "transcript": parts[0]["text"].strip(),
                            "provider": "Google Gemini Multimodal STT"
                        }
            return {"success": False, "error": f"STT failed with status {res.status_code}: {res.text[:150]}"}
        except Exception as e:
            return {"success": False, "error": f"STT request exception: {str(e)}"}

gemini_voice_provider = GeminiVoiceProvider()
