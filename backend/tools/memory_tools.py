from typing import Dict, Any
from backend.services.memory_service import memory_service
from backend.services.audit_service import audit_service
from backend.tools.registry import registry, RiskLevel

@registry.register(
    name="memory.store",
    description="Store a permanent memory, user preference, project detail, or note in JARVIS long-term memory vault.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["user_preference", "preferences", "projects", "people", "routines", "notes"],
                "description": "Category of memory"
            },
            "key": {"type": "string", "description": "Subject or key of the memory (e.g. main_project)"},
            "value": {"type": "string", "description": "The exact fact or preference to remember"}
        },
        "required": ["category", "key", "value"]
    }
)
def store_memory(category: str, key: str, value: str):
    res = memory_service.store_memory(
        key=key,
        value=value,
        memory_type=category,
        source="conversation"
    )

    audit_service.log_audit(
        task_id="memory_op",
        agent="MemoryService",
        tool="memory.store",
        risk_level="MEDIUM",
        permission_decision="APPROVED",
        status="success" if res.get("success") else "failed",
        details={"key": key, "category": category}
    )

    return {
        "success": res.get("success", True),
        "key": key,
        "value": value,
        "category": category,
        "message": f"I have saved this to my persistent memory vault: '{key}' -> '{value}'."
    }

@registry.register(
    name="memory.search",
    description="Search long-term memory for previously remembered facts, preferences, or project details.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term or concept to recall"}
        },
        "required": ["query"]
    }
)
def search_memory(query: str):
    memories = memory_service.search_memory(query=query, limit=10)
    return {
        "query": query,
        "match_count": len(memories),
        "memories": memories
    }

@registry.register(
    name="memory.list",
    description="List all stored personal memories in the vault.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_memories():
    memories = memory_service.list_memories(limit=50)
    return {
        "total": len(memories),
        "memories": memories
    }
