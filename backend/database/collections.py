from typing import Optional
from pymongo.collection import Collection
from backend.database.mongodb import get_database

class Collections:
    USERS = "users"
    CONVERSATIONS = "conversations"
    MESSAGES = "messages"
    MEMORIES = "memories"
    TASKS = "tasks"
    AGENT_RUNS = "agent_runs"
    TOOL_EXECUTIONS = "tool_executions"
    VOICE_SESSIONS = "voice_sessions"
    PREFERENCES = "preferences"
    AUDIT_LOGS = "audit_logs"
    PERSONAL_PROFILES = "personal_profiles"
    KNOWLEDGE_DOCUMENTS = "knowledge_documents"
    KNOWLEDGE_CHUNKS = "knowledge_chunks"
    KNOWLEDGE_FACTS = "knowledge_facts"
    TIMETABLES = "timetables"
    KNOWLEDGE_SOURCES = "knowledge_sources"

def get_collection(collection_name: str) -> Optional[Collection]:
    """Retrieve a collection instance from the active MongoDB database."""
    db = get_database()
    if db is None:
        return None
    return db[collection_name]

# Helper accessors
def get_users_col() -> Optional[Collection]:
    return get_collection(Collections.USERS)

def get_conversations_col() -> Optional[Collection]:
    return get_collection(Collections.CONVERSATIONS)

def get_messages_col() -> Optional[Collection]:
    return get_collection(Collections.MESSAGES)

def get_memories_col() -> Optional[Collection]:
    return get_collection(Collections.MEMORIES)

def get_tasks_col() -> Optional[Collection]:
    return get_collection(Collections.TASKS)

def get_agent_runs_col() -> Optional[Collection]:
    return get_collection(Collections.AGENT_RUNS)

def get_tool_executions_col() -> Optional[Collection]:
    return get_collection(Collections.TOOL_EXECUTIONS)

def get_voice_sessions_col() -> Optional[Collection]:
    return get_collection(Collections.VOICE_SESSIONS)

def get_preferences_col() -> Optional[Collection]:
    return get_collection(Collections.PREFERENCES)

def get_audit_logs_col() -> Optional[Collection]:
    return get_collection(Collections.AUDIT_LOGS)

def get_personal_profiles_col() -> Optional[Collection]:
    return get_collection(Collections.PERSONAL_PROFILES)

def get_knowledge_docs_col() -> Optional[Collection]:
    return get_collection(Collections.KNOWLEDGE_DOCUMENTS)

def get_knowledge_chunks_col() -> Optional[Collection]:
    return get_collection(Collections.KNOWLEDGE_CHUNKS)

def get_knowledge_facts_col() -> Optional[Collection]:
    return get_collection(Collections.KNOWLEDGE_FACTS)

def get_timetables_col() -> Optional[Collection]:
    return get_collection(Collections.TIMETABLES)

def get_knowledge_sources_col() -> Optional[Collection]:
    return get_collection(Collections.KNOWLEDGE_SOURCES)

