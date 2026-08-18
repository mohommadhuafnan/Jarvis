import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.database.collections import get_tasks_col
from backend.database.db import get_db

logger = logging.getLogger("JARVIS.Services.Task")

class TaskStatus:
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    PAUSED = "PAUSED"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    ALL = [
        PLANNED, RUNNING, WAITING_CONFIRMATION, PAUSED,
        RECOVERING, COMPLETED, FAILED, CANCELLED
    ]

class TaskService:
    """
    Persistent Autonomous Task & Reminder Service backed by MongoDB Atlas
    with local SQLite retention fallback for 100% offline uptime and resilience.
    """

    def create_task(
        self,
        objective: str,
        description: str = "",
        agent: str = "TaskAgent",
        priority: str = "medium",
        deadline: Optional[str] = None,
        tags: Optional[List[str]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create and persist a new task in MongoDB and SQLite.
        """
        tid = task_id or f"TASK-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now().isoformat()
        tag_list = tags or ["autonomous", agent.lower()]

        doc = {
            "taskId": tid,
            "objective": objective.strip(),
            "description": description.strip(),
            "status": TaskStatus.PLANNED,
            "progress": 0,
            "currentStep": "Task initialized",
            "agent": agent,
            "priority": priority,
            "deadline": deadline or "",
            "tags": tag_list,
            "createdAt": now,
            "updatedAt": now
        }

        # 1. Primary: MongoDB Storage
        try:
            col = get_tasks_col()
            if col is not None:
                col.replace_one({"taskId": tid}, doc, upsert=True)
                logger.info(f"Created task in MongoDB: {tid} - '{objective}'")
        except Exception as e:
            logger.warning(f"MongoDB storage unavailable for task: {e}")

        # 2. Resilient SQLite Storage
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO tasks (id, title, description, priority, status, deadline, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                status=excluded.status,
                updated_at=excluded.updated_at
            """, (
                tid,
                objective.strip(),
                description.strip(),
                priority,
                TaskStatus.PLANNED,
                deadline or "",
                json.dumps(tag_list),
                now,
                now
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving task to SQLite: {e}")

        return {k: v for k, v in doc.items() if k != "_id"}

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        objective: Optional[str] = None,
        description: Optional[str] = None,
        agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update state, progress, or metadata of an existing task.
        """
        updates: Dict[str, Any] = {"updatedAt": datetime.now().isoformat()}

        if status:
            clean_status = status.upper()
            if clean_status in TaskStatus.ALL:
                updates["status"] = clean_status
                if clean_status == TaskStatus.COMPLETED and progress is None:
                    updates["progress"] = 100
            else:
                updates["status"] = clean_status

        if progress is not None:
            updates["progress"] = max(0, min(100, progress))

        if current_step is not None:
            updates["currentStep"] = current_step

        if objective is not None:
            updates["objective"] = objective

        if description is not None:
            updates["description"] = description

        if agent is not None:
            updates["agent"] = agent

        # 1. Update in MongoDB
        try:
            col = get_tasks_col()
            if col is not None:
                res = col.find_one_and_update(
                    {"taskId": task_id},
                    {"$set": updates},
                    return_document=True
                )
                if res:
                    return {"success": True, "task": {k: v for k, v in res.items() if k != "_id"}}
        except Exception:
            pass

        # 2. Update in SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status=?, updated_at=? WHERE id=?", (updates.get("status", TaskStatus.COMPLETED), datetime.now().isoformat(), task_id))
            conn.commit()
            conn.close()
            return {"success": True, "task": {"taskId": task_id, "status": updates.get("status")}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific task by taskId or fuzzy title match.
        """
        # 1. Try MongoDB
        try:
            col = get_tasks_col()
            if col is not None:
                doc = col.find_one(
                    {
                        "$or": [
                            {"taskId": task_id},
                            {"objective": {"$regex": f"^{task_id}$", "$options": "i"}}
                        ]
                    },
                    {"_id": 0}
                )
                if doc:
                    return doc
        except Exception:
            pass

        # 2. Try SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id=? OR LOWER(title)=LOWER(?) LIMIT 1", (task_id, task_id))
            row = cursor.fetchone()
            conn.close()
            if row:
                d = dict(row)
                return {
                    "taskId": d["id"],
                    "objective": d["title"],
                    "description": d["description"],
                    "priority": d["priority"],
                    "status": d["status"],
                    "deadline": d["deadline"],
                    "tags": json.loads(d["tags"]) if d.get("tags") else []
                }
        except Exception:
            pass

        return None

    def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all tasks, optionally filtered by status.
        """
        # 1. Try MongoDB
        try:
            col = get_tasks_col()
            if col is not None:
                filter_q: Dict[str, Any] = {}
                if status and status.lower() != "all":
                    filter_q["status"] = status.upper()
                cursor = col.find(filter_q, {"_id": 0}).sort("updatedAt", -1).limit(limit)
                results = list(cursor)
                if results:
                    return results
        except Exception:
            pass

        # 2. Try SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            if status and status.lower() != "all":
                cursor.execute("SELECT * FROM tasks WHERE status=? ORDER BY updated_at DESC LIMIT ?", (status.upper(), limit))
            else:
                cursor.execute("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            items = []
            for r in rows:
                d = dict(r)
                items.append({
                    "taskId": d["id"],
                    "objective": d["title"],
                    "description": d["description"],
                    "priority": d["priority"],
                    "status": d["status"],
                    "deadline": d["deadline"],
                    "tags": json.loads(d["tags"]) if d.get("tags") else []
                })
            return items
        except Exception:
            return []

    def recover_interrupted_tasks(self) -> List[Dict[str, Any]]:
        """
        Scan for tasks in RUNNING or WAITING_CONFIRMATION states on restart and mark as RECOVERING.
        """
        try:
            col = get_tasks_col()
            if col is not None:
                now = datetime.now().isoformat()
                cursor = col.find(
                    {"status": {"$in": [TaskStatus.RUNNING, TaskStatus.WAITING_CONFIRMATION]}},
                    {"_id": 0}
                )
                interrupted = list(cursor)
                if interrupted:
                    col.update_many(
                        {"status": {"$in": [TaskStatus.RUNNING, TaskStatus.WAITING_CONFIRMATION]}},
                        {"$set": {"status": TaskStatus.RECOVERING, "currentStep": "Recovered after system restart", "updatedAt": now}}
                    )
                return interrupted
        except Exception:
            pass
        return []

task_service = TaskService()
