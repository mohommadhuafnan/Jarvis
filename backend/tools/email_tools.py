import uuid
from datetime import datetime
from typing import Optional
from backend.database.db import get_db
from backend.tools.registry import registry, RiskLevel

# Sample email inbox state
_SAMPLE_EMAILS = [
    {
        "id": "em_1",
        "sender": "Dr. Sarah Vance <s.vance@agrimind.ai>",
        "subject": "AgriMind Phase 2 Deployment Status & Test Run",
        "snippet": "The model checkpoints have finished training with 98.4% validation accuracy. Ready for live sensor feed testing.",
        "date": "Today, 09:15",
        "unread": True,
        "priority": "HIGH"
    },
    {
        "id": "em_2",
        "sender": "Security Operations <sec-ops@jarvis.corp>",
        "subject": "Firewall & Security Threat Report: All Nodes Clear",
        "snippet": "All perimeter subnets inspected. Zero unauthorized intrusions detected in the last 24 hours.",
        "date": "Today, 08:30",
        "unread": True,
        "priority": "MEDIUM"
    },
    {
        "id": "em_3",
        "sender": "Cloud Infrastructure <alerts@cloudcluster.io>",
        "subject": "Cluster Resource Optimization Report",
        "snippet": "GPU memory allocation reduced by 14% while maintaining sub-50ms inference latency.",
        "date": "Yesterday, 19:40",
        "unread": False,
        "priority": "LOW"
    }
]

@registry.register(
    name="email.read",
    description="Retrieve emails from inbox with unread counts, senders, and summaries.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {
            "unread_only": {"type": "boolean", "description": "Filter by unread messages"}
        },
        "required": []
    }
)
def read_emails(unread_only: bool = False):
    emails = [e for e in _SAMPLE_EMAILS if not unread_only or e["unread"]]
    return {
        "total": len(_SAMPLE_EMAILS),
        "unread_count": sum(1 for e in _SAMPLE_EMAILS if e["unread"]),
        "emails": emails,
        "summary": f"Found {len(emails)} emails. {sum(1 for e in emails if e['unread'])} are unread."
    }

@registry.register(
    name="email.draft",
    description="Draft an email response or new message for user review before sending.",
    risk_level=RiskLevel.MEDIUM,
    parameters={
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "Email address of the recipient"},
            "subject": {"type": "string", "description": "Subject of the email"},
            "body": {"type": "string", "description": "Body content of the email draft"}
        },
        "required": ["recipient", "subject", "body"]
    }
)
def draft_email(recipient: str, subject: str, body: str):
    draft_id = f"draft_{uuid.uuid4().hex[:8]}"
    return {
        "success": True,
        "draft_id": draft_id,
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "status": "DRAFT_CREATED",
        "message": f"Draft prepared for '{recipient}' with subject '{subject}'. Confirmation required before sending."
    }

@registry.register(
    name="email.send",
    description="Send an email to a recipient (HIGH RISK: requires user confirmation).",
    risk_level=RiskLevel.HIGH,
    parameters={
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Subject of the email"},
            "body": {"type": "string", "description": "Body content of the email"}
        },
        "required": ["recipient", "subject", "body"]
    }
)
def send_email(recipient: str, subject: str, body: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activity_logs (id, module, action, details, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (f"act_{uuid.uuid4().hex[:8]}", "Email", f"Sent email to {recipient}", f"Subject: {subject}", "success", datetime.now().strftime("%H:%M"))
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "recipient": recipient,
        "subject": subject,
        "status": "SENT",
        "message": f"Email successfully dispatched to '{recipient}'."
    }
