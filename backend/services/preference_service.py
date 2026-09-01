import logging
from datetime import datetime
from typing import Dict, Any, Optional
from backend.config import USER_NAME
from backend.database.collections import get_preferences_col

logger = logging.getLogger("JARVIS.Services.Preference")

class PreferenceService:
    """
    User Preferences & Personalization Service backed by MongoDB.
    """

    def __init__(self):
        self.default_user = USER_NAME or "default_user"

    def set_preference(self, key: str, value: Any, user_id: Optional[str] = None) -> Dict[str, Any]:
        col = get_preferences_col()
        uid = user_id or self.default_user
        now = datetime.now().isoformat()

        doc = {
            "userId": uid,
            "key": key,
            "value": value,
            "updatedAt": now
        }

        if col is not None:
            try:
                col.update_one(
                    {"userId": uid, "key": key},
                    {"$set": doc},
                    upsert=True
                )
                logger.info(f"Updated preference for {uid}: '{key}' -> '{value}'")
                return {"success": True, "key": key, "value": value, "userId": uid}
            except Exception as e:
                logger.error(f"Error setting preference '{key}': {e}")
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "MongoDB unavailable"}

    def get_preference(self, key: str, default: Any = None, user_id: Optional[str] = None) -> Any:
        col = get_preferences_col()
        uid = user_id or self.default_user
        if col is not None:
            try:
                doc = col.find_one({"userId": uid, "key": key}, {"_id": 0})
                if doc:
                    return doc.get("value", default)
            except Exception as e:
                logger.error(f"Error getting preference '{key}': {e}")
        return default

    def get_all_preferences(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        col = get_preferences_col()
        uid = user_id or self.default_user
        if col is None:
            return {}

        try:
            cursor = col.find({"userId": uid}, {"_id": 0})
            return {doc["key"]: doc.get("value") for doc in cursor if "key" in doc}
        except Exception as e:
            logger.error(f"Error getting all preferences for '{uid}': {e}")
            return {}

preference_service = PreferenceService()
