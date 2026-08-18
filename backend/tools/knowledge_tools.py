from typing import Dict, Any, Optional
from backend.services.knowledge_service import knowledge_service
from backend.services.audit_service import audit_service
from backend.tools.registry import registry, RiskLevel

@registry.register(
    name="knowledge.get_today_lectures",
    description="Retrieve the user's scheduled university lectures and classes for today or a specific day from their active semester timetable.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {
            "weekday": {
                "type": "string",
                "description": "Optional target day e.g. 'today', 'tomorrow', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'"
            }
        },
        "required": []
    }
)
def get_today_lectures(weekday: Optional[str] = "today"):
    res = knowledge_service.get_today_lectures(target_weekday=weekday)
    return res

@registry.register(
    name="knowledge.get_next_class",
    description="Determine the next immediate upcoming university lecture/class today based on the current time.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_next_class():
    return knowledge_service.get_next_class()

@registry.register(
    name="knowledge.get_timetable",
    description="Retrieve the user's complete active weekly university timetable.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_timetable():
    return knowledge_service.get_active_timetable()

@registry.register(
    name="knowledge.get_profile",
    description="Retrieve the user's structured personal profile, including degree, year, primary project, university, and preferences.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_profile():
    profile = knowledge_service.get_personal_profile()
    return {
        "success": True,
        "profile": profile,
        "summary": f"Degree: {profile.get('degree')}, Year: {profile.get('year')}, Primary Project: {profile.get('primary_project')}"
    }

@registry.register(
    name="knowledge.search_vault",
    description="Search the Personal Knowledge Vault for facts, project details, assignment deadlines, or notes.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term or concept to find in vault"}
        },
        "required": ["query"]
    }
)
def search_vault(query: str):
    return knowledge_service.search_vault(query=query)

@registry.register(
    name="knowledge.forget",
    description="Delete or deactivate specific knowledge, a timetable, or facts from the vault upon user request.",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "The item, document, or concept to forget"}
        },
        "required": ["target"]
    }
)
def forget_knowledge(target: str):
    res = knowledge_service.forget_knowledge(target=target)
    audit_service.log_audit(
        task_id="knowledge_forget",
        agent="KnowledgeService",
        tool="knowledge.forget",
        risk_level="MEDIUM",
        permission_decision="APPROVED",
        status="success",
        details=f"Forgot knowledge related to '{target}'"
    )
    return res
