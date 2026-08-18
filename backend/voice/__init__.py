from backend.voice.base import BaseVoiceProvider
from backend.voice.gemini_voice_provider import GeminiVoiceProvider
from backend.voice.valsea_stt import valsea_stt, ValseaSTT
from backend.voice.valsea_tts import valsea_tts, ValseaTTS
from backend.voice.conversation_manager import conversation_manager, ConversationManager
from backend.voice.audio_session import AudioSession
from backend.voice.voice_gateway import voice_gateway, VoiceGateway

_current_provider: BaseVoiceProvider = GeminiVoiceProvider()

def get_voice_provider() -> BaseVoiceProvider:
    global _current_provider
    return _current_provider

def set_voice_provider(provider: BaseVoiceProvider):
    global _current_provider
    _current_provider = provider

__all__ = [
    "BaseVoiceProvider",
    "GeminiVoiceProvider",
    "valsea_stt",
    "ValseaSTT",
    "valsea_tts",
    "ValseaTTS",
    "conversation_manager",
    "ConversationManager",
    "AudioSession",
    "voice_gateway",
    "VoiceGateway",
    "get_voice_provider",
    "set_voice_provider"
]
