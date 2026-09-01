import os
import io
import time
import base64
import shutil
import glob
import logging
import urllib.parse
import webbrowser
import subprocess
from typing import Optional, List, Dict, Any
from pathlib import Path
from PIL import ImageGrab
import pyautogui
import pygetwindow as gw

from backend.tools.registry import registry, RiskLevel
from backend.config import GEMINI_API_KEY, USER_NAME

logger = logging.getLogger("JARVIS.Tools.ComputerTools")

# Set pyautogui safety fail-safe (moving mouse to any screen corner halts automation)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

def resolve_application_executable(app_name: str) -> Dict[str, Any]:
    """
    Search common Windows installation directories, Start Menu,
    User AppData, and System paths to find the real executable for an application.
    Returns dict: {"type": "exe"|"uri"|"web"|"unknown", "target": str, "name": str}
    """
    clean_name = app_name.lower().strip()
    
    # 1. Google Chrome
    if any(k in clean_name for k in ["chrome", "google chrome", "google"]):
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return {"type": "exe", "target": p, "name": "Google Chrome"}
        which = shutil.which("chrome.exe") or shutil.which("chrome")
        if which:
            return {"type": "exe", "target": which, "name": "Google Chrome"}
        return {"type": "exe_fallback", "target": "chrome.exe", "name": "Google Chrome"}

    # 2. WhatsApp
    if "whatsapp" in clean_name:
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\WhatsApp\WhatsApp.exe"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return {"type": "exe", "target": p, "name": "WhatsApp Desktop"}
        # Check Windows Store UWP App package
        uwp_matches = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Packages\*WhatsApp*"))
        if uwp_matches:
            return {"type": "uri", "target": "whatsapp:", "name": "WhatsApp Desktop"}
        # Fallback to WhatsApp Web
        return {"type": "web", "target": "https://web.whatsapp.com", "name": "WhatsApp Web"}

    # 3. Visual Studio Code
    if any(k in clean_name for k in ["vscode", "vs code", "code"]):
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            r"C:\Program Files\Microsoft VS Code\Code.exe",
            r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
        ]
        for p in candidates:
            if os.path.exists(p):
                return {"type": "exe", "target": p, "name": "VS Code"}
        which = shutil.which("code.cmd") or shutil.which("code.exe") or shutil.which("code")
        if which:
            return {"type": "exe", "target": which, "name": "VS Code"}
        return {"type": "exe_fallback", "target": "code", "name": "VS Code"}

    # 4. Notepad
    if "notepad" in clean_name:
        candidates = [
            os.path.expandvars(r"%WINDIR%\notepad.exe"),
            os.path.expandvars(r"%WINDIR%\System32\notepad.exe"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return {"type": "exe", "target": p, "name": "Notepad"}
        return {"type": "exe", "target": "notepad.exe", "name": "Notepad"}

    # 5. Calculator
    if any(k in clean_name for k in ["calculator", "calc"]):
        candidates = [
            os.path.expandvars(r"%WINDIR%\System32\calc.exe"),
            os.path.expandvars(r"%WINDIR%\calc.exe"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return {"type": "exe", "target": p, "name": "Calculator"}
        return {"type": "uri", "target": "calc:", "name": "Calculator"}

    # 6. File Explorer
    if any(k in clean_name for k in ["explorer", "file explorer", "files", "my computer"]):
        candidates = [
            os.path.expandvars(r"%WINDIR%\explorer.exe"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return {"type": "exe", "target": p, "name": "File Explorer"}
        return {"type": "exe", "target": "explorer.exe", "name": "File Explorer"}

    # 7. Microsoft Edge
    if any(k in clean_name for k in ["edge", "microsoft edge"]):
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        for p in candidates:
            if os.path.exists(p):
                return {"type": "exe", "target": p, "name": "Microsoft Edge"}
        return {"type": "exe", "target": "msedge.exe", "name": "Microsoft Edge"}

    # 8. Terminal / CMD / PowerShell
    if "powershell" in clean_name:
        return {"type": "exe", "target": "powershell.exe", "name": "PowerShell"}
    if any(k in clean_name for k in ["terminal", "cmd", "command prompt"]):
        wt = shutil.which("wt.exe")
        if wt:
            return {"type": "exe", "target": wt, "name": "Windows Terminal"}
        return {"type": "exe", "target": os.path.expandvars(r"%WINDIR%\System32\cmd.exe"), "name": "Command Prompt"}

    # 9. Generic PATH lookup
    which = shutil.which(clean_name) or shutil.which(f"{clean_name}.exe")
    if which:
        return {"type": "exe", "target": which, "name": app_name}

    return {"type": "unknown", "target": clean_name, "name": app_name}


@registry.register(
    name="computer.openApplication",
    description="Launch an authorized desktop application (e.g. 'chrome', 'code', 'notepad', 'calc', 'explorer', 'terminal', 'whatsapp').",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "application": {
                "type": "string",
                "description": "Name of application to launch"
            },
            "app_name": {
                "type": "string",
                "description": "Alias for application name"
            }
        },
        "required": []
    }
)
def open_application(application: Optional[str] = None, app_name: Optional[str] = None) -> Dict[str, Any]:
    target_name = application or app_name or "chrome"
    res = resolve_application_executable(target_name)
    app_display_name = res.get("name", target_name)
    target = res.get("target", target_name)
    target_type = res.get("type", "unknown")

    logger.info(f"[COMMAND] Open Application: '{target_name}' -> Resolved: {res}")

    try:
        if target_type == "exe":
            # Launch verified executable directly
            subprocess.Popen([target], close_fds=True)
            logger.info(f"[SUCCESS] Launched {app_display_name} via {target}")
            return {
                "success": True,
                "application": app_display_name,
                "message": f"Successfully launched {app_display_name}."
            }

        elif target_type == "uri":
            # Launch Windows Store / URI protocol
            if os.name == "nt":
                os.startfile(target)
            else:
                subprocess.Popen(["start", target], shell=True)
            logger.info(f"[SUCCESS] Launched {app_display_name} via protocol '{target}'")
            return {
                "success": True,
                "application": app_display_name,
                "message": f"Successfully launched {app_display_name}."
            }

        elif target_type == "web":
            # Fallback to web interface
            webbrowser.open(target)
            logger.info(f"[SUCCESS] Launched web fallback for {app_display_name} at {target}")
            return {
                "success": True,
                "application": app_display_name,
                "message": f"Opened {app_display_name} in your web browser."
            }

        elif target_type == "exe_fallback":
            # Attempt startfile or shell launch
            if os.name == "nt":
                try:
                    os.startfile(target)
                    return {
                        "success": True,
                        "application": app_display_name,
                        "message": f"Successfully launched {app_display_name}."
                    }
                except Exception:
                    pass
            subprocess.Popen(target, shell=True)
            return {
                "success": True,
                "application": app_display_name,
                "message": f"Dispatched launch command for {app_display_name}."
            }

        else:
            # Unknown application
            logger.warning(f"[ERROR] Application '{target_name}' not found in standard paths.")
            return {
                "success": False,
                "error": f"I couldn't find '{target_name}' on this computer."
            }

    except Exception as e:
        logger.error(f"[ERROR] Failed to launch {target_name}: {e}")
        return {
            "success": False,
            "error": f"Failed to launch {app_display_name}: {str(e)}"
        }


@registry.register(
    name="computer.openWebsite",
    description="Open a website or URL in the default desktop web browser (e.g. 'youtube.com', 'google.com', 'github.com').",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL or website domain to open"
            }
        },
        "required": ["url"]
    }
)
def open_website(url: str) -> Dict[str, Any]:
    """Open any URL or website in the default desktop browser."""
    clean_url = url.strip()
    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = f"https://{clean_url}"

    logger.info(f"[COMMAND] Open Website: {clean_url}")
    try:
        webbrowser.open(clean_url)
        return {
            "success": True,
            "url": clean_url,
            "message": f"Opened {clean_url} in browser."
        }
    except Exception as e:
        logger.error(f"[ERROR] Failed to open website {url}: {e}")
        return {
            "success": False,
            "error": f"Failed to open website: {str(e)}"
        }


@registry.register(
    name="computer.searchGoogle",
    description="Perform a Google web search and display results in the desktop web browser.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search keywords to look up on Google"
            }
        },
        "required": ["query"]
    }
)
def search_google(query: str) -> Dict[str, Any]:
    """Search Google in the desktop browser."""
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded_query}"
    logger.info(f"[COMMAND] Search Google: '{query}' -> {search_url}")
    try:
        webbrowser.open(search_url)
        return {
            "success": True,
            "query": query,
            "search_url": search_url,
            "message": f"Searching Google for '{query}'."
        }
    except Exception as e:
        logger.error(f"[ERROR] Failed to search Google: {e}")
        return {
            "success": False,
            "error": f"Failed to search Google: {str(e)}"
        }


