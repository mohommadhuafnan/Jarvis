import os
import re
import json
import uuid
import hashlib
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
from backend.config import GEMINI_API_KEY, USER_NAME, BASE_DIR
from backend.database.collections import (
    get_personal_profiles_col,
    get_knowledge_docs_col,
    get_knowledge_facts_col,
    get_timetables_col,
    get_memories_col
)
from backend.database.db import get_db, init_db

logger = logging.getLogger("JARVIS.Services.Knowledge")

STORAGE_VAULT_DIR = Path(BASE_DIR) / "storage" / "vault"
STORAGE_VAULT_DIR.mkdir(parents=True, exist_ok=True)

class KnowledgeService:
    """
    JARVIS Personal Knowledge Vault & User Context Engine.
    Handles multimodal ingestion (PDF, Images, Text), structured timetable extraction,
    profile management, semantic retrieval, versioning/superseding, and grounding.
    """

    def __init__(self):
        init_db()
        self.default_user = USER_NAME or "default_user"
        self.api_key = GEMINI_API_KEY or ""

    def _call_gemini_json(self, prompt: str, image_bytes: Optional[bytes] = None, mime_type: str = "image/png") -> Dict[str, Any]:
        """Direct Gemini REST API call requesting structured JSON extraction with fallback models."""
        models = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.0-flash", "gemini-2.5-flash"]
        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                headers = {"Content-Type": "application/json", "X-goog-api-key": self.api_key}

                parts: List[Dict[str, Any]] = []
                if image_bytes:
                    import base64
                    b64 = base64.b64encode(image_bytes).decode("utf-8")
                    parts.append({"inline_data": {"mime_type": mime_type, "data": b64}})
                parts.append({"text": prompt})

                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json"
                    }
                }

                resp = requests.post(url, headers=headers, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        # Parse JSON text
                        text_clean = re.sub(r"^```json\s*", "", text.strip())
                        text_clean = re.sub(r"\s*```$", "", text_clean)
                        return json.loads(text_clean)
            except Exception as e:
                logger.warning(f"Gemini call with {model} failed: {e}")
                continue

        return {}

    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file for deduplication and versioning."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def analyze_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """
        Multimodal analysis of an uploaded PDF, Image, or Text file.
        Extracts structured knowledge (timetable, profile, deadlines, facts).
        """
        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        file_hash = self.compute_file_hash(file_path)
        ext = Path(original_filename).suffix.lower()
        now_str = datetime.datetime.now().isoformat()

        extracted_text = ""
        is_pdf = ext == ".pdf"
        is_image = ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]

        if is_pdf:
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                pages_text = []
                for i, page in enumerate(reader.pages):
                    t = page.extract_text() or ""
                    pages_text.append(f"--- Page {i+1} ---\n{t}")
                extracted_text = "\n".join(pages_text)
            except Exception as e:
                logger.error(f"Error extracting text with pypdf: {e}")

        # Construct Extraction Prompt for Gemini
        extraction_prompt = f"""You are the JARVIS Personal Knowledge Ingestion Engine.
Analyze the following document content uploaded by the user ({self.default_user}).
Original filename: {original_filename}

Extract all structured information into this exact JSON format:
{{
  "document_type": "timetable" | "assignment" | "project" | "profile" | "syllabus" | "general",
  "title": "Document Title",
  "summary": "Clear 2-sentence summary of what this document contains.",
  "confidence": 0.98,
  "profile": {{
    "degree": "string or null",
    "year": "string or null",
    "semester": "string or null",
    "university": "string or null",
    "primary_project": "string or null"
  }},
  "timetable_entries": [
    {{
      "weekday": "Monday | Tuesday | Wednesday | Thursday | Friday | Saturday | Sunday",
      "start_time": "HH:MM (24-hour format e.g. 09:00 or 13:30)",
      "end_time": "HH:MM (24-hour format e.g. 11:00 or 15:30)",
      "subject": "Full subject name e.g. Network Switching and Routing",
      "code": "Course code e.g. NST201 or null",
      "room": "Room or lab e.g. E301 or Lab 2",
      "lecturer": "Lecturer name if present or null"
    }}
  ],
  "deadlines": [
    {{
      "title": "Task/Assignment name",
      "subject": "Subject name",
      "due_date": "YYYY-MM-DD or relative description",
      "instructions": "Brief instructions"
    }}
  ],
  "facts": [
    {{
      "category": "education" | "project" | "preference" | "schedule" | "notes",
      "key": "Fact subject or key",
      "value": "Detailed fact value",
      "confidence": 0.95
    }}
  ]
}}

DOCUMENT CONTENT:
{extracted_text[:12000] if extracted_text else "Inspect the attached image visual layout carefully."}
"""

        extracted_data = {}
        if self.api_key:
            if is_image:
                with open(file_path, "rb") as img_f:
                    img_bytes = img_f.read()
                mime = "image/png" if ext == ".png" else "image/jpeg"
                extracted_data = self._call_gemini_json(extraction_prompt, image_bytes=img_bytes, mime_type=mime)
            else:
                extracted_data = self._call_gemini_json(extraction_prompt)

        # Heuristic fallback if API unavailable or empty
        if not extracted_data:
            extracted_data = self._heuristic_extract(original_filename, extracted_text)

        # Check if timetable detected
        tt_entries = extracted_data.get("timetable_entries", [])
        doc_type = extracted_data.get("document_type", "general")
        if tt_entries or "timetable" in original_filename.lower() or "schedule" in original_filename.lower():
            doc_type = "timetable"
            extracted_data["document_type"] = "timetable"

        return {
            "doc_id": doc_id,
            "filename": original_filename,
            "file_path": str(file_path),
            "file_hash": file_hash,
            "doc_type": doc_type,
            "summary": extracted_data.get("summary", f"Ingested {original_filename}"),
            "extracted_data": extracted_data,
            "is_timetable": doc_type == "timetable" or len(tt_entries) > 0,
            "timetable_count": len(tt_entries),
            "facts_count": len(extracted_data.get("facts", []))
        }

    def _heuristic_extract(self, filename: str, text: str) -> Dict[str, Any]:
        """Deterministic regex-based fallback extractor for timetables and profile facts."""
        facts = []
        timetable = []
        lower = (filename + " " + text).lower()
        now_date = datetime.date.today().isoformat()

        # Timetable detection
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        lines = text.split("\n")
        current_day = "Monday"
        for line in lines:
            for d in weekdays:
                if d.lower() in line.lower():
                    current_day = d
            # Search for time pattern e.g. 09:00 - 11:00 or 9:00 AM
            time_match = re.search(r"(\d{1,2}:\d{2})\s*(?:-|to)?\s*(\d{1,2}:\d{2})?", line)
            if time_match:
                st = time_match.group(1)
                et = time_match.group(2) or ""
                # extract subject text
                subj = re.sub(r"\d{1,2}:\d{2}", "", line).strip("- :,")
                if len(subj) > 3:
                    timetable.append({
                        "weekday": current_day,
                        "start_time": st,
                        "end_time": et,
                        "subject": subj,
                        "code": "",
                        "room": "Main Hall",
                        "lecturer": ""
                    })

        doc_type = "timetable" if timetable or "timetable" in lower else "general"

        # Profile heuristic
        profile = {}
        if "bict" in lower:
            profile["degree"] = "BICT"
            facts.append({"category": "education", "key": "degree", "value": "BICT", "confidence": 1.0})
        if "2nd year" in lower or "second year" in lower:
            profile["year"] = "2nd Year"
            facts.append({"category": "education", "key": "year", "value": "2nd Year", "confidence": 1.0})
        if "agrimind" in lower:
            profile["primary_project"] = "AgriMind AI"
            facts.append({"category": "project", "key": "primary_project", "value": "AgriMind AI", "confidence": 1.0})

        return {
            "document_type": doc_type,
            "title": filename,
            "summary": f"Structured extraction for {filename}. Detected {len(timetable)} classes and {len(facts)} profile facts.",
            "confidence": 0.90,
            "profile": profile,
            "timetable_entries": timetable,
            "deadlines": [],
            "facts": facts
        }

    def save_extracted_knowledge(
        self,
        doc_id: str,
        filename: str,
        file_path: str,
        extracted_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Permanently commit extracted knowledge into MongoDB Atlas & SQLite fallback.
        Handles versioning (superseding old timetables with new ones).
        """
        uid = user_id or self.default_user
        now_str = datetime.datetime.now().isoformat()
        doc_type = extracted_data.get("document_type", "general")
        summary = extracted_data.get("summary", "")
        file_hash = self.compute_file_hash(file_path) if os.path.exists(file_path) else ""

        # 1. Handle Timetable Versioning (Mark older active timetables as superseded)
        is_timetable = doc_type == "timetable" or bool(extracted_data.get("timetable_entries"))
        if is_timetable:
            self._supersede_old_timetables(uid)

        # 2. Save Knowledge Document Record
        doc_record = {
            "id": doc_id,
            "userId": uid,
            "filename": filename,
            "filePath": str(file_path),
            "fileHash": file_hash,
            "mimeType": "application/pdf" if filename.endswith(".pdf") else "image/png",
            "docType": doc_type,
            "summary": summary,
            "extractedCount": len(extracted_data.get("timetable_entries", [])) + len(extracted_data.get("facts", [])),
            "isActive": True,
            "uploadedAt": now_str
        }

        # MongoDB
        try:
            col_docs = get_knowledge_docs_col()
            if col_docs is not None:
                col_docs.update_one({"id": doc_id}, {"$set": doc_record}, upsert=True)
        except Exception as e:
            logger.warning(f"MongoDB doc save failed: {e}")

        # SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO knowledge_documents
            (id, filename, file_path, file_hash, mime_type, doc_type, summary, extracted_count, is_active, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                doc_id, filename, str(file_path), file_hash,
                doc_record["mimeType"], doc_type, summary,
                doc_record["extractedCount"], now_str
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SQLite doc save error: {e}")

        # 3. Save Structured Timetable Entries
        tt_entries = extracted_data.get("timetable_entries", [])
        if tt_entries:
            self._save_timetable_entries(doc_id, tt_entries, uid)

        # 4. Save Structured Facts & Profile
        facts = extracted_data.get("facts", [])
        self._save_facts_and_profile(doc_id, facts, extracted_data.get("profile", {}), filename, uid)

        return {
            "success": True,
            "doc_id": doc_id,
            "filename": filename,
            "doc_type": doc_type,
            "is_timetable": is_timetable,
            "timetable_count": len(tt_entries),
            "facts_count": len(facts),
            "message": f"Successfully ingested '{filename}' into Personal Knowledge Vault."
        }

    def _supersede_old_timetables(self, user_id: str):
        """Mark older active timetables as superseded/inactive."""
        try:
            col_tt = get_timetables_col()
            if col_tt is not None:
                col_tt.update_many({"userId": user_id, "isActive": True}, {"$set": {"isActive": False, "supersededAt": datetime.datetime.now().isoformat()}})
            col_docs = get_knowledge_docs_col()
            if col_docs is not None:
                col_docs.update_many({"userId": user_id, "docType": "timetable", "isActive": True}, {"$set": {"isActive": False}})
        except Exception:
            pass

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE timetables SET is_active = 0 WHERE is_active = 1")
            cursor.execute("UPDATE knowledge_documents SET is_active = 0 WHERE doc_type = 'timetable' AND is_active = 1")
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _save_timetable_entries(self, doc_id: str, entries: List[Dict[str, Any]], user_id: str):
        """Persist timetable entries to MongoDB and SQLite."""
        now_str = datetime.datetime.now().isoformat()
        # MongoDB
        try:
            col_tt = get_timetables_col()
            if col_tt is not None:
                mongo_docs = []
                for idx, e in enumerate(entries):
                    mongo_docs.append({
                        "id": f"tt_{doc_id}_{idx}",
                        "documentId": doc_id,
                        "userId": user_id,
                        "weekday": e.get("weekday", "Monday").capitalize(),
                        "startTime": e.get("start_time", "09:00"),
                        "endTime": e.get("end_time", ""),
                        "subject": e.get("subject", "Class"),
                        "code": e.get("code", ""),
                        "room": e.get("room", "TBD"),
                        "lecturer": e.get("lecturer", ""),
                        "isActive": True,
                        "createdAt": now_str
                    })
                if mongo_docs:
                    col_tt.insert_many(mongo_docs)
        except Exception as e:
            logger.warning(f"MongoDB timetable insert error: {e}")

        # SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            for idx, e in enumerate(entries):
                cursor.execute("""
                INSERT OR REPLACE INTO timetables
                (id, document_id, semester, weekday, start_time, end_time, subject, code, room, lecturer, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (
                    f"tt_{doc_id}_{idx}",
                    doc_id,
                    e.get("semester", "Current"),
                    e.get("weekday", "Monday").capitalize(),
                    e.get("start_time", "09:00"),
                    e.get("end_time", ""),
                    e.get("subject", "Class"),
                    e.get("code", ""),
                    e.get("room", "TBD"),
                    e.get("lecturer", ""),
                    now_str
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SQLite timetable insert error: {e}")

    def _save_facts_and_profile(
        self,
        doc_id: str,
        facts: List[Dict[str, Any]],
        profile: Dict[str, Any],
        source_name: str,
        user_id: str
    ):
        """Save facts and merge profile updates into MongoDB and SQLite."""
        now_str = datetime.datetime.now().isoformat()

        # Update facts
        try:
            conn = get_db()
            cursor = conn.cursor()
            for idx, f in enumerate(facts):
                fid = f"fact_{doc_id}_{idx}"
                cursor.execute("""
                INSERT OR REPLACE INTO knowledge_facts
                (id, document_id, category, fact_type, key, value, confidence, source_type, source_name, page, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'document', ?, 1, 1, ?)
                """, (
                    fid, doc_id, f.get("category", "general"), "fact",
                    f.get("key", "info"), f.get("value", ""),
                    f.get("confidence", 1.0), source_name, now_str
                ))
                # Also mirror into memory_vault for backward compatibility
                cursor.execute("""
                INSERT OR REPLACE INTO memory_vault (id, category, key, value, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"mem_{fid}", f.get("category", "notes"),
                    f.get("key", "info"), f.get("value", ""),
                    json.dumps(["knowledge_vault", source_name]),
                    now_str, now_str
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SQLite fact insert error: {e}")

        # Update Personal Profile
        if profile:
            self.update_personal_profile(profile, user_id=user_id)

    def update_personal_profile(self, updates: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Update and merge fields into the structured Personal Profile."""
        uid = user_id or self.default_user
        current = self.get_personal_profile(user_id=uid)
        now_str = datetime.datetime.now().isoformat()

        for k, v in updates.items():
            if v is not None and str(v).strip():
                current[k] = v

        current["updated_at"] = now_str

        # MongoDB
        try:
            col = get_personal_profiles_col()
            if col is not None:
                col.update_one({"userId": uid}, {"$set": {"userId": uid, "profile": current, "updatedAt": now_str}}, upsert=True)
        except Exception:
            pass

        # SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO personal_profiles (user_id, profile_json, updated_at)
            VALUES (?, ?, ?)
            """, (uid, json.dumps(current), now_str))
            conn.commit()
            conn.close()
        except Exception:
            pass

        return current

    def get_personal_profile(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve structured personal profile for the user."""
        uid = user_id or self.default_user
        profile = {
            "name": uid,
            "degree": "BICT",
            "year": "2nd Year",
            "semester": "Semester 1",
            "university": "Faculty of Technology",
            "primary_project": "AgriMind AI",
            "interests": ["Artificial Intelligence", "Autonomous Agents", "Robotics", "Full-Stack Dev"],
            "preferences": {"language": "English", "theme": "Crimson Cyberpunk HUD", "verbosity": "concise"}
        }

        # Try SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT profile_json FROM personal_profiles WHERE user_id = ?", (uid,))
            row = cursor.fetchone()
            if row and row["profile_json"]:
                stored = json.loads(row["profile_json"])
                profile.update(stored)
            conn.close()
        except Exception:
            pass

        return profile

    def get_today_lectures(self, target_weekday: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Query active timetable for classes on today or a specific weekday.
        Returns sorted schedule with formatted spoken synthesis.
        """
        now = datetime.datetime.now()
        if not target_weekday or target_weekday.lower() in ["today", "now"]:
            weekday = now.strftime("%A")
            display_day = "today"
        elif target_weekday.lower() == "tomorrow":
            weekday = (now + datetime.timedelta(days=1)).strftime("%A")
            display_day = "tomorrow"
        else:
            weekday = target_weekday.capitalize()
            display_day = weekday

        classes = []
        active_doc_name = "Semester Timetable"

        # 1. Fetch from SQLite active timetable
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT t.*, d.filename FROM timetables t
            LEFT JOIN knowledge_documents d ON t.document_id = d.id
            WHERE t.is_active = 1 AND LOWER(t.weekday) = LOWER(?)
            ORDER BY t.start_time ASC
            """, (weekday,))
            rows = cursor.fetchall()
            for r in rows:
                if r["filename"]:
                    active_doc_name = r["filename"]
                classes.append({
                    "weekday": r["weekday"],
                    "start_time": r["start_time"],
                    "end_time": r["end_time"],
                    "subject": r["subject"],
                    "code": r["code"],
                    "room": r["room"],
                    "lecturer": r["lecturer"]
                })
            conn.close()
        except Exception as e:
            logger.error(f"Error querying timetable classes: {e}")

        # Construct Truthful Spoken Response
        if not classes:
            spoken = f"Boss, you have no lectures scheduled for {display_day} on your active timetable."
        else:
            parts = []
            for c in classes:
                st = c["start_time"]
                # Format 09:00 -> 9:00 AM or 13:00 -> 1:00 PM
                try:
                    t_obj = datetime.datetime.strptime(st, "%H:%M")
                    t_str = t_obj.strftime("%I:%M %p").lstrip("0")
                except Exception:
                    t_str = st
                room_str = f" in {c['room']}" if c.get("room") and c["room"] != "TBD" else ""
                parts.append(f"{t_str} — {c['subject']}{room_str}")

            class_count = len(classes)
            count_word = "one lecture" if class_count == 1 else f"{class_count} lectures"
            spoken = f"Boss, {display_day} you have {count_word}: " + ", and ".join(parts) + "."

        return {
            "success": True,
            "weekday": weekday,
            "display_day": display_day,
            "count": len(classes),
            "classes": classes,
            "active_document": active_doc_name,
            "spoken_summary": spoken
        }

    def get_next_class(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Determine the next immediate class today based on current time."""
        now = datetime.datetime.now()
        current_time_str = now.strftime("%H:%M")
        today_res = self.get_today_lectures(target_weekday="today", user_id=user_id)
        classes = today_res.get("classes", [])

        upcoming = [c for c in classes if c.get("start_time", "00:00") >= current_time_str]
        if not upcoming:
            if classes:
                return {
                    "success": True,
                    "has_next": False,
                    "spoken_summary": "Boss, all your scheduled lectures for today are finished."
                }
            return {
                "success": True,
                "has_next": False,
                "spoken_summary": "Boss, you don't have any lectures scheduled for today."
            }

        next_c = upcoming[0]
        st = next_c["start_time"]
        try:
            t_obj = datetime.datetime.strptime(st, "%H:%M")
            t_str = t_obj.strftime("%I:%M %p").lstrip("0")
        except Exception:
            t_str = st
        room_str = f" in room {next_c['room']}" if next_c.get("room") else ""

        spoken = f"Boss, your next class is {next_c['subject']} at {t_str}{room_str}."
        return {
            "success": True,
            "has_next": True,
            "next_class": next_c,
            "spoken_summary": spoken
        }

    def get_active_timetable(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve full active timetable grouped by weekday."""
        grouped: Dict[str, List[Dict[str, Any]]] = {
            "Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []
        }
        active_doc = None

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT t.*, d.filename FROM timetables t
            LEFT JOIN knowledge_documents d ON t.document_id = d.id
            WHERE t.is_active = 1
            ORDER BY t.start_time ASC
            """)
            rows = cursor.fetchall()
            for r in rows:
                day = r["weekday"].capitalize()
                if day in grouped:
                    grouped[day].append({
                        "id": r["id"],
                        "start_time": r["start_time"],
                        "end_time": r["end_time"],
                        "subject": r["subject"],
                        "code": r["code"],
                        "room": r["room"],
                        "lecturer": r["lecturer"]
                    })
                if r["filename"]:
                    active_doc = r["filename"]
            conn.close()
        except Exception as e:
            logger.error(f"Error fetching full active timetable: {e}")

        total_classes = sum(len(v) for v in grouped.values())
        return {
            "success": True,
            "active_document": active_doc or "No timetable active",
            "total_classes": total_classes,
            "timetable": grouped
        }

    def get_all_documents(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all ingested knowledge documents with active status and summaries."""
        docs = []
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_documents ORDER BY uploaded_at DESC")
            rows = cursor.fetchall()
            for r in rows:
                docs.append({
                    "id": r["id"],
                    "filename": r["filename"],
                    "doc_type": r["doc_type"],
                    "summary": r["summary"],
                    "extracted_count": r["extracted_count"],
                    "is_active": bool(r["is_active"]),
                    "uploaded_at": r["uploaded_at"]
                })
            conn.close()
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
        return docs

    def search_vault(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search across personal profile, documents, structured facts, and memories.
        """
        clean_q = query.lower().strip()
        results = []

        # 1. Search Profile
        profile = self.get_personal_profile()
        for k, v in profile.items():
            if isinstance(v, str) and (clean_q in k.lower() or clean_q in v.lower()):
                results.append({
                    "type": "profile",
                    "key": k,
                    "value": v,
                    "source": "Personal Profile",
                    "confidence": 1.0
                })

        # 2. Search Facts
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM knowledge_facts
            WHERE is_active = 1 AND (LOWER(key) LIKE ? OR LOWER(value) LIKE ? OR LOWER(category) LIKE ?)
            LIMIT ?
            """, (f"%{clean_q}%", f"%{clean_q}%", f"%{clean_q}%", limit))
            rows = cursor.fetchall()
            for r in rows:
                results.append({
                    "type": "fact",
                    "category": r["category"],
                    "key": r["key"],
                    "value": r["value"],
                    "source": r["source_name"] or "Knowledge Document",
                    "confidence": r["confidence"]
                })
            conn.close()
        except Exception:
            pass

        return {
            "query": query,
            "count": len(results),
            "results": results
        }

    def forget_knowledge(self, target: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Remove or deactivate specific personal knowledge records or documents."""
        clean = target.strip().lower()
        now_str = datetime.datetime.now().isoformat()

        # Check if full reset
        if clean in ["everything", "all", "all personal knowledge", "all memory"]:
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM knowledge_facts")
                cursor.execute("DELETE FROM timetables")
                cursor.execute("UPDATE knowledge_documents SET is_active = 0")
                cursor.execute("DELETE FROM memory_vault")
                conn.commit()
                conn.close()
            except Exception:
                pass
            return {"success": True, "message": "All personal knowledge vault records have been wiped, Boss."}

        # Check if deleting timetable
        if "timetable" in clean or "schedule" in clean:
            self._supersede_old_timetables(self.default_user)
            return {"success": True, "message": "Your active timetable has been deactivated, Boss."}

        # Remove matching facts/memories
        deleted_count = 0
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
            DELETE FROM knowledge_facts
            WHERE LOWER(key) LIKE ? OR LOWER(value) LIKE ?
            """, (f"%{clean}%", f"%{clean}%"))
            deleted_count += cursor.rowcount

            cursor.execute("""
            DELETE FROM memory_vault
            WHERE LOWER(key) LIKE ? OR LOWER(value) LIKE ?
            """, (f"%{clean}%", f"%{clean}%"))
            deleted_count += cursor.rowcount

            conn.commit()
            conn.close()
        except Exception:
            pass

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"I have removed knowledge relating to '{target}' from the vault, Boss."
        }

# Global Singleton instance
knowledge_service = KnowledgeService()
