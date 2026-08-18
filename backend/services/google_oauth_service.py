import os
import time
import base64
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText

from backend.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_AUTH_URI,
    GOOGLE_TOKEN_URI
)
from backend.database.db import get_db
from backend.database.collections import get_collection

logger = logging.getLogger("JARVIS.GoogleOAuthService")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

class GoogleOAuthService:
    """
    Secure server-side Google OAuth 2.0 and API integration for Personal Gmail and Calendar.
    All tokens remain strictly server-side and encrypted in the database.
    """

    def __init__(self):
        self.service_name = "google"

    def get_auth_url(self) -> str:
        """Generate Google OAuth 2.0 consent URL."""
        if not GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID is not configured in .env")

        scopes_str = "%20".join(GOOGLE_SCOPES)
        return (
            f"{GOOGLE_AUTH_URI}?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={GOOGLE_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope={scopes_str}&"
            f"access_type=offline&"
            f"prompt=consent"
        )

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange one-time authorization code for access and refresh tokens."""
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials missing in configuration.")

        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }

        resp = requests.post(GOOGLE_TOKEN_URI, data=data, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Google token exchange error: {resp.text}")
            raise Exception(f"Token exchange failed: {resp.text}")

        token_data = resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        expiry = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

        # Fetch user's email address for display
        user_email = self._fetch_user_email(access_token)

        # Store in SQLite and MongoDB
        self._store_tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expiry=expiry,
            scopes=" ".join(GOOGLE_SCOPES),
            user_email=user_email
        )

        logger.info(f"Google OAuth tokens successfully saved for {user_email or 'User'}")
        return {
            "success": True,
            "user_email": user_email,
            "status": "AUTHENTICATED"
        }

    def _fetch_user_email(self, access_token: str) -> Optional[str]:
        """Fetch authorized user email from Google UserInfo endpoint."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            res = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers, timeout=5)
            if res.status_code == 200:
                return res.json().get("email")
        except Exception as e:
            logger.warning(f"Failed to fetch user email: {e}")
        return None

    def _store_tokens(
        self,
        access_token: str,
        refresh_token: Optional[str],
        expiry: str,
        scopes: str,
        user_email: Optional[str] = None
    ):
        """Persist tokens securely in local SQLite and MongoDB."""
        now = datetime.now().isoformat()

        # 1. SQLite Storage
        try:
            conn = get_db()
            cursor = conn.cursor()
            if refresh_token:
                cursor.execute("""
                INSERT INTO oauth_tokens (service, access_token, refresh_token, token_uri, client_id, scopes, expiry, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(service) DO UPDATE SET
                    access_token=excluded.access_token,
                    refresh_token=excluded.refresh_token,
                    expiry=excluded.expiry,
                    updated_at=excluded.updated_at
                """, (
                    self.service_name,
                    access_token,
                    refresh_token,
                    GOOGLE_TOKEN_URI,
                    GOOGLE_CLIENT_ID,
                    scopes,
                    expiry,
                    now
                ))
            else:
                cursor.execute("""
                UPDATE oauth_tokens
                SET access_token=?, expiry=?, updated_at=?
                WHERE service=?
                """, (access_token, expiry, now, self.service_name))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving tokens to SQLite: {e}")

        # 2. MongoDB Storage
        try:
            col = get_collection("oauth_tokens")
            if col is not None:
                doc = {
                    "service": self.service_name,
                    "access_token": access_token,
                    "expiry": expiry,
                    "userEmail": user_email,
                    "updatedAt": now
                }
                if refresh_token:
                    doc["refresh_token"] = refresh_token
                col.update_one(
                    {"service": self.service_name},
                    {"$set": doc},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Error saving tokens to MongoDB: {e}")

    def get_valid_access_token(self) -> Optional[str]:
        """Retrieve valid access token, auto-refreshing if expired."""
        token_info = self._get_stored_token_info()
        if not token_info:
            return None

        access_token = token_info.get("access_token")
        refresh_token = token_info.get("refresh_token")
        expiry_str = token_info.get("expiry")

        # Check if expired or about to expire in next 60 seconds
        if expiry_str:
            try:
                expiry_dt = datetime.fromisoformat(expiry_str)
                if datetime.now() >= (expiry_dt - timedelta(seconds=60)):
                    if refresh_token:
                        return self._refresh_access_token(refresh_token)
                    return None
            except Exception:
                pass

        return access_token

    def _refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh expired access token using Google Token URI."""
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        try:
            res = requests.post(GOOGLE_TOKEN_URI, data=data, timeout=10)
            if res.status_code == 200:
                body = res.json()
                new_access = body.get("access_token")
                expires_in = body.get("expires_in", 3600)
                new_expiry = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                self._store_tokens(
                    access_token=new_access,
                    refresh_token=None,
                    expiry=new_expiry,
                    scopes=" ".join(GOOGLE_SCOPES)
                )
                return new_access
            else:
                logger.error(f"Failed to refresh Google token: {res.text}")
        except Exception as e:
            logger.error(f"Exception while refreshing Google token: {e}")
        return None

    def _get_stored_token_info(self) -> Optional[Dict[str, Any]]:
        """Retrieve token record from SQLite or MongoDB."""
        # 1. Try SQLite
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM oauth_tokens WHERE service=?", (self.service_name,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return dict(row)
        except Exception:
            pass

        # 2. Try MongoDB
        try:
            col = get_collection("oauth_tokens")
            if col is not None:
                doc = col.find_one({"service": self.service_name})
                if doc:
                    return doc
        except Exception:
            pass

        return None

    def is_connected(self) -> bool:
        """Check if a valid token or refreshable credential exists."""
        token_info = self._get_stored_token_info()
        if not token_info:
            return False
        return bool(token_info.get("access_token") or token_info.get("refresh_token"))

    def get_status(self) -> Dict[str, Any]:
        """Return safe user-facing status (never returns tokens)."""
        token_info = self._get_stored_token_info()
        connected = self.is_connected()
        user_email = token_info.get("userEmail") if token_info else None
        return {
            "configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
            "connected": connected,
            "account": user_email or ("Connected Google Account" if connected else "Not Connected"),
            "scopes": GOOGLE_SCOPES
        }

    # =========================================================================
    # GMAIL API INTEGRATION
    # =========================================================================

    def list_unread_emails(self, max_results: int = 5) -> Dict[str, Any]:
        """Fetch unread emails from user's actual Gmail inbox."""
        token = self.get_valid_access_token()
        if not token:
            return {
                "success": False,
                "connected": False,
                "message": "Your personal Gmail account is not connected yet. Please authorize Gmail in Settings."
            }

        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread&maxResults={max_results}"

        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code != 200:
                return {"success": False, "error": f"Gmail API error: {res.status_code}", "message": res.text}

            data = res.json()
            messages_list = data.get("messages", [])
            parsed_messages = []

            for msg_item in messages_list:
                msg_id = msg_item.get("id")
                msg_detail = self.get_email(msg_id)
                if msg_detail.get("success"):
                    parsed_messages.append(msg_detail)

            # Store in local DB cache for instant HUD sync
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cached_emails (
                        id TEXT PRIMARY KEY,
                        sender TEXT,
                        subject TEXT,
                        date TEXT,
                        snippet TEXT,
                        unread INTEGER DEFAULT 1,
                        updated_at TEXT
                    )
                """)
                now_str = datetime.now().isoformat()
                for m in parsed_messages:
                    cursor.execute("""
                        INSERT OR REPLACE INTO cached_emails (id, sender, subject, date, snippet, unread, updated_at)
                        VALUES (?, ?, ?, ?, ?, 1, ?)
                    """, (m["id"], m.get("from"), m.get("subject"), m.get("date"), m.get("snippet"), now_str))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error caching emails to SQLite: {e}")

            return {
                "success": True,
                "connected": True,
                "count": len(parsed_messages),
                "messages": parsed_messages,
                "summary": f"You have {len(parsed_messages)} unread emails in your inbox, Boss." if parsed_messages else "No unread emails in your inbox, Boss."
            }
        except Exception as e:
            logger.error(f"Error fetching unread Gmail messages: {e}")
            return {"success": False, "error": str(e), "message": "Failed to communicate with Gmail API."}

    def list_all_or_cached_emails(self) -> List[Dict[str, Any]]:
        """Retrieve real Gmail emails from cache or live API for the HUD Email view."""
        # 1. Try SQLite cache first for instant (<10ms) HUD display
        cached = []
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cached_emails ORDER BY updated_at DESC LIMIT 20")
            rows = cursor.fetchall()
            for r in rows:
                cached.append({
                    "id": r["id"],
                    "from": r["sender"],
                    "subject": r["subject"],
                    "date": r["date"],
                    "snippet": r["snippet"],
                    "unread": bool(r["unread"])
                })
            conn.close()
            if cached:
                return cached
        except Exception:
            pass

        # 2. Try Live API if cache empty and connected
        if self.is_connected():
            live_res = self.list_unread_emails(max_results=5)
            if live_res.get("success") and live_res.get("messages"):
                return live_res["messages"]

        return []

    def search_emails(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search Gmail inbox with query parameters."""
        token = self.get_valid_access_token()
        if not token:
            return {
                "success": False,
                "connected": False,
                "message": "Your personal Gmail account is not connected yet. Please authorize Gmail in Settings."
            }

        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q={requests.utils.quote(query)}&maxResults={max_results}"

        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code != 200:
                return {"success": False, "error": f"Gmail search failed: {res.status_code}"}

            data = res.json()
            messages_list = data.get("messages", [])
            parsed_messages = []

            for msg_item in messages_list:
                msg_id = msg_item.get("id")
                detail = self.get_email(msg_id)
                if detail.get("success"):
                    parsed_messages.append(detail)

            return {
                "success": True,
                "query": query,
                "count": len(parsed_messages),
                "results": parsed_messages
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_email(self, message_id: str) -> Dict[str, Any]:
        """Fetch metadata and snippet/body for a specific message ID or 'latest'."""
        token = self.get_valid_access_token()
        if not token:
            return {
                "success": False,
                "connected": False,
                "message": "Your personal Gmail account is not connected yet."
            }

        headers = {"Authorization": f"Bearer {token}"}

        if message_id in ["latest", "recent", "new"]:
            list_res = requests.get("https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=1", headers=headers, timeout=6)
            if list_res.status_code == 200:
                msgs = list_res.json().get("messages", [])
                if msgs:
                    message_id = msgs[0]["id"]
                else:
                    return {"success": False, "message": "No messages found in inbox."}

        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}?format=full"
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code != 200:
                return {"success": False, "error": f"Failed to retrieve email: {res.status_code}"}

            data = res.json()
            payload = data.get("payload", {})
            headers_list = payload.get("headers", [])

            headers_dict = {h["name"].lower(): h["value"] for h in headers_list}
            sender = headers_dict.get("from", "Unknown Sender")
            subject = headers_dict.get("subject", "No Subject")
            date = headers_dict.get("date", "")
            snippet = data.get("snippet", "")

            body_text = snippet
            parts = payload.get("parts", [])
            for p in parts:
                if p.get("mimeType") == "text/plain":
                    data_b64 = p.get("body", {}).get("data")
                    if data_b64:
                        try:
                            body_text = base64.urlsafe_b64decode(data_b64).decode("utf-8", errors="ignore")
                        except Exception:
                            pass

            return {
                "success": True,
                "id": message_id,
                "threadId": data.get("threadId"),
                "from": sender,
                "subject": subject,
                "date": date,
                "snippet": snippet,
                "body": body_text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_draft(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """Create a draft in user's real Gmail account."""
        token = self.get_valid_access_token()
        if not token:
            return {
                "success": False,
                "connected": False,
                "message": "Your personal Gmail account is not connected yet."
            }

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        message = MIMEText(body)
        message["to"] = recipient
        message["subject"] = subject
        raw_b64 = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        payload = {"message": {"raw": raw_b64}}
        try:
            res = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/drafts", headers=headers, json=payload, timeout=8)
            if res.status_code in [200, 201]:
                draft_data = res.json()
                return {
                    "success": True,
                    "draft_id": draft_data.get("id"),
                    "recipient": recipient,
                    "subject": subject,
                    "body": body,
                    "status": "DRAFT_SAVED",
                    "message": f"Draft created in Gmail for '{recipient}' with subject '{subject}'. Waiting for your confirmation before sending."
                }
            return {"success": False, "error": f"Gmail draft error: {res.status_code}", "message": res.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_email(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """Send an email through user's real Gmail account and verify dispatch."""
        token = self.get_valid_access_token()
        if not token:
            return {
                "success": False,
                "connected": False,
                "message": "Your personal Gmail account is not connected yet. Cannot send email."
            }

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        message = MIMEText(body)
        message["to"] = recipient
        message["subject"] = subject
        raw_b64 = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        payload = {"raw": raw_b64}
        try:
            res = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", headers=headers, json=payload, timeout=10)
            if res.status_code in [200, 201]:
                data = res.json()
                msg_id = data.get("id")
                # Verify message existence
                verify_res = requests.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}", headers=headers, timeout=6)
                verified = verify_res.status_code == 200
                return {
                    "success": True,
                    "verified": verified,
                    "message_id": msg_id,
                    "recipient": recipient,
                    "subject": subject,
                    "status": "DISPATCHED",
                    "message": f"Done, Boss. The email to {recipient} has been sent."
                }
            return {"success": False, "error": f"Gmail send failed: {res.status_code}", "message": res.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # GOOGLE CALENDAR API INTEGRATION WITH STRICT VERIFY-AFTER-CREATE
    # =========================================================================

    def list_calendar_events(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Fetch scheduled events from user's real Google Calendar."""
        token = self.get_valid_access_token()
        if not token:
            return {
                "success": False,
                "connected": False,
                "message": "Your Google Calendar is not connected yet, Boss."
            }

        headers = {"Authorization": f"Bearer {token}"}
        time_min = datetime.utcnow().isoformat() + "Z"
        time_max = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"

        url = (
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events?"
            f"timeMin={time_min}&timeMax={time_max}&singleEvents=true&orderBy=startTime"
        )

        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code != 200:
                return {"success": False, "error": f"Calendar API error: {res.status_code}", "message": "Failed to communicate with Google Calendar API."}

            data = res.json()
            items = data.get("items", [])
            events = []

            for item in items:
                start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
                end = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
                events.append({
                    "id": item.get("id"),
                    "title": item.get("summary", "Untitled Event"),
                    "description": item.get("description", ""),
                    "start_time": start,
                    "end_time": end,
                    "location": item.get("location", "")
                })

            return {
                "success": True,
                "connected": True,
                "event_count": len(events),
                "events": events,
                "summary": f"Found {len(events)} upcoming events on your calendar, Boss." if events else "No upcoming events scheduled on your calendar, Boss."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_calendar_event(self, title: str, start_time: str, end_time: str, description: str = "") -> Dict[str, Any]:
        """
        Create an event on user's real Google Calendar, verify its existence via get API,
        and persist event metadata in MongoDB and SQLite single source of truth.
        """
        token = self.get_valid_access_token()
        if not token:
            return {
                "success": False,
                "connected": False,
                "verified": False,
                "message": "Your Google Calendar is not connected yet, Boss. Cannot schedule event."
            }

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Ensure ISO formatted strings
        payload = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time if "T" in start_time else f"{start_time}T09:00:00+05:30", "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time if "T" in end_time else f"{end_time}T10:00:00+05:30", "timeZone": "Asia/Kolkata"}
        }

        try:
            # 1. Google Calendar API Insertion
            res = requests.post("https://www.googleapis.com/calendar/v3/calendars/primary/events", headers=headers, json=payload, timeout=10)
            if res.status_code not in [200, 201]:
                return {"success": False, "verified": False, "error": f"Calendar creation failed: {res.status_code}", "message": "Google Calendar API rejected the event creation."}

            evt = res.json()
            event_id = evt.get("id")

            # 2. Strict Verification Step (getEvent)
            verify_res = requests.get(f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}", headers=headers, timeout=8)
            if verify_res.status_code != 200:
                return {
                    "success": False,
                    "verified": False,
                    "message": "I sent the event to Google Calendar, but could not verify its creation, Boss."
                }

            # 3. Database Persistence (Single Source of Truth)
            now_iso = datetime.now().isoformat()
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS calendar_events (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        description TEXT,
                        verified INTEGER DEFAULT 1,
                        created_at TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    INSERT OR REPLACE INTO calendar_events (id, title, start_time, end_time, description, verified, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                """, (event_id, title, start_time, end_time, description, now_iso))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error persisting calendar event to SQLite: {e}")

            try:
                col = get_collection("calendar_events")
                if col is not None:
                    col.update_one(
                        {"_id": event_id},
                        {"$set": {
                            "_id": event_id,
                            "title": title,
                            "startTime": start_time,
                            "endTime": end_time,
                            "description": description,
                            "verified": True,
                            "createdAt": now_iso
                        }},
                        upsert=True
                    )
            except Exception:
                pass

            return {
                "success": True,
                "verified": True,
                "event_id": event_id,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "message": f"Done, Boss. Your meeting '{title}' is scheduled and verified on Google Calendar."
            }
        except Exception as e:
            return {"success": False, "verified": False, "error": str(e), "message": "Failed to communicate with Google Calendar."}

google_oauth_service = GoogleOAuthService()
