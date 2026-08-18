import time
import uuid
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.database.db import get_db
from backend.database.collections import get_collection

logger = logging.getLogger("JARVIS.SchedulerService")

class SchedulerService:
    """
    Persistent background reminder scheduler daemon.
    Survives restarts, polls MongoDB Atlas and local SQLite, detects due reminders,
    and dispatches automatic voice alerts to the user without any button presses.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._due_queue: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._init_sqlite()

    def _init_sqlite(self):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_reminders (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    reminder_time TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    delivered INTEGER DEFAULT 0,
                    delivered_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing SQLite scheduler table: {e}")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("JARVIS Background Reminder Scheduler started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("JARVIS Background Reminder Scheduler stopped.")

    def add_reminder(self, title: str, reminder_time: str, due_at: Optional[str] = None) -> Dict[str, Any]:
        """
        Persist reminder to both MongoDB Atlas and SQLite fallback.
        """
        reminder_id = f"rem_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now().isoformat()
        
        # If due_at is not an ISO string, parse or fallback to current time
        due_iso = due_at or now_iso

        # 1. SQLite Storage
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO scheduled_reminders (id, title, reminder_time, due_at, delivered, created_at)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (reminder_id, title, reminder_time, due_iso, now_iso))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to persist reminder to SQLite: {e}")

        # 2. MongoDB Storage
        try:
            col = get_collection("reminders")
            if col is not None:
                col.update_one(
                    {"_id": reminder_id},
                    {"$set": {
                        "_id": reminder_id,
                        "title": title,
                        "reminder_time": reminder_time,
                        "due_at": due_iso,
                        "delivered": False,
                        "createdAt": now_iso
                    }},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Failed to persist reminder to MongoDB: {e}")

        logger.info(f"Reminder registered: '{title}' due at {due_iso}")
        return {
            "success": True,
            "id": reminder_id,
            "title": title,
            "reminder_time": reminder_time,
            "due_at": due_iso,
            "message": f"Reminder for '{title}' saved and armed."
        }

    def _run_loop(self):
        """Background continuous checking loop (runs every 3 seconds)."""
        while self._running:
            try:
                self._check_due_reminders()
            except Exception as e:
                logger.error(f"Error in scheduler check loop: {e}")
            time.sleep(3)

    def _check_due_reminders(self):
        now = datetime.now()
        now_iso = now.isoformat()

        due_items = []

        # 1. Check SQLite for pending reminders
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, reminder_time, due_at 
                FROM scheduled_reminders 
                WHERE delivered = 0 AND due_at <= ?
            """, (now_iso,))
            rows = cursor.fetchall()
            for r in rows:
                due_items.append({
                    "id": r["id"],
                    "title": r["title"],
                    "reminder_time": r["reminder_time"],
                    "due_at": r["due_at"]
                })
            conn.close()
        except Exception as e:
            logger.error(f"Error querying due reminders from SQLite: {e}")

        # 2. Check MongoDB for pending reminders
        try:
            col = get_collection("reminders")
            if col is not None:
                mongo_docs = list(col.find({"delivered": False, "due_at": {"$lte": now_iso}}))
                for doc in mongo_docs:
                    doc_id = str(doc.get("_id"))
                    if not any(d["id"] == doc_id for d in due_items):
                        due_items.append({
                            "id": doc_id,
                            "title": doc.get("title", "Reminder"),
                            "reminder_time": doc.get("reminder_time", "Now"),
                            "due_at": doc.get("due_at", now_iso)
                        })
        except Exception as e:
            pass

        # 3. Mark as delivered and push to announcement queue
        for item in due_items:
            self._mark_delivered(item["id"])
            with self._lock:
                # Avoid duplicate queue entries
                if not any(q["id"] == item["id"] for q in self._due_queue):
                    spoken_msg = f"Boss, this is your reminder. You have your {item['title']} scheduled for {item['reminder_time']}."
                    self._due_queue.append({
                        "id": item["id"],
                        "title": item["title"],
                        "reminder_time": item["reminder_time"],
                        "spoken_notification": spoken_msg,
                        "timestamp": now_iso
                    })
                    logger.info(f"DUE REMINDER FIRED: {spoken_msg}")

    def _mark_delivered(self, reminder_id: str):
        now_iso = datetime.now().isoformat()
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE scheduled_reminders SET delivered = 1, delivered_at = ? WHERE id = ?", (now_iso, reminder_id))
            conn.commit()
            conn.close()
        except Exception:
            pass

        try:
            col = get_collection("reminders")
            if col is not None:
                col.update_one({"_id": reminder_id}, {"$set": {"delivered": True, "deliveredAt": now_iso}})
        except Exception:
            pass

    def pop_due_notifications(self) -> List[Dict[str, Any]]:
        """Retrieve and clear queued due notifications for frontend voice delivery."""
        with self._lock:
            notifications = list(self._due_queue)
            self._due_queue.clear()
            return notifications

    def get_all_reminders(self) -> List[Dict[str, Any]]:
        """Return all stored reminders."""
        reminders = []
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scheduled_reminders ORDER BY due_at ASC")
            rows = cursor.fetchall()
            for r in rows:
                reminders.append(dict(r))
            conn.close()
        except Exception:
            pass
        return reminders

scheduler_service = SchedulerService()
