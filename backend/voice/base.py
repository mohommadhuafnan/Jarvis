from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseVoiceProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_data_base64: str) -> Dict[str, Any]:
        """Transcribe base64 audio data into text."""
        pass

    @abstractmethod
    def synthesize(self, text: str, voice_name: str = "Puck") -> Dict[str, Any]:
        """Synthesize text into natural audio base64 stream."""
        pass
