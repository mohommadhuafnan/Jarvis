"""
JARVIS Tool Package Initialization
Loads all tool modules into the global singleton ToolRegistry.
"""

from backend.tools.registry import registry, RiskLevel, ToolDefinition

# Import all tool modules to trigger @registry.register decorators
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

__all__ = [
    "registry",
    "RiskLevel",
    "ToolDefinition",
]
