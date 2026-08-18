import logging
from typing import Optional, Dict, Any
from backend.services.task_service import task_service, TaskStatus
from backend.services.audit_service import audit_service
from backend.tools.registry import registry, RiskLevel

logger = logging.getLogger("JARVIS.Tools.Tasks")

@registry.register(
    name="tasks.list",
    description="Retrieve all personal tasks and their completion status.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["all", "pending", "running", "completed", "paused"],
                "description": "Filter by task status."
            }
        },
        "required": []
    }
)
def list_tasks(status: str = "all"):
    tasks = task_service.list_tasks(status=status if status != "all" else None, limit=50)
    return {
        "count": len(tasks),
        "tasks": tasks
    }

@registry.register(
    name="tasks.create",
    description="Create a new autonomous or personal task/reminder in task vault.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title or objective of the task"},
            "description": {"type": "string", "description": "Detailed notes or reminder message"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority level"},
            "deadline": {"type": "string", "description": "Target time or date for reminder/deadline (e.g. '8:00 PM' or '2026-08-19 20:00')"}
        },
        "required": ["title"]
    }
)
def create_task(title: str, description: str = "", priority: str = "medium", deadline: Optional[str] = None):
    res = task_service.create_task(
        objective=title,
        description=description,
        priority=priority,
        deadline=deadline,
        agent="TaskAgent"
    )

    task_id = res.get("taskId", "TASK-LOCAL")

    audit_service.log_audit(
        task_id=task_id,
        agent="TaskService",
        tool="tasks.create",
        risk_level="LOW",
        permission_decision="APPROVED",
        status="success",
        details={"title": title, "priority": priority, "deadline": deadline}
    )

    return {
        "success": True,
        "task_id": task_id,
        "title": title,
        "deadline": deadline,
        "status": res.get("status", TaskStatus.PLANNED),
        "message": f"Task '{title}' has been scheduled and persisted successfully."
    }

@registry.register(
    name="tasks.create_reminder",
    description="Set a time-based voice/notification reminder at a specific time (e.g. '8:00 PM').",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "reminder_text": {"type": "string", "description": "The reminder message or task to perform"},
            "reminder_time": {"type": "string", "description": "The exact time or time expression (e.g. '8 PM', '20:00', 'tomorrow at 9 AM')"}
        },
        "required": ["reminder_text", "reminder_time"]
    }
)
def create_reminder(reminder_text: str, reminder_time: str) -> Dict[str, Any]:
    """Create a persistent time-based reminder."""
    res = task_service.create_task(
        objective=f"Reminder: {reminder_text}",
        description=f"Trigger voice alert for: {reminder_text}",
        priority="high",
        deadline=reminder_time,
        tags=["reminder", "voice_alert"]
    )
    return {
        "success": True,
        "reminder_text": reminder_text,
        "reminder_time": reminder_time,
        "task_id": res.get("taskId"),
        "message": f"Reminder set for {reminder_time}: '{reminder_text}'."
    }

@registry.register(
    name="tasks.complete",
    description="Mark an existing task as completed in the database.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "ID or title of the task to complete"}
        },
        "required": ["task_id"]
    }
)
def complete_task(task_id: str):
    task = task_service.get_task(task_id)
    if not task:
        return {"success": False, "message": f"No task found matching '{task_id}' in database."}

    t_id = task["taskId"]
    t_title = task["objective"]

    task_service.update_task(
        task_id=t_id,
        status=TaskStatus.COMPLETED,
        progress=100,
        current_step="Completed"
    )

    audit_service.log_audit(
        task_id=t_id,
        agent="TaskService",
        tool="tasks.complete",
        risk_level="LOW",
        permission_decision="APPROVED",
        status="success",
        details={"taskId": t_id, "title": t_title}
    )

    return {
        "success": True,
        "task_id": t_id,
        "title": t_title,
        "status": "COMPLETED",
        "message": f"Task '{t_title}' marked as completed."
    }