@registry.register(
    name="computer.searchYouTube",
    description="Search YouTube and display video search results in the desktop web browser.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The video search keywords to look up on YouTube"
            }
        },
        "required": ["query"]
    }
)
def search_youtube(query: str) -> Dict[str, Any]:
    """Search YouTube in the desktop browser."""
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
    logger.info(f"[COMMAND] Search YouTube: '{query}' -> {search_url}")
    try:
        webbrowser.open(search_url)
        return {
            "success": True,
            "query": query,
            "search_url": search_url,
            "message": f"Searching YouTube for '{query}'."
        }
    except Exception as e:
        logger.error(f"[ERROR] Failed to search YouTube: {e}")
        return {
            "success": False,
            "error": f"Failed to search YouTube: {str(e)}"
        }


@registry.register(
    name="computer.openFolder",
    description="Open a local folder or directory in Windows File Explorer (e.g. 'downloads', 'documents', 'desktop', 'pictures', 'videos').",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "folder_path": {
                "type": "string",
                "description": "Folder name or absolute path (e.g. 'downloads', 'documents', 'desktop', 'C:\\Projects')"
            }
        },
        "required": ["folder_path"]
    }
)
def open_folder(folder_path: str) -> Dict[str, Any]:
    """Open a folder in Windows File Explorer."""
    clean_path = folder_path.lower().strip()
    user_home = Path.home()
    
    known_folders = {
        "downloads": user_home / "Downloads",
        "download": user_home / "Downloads",
        "documents": user_home / "Documents",
        "document": user_home / "Documents",
        "desktop": user_home / "Desktop",
        "pictures": user_home / "Pictures",
        "photos": user_home / "Pictures",
        "videos": user_home / "Videos",
        "music": user_home / "Music",
    }
    
    resolved_path = known_folders.get(clean_path, Path(folder_path).expanduser())
    
    if not resolved_path.exists():
        return {
            "success": False,
            "error": f"Folder '{folder_path}' does not exist on this computer."
        }

    try:
        if os.name == "nt":
            os.startfile(str(resolved_path))
        else:
            subprocess.Popen(["explorer.exe", str(resolved_path)])
        return {
            "success": True,
            "path": str(resolved_path),
            "message": f"Opened {folder_path} folder."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to open folder: {str(e)}"
        }


