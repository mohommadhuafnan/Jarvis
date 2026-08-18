import logging
import sqlite3
from datetime import datetime
from backend.config import DB_PATH, USER_NAME
from backend.database.collections import (
    get_tasks_col,
    get_memories_col,
    get_audit_logs_col,
    get_preferences_col
)

logger = logging.getLogger("JARVIS.Database.Migration")

def run_sqlite_to_mongodb_migration() -> dict:
    """
    Migrate initial tasks, memory_vault, and activity_logs from SQLite to MongoDB Atlas.
    Idempotent: skips records that already exist in MongoDB.
    """
    stats = {
        "tasks_migrated": 0,
        "memories_migrated": 0,
        "logs_migrated": 0,
        "errors": []
    }

    if not DB_PATH.exists():
        logger.info("No SQLite database found to migrate.")
        return stats

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Migrate Tasks
        tasks_col = get_tasks_col()
        if tasks_col is not None:
            try:
                cursor.execute("SELECT * FROM tasks")
                rows = cursor.fetchall()
                for r in rows:
                    t_id = r["id"]
                    existing = tasks_col.find_one({"taskId": t_id})
                    if not existing:
                        status_map = {
                            "pending": "RUNNING",
                            "completed": "COMPLETED",
                            "cancelled": "CANCELLED"
                        }
                        status_val = status_map.get(r["status"].lower(), r["status"].upper())
                        doc = {
                            "taskId": t_id,
                            "objective": r["title"],
                            "description": r["description"] or "",
                            "status": status_val,
                            "progress": 100 if status_val == "COMPLETED" else 25,
                            "currentStep": "Migrated from local storage",
                            "agent": "CodingAgent",
                            "priority": r["priority"] or "medium",
                            "deadline": r["deadline"] or "",
                            "tags": [t.strip() for t in (r["tags"] or "").split(",") if t.strip()],
                            "createdAt": r["created_at"],
                            "updatedAt": r["updated_at"]
                        }
                        tasks_col.insert_one(doc)
                        stats["tasks_migrated"] += 1
            except Exception as e:
                stats["errors"].append(f"Task migration error: {e}")

        # 2. Migrate Memories
        mem_col = get_memories_col()
        if mem_col is not None:
            try:
                cursor.execute("SELECT * FROM memory_vault")
                rows = cursor.fetchall()
                for r in rows:
                    key = r["key"]
                    existing = mem_col.find_one({"userId": USER_NAME, "key": key})
                    if not existing:
                        doc = {
                            "userId": USER_NAME,
                            "type": r["category"] or "user_preference",
                            "key": key,
                            "value": r["value"],
                            "source": "sqlite_migration",
                            "tags": [t.strip() for t in (r["tags"] or "").split(",") if t.strip()],
                            "createdAt": r["created_at"],
                            "updatedAt": r["updated_at"]
                        }
                        mem_col.insert_one(doc)
                        stats["memories_migrated"] += 1
            except Exception as e:
                stats["errors"].append(f"Memory migration error: {e}")

        # 3. Migrate Activity Logs to Audit Logs
        audit_col = get_audit_logs_col()
        if audit_col is not None:
            try:
                cursor.execute("SELECT * FROM activity_logs")
                rows = cursor.fetchall()
                for r in rows:
                    log_id = r["id"]
                    existing = audit_col.find_one({"taskId": log_id})
                    if not existing:
                        doc = {
                            "taskId": log_id,
                            "timestamp": r["created_at"] or datetime.now().isoformat(),
                            "agent": r["module"] or "System",
                            "tool": r["action"] or "SystemAction",
                            "riskLevel": "READ_ONLY",
                            "permissionDecision": "APPROVED",
                            "status": r["status"] or "success",
                            "details": r["details"] or ""
                        }
                        audit_col.insert_one(doc)
                        stats["logs_migrated"] += 1
            except Exception as e:
                stats["errors"].append(f"Audit log migration error: {e}")

        conn.close()
        logger.info(f"Migration completed: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        stats["errors"].append(str(e))
        return stats
