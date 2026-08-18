import logging
import pymongo
from backend.database.collections import (
    get_conversations_col,
    get_messages_col,
    get_memories_col,
    get_tasks_col,
    get_agent_runs_col,
    get_audit_logs_col,
    get_preferences_col,
    get_voice_sessions_col,
    get_users_col
)

logger = logging.getLogger("JARVIS.Database.Indexes")

def create_indexes():
    """
    Ensure all optimal indexes are created on MongoDB collections.
    Safe and idempotent — skips if indexes already exist.
    """
    try:
        # 1. Conversations
        conv_col = get_conversations_col()
        if conv_col is not None:
            conv_col.create_index([("conversationId", pymongo.ASCENDING)], unique=True, sparse=True)
            conv_col.create_index([("userId", pymongo.ASCENDING)])
            conv_col.create_index([("updatedAt", pymongo.DESCENDING)])
            logger.info("Ensured indexes on 'conversations'")

        # 2. Messages
        msg_col = get_messages_col()
        if msg_col is not None:
            msg_col.create_index([("conversationId", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING)])
            msg_col.create_index([("timestamp", pymongo.DESCENDING)])
            logger.info("Ensured indexes on 'messages'")

        # 3. Memories
        mem_col = get_memories_col()
        if mem_col is not None:
            mem_col.create_index([("userId", pymongo.ASCENDING), ("key", pymongo.ASCENDING)])
            mem_col.create_index([("type", pymongo.ASCENDING)])
            mem_col.create_index([("updatedAt", pymongo.DESCENDING)])
            logger.info("Ensured indexes on 'memories'")

        # 4. Tasks
        task_col = get_tasks_col()
        if task_col is not None:
            task_col.create_index([("taskId", pymongo.ASCENDING)], unique=True, sparse=True)
            task_col.create_index([("status", pymongo.ASCENDING)])
            task_col.create_index([("updatedAt", pymongo.DESCENDING)])
            logger.info("Ensured indexes on 'tasks'")

        # 5. Agent Runs
        agent_col = get_agent_runs_col()
        if agent_col is not None:
            agent_col.create_index([("taskId", pymongo.ASCENDING)])
            agent_col.create_index([("startedAt", pymongo.DESCENDING)])
            agent_col.create_index([("runId", pymongo.ASCENDING)], unique=True, sparse=True)
            logger.info("Ensured indexes on 'agent_runs'")

        # 6. Audit Logs
        audit_col = get_audit_logs_col()
        if audit_col is not None:
            audit_col.create_index([("taskId", pymongo.ASCENDING)])
            audit_col.create_index([("timestamp", pymongo.DESCENDING)])
            audit_col.create_index([("riskLevel", pymongo.ASCENDING)])
            logger.info("Ensured indexes on 'audit_logs'")

        # 7. Preferences
        pref_col = get_preferences_col()
        if pref_col is not None:
            pref_col.create_index([("userId", pymongo.ASCENDING), ("key", pymongo.ASCENDING)], unique=True)
            logger.info("Ensured indexes on 'preferences'")

        # 8. Voice Sessions
        voice_col = get_voice_sessions_col()
        if voice_col is not None:
            voice_col.create_index([("sessionId", pymongo.ASCENDING)], unique=True, sparse=True)
            voice_col.create_index([("startedAt", pymongo.DESCENDING)])
            logger.info("Ensured indexes on 'voice_sessions'")

        # 9. Users
        user_col = get_users_col()
        if user_col is not None:
            user_col.create_index([("userId", pymongo.ASCENDING)], unique=True, sparse=True)
            logger.info("Ensured indexes on 'users'")

        return True
    except Exception as e:
        logger.error(f"Error ensuring MongoDB indexes: {e}")
        return False