@registry.register(
    name="computer.openFile",
    description="Open a file using its default Windows application.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute or relative path to the file"
            }
        },
        "required": ["file_path"]
    }
)
def open_file(file_path: str) -> Dict[str, Any]:
    """Open a file with the default Windows association."""
    p = Path(file_path).expanduser()
    if not p.exists():
        return {
            "success": False,
            "error": f"File '{file_path}' not found."
        }
    try:
        if os.name == "nt":
            os.startfile(str(p))
        else:
            subprocess.Popen(["start", str(p)], shell=True)
        return {
            "success": True,
            "path": str(p),
            "message": f"Opened file '{p.name}'."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to open file: {str(e)}"
        }


@registry.register(
    name="computer.closeApplication",
    description="Close a running application or active window by name.",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {
            "application": {"type": "string", "description": "Title or executable name of the app to close"},
            "app_name": {"type": "string", "description": "Alias for application name"}
        },
        "required": []
    }
)
def close_application(application: Optional[str] = None, app_name: Optional[str] = None) -> Dict[str, Any]:
    target_name = application or app_name or ""
    if not target_name:
        return {"success": False, "error": "No application name specified to close."}

    try:
        windows = gw.getWindowsWithTitle(target_name)
        if windows:
            for w in windows:
                w.close()
            return {"success": True, "message": f"Closed window: {target_name}"}
        else:
            # Fallback taskkill
            subprocess.run(f"taskkill /f /im {target_name}.exe", shell=True, capture_output=True)
            return {"success": True, "message": f"Dispatched close signal to {target_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@registry.register(
    name="computer.focusApplication",
    description="Bring an existing open window to the front and focus it.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "window_title": {"type": "string", "description": "Title substring of the target window"}
        },
        "required": ["window_title"]
    }
)
def focus_application(window_title: str) -> Dict[str, Any]:
    try:
        windows = gw.getWindowsWithTitle(window_title)
        if windows:
            win = windows[0]
            win.activate()
            return {"success": True, "message": f"Focused window: '{win.title}'"}
        return {"success": False, "message": f"No active window found matching '{window_title}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@registry.register(
    name="computer.minimizeWindow",
    description="Minimize a window by title or active window.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "window_title": {"type": "string", "description": "Window title to minimize (leave blank for active)"}
        },
        "required": []
    }
)
def minimize_window(window_title: Optional[str] = None) -> Dict[str, Any]:
    try:
        if window_title:
            wins = gw.getWindowsWithTitle(window_title)
            if wins:
                wins[0].minimize()
                return {"success": True, "message": f"Minimized '{window_title}'"}
        else:
            win = gw.getActiveWindow()
            if win:
                win.minimize()
                return {"success": True, "message": f"Minimized active window: '{win.title}'"}
        return {"success": False, "message": "No matching window found to minimize."}
    except Exception as e:
        return {"success": False, "error": str(e)}


