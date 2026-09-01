import os
import sys
import webbrowser
import logging
import threading
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

from backend.config import LOG_FILE_PATH
from backend.background_service import background_service
from backend.voice.wake_word_detector import WakeWordState

logger = logging.getLogger("JARVIS.Tray")

def create_tray_icon_image(state: str = "READY") -> Image.Image:
    """
    Dynamically generates a high-contrast Cyberpunk Red Reactor Orb icon (64x64)
    with status-responsive inner core.
    """
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # State colors
    if state == "ACTIVATED" or state == "SPEAKING":
        core_color = (255, 30, 30, 255) # Bright Neon Crimson
        outer_color = (200, 0, 40, 200)
    elif state == "LISTENING_FOR_WAKE_WORD":
        core_color = (0, 220, 255, 255) # Cyan Listening
        outer_color = (0, 150, 200, 200)
    elif state == "ERROR":
        core_color = (255, 165, 0, 255) # Amber Warning
        outer_color = (180, 100, 0, 200)
    else: # READY / IDLE
        core_color = (220, 20, 60, 255) # Crimson Red
        outer_color = (139, 0, 0, 180)

    # Outer reactor ring
    draw.ellipse([4, 4, 60, 60], outline=outer_color, width=3)
    # Middle targeting ring
    draw.ellipse([14, 14, 50, 50], outline=outer_color, width=2)
    # Inner energy core
    draw.ellipse([22, 22, 42, 42], fill=core_color)

    return img

class JarvisTrayApp:
    """
    Windows System Tray Application for JARVIS.
    Provides instant status visibility and quick controls from the Windows taskbar.
    """

    def __init__(self):
        self.icon: Optional[pystray.Icon] = None
        self._bg_thread: Optional[threading.Thread] = None

    def _open_dashboard(self, icon, item):
        logger.info("Opening JARVIS Cyberpunk HUD in browser...")
        webbrowser.open("http://localhost:5173")

    def _wake_jarvis(self, icon, item):
        logger.info("Tray: Waking JARVIS...")
        background_service.start_active_voice_session(reason="Tray Wake Request")

    def _sleep_jarvis(self, icon, item):
        logger.info("Tray: Putting JARVIS to sleep...")
        background_service.end_active_voice_session(reason="Tray Sleep Request")

    def _restart_jarvis(self, icon, item):
        logger.info("Tray: Restarting JARVIS Background Service...")
        background_service.stop()
        time.sleep(1)
        self._bg_thread = threading.Thread(
            target=background_service.run_forever,
            daemon=True,
            name="JARVIS-BackgroundService-Thread"
        )
        self._bg_thread.start()

    def _view_logs(self, icon, item):
        logger.info(f"Tray: Opening log file {LOG_FILE_PATH}...")
        if LOG_FILE_PATH.exists():
            if os.name == "nt":
                os.startfile(str(LOG_FILE_PATH))
            else:
                webbrowser.open(str(LOG_FILE_PATH))

    def _exit_jarvis(self, icon, item):
        logger.info("Tray: Exiting JARVIS...")
        background_service.stop()
        icon.stop()
        sys.exit(0)

    def _get_status_label(self, item) -> str:
        state = background_service.detector.state.value
        return f"Status: {state.replace('_', ' ').title()}"

    def run(self):
        # Start background service daemon in separate thread if not already running
        if not background_service.is_running:
            self._bg_thread = threading.Thread(
                target=background_service.run_forever,
                daemon=True,
                name="JARVIS-BackgroundService-Thread"
            )
            self._bg_thread.start()

        # Build Tray Context Menu
        menu = pystray.Menu(
            item("JARVIS AI Operating System", lambda icon, item: None, enabled=False),
            item(self._get_status_label, lambda icon, item: None, enabled=False),
            pystray.Menu.SEPARATOR,
            item("Wake JARVIS", self._wake_jarvis),
            item("Sleep JARVIS", self._sleep_jarvis),
            pystray.Menu.SEPARATOR,
            item("Open Dashboard (HUD)", self._open_dashboard, default=True),
            item("View Logs", self._view_logs),
            item("Restart JARVIS", self._restart_jarvis),
            pystray.Menu.SEPARATOR,
            item("Exit JARVIS", self._exit_jarvis)
        )

        icon_image = create_tray_icon_image("READY")
        self.icon = pystray.Icon("JARVIS", icon_image, "JARVIS — AI Desktop Assistant", menu)
        logger.info("JARVIS System Tray initialized.")
        self.icon.run()

if __name__ == "__main__":
    app = JarvisTrayApp()
    app.run()
