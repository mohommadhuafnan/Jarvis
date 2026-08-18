import inspect
import json
from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel, Field

class RiskLevel:
    READ_ONLY = "READ_ONLY"   # Passive inspection, safe queries (no confirmation required)
    LOW_RISK = "LOW_RISK"     # Benign workspace actions (create task, write workspace file)
    CONFIRM = "CONFIRM"       # External communication, state updates (send email, create calendar event, form submit)
    HIGH_RISK = "HIGH_RISK"   # Destructive actions (delete files, delete calendar events, shell commands)

    # Aliases for backward compatibility
    LOW = "LOW_RISK"
    MEDIUM = "CONFIRM"
    HIGH = "HIGH_RISK"

class ToolDefinition(BaseModel):
    name: str
    description: str
    permission_level: str = RiskLevel.LOW_RISK
    parameters: Dict[str, Any] = Field(default_factory=dict)
    agent_category: str = "computer"

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._definitions: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        risk_level: str = RiskLevel.LOW_RISK,
        parameters: Optional[Dict[str, Any]] = None,
        agent_category: str = "computer"
    ):
        """Decorator to register a tool function with typed schema and permission level."""
        def decorator(func: Callable):
            params = parameters or {
                "type": "object",
                "properties": {},
                "required": []
            }
            self._tools[name] = func
            self._definitions[name] = ToolDefinition(
                name=name,
                description=description,
                permission_level=risk_level,
                parameters=params,
                agent_category=agent_category
            )
            return func
        return decorator

    def register_tool(self, name: str, func: Callable, description: str, risk_level: str = RiskLevel.LOW_RISK, parameters: Optional[Dict[str, Any]] = None, agent_category: str = "computer"):
        params = parameters or {"type": "object", "properties": {}, "required": []}
        self._tools[name] = func
        self._definitions[name] = ToolDefinition(
            name=name,
            description=description,
            permission_level=risk_level,
            parameters=params,
            agent_category=agent_category
        )

    def remove_tool(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            self._definitions.pop(name, None)
            return True
        return False

    def get_tool(self, name: str) -> Optional[Callable]:
        canonical_name = name.replace("_", ".", 1) if name not in self._tools else name
        return self._tools.get(canonical_name)

    def get_definition(self, name: str) -> Optional[ToolDefinition]:
        canonical_name = name.replace("_", ".", 1) if name not in self._definitions else name
        return self._definitions.get(canonical_name)

    def list_tools(self, agent_category: Optional[str] = None) -> List[Dict[str, Any]]:
        tools_list = []
        for defn in self._definitions.values():
            if agent_category is None or defn.agent_category == agent_category:
                tools_list.append(defn.dict())
        return tools_list

    def get_gemini_declarations(self, agent_category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate Gemini FunctionDeclarations schema array."""
        declarations = []
        for defn in self._definitions.values():
            if agent_category is None or defn.agent_category == agent_category:
                declarations.append({
                    "name": defn.name.replace(".", "_"),
                    "description": f"[{defn.permission_level}] {defn.description}",
                    "parameters": defn.parameters
                })
        return declarations

    def execute(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a tool with argument validation and structured result wrapping."""
        args = args or {}
        canonical_name = tool_name
        if canonical_name not in self._tools:
            alt_name = tool_name.replace("_", ".", 1)
            if alt_name in self._tools:
                canonical_name = alt_name

        if canonical_name not in self._tools:
            return {
                "success": False,
                "error": {
                    "code": "TOOL_NOT_FOUND",
                    "message": f"Tool '{tool_name}' is not registered in the Tool Registry."
                }
            }

        func = self._tools[canonical_name]
        defn = self._definitions.get(canonical_name)
        permission_level = defn.permission_level if defn else RiskLevel.LOW_RISK

        try:
            result = func(**args)
            return {
                "success": True,
                "tool": canonical_name,
                "permission_level": permission_level,
                "result": result
            }
        except TypeError as te:
            return {
                "success": False,
                "tool": canonical_name,
                "permission_level": permission_level,
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": f"Argument signature mismatch: {str(te)}"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "tool": canonical_name,
                "permission_level": permission_level,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                }
            }

# Global Singleton Tool Registry
registry = ToolRegistry()