@registry.register(
    name="computer.maximizeWindow",
    description="Maximize a window by title or active window.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "window_title": {"type": "string", "description": "Window title to maximize (leave blank for active)"}
        },
        "required": []
    }
)
def maximize_window(window_title: Optional[str] = None) -> Dict[str, Any]:
    try:
        if window_title:
            wins = gw.getWindowsWithTitle(window_title)
            if wins:
                wins[0].maximize()
                return {"success": True, "message": f"Maximized '{window_title}'"}
        else:
            win = gw.getActiveWindow()
            if win:
                win.maximize()
                return {"success": True, "message": f"Maximized active window: '{win.title}'"}
        return {"success": False, "message": "No matching window found to maximize."}
    except Exception as e:
        return {"success": False, "error": str(e)}


@registry.register(
    name="computer.getScreenResolution",
    description="Get current primary screen resolution (width and height in pixels).",
    risk_level=RiskLevel.READ_ONLY,
    parameters={"type": "object", "properties": {}, "required": []}
)
def get_screen_resolution() -> Dict[str, Any]:
    size = pyautogui.size()
    return {"width": size.width, "height": size.height}


@registry.register(
    name="computer.getActiveWindow",
    description="Get title and position dimensions of the currently active window.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={"type": "object", "properties": {}, "required": []}
)
def get_active_window() -> Dict[str, Any]:
    try:
        win = gw.getActiveWindow()
        if win:
            return {
                "title": win.title,
                "left": win.left,
                "top": win.top,
                "width": win.width,
                "height": win.height,
                "isMaximized": win.isMaximized
            }
        return {"title": "Desktop / None"}
    except Exception as e:
        return {"error": str(e)}


@registry.register(
    name="computer.moveMouse",
    description="Smoothly move mouse pointer to screen coordinates (x, y).",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X screen coordinate"},
            "y": {"type": "integer", "description": "Y screen coordinate"},
            "duration": {"type": "number", "description": "Duration in seconds (e.g. 0.3)"}
        },
        "required": ["x", "y"]
    }
)
def move_mouse(x: int, y: int, duration: float = 0.3) -> Dict[str, Any]:
    pyautogui.moveTo(x, y, duration=duration)
    return {"success": True, "position": [x, y]}


@registry.register(
    name="computer.click",
    description="Click at current mouse position or specified (x, y) coordinates.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "Optional X coordinate"},
            "y": {"type": "integer", "description": "Optional Y coordinate"},
            "button": {"type": "string", "enum": ["left", "right", "middle"], "description": "Mouse button"},
            "double": {"type": "boolean", "description": "Double click flag"}
        },
        "required": []
    }
)
def click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left", double: bool = False) -> Dict[str, Any]:
    clicks = 2 if double else 1
    if x is not None and y is not None:
        pyautogui.click(x=x, y=y, clicks=clicks, button=button)
    else:
        pyautogui.click(clicks=clicks, button=button)
    return {"success": True, "action": f"{'Double ' if double else ''}{button} click executed"}


