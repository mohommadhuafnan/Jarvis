import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("JARVIS.StartupService")

class StartupService:
    """
    Manages non-elevated Windows Startup configuration for JARVIS.
    Creates or removes a Windows Startup entry in the user's startup folder:
    %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\
    """

    def __init__(self):
        self.appdata = os.getenv("APPDATA", "")
        self.startup_folder = Path(self.appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" if self.appdata else Path.home()
        self.shortcut_bat = self.startup_folder / "JARVIS_AutoStart.bat"
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.start_bg_bat = self.base_dir / "start_background.bat"

    def is_startup_enabled(self) -> bool:
        """Check if JARVIS auto-start is currently enabled."""
        return self.shortcut_bat.exists()

    def enable_startup(self) -> Dict[str, Any]:
        """Enable auto-start on Windows user login."""
        try:
            self.startup_folder.mkdir(parents=True, exist_ok=True)
            bat_content = f"""@echo off
cd /d "{self.base_dir}"
start "" /b python backend/background_service.py
"""
            with open(self.shortcut_bat, "w") as f:
                f.write(bat_content)

            logger.info(f"Enabled Windows auto-start: {self.shortcut_bat}")
            return {
                "success": True,
                "enabled": True,
                "path": str(self.shortcut_bat),
                "message": "JARVIS auto-start configured successfully."
            }
        except Exception as e:
            logger.error(f"Failed to enable Windows auto-start: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def disable_startup(self) -> Dict[str, Any]:
        """Disable auto-start on Windows user login."""
        try:
            if self.shortcut_bat.exists():
                self.shortcut_bat.unlink()
            logger.info("Disabled Windows auto-start.")
            return {
                "success": True,
                "enabled": False,
                "message": "JARVIS auto-start removed."
            }
        except Exception as e:
            logger.error(f"Failed to disable Windows auto-start: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            "startup_enabled": self.is_startup_enabled(),
            "startup_path": str(self.shortcut_bat),
            "project_root": str(self.base_dir)
        }

startup_service = StartupService()
