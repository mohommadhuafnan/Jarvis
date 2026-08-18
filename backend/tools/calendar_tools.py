import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from backend.tools.registry import registry, RiskLevel
from backend.services.google_oauth_service import google_oauth_service
from backend.services.audit_service import audit_service

logger = logging.getLogger("JARVIS.Tools.Calendar")

@registry.register(
    name="calendar.listEvents",
    description="List Google Calendar events for the upcoming days or specific date.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {
            "days_ahead": {"type": "integer", "description": "Number of days ahead to fetch (default 7)"},
            "date": {"type": "string", "description": "Specific date (optional)"}
        },
        "required": []
    },
    agent_category="google"
)
def list_events(days_ahead: int = 7, date: Optional[str] = None):
    res = google_oauth_service.list_calendar_events(days_ahead=days_ahead)
    return res

@registry.register(
    name="calendar.getEvents",
    description="Retrieve calendar events.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {
            "days_ahead": {"type": "integer", "description": "Days ahead (default 7)"}
        },
        "required": []
    },
    agent_category="google"
)
def get_events(days_ahead: int = 7):
    return list_events(days_ahead=days_ahead)

@registry.register(
    name="calendar.createEvent",
    description="Schedule a new meeting or event in Google Calendar (CONFIRM: requires confirmation).",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Event title or meeting subject"},
            "start_time": {"type": "string", "description": "Start datetime ISO string (e.g. 2026-08-19T10:00:00)"},
            "end_time": {"type": "string", "description": "End datetime ISO string (e.g. 2026-08-19T11:00:00)"},
            "description": {"type": "string", "description": "Event description or agenda"}
        },
        "required": ["title", "start_time", "end_time"]
    },
    agent_category="google"
)
def create_event(title: str, start_time: str, end_time: str, description: str = ""):
    res = google_oauth_service.create_calendar_event(
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description
    )
    if res.get("success"):
        audit_service.log_audit(
            task_id="calendar_create",
            agent="CalendarAgent",
            tool="calendar.createEvent",
            risk_level="CONFIRM",
            permission_decision="APPROVED",
            status="success",
            details={"title": title, "start_time": start_time}
        )
    return res