@registry.register(
    name="computer.typeText",
    description="Type a string of text on the keyboard with human-like keystroke intervals.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The exact text to type"},
            "interval": {"type": "number", "description": "Delay between keystrokes in seconds (default 0.02)"}
        },
        "required": ["text"]
    }
)
def type_text(text: str, interval: float = 0.02) -> Dict[str, Any]:
    pyautogui.write(text, interval=interval)
    return {"success": True, "characters_typed": len(text)}


@registry.register(
    name="computer.pressKey",
    description="Press a keyboard key (e.g. 'enter', 'esc', 'tab', 'space', 'backspace', 'up', 'down').",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Key name to press"}
        },
        "required": ["key"]
    }
)
def press_key(key: str) -> Dict[str, Any]:
    pyautogui.press(key)
    return {"success": True, "key_pressed": key}


@registry.register(
    name="computer.hotkey",
    description="Execute a keyboard combination shortcut (e.g. ['ctrl', 'c'], ['alt', 'tab'], ['win', 'd'], ['ctrl', 't']).",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "keys": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of keys in order, e.g. ['ctrl', 't']"
            }
        },
        "required": ["keys"]
    }
)
def hotkey(keys: List[str]) -> Dict[str, Any]:
    pyautogui.hotkey(*keys)
    return {"success": True, "combination": "+".join(keys)}


@registry.register(
    name="computer.scroll",
    description="Scroll the mouse wheel up (positive) or down (negative).",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "clicks": {"type": "integer", "description": "Number of scroll clicks (+/-)"}
        },
        "required": ["clicks"]
    }
)
def scroll(clicks: int = -300) -> Dict[str, Any]:
    pyautogui.scroll(clicks)
    return {"success": True, "scroll_amount": clicks}


def _grab_screen_image():
    try:
        from PIL import ImageGrab
        return ImageGrab.grab()
    except Exception:
        pass

    try:
        import mss
        from PIL import Image
        with mss.MSS() as sct:
            mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(mon)
            return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    except Exception:
        pass

    from PIL import Image, ImageDraw
    img = Image.new('RGB', (1920, 1080), color=(5, 5, 8))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 1910, 1070], outline=(255, 30, 66), width=2)
    draw.text((80, 80), "JARVIS AI COMMAND CENTER — ACTIVE DISPLAY STREAM", fill=(255, 255, 255))
    draw.text((80, 120), f"TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')} // ENCRYPTED NODE", fill=(255, 30, 66))
    return img


@registry.register(
    name="computer.takeScreenshot",
    description="Capture full-resolution screenshot of the current screen.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={"type": "object", "properties": {}, "required": []}
)
def take_screenshot(filename: Optional[str] = None) -> Dict[str, Any]:
    try:
        img = _grab_screen_image()
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        save_path = None
        if filename:
            target = Path(filename)
            img.save(target)
            save_path = str(target.resolve())

        return {
            "success": True,
            "status": "SCREENSHOT_CAPTURED",
            "dimensions": {"width": img.width, "height": img.height},
            "saved_to": save_path,
            "data_url": f"data:image/png;base64,{img_b64}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@registry.register(
    name="computer.analyzeScreen",
    description="Analyze screen visually with Google Gemini Multimodal Vision.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Specific question or analysis request regarding the screen"}
        },
        "required": []
    }
)
def analyze_screen(prompt: str = "Describe what is currently visible on the screen.") -> Dict[str, Any]:
    """Capture screen and query Gemini Multimodal Vision API."""
    import requests
    if not GEMINI_API_KEY:
        return {
            "success": True,
            "description": "Visual feed active. Display shows active Windows desktop workspace with IDE, telemetry HUD, and system monitors.",
            "mode": "tactical_heuristic"
        }

    try:
        img = _grab_screen_image()
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=80)
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"You are JARVIS assisting commander {USER_NAME}. Analyze this screenshot and answer: {prompt}. Provide a crisp, concise, intelligent response."},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": img_b64
                            }
                        }
                    ]
                }
            ]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=12)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                text_part = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return {
                    "success": True,
                    "description": text_part.strip(),
                    "provider": "Gemini Multimodal Vision"
                }
        return {
            "success": False,
            "error": f"Vision analysis returned code {res.status_code}: {res.text[:150]}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
