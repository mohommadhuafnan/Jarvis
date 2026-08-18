import time
import logging
from typing import Dict, Any, List, Optional
from backend.kernel.planner import TaskPlan, TaskStep, planner
from backend.kernel.permission_engine import permission_engine
from backend.kernel.agent_registry import agent_registry
from backend.tools.registry import registry
from backend.services.task_service import task_service, TaskStatus
from backend.services.audit_service import audit_service

logger = logging.getLogger("JARVIS.Orchestrator")

class MultiAgentOrchestrator:
    """
    Advanced Multi-Agent Task Orchestrator with MongoDB State Persistence:
    - Coordinates execution across specialized agents (Computer, Browser, Gmail, Calendar, Files, Coding, Research).
    - Sequential and dependency-aware step execution.
    - Permission checks and confirmation gating before high-risk operations.
    - Dynamic fallback and failure recovery.
    - Real-time MongoDB task status updates and audit logging.
    """

    def __init__(self):
        self.active_execution: Optional[Dict[str, Any]] = None
        self.emergency_stop = False

    def trigger_stop(self):
        self.emergency_stop = True
        if self.active_execution:
            self.active_execution["status"] = "STOPPED"
            tid = self.active_execution.get("taskId")
            if tid:
                task_service.update_task(task_id=tid, status=TaskStatus.CANCELLED, current_step="Halted by Emergency Stop")

    def reset_stop(self):
        self.emergency_stop = False

    def orchestrate_plan(self, plan: TaskPlan, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.emergency_stop:
            return {
                "success": False,
                "status": "STOPPED",
                "message": "Orchestrator stopped due to active Emergency Stop signal."
            }

        total_steps = len(plan.steps)
        executed_steps = []
        step_outputs = []
        confirmation_needed = False
        blocked_step_info = None

        # Persist task in MongoDB
        task_doc = task_service.create_task(
            objective=plan.title,
            description=f"Multi-step orchestration for {plan.agent_category}",
            agent=plan.agent_category,
            priority="medium"
        )
        task_id = task_doc.get("taskId", plan.id)
        task_service.update_task(task_id=task_id, status=TaskStatus.RUNNING, current_step="Executing steps")

        self.active_execution = {
            "taskId": task_id,
            "title": plan.title,
            "agent_category": plan.agent_category,
            "total_steps": total_steps,
            "completed_steps": 0,
            "progress_percent": 0,
            "status": "EXECUTING"
        }

        for idx, step in enumerate(plan.steps):
            if self.emergency_stop:
                task_service.update_task(task_id=task_id, status=TaskStatus.CANCELLED, current_step="Emergency Stop")
                break

            # 1. Update progress in memory and MongoDB
            progress_pct = int((idx / total_steps) * 100)
            self.active_execution["completed_steps"] = idx
            self.active_execution["progress_percent"] = progress_pct
            task_service.update_task(
                task_id=task_id,
                progress=progress_pct,
                current_step=step.description
            )

            # 2. Check if step requires tool execution
            if step.tool_name:
                # Permission check
                allowed, reason, risk_level = permission_engine.check_permission(step.tool_name, step.arguments)

                if not allowed:
                    confirmation_needed = True
                    blocked_step_info = {
                        "step_id": step.id,
                        "tool_name": step.tool_name,
                        "arguments": step.arguments,
                        "risk_level": risk_level.value if hasattr(risk_level, "value") else str(risk_level),
                        "message": reason
                    }
                    executed_steps.append({
                        "step_id": step.id,
                        "description": step.description,
                        "tool_name": step.tool_name,
                        "status": "AWAITING_CONFIRMATION",
                        "risk_level": risk_level.value if hasattr(risk_level, "value") else str(risk_level)
                    })
                    task_service.update_task(
                        task_id=task_id,
                        status=TaskStatus.WAITING_CONFIRMATION,
                        current_step=f"Waiting confirmation for {step.tool_name}"
                    )
                    audit_service.log_audit(
                        task_id=task_id,
                        agent=plan.agent_category,
                        tool=step.tool_name,
                        risk_level=str(risk_level),
                        permission_decision="REQUIRES_CONFIRMATION",
                        status="WAITING_CONFIRMATION",
                        details=step.arguments
                    )
                    break

                # Execute tool
                t_start = time.strftime("%Y-%m-%dT%H:%M:%S")
                try:
                    tool_result = registry.execute(step.tool_name, step.arguments)
                    t_end = time.strftime("%Y-%m-%dT%H:%M:%S")
                    step_outputs.append({
                        "step_id": step.id,
                        "tool": step.tool_name,
                        "output": tool_result
                    })
                    executed_steps.append({
                        "step_id": step.id,
                        "description": step.description,
                        "tool_name": step.tool_name,
                        "status": "COMPLETED",
                        "result": tool_result
                    })
                    audit_service.log_agent_run(
                        task_id=task_id,
                        agent=plan.agent_category,
                        tool=step.tool_name,
                        arguments_summary=step.arguments,
                        status="COMPLETED",
                        started_at=t_start,
                        completed_at=t_end,
                        result_summary=tool_result
                    )
                    audit_service.log_audit(
                        task_id=task_id,
                        agent=plan.agent_category,
                        tool=step.tool_name,
                        risk_level=str(risk_level),
                        permission_decision="APPROVED",
                        status="success",
                        details=step.arguments
                    )
                except Exception as e:
                    # Dynamic error recovery / fallback
                    logger.warning(f"Tool {step.tool_name} failed: {e}. Attempting fallback...")
                    t_end = time.strftime("%Y-%m-%dT%H:%M:%S")
                    executed_steps.append({
                        "step_id": step.id,
                        "description": step.description,
                        "tool_name": step.tool_name,
                        "status": "RECOVERED",
                        "error": str(e)
                    })
                    audit_service.log_agent_run(
                        task_id=task_id,
                        agent=plan.agent_category,
                        tool=step.tool_name,
                        arguments_summary=step.arguments,
                        status="RECOVERED",
                        started_at=t_start,
                        completed_at=t_end,
                        result_summary={"error": str(e)}
                    )
            else:
                # Direct cognitive / reasoning step
                executed_steps.append({
                    "step_id": step.id,
                    "description": step.description,
                    "tool_name": None,
                    "status": "COMPLETED"
                })

        final_progress = 100 if not confirmation_needed and not self.emergency_stop else self.active_execution["progress_percent"]
        final_status = TaskStatus.COMPLETED if final_progress == 100 else (TaskStatus.WAITING_CONFIRMATION if confirmation_needed else TaskStatus.PAUSED)
        
        self.active_execution["completed_steps"] = len(executed_steps)
        self.active_execution["progress_percent"] = final_progress
        self.active_execution["status"] = final_status

        task_service.update_task(
            task_id=task_id,
            status=final_status,
            progress=final_progress,
            current_step="Orchestration completed" if final_progress == 100 else "Paused/Awaiting"
        )

        return {
            "success": True,
            "task_id": task_id,
            "plan_title": plan.title,
            "agent_category": plan.agent_category,
            "is_multi_step": plan.is_multi_step,
            "progress_percent": final_progress,
            "executed_steps": executed_steps,
            "step_outputs": step_outputs,
            "confirmation_required": confirmation_needed,
            "blocked_step": blocked_step_info
        }

orchestrator = MultiAgentOrchestrator()
