import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import USER_NAME
from backend.database.collections import get_memories_col
from backend.database.db import get_db

logger = logging.getLogger("JARVIS.Services.Memory")

class MemoryService:
    """
    Persistent Long-Term Memory Service for JARVIS backed by MongoDB Atlas
    with local SQLite retention fallback for 100% offline uptime and resilience.
    """

    def __init__(self):
        self.default_user = USER_NAME or "RAVIT"

    def _parse_tags(self, raw: Any) -> List[str]:
        if not raw:
            return []
        if isinstance(raw, list):
            return raw
        try:
            val = json.loads(raw)
            return val if isinstance(val, list) else [str(val)]
        except Exception:
            return [t.strip() for t in str(raw).split(",") if t.strip()]

    def store_memory(
        self,
        key: str,
        value: str,
        memory_type: str = "user_preference",
        source: str = "conversation",
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Store or update a key-value memory in MongoDB with SQLite persistence.
        """
        uid = user_id or self.default_user
        now = datetime.now().isoformat()
        clean_key = key.strip()
        tag_list = tags or [memory_type, clean_key.lower()]

        doc = {
            "userId": uid,
            "type": memory_type,
            "key": clean_key,
            "value": value.strip(),
            "source": source,
            "tags": tag_list,
            "updatedAt": now
        }

        # 1. Primary: MongoDB Storage
        mongo_success = False
        try:
            col = get_memories_col()
            if col is not None:
                res = col.update_one(
                    {"userId": uid, "key": {"$regex": f"^{clean_key}$", "$options": "i"}},
                    {"$set": doc, "$setOnInsert": {"createdAt": now, "id": f"mem_{uuid.uuid4().hex[:8]}"}},
                    upsert=True
                )
                mongo_success = True
                logger.info(f"Stored memory in MongoDB: '{clean_key}' -> '{value}'")
        except Exception as e:
            logger.warning(f"MongoDB storage unavailable, saving to SQLite: {e}")

        # 2. Resilient SQLite Storage
        try:
            conn = get_db()
            cursor = conn.cursor()
            mem_id = f"mem_{uuid.uuid4().hex[:8]}"
            cursor.execute("""
            INSERT INTO memory_vault (id, category, key, value, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
            """, (
                mem_id,
                memory_type,
                clean_key,
                value.strip(),
                json.dumps(tag_list),
                now,
                now
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving memory to SQLite: {e}")

        return {
            "success": True,
            "key": clean_key,
            "value": value,
            "type": memory_type,
            "source": source,
            "updatedAt": now
        }

    def get_memory(self, key: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by exact or case-insensitive key.
        """
        uid = user_id or self.default_user
        clean_key = key.strip()

        # 1. Try MongoDB
        try:
            col = get_memories_col()
            if col is not None:
                doc = col.find_one(
                    {"userId": uid, "key": {"$regex": f"^{clean_key}$", "$options": "i"}},
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
            cursor.execute("SELECT * FROM memory_vault WHERE LOWER(key) = LOWER(?) ORDER BY updated_at DESC LIMIT 1", (clean_key,))
            row = cursor.fetchone()
            conn.close()
            if row:
                d = dict(row)
                return {
                    "key": d["key"],
                    "value": d["value"],
                    "category": d["category"],
                    "type": d["category"],
                    "tags": self._parse_tags(d.get("tags")),
                    "updatedAt": d["updated_at"]
                }
        except Exception:
            pass

        return None

    def search_memory(self, query: str, user_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories across key, value, and tags.
        """
        uid = user_id or self.default_user
        clean_q = query.strip()
        results = []

        # 1. Try MongoDB
        try:
            col = get_memories_col()
            if col is not None:
                regex_query = {"$regex": clean_q, "$options": "i"}
                cursor = col.find(
                    {
                        "userId": uid,
                        "$or": [
                            {"key": regex_query},
                            {"value": regex_query},
                            {"tags": regex_query},
                            {"type": regex_query}
                        ]
                    },
                    {"_id": 0}
                ).sort("updatedAt", -1).limit(limit)
                results = list(cursor)
                if results:
                    return results
        except Exception:
            pass

        # 2. Try SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            like_pattern = f"%{clean_q}%"
            like_underscore = f"%{clean_q.replace(' ', '_')}%"
            tokens = [t.strip() for t in clean_q.split() if len(t.strip()) > 1]

            query_sql = """
            SELECT * FROM memory_vault
            WHERE key LIKE ? OR key LIKE ? OR value LIKE ? OR category LIKE ? OR tags LIKE ?
            """
            params: List[Any] = [like_pattern, like_underscore, like_pattern, like_pattern, like_pattern]

            for token in tokens:
                t_pat = f"%{token}%"
                query_sql += " OR key LIKE ? OR value LIKE ?"
                params.extend([t_pat, t_pat])

            query_sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            conn.close()
            seen_keys = set()
            for r in rows:
                d = dict(r)
                if d["key"] not in seen_keys:
                    seen_keys.add(d["key"])
                    results.append({
                        "key": d["key"],
                        "value": d["value"],
                        "category": d["category"],
                        "type": d["category"],
                        "tags": self._parse_tags(d.get("tags")),
                        "updatedAt": d["updated_at"]
                    })
        except Exception as e:
            logger.error(f"Error searching SQLite memory vault: {e}")

        return results

    def list_memories(
        self,
        user_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List all memories for a user, optionally filtered by type.
        """
        uid = user_id or self.default_user
        results = []

        # 1. Try MongoDB
        try:
            col = get_memories_col()
            if col is not None:
                filter_query: Dict[str, Any] = {"userId": uid}
                if memory_type:
                    filter_query["type"] = memory_type
                cursor = col.find(filter_query, {"_id": 0}).sort("updatedAt", -1).limit(limit)
                results = list(cursor)
                if results:
                    return results
        except Exception:
            pass

        # 2. Try SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            if memory_type:
                cursor.execute("SELECT * FROM memory_vault WHERE category=? ORDER BY updated_at DESC LIMIT ?", (memory_type, limit))
            else:
                cursor.execute("SELECT * FROM memory_vault ORDER BY updated_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            for r in rows:
                d = dict(r)
                results.append({
                    "id": d["id"],
                    "key": d["key"],
                    "value": d["value"],
                    "category": d["category"],
                    "type": d["category"],
                    "tags": self._parse_tags(d.get("tags")),
                    "updatedAt": d["updated_at"]
                })
        except Exception:
            pass

        return results

    def delete_memory(self, key_or_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a memory by key or ID.
        """
        uid = user_id or self.default_user
        deleted = False

        try:
            col = get_memories_col()
            if col is not None:
                res = col.delete_one({
                    "userId": uid,
                    "$or": [
                        {"key": key_or_id},
                        {"id": key_or_id}
                    ]
                })
                deleted = res.deleted_count > 0
        except Exception:
            pass

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memory_vault WHERE key=? OR id=?", (key_or_id, key_or_id))
            conn.commit()
            conn.close()
            deleted = True
        except Exception:
            pass

        return deleted

memory_service = MemoryService()
