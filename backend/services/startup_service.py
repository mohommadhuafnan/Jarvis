import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("JARVIS.StartupService")

class StartupService:
    """
    Manages non-elevated Windows Startup configuration for JARVIS.
    Creates or removes a silent Windows Startup entry in the user's startup folder:
    %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\
    Uses VBScript / pythonw.exe for 100% silent execution without terminal windows.
    """

    def __init__(self):
        self.appdata = os.getenv("APPDATA", "")
        self.startup_folder = Path(self.appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" if self.appdata else Path.home()
        self.shortcut_vbs = self.startup_folder / "JARVIS_AutoStart.vbs"
        self.shortcut_bat = self.startup_folder / "JARVIS_AutoStart.bat"
        self.base_dir = Path(__file__).resolve().parent.parent.parent

    def is_startup_enabled(self) -> bool:
        """Check if JARVIS auto-start is currently enabled."""
        return self.shortcut_vbs.exists() or self.shortcut_bat.exists()

    def enable_startup(self) -> Dict[str, Any]:
        """Enable silent auto-start on Windows user login."""
        try:
            # Locate pythonw.exe in virtual environment or fallback
            venv_pythonw = self.base_dir / ".venv" / "Scripts" / "pythonw.exe"
            if venv_pythonw.exists():
                pythonw_exe = venv_pythonw
            else:
                py_dir = Path(sys.executable).parent
                pythonw_exe = py_dir / "pythonw.exe" if (py_dir / "pythonw.exe").exists() else Path(sys.executable)

            tray_script = self.base_dir / "backend" / "tray.py"

            vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{str(self.base_dir).replace('\\', '\\\\')}"
WshShell.Run chr(34) & "{str(pythonw_exe).replace('\\', '\\\\')}" & chr(34) & " " & chr(34) & "{str(tray_script).replace('\\', '\\\\')}" & chr(34), 0, False
Set WshShell = Nothing
'''
            with open(self.shortcut_vbs, "w", encoding="utf-8") as f:
                f.write(vbs_content)

            # Remove old .bat if exists
            if self.shortcut_bat.exists():
                try:
                    self.shortcut_bat.unlink()
                except Exception:
                    pass

            logger.info(f"Enabled Windows silent auto-start: {self.shortcut_vbs}")
            return {
                "success": True,
                "enabled": True,
                "path": str(self.shortcut_vbs),
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
            if self.shortcut_vbs.exists():
                self.shortcut_vbs.unlink()
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
            "startup_path": str(self.shortcut_vbs),
            "project_root": str(self.base_dir)
        }

startup_service = StartupService()
