import os
import uuid
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from backend.tools.registry import registry, RiskLevel
from backend.services.google_oauth_service import google_oauth_service
from backend.services.audit_service import audit_service

logger = logging.getLogger("JARVIS.Tools.Gmail")

def sanitize_email_content(text: str) -> str:
    """Wrap untrusted email content in protective delimiters to neutralize prompt injections."""
    clean = re.sub(r'[\r\n]+', ' ', text).strip()[:1500]
    return f"<untrusted_email_data>\n{clean}\n</untrusted_email_data>"

@registry.register(
    name="gmail.getUnreadEmails",
    description="Retrieve unread emails from Gmail with sender, subject, date, and summary.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Maximum number of messages to return (default 5)"}
        },
        "required": []
    },
    agent_category="google"
)
def get_unread_emails(max_results: int = 5):
    res = google_oauth_service.list_unread_emails(max_results=max_results)
    return res

@registry.register(
    name="gmail.searchEmails",
    description="Search Gmail inbox using standard queries (e.g. 'is:unread', 'from:university', 'subject:meeting').",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Gmail search query (e.g. 'from:university.edu' or 'assignment')"}
        },
        "required": ["query"]
    },
    agent_category="google"
)
def search_emails(query: str):
    res = google_oauth_service.search_emails(query=query)
    return res

@registry.register(
    name="gmail.getEmail",
    description="Retrieve full body content and attachments metadata for a specific email ID or 'latest'.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {
            "message_id": {"type": "string", "description": "ID of the email message to read"}
        },
        "required": ["message_id"]
    },
    agent_category="google"
)
def get_email(message_id: str):
    res = google_oauth_service.get_email(message_id=message_id)
    if res.get("success") and "body" in res:
        res["protected_body"] = sanitize_email_content(res["body"])
    return res

@registry.register(
    name="gmail.createDraft",
    description="Create a draft email in Gmail without sending it.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Email subject line"},
            "body": {"type": "string", "description": "Email body content"}
        },
        "required": ["recipient", "subject", "body"]
    },
    agent_category="google"
)
def create_draft(recipient: str, subject: str, body: str):
    res = google_oauth_service.create_draft(recipient=recipient, subject=subject, body=body)
    return res

@registry.register(
    name="gmail.reply",
    description="Draft a reply in an existing email thread (CONFIRM: requires confirmation to send).",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {
            "thread_id": {"type": "string", "description": "ID of thread to reply to"},
            "recipient": {"type": "string", "description": "Recipient address"},
            "body": {"type": "string", "description": "Reply body text"}
        },
        "required": ["recipient", "body"]
    },
    agent_category="google"
)
def reply_email(recipient: str, body: str, thread_id: Optional[str] = None):
    subject = "Re: Follow up"
    res = google_oauth_service.create_draft(recipient=recipient, subject=subject, body=body)
    return res

@registry.register(
    name="gmail.send",
    description="Send an email through Gmail (CONFIRM: requires explicit user confirmation).",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Subject of the email"},
            "body": {"type": "string", "description": "Body content of the email"}
        },
        "required": ["recipient", "subject", "body"]
    },
    agent_category="google"
)
def send_email(recipient: str, subject: str, body: str):
    res = google_oauth_service.send_email(recipient=recipient, subject=subject, body=body)
    if res.get("success"):
        audit_service.log_audit(
            task_id="gmail_send",
            agent="GmailAgent",
            tool="gmail.send",
            risk_level="CONFIRM",
            permission_decision="APPROVED",
            status="success",
            details={"recipient": recipient, "subject": subject}
        )
    return res

# Aliases for backward compatibility
@registry.register(
    name="email.read",
    description="Read unread emails from Gmail.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={"type": "object", "properties": {"unread_only": {"type": "boolean"}}, "required": []}
)
def email_read_alias(unread_only: bool = True):
    return get_unread_emails(max_results=5)

@registry.register(
    name="email.draft",
    description="Draft an email without sending.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {
            "recipient": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"}
        },
        "required": ["recipient", "subject", "body"]
    }
)
def email_draft_alias(recipient: str, subject: str, body: str):
    return create_draft(recipient=recipient, subject=subject, body=body)

@registry.register(
    name="email.send",
    description="Send an email with confirmation.",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {
            "recipient": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"}
        },
        "required": ["recipient", "subject", "body"]
    }
)
def email_send_alias(recipient: str, subject: str, body: str):
    return send_email(recipient=recipient, subject=subject, body=body)
