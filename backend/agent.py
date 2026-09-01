import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import all tool modules to populate registry
import backend.tools.system_tools
import backend.tools.task_tools
import backend.tools.calendar_tools
import backend.tools.email_tools
import backend.tools.gmail_tools
import backend.tools.web_tools
import backend.tools.file_tools
import backend.tools.code_sandbox
import backend.tools.vision_tools
import backend.tools.computer_tools
import backend.tools.browser_tools
import backend.tools.memory_tools
import backend.tools.whatsapp_tools
import backend.tools.knowledge_tools

from backend.config import (
    LIVEKIT_URL,
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    GOOGLE_API_KEY,
    GEMINI_API_KEY,
    ASSISTANT_NAME,
    USER_NAME,
    DEFAULT_VOICE,
    DEFAULT_MODEL,
)
from backend.voice.livekit_tools import execute_jarvis_tool
from backend.services.memory_service import memory_service
from backend.services.conversation_service import conversation_service
from backend.services.knowledge_service import knowledge_service

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    function_tool,
    room_io,
    cli,
)
from livekit.plugins import google

logger = logging.getLogger("JARVIS.Agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class JarvisVoiceAgent(Agent):
    """
    JARVIS Autonomous Voice Agent powered by Gemini Realtime & LiveKit WebRTC.
    Connects speech-to-speech intelligence directly to JARVIS computer control,
    browser automation, communication APIs, sandboxes, and memory systems.
    """

    def __init__(self):
        super().__init__(
            instructions=(
                f"You are {ASSISTANT_NAME}, the personal AI voice assistant and computer operating system to Boss (Commander {USER_NAME}). "
                "Speak naturally, concisely, and conversationally in 1-2 clear spoken sentences. "
                "Always address the user as 'Boss'. "
                "You have full autonomous computer control, browser automation, Gmail, Google Calendar, memory vault, and Knowledge timetable tools. "
                "CRITICAL RULES: "
                "1. When the user asks to perform an action (e.g. open Chrome, check calendar, send email, take screenshot, search Google, read files), invoke the appropriate tool. "
                "2. NEVER claim an action was performed unless the underlying tool returned success. "
                "3. If a tool fails or requires confirmation, state the actual status truthfully. "
                "4. Answer questions directly, intelligently, and respectfully."
            )
        )

    # -------------------------------------------------------------
    # COMPUTER CONTROL & DESKTOP TOOLS
    # -------------------------------------------------------------
    @function_tool()
    async def open_application(self, context: RunContext, app_name: str) -> Dict[str, Any]:
        """Launch or open a native desktop application on the user's computer.

        Args:
            app_name: Name of the application (e.g., 'Chrome', 'Notepad', 'VS Code', 'Calculator', 'Explorer', 'WhatsApp').
        """
        logger.info(f"Tool Call: open_application('{app_name}')")
        return execute_jarvis_tool("computer.openApplication", {"app_name": app_name})

    @function_tool()
    async def take_screenshot(self, context: RunContext) -> Dict[str, Any]:
        """Capture a real-time screenshot of the user's computer screen."""
        logger.info("Tool Call: take_screenshot()")
        return execute_jarvis_tool("computer.screenshot", {})

    @function_tool()
    async def press_keyboard_keys(self, context: RunContext, keys: List[str]) -> Dict[str, Any]:
        """Simulate a keyboard shortcut or key combination.

        Args:
            keys: List of keys to press together (e.g. ['ctrl', 'c'], ['alt', 'tab'], ['win', 'd']).
        """
        logger.info(f"Tool Call: press_keyboard_keys({keys})")
        return execute_jarvis_tool("computer.keyCombination", {"keys": keys})

    # -------------------------------------------------------------
    # WEB & BROWSER AUTOMATION TOOLS
    # -------------------------------------------------------------
    @function_tool()
    async def search_web(self, context: RunContext, query: str) -> Dict[str, Any]:
        """Search the web for up-to-date information, news, or answers.

        Args:
            query: The search query to look up on the web.
        """
        logger.info(f"Tool Call: search_web('{query}')")
        return execute_jarvis_tool("browser.search", {"query": query})

    @function_tool()
    async def open_browser_url(self, context: RunContext, url: str) -> Dict[str, Any]:
        """Navigate to a specific website or URL in the browser.

        Args:
            url: The web URL to open (e.g. 'https://github.com', 'https://google.com').
        """
        logger.info(f"Tool Call: open_browser_url('{url}')")
        return execute_jarvis_tool("browser.open", {"url": url})

    # -------------------------------------------------------------
    # GOOGLE CALENDAR TOOLS
    # -------------------------------------------------------------
    @function_tool()
    async def get_calendar_events(self, context: RunContext, days_ahead: int = 7) -> Dict[str, Any]:
        """Retrieve scheduled meetings and events from Google Calendar.

        Args:
            days_ahead: Number of days ahead to search (default 7).
        """
        logger.info(f"Tool Call: get_calendar_events(days_ahead={days_ahead})")
        return execute_jarvis_tool("calendar.getEvents", {"days_ahead": days_ahead})

    @function_tool()
    async def create_calendar_event(
        self,
        context: RunContext,
        title: str,
        start_time: str,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Schedule a new event in Google Calendar.

        Args:
            title: Title/subject of the meeting or event.
            start_time: Start time in ISO format or natural language (e.g. '2026-09-02T10:00:00').
            end_time: Optional end time.
        """
        logger.info(f"Tool Call: create_calendar_event('{title}', '{start_time}')")
        return execute_jarvis_tool("calendar.createEvent", {
            "title": title,
            "start_time": start_time,
            "end_time": end_time
        })

    # -------------------------------------------------------------
    # GMAIL & EMAIL TOOLS
    # -------------------------------------------------------------
    @function_tool()
    async def read_emails(self, context: RunContext, unread_only: bool = False) -> Dict[str, Any]:
        """Read recent emails from Gmail inbox.

        Args:
            unread_only: If true, only fetches unread emails.
        """
        logger.info(f"Tool Call: read_emails(unread_only={unread_only})")
        return execute_jarvis_tool("gmail.read", {"unread_only": unread_only})

    @function_tool()
    async def send_email(
        self,
        context: RunContext,
        recipient: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Send an email through Gmail.

        Args:
            recipient: Recipient email address.
            subject: Email subject.
            body: Email body text.
        """
        logger.info(f"Tool Call: send_email(to='{recipient}', subject='{subject}')")
        return execute_jarvis_tool("gmail.send", {
            "recipient": recipient,
            "subject": subject,
            "body": body
        })

    # -------------------------------------------------------------
    # SANDBOX & FILESYSTEM TOOLS
    # -------------------------------------------------------------
    @function_tool()
    async def list_workspace_files(self, context: RunContext) -> Dict[str, Any]:
        """List all files in the JARVIS workspace sandbox."""
        logger.info("Tool Call: list_workspace_files()")
        return execute_jarvis_tool("files.list", {})

    @function_tool()
    async def read_workspace_file(self, context: RunContext, filename: str) -> Dict[str, Any]:
        """Read the contents of a file in the workspace sandbox.

        Args:
            filename: Name of the file to read.
        """
        logger.info(f"Tool Call: read_workspace_file('{filename}')")
        return execute_jarvis_tool("files.read", {"filename": filename})

    @function_tool()
    async def write_workspace_file(self, context: RunContext, filename: str, content: str) -> Dict[str, Any]:
        """Create or update a text file in the workspace sandbox.

        Args:
            filename: Name of the file.
            content: Content to write.
        """
        logger.info(f"Tool Call: write_workspace_file('{filename}')")
        return execute_jarvis_tool("files.create", {"filename": filename, "content": content})

    @function_tool()
    async def run_code_sandbox(self, context: RunContext, language: str, code: str) -> Dict[str, Any]:
        """Execute code in an isolated subprocess sandbox and return the output.

        Args:
            language: 'python' or 'javascript' / 'node'.
            code: The code string to execute.
        """
        logger.info(f"Tool Call: run_code_sandbox(language='{language}')")
        return execute_jarvis_tool("code.run", {"language": language, "code": code})

    # -------------------------------------------------------------
    # LONG-TERM MEMORY & KNOWLEDGE VAULT
    # -------------------------------------------------------------
    @function_tool()
    async def store_memory(self, context: RunContext, key: str, value: str, category: str = "preference") -> Dict[str, Any]:
        """Save a key fact, user preference, or project note to the long-term memory vault.

        Args:
            key: Subject or identifier (e.g. 'favorite_ide', 'active_project').
            value: Details to remember (e.g. 'VS Code', 'AgriMind AI').
            category: Category name (e.g. 'preference', 'project', 'personal').
        """
        logger.info(f"Tool Call: store_memory('{key}', '{value}')")
        return execute_jarvis_tool("memory.store", {"key": key, "value": value, "category": category})

    @function_tool()
    async def search_memory(self, context: RunContext, query: str) -> Dict[str, Any]:
        """Search the long-term memory vault for previously stored facts or preferences.

        Args:
            query: Topic or keyword to search in memories.
        """
        logger.info(f"Tool Call: search_memory('{query}')")
        return execute_jarvis_tool("memory.search", {"query": query})

    @function_tool()
    async def get_today_lectures(self, context: RunContext, weekday: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve today's or a specified weekday's lecture timetable from the Knowledge Vault.

        Args:
            weekday: Optional weekday (e.g. 'Monday', 'Tuesday'). Defaults to current day.
        """
        logger.info(f"Tool Call: get_today_lectures(weekday='{weekday}')")
        return execute_jarvis_tool("knowledge.get_today_lectures", {"weekday": weekday})

    @function_tool()
    async def get_next_class(self, context: RunContext) -> Dict[str, Any]:
        """Retrieve the immediate next class or lecture scheduled for today."""
        logger.info("Tool Call: get_next_class()")
        return execute_jarvis_tool("knowledge.get_next_class", {})

    @function_tool()
    async def get_system_diagnostics(self, context: RunContext) -> Dict[str, Any]:
        """Retrieve system CPU, RAM, disk, OS telemetry, and current time."""
        logger.info("Tool Call: get_system_diagnostics()")
        return execute_jarvis_tool("system.getDiagnostics", {})


server = AgentServer()

@server.rtc_session(agent_name="jarvis-agent")
async def jarvis_agent_session(ctx: JobContext):
    """
    LiveKit RTC Session Entrypoint.
    Binds the Gemini Live RealtimeModel and connects to the WebRTC room.
    """
    logger.info(f"[JARVIS Agent] Starting session in room: {ctx.room.name}")

    model_name = DEFAULT_MODEL if "gemini" in DEFAULT_MODEL else "gemini-2.5-flash"
    
    # Initialize Realtime Gemini model
    realtime_model = google.realtime.RealtimeModel(
        model=model_name,
        voice=DEFAULT_VOICE or "Puck",
        api_key=GOOGLE_API_KEY or GEMINI_API_KEY,
    )

    session = AgentSession(
        llm=realtime_model,
    )

    agent_instance = JarvisVoiceAgent()

    await session.start(
        agent=agent_instance,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            video_input=False,
        ),
    )

    logger.info("[JARVIS Agent] Realtime Voice Session established.")


if __name__ == "__main__":
    cli.run_app(server)
