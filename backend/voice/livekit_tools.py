import logging
import time
from typing import Dict, Any, List, Optional
from backend.tools.registry import registry, RiskLevel
from backend.kernel.permission_engine import permission_engine
from backend.services.audit_service import audit_service
from backend.services.memory_service import memory_service
from backend.services.task_service import task_service

logger = logging.getLogger("JARVIS.Voice.LiveKitTools")

def execute_jarvis_tool(
    tool_name: str,
    args: Dict[str, Any],
    agent_category: str = "VoiceAgent"
) -> Dict[str, Any]:
    """
    Executes a JARVIS tool safely through the Permission Engine and Tool Registry.
    Guarantees structured success/failure return without hallucinations.
    """
    start_time = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # 1. Permission & Safety check
    allowed, reason, risk = permission_engine.check_permission(tool_name, args)
    if not allowed:
        audit_service.log_audit(
            task_id=f"voice_act_{int(time.time())}",
            agent=agent_category,
            tool=tool_name,
            risk_level=str(risk),
            permission_decision="CONFIRMATION_REQUIRED",
            status="PENDING_CONFIRMATION",
            details=args
        )
        return {
            "success": False,
            "confirmation_required": True,
            "tool": tool_name,
            "risk_level": str(risk),
            "reason": reason,
            "error": f"Confirmation required before executing {tool_name}. Reason: {reason}"
        }

    # 2. Tool Execution
    result = registry.execute(tool_name, args)
    end_time = time.strftime("%Y-%m-%dT%H:%M:%S")

    # 3. Log Audit & Agent Run
    is_success = result.get("success", False)
    audit_service.log_audit(
        task_id=f"voice_act_{int(time.time())}",
        agent=agent_category,
        tool=tool_name,
        risk_level=str(risk),
        permission_decision="APPROVED",
        status="success" if is_success else "failed",
        details=args
    )
    audit_service.log_agent_run(
        task_id=f"voice_act_{int(time.time())}",
        agent=agent_category,
        tool=tool_name,
        arguments_summary=args,
        status="COMPLETED" if is_success else "FAILED",
        started_at=start_time,
        completed_at=end_time,
        result_summary=result
    )

    return result
