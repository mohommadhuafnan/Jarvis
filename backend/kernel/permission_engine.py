from typing import Dict, Any, Tuple
import backend.tools
from backend.tools.registry import RiskLevel, registry

class PermissionEngine:
    """
    Centralized Permission Engine for JARVIS.
    Enforces risk levels:
    - READ_ONLY: Safe passive operations (No confirmation)
    - LOW_RISK: Safe workspace operations (No confirmation)
    - CONFIRM: External side-effects / state modifications (User confirmation required)
    - HIGH_RISK: Destructive actions / shell execution (Explicit double-check required)
    """

    def check_permission(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str, RiskLevel]:
        defn = registry.get_definition(tool_name)
        if not defn:
            return False, f"Tool '{tool_name}' is not registered in security matrix.", RiskLevel.HIGH_RISK

        level = defn.permission_level

        if level in [RiskLevel.READ_ONLY, RiskLevel.LOW_RISK]:
            return True, "Auto-approved by safety engine.", level

        if level == RiskLevel.CONFIRM:
            return False, f"Confirmation required before executing {tool_name}.", level

        if level == RiskLevel.HIGH_RISK:
            return False, f"HIGH RISK: Explicit confirmation required for destructive action {tool_name}.", level

        return False, "Unknown permission level.", RiskLevel.HIGH_RISK

permission_engine = PermissionEngine()
