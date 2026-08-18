from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class AgentDescriptor:
    name: str
    category: str
    description: str
    capabilities: List[str]
    tools: List[str]
    health_status: str = "HEALTHY"
    risk_profile: str = "LOW"

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentDescriptor] = {}
        self._register_default_agents()

    def register_agent(self, descriptor: AgentDescriptor):
        self._agents[descriptor.name.lower()] = descriptor

    def get_agent(self, name: str) -> Optional[AgentDescriptor]:
        return self._agents.get(name.lower())

    def list_agents(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": a.name,
                "category": a.category,
                "description": a.description,
                "capabilities": a.capabilities,
                "tools": a.tools,
                "health_status": a.health_status,
                "risk_profile": a.risk_profile
            }
            for a in self._agents.values()
        ]

    def _register_default_agents(self):
        # 1. Computer Control Agent
        self.register_agent(AgentDescriptor(
            name="ComputerAgent",
            category="computer",
            description="Native Windows OS automation, window viewport management, PyAutoGUI hardware simulation, and Gemini screen vision.",
            capabilities=["app_launching", "window_management", "mouse_keyboard_simulation", "multimodal_screen_vision"],
            tools=[
                "computer.openApplication", "computer.closeApplication", "computer.focusApplication",
                "computer.minimizeWindow", "computer.maximizeWindow", "computer.moveMouse",
                "computer.click", "computer.typeText", "computer.pressKey", "computer.hotkey",
                "computer.scroll", "computer.takeScreenshot", "computer.analyzeScreen"
            ],
            health_status="HEALTHY",
            risk_profile="MEDIUM"
        ))

        # 2. Playwright Browser Agent
        self.register_agent(AgentDescriptor(
            name="BrowserAgent",
            category="browser",
            description="Playwright DOM and accessibility automation, multi-tab session management, web scraping, and form interaction.",
            capabilities=["dom_scraping", "tab_management", "web_search", "accessibility_navigation", "form_filling"],
            tools=[
                "browser.open", "browser.navigate", "browser.newTab", "browser.closeTab",
                "browser.getTabs", "browser.getCurrentUrl", "browser.getPageTitle", "browser.readPage",
                "browser.findText", "browser.clickElement", "browser.typeIntoField", "browser.selectOption",
                "browser.scroll", "browser.goBack", "browser.goForward", "browser.refresh",
                "browser.screenshot", "browser.submitForm", "browser.search"
            ],
            health_status="HEALTHY",
            risk_profile="LOW"
        ))

        # 3. Google Gmail Agent
        self.register_agent(AgentDescriptor(
            name="GmailAgent",
            category="google",
            description="Secure Google Gmail API integration, OAuth inbox scanning, thread-safe email replies, prompt-injection defense, and drafting.",
            capabilities=["unread_scanning", "query_search", "prompt_injection_sanitization", "draft_creation", "secure_sending"],
            tools=[
                "gmail.getUnreadEmails", "gmail.searchEmails", "gmail.getEmail", "gmail.createDraft",
                "gmail.reply", "gmail.send", "gmail.archive", "gmail.addLabel"
            ],
            health_status="HEALTHY",
            risk_profile="MEDIUM"
        ))

        # 4. Google Calendar Agent
        self.register_agent(AgentDescriptor(
            name="CalendarAgent",
            category="google",
            description="Google Calendar scheduling, conflict matrix resolution, availability calculation, and cross-agent briefing correlation.",
            capabilities=["event_scheduling", "conflict_detection", "free_time_calculation", "timezone_parsing", "event_rescheduling"],
            tools=[
                "calendar.listCalendars", "calendar.listEvents", "calendar.getEvents", "calendar.getEvent",
                "calendar.createEvent", "calendar.updateEvent", "calendar.deleteEvent",
                "calendar.checkAvailability", "calendar.findFreeTime"
            ],
            health_status="HEALTHY",
            risk_profile="MEDIUM"
        ))

        # 5. File System & Memory Agent
        self.register_agent(AgentDescriptor(
            name="FileAgent",
            category="files",
            description="Local workspace file system access, document discovery, structured note persistence, and long-term semantic memory vault.",
            capabilities=["file_listing", "safe_file_reading", "file_writing", "semantic_memory_vault"],
            tools=["files.list", "files.read", "files.write", "memory.store", "memory.retrieve", "memory.search"],
            health_status="HEALTHY",
            risk_profile="LOW"
        ))

        # 6. Coding & Sandbox Agent
        self.register_agent(AgentDescriptor(
            name="CodingAgent",
            category="coding",
            description="Isolated subprocess code execution environment with hard execution timeouts and syntax checking for Python and Node.js.",
            capabilities=["code_generation", "subprocess_sandbox", "stdout_stderr_auditing", "execution_timeout_guards"],
            tools=["code.run", "code.test"],
            health_status="HEALTHY",
            risk_profile="HIGH"
        ))

        # 7. Research & Web Agent
        self.register_agent(AgentDescriptor(
            name="ResearchAgent",
            category="research",
            description="Global network index querying, multi-source verification, technical documentation scraping, and knowledge synthesis.",
            capabilities=["web_querying", "source_validation", "knowledge_synthesis", "content_extraction"],
            tools=["web.search", "web.fetch"],
            health_status="HEALTHY",
            risk_profile="LOW"
        ))

agent_registry = AgentRegistry()
