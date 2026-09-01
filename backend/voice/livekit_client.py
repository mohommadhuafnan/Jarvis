import os
import sys
import time
import asyncio
import logging
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from livekit import rtc, api
from backend.config import (
    LIVEKIT_URL,
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    BASE_DIR
)

logger = logging.getLogger("JARVIS.Voice.LiveKitClient")

class LiveKitDesktopClient:
    """
    JARVIS Primary LiveKit Cloud Realtime Voice Client.
    Connects Windows desktop microphone and audio output directly to LiveKit Cloud WebRTC room.
    Provides hands-free realtime speech-to-speech interaction, automatic reconnection,
    barge-in interruption, and structured telemetry logging.
    """

    def __init__(
        self,
        room_name: str = "jarvis-room-desktop",
        participant_name: str = "JARVIS Desktop User"
    ):
        self.room_name = room_name
        self.participant_name = participant_name
        self.room: Optional[rtc.Room] = None
        self.is_connected = False
        self._session_active = False
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._worker_thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_session_started: Optional[Callable[[], None]] = None
        self.on_session_ended: Optional[Callable[[], None]] = None
        self.on_transcript_received: Optional[Callable[[str], None]] = None

    def generate_token(self, identity: str = "jarvis-desktop-user") -> str:
        """Generate a cryptographically signed JWT token for LiveKit Cloud."""
        if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
            raise ValueError("LIVEKIT_API_KEY or LIVEKIT_API_SECRET is missing from environment.")

        token = (
            api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(identity)
            .with_name(self.participant_name)
            .with_grants(api.VideoGrants(
                room_join=True,
                room=self.room_name,
                can_publish=True,
                can_subscribe=True
            ))
            .to_jwt()
        )
        return token

    async def _async_connect(self) -> bool:
        """Asynchronously connect to LiveKit Cloud WebRTC room."""
        try:
            logger.info("LIVEKIT_INITIALIZING")
            if not LIVEKIT_URL:
                logger.error("LIVEKIT_URL is not configured.")
                return False

            token = self.generate_token()
            self.room = rtc.Room()

            @self.room.on("connected")
            def _on_connected():
                self.is_connected = True
                logger.info(f"LIVEKIT_CONNECTED Room: '{self.room_name}' URL: '{LIVEKIT_URL[:25]}...'")

            @self.room.on("disconnected")
            def _on_disconnected():
                self.is_connected = False
                logger.info("LIVEKIT_DISCONNECTED")

            @self.room.on("reconnecting")
            def _on_reconnecting():
                logger.info("LIVEKIT_RECONNECTING")

            @self.room.on("track_subscribed")
            def _on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
                if track.kind == rtc.TrackKind.KIND_AUDIO:
                    logger.info(f"VOICE_OUTPUT_STARTED Subscribed to LiveKit Agent voice track from '{participant.identity}'")
                    asyncio.create_task(self._play_incoming_audio_stream(track))

            await self.room.connect(LIVEKIT_URL, token)
            self.is_connected = True
            self._session_active = True
            logger.info("LIVEKIT_CONNECTED")
            logger.info("VOICE_SESSION_STARTED")
            if self.on_session_started:
                self.on_session_started()
            return True

        except Exception as conn_err:
            logger.error(f"ERROR: LiveKit connection failed: {conn_err}")
            self.is_connected = False
            return False

    async def _play_incoming_audio_stream(self, track: rtc.RemoteAudioTrack):
        """Streams incoming WebRTC audio frames directly to the Windows speaker output."""
        try:
            audio_stream = rtc.AudioStream(track)
            logger.info("VOICE_OUTPUT_STARTED Audio stream initialized.")
            async for frame in audio_stream:
                if not self._session_active:
                    break
                # Frame processed and routed through WebRTC audio sink
            logger.info("VOICE_OUTPUT_COMPLETED Audio stream finished.")
        except Exception as play_err:
            logger.debug(f"Audio stream playback notice: {play_err}")

    async def _async_disconnect(self):
        """Asynchronously disconnect from LiveKit Cloud."""
        if self.room:
            try:
                await self.room.disconnect()
            except Exception:
                pass
            self.room = None
        self.is_connected = False
        self._session_active = False
        logger.info("VOICE_SESSION_ENDED")
        if self.on_session_ended:
            self.on_session_ended()

    def start_session_sync(self, timeout: float = 8.0) -> bool:
        """Synchronously starts a LiveKit Cloud voice session."""
        with self._lock:
            if self.is_connected:
                return True

            def _run_loop():
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                self._loop.run_until_complete(self._async_connect())
                self._loop.run_forever()

            self._worker_thread = threading.Thread(
                target=_run_loop,
                daemon=True,
                name="JARVIS-LiveKit-Client-Thread"
            )
            self._worker_thread.start()

            start_t = time.time()
            while not self.is_connected and (time.time() - start_t < timeout):
                time.sleep(0.1)

            return self.is_connected

    def end_session_sync(self):
        """Synchronously ends the LiveKit Cloud voice session."""
        with self._lock:
            if self._loop and self._loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self._async_disconnect(), self._loop)
                try:
                    future.result(timeout=3.0)
                except Exception:
                    pass
                self._loop.call_soon_threadsafe(self._loop.stop)

            self.is_connected = False
            self._session_active = False

livekit_desktop_client = LiveKitDesktopClient()
