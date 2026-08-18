import os
import subprocess
import urllib.parse
import webbrowser
import logging
from typing import Dict, Any, Optional
from backend.tools.registry import registry, RiskLevel
from backend.services.memory_service import memory_service
from backend.services.audit_service import audit_service

logger = logging.getLogger("JARVIS.Tools.WhatsApp")

@registry.register(
    name="whatsapp.open",
    description="Launch WhatsApp Desktop application or WhatsApp Web in default browser.",
    risk_level=RiskLevel.LOW,
    parameters={"type": "object", "properties": {}, "required": []}
)
def open_whatsapp() -> Dict[str, Any]:
    """Launch WhatsApp Desktop via Windows Protocol handler or WhatsApp Web fallback."""
    try:
        # Try native Windows URI protocol for WhatsApp Desktop
        res = subprocess.run("start whatsapp:", shell=True, capture_output=True)
        if res.returncode == 0:
            return {"success": True, "message": "WhatsApp Desktop opened successfully."}
    except Exception as e:
        logger.warning(f"Native WhatsApp launch failed: {e}")

    try:
        # Fallback to WhatsApp Web in browser
        webbrowser.open("https://web.whatsapp.com")
        return {"success": True, "message": "WhatsApp Web opened in browser."}
    except Exception as e:
        return {"success": False, "error": f"Failed to open WhatsApp: {str(e)}"}

@registry.register(
    name="whatsapp.send_message",
    description="Compose and dispatch a WhatsApp message to a contact or phone number. Requires user confirmation.",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {
            "recipient": {
                "type": "string",
                "description": "Name of contact or phone number with country code (e.g. 'John' or '+1234567890')"
            },
            "message": {
                "type": "string",
                "description": "The exact message text to send"
            }
        },
        "required": ["recipient", "message"]
    }
)
def send_whatsapp_message(recipient: str, message: str) -> Dict[str, Any]:
    """
    Send WhatsApp message to recipient.
    Resolves contact phone number from memory vault if available.
    Dispatches via WhatsApp protocol URL or web client.
    """
    clean_recipient = recipient.strip()
    clean_msg = message.strip()
    encoded_text = urllib.parse.quote(clean_msg)

    # 1. Check if recipient is a raw phone number (starts with + or contains mostly digits)
    phone_digits = "".join(c for c in clean_recipient if c.isdigit())
    target_phone = clean_recipient if len(phone_digits) >= 7 else None

    # 2. If not a phone number, search memory vault for saved contact info
    if not target_phone:
        memories = memory_service.search_memory(query=clean_recipient)
        for mem in memories:
            val = mem.get("value", "")
            val_digits = "".join(c for c in val if c.isdigit())
            if len(val_digits) >= 7:
                target_phone = val.strip()
                break

    try:
        if target_phone:
            # Clean phone format
            safe_phone = "".join(c for c in target_phone if c.isdigit() or c == "+")
            whatsapp_url = f"https://api.whatsapp.com/send?phone={safe_phone}&text={encoded_text}"
            webbrowser.open(whatsapp_url)
            
            audit_service.log_audit(
                task_id="whatsapp_msg",
                agent="WhatsAppAgent",
                tool="whatsapp.send_message",
                risk_level="CONFIRM",
                permission_decision="APPROVED",
                status="success",
                details={"recipient": clean_recipient, "phone": safe_phone, "message_preview": clean_msg[:50]}
            )
            return {
                "success": True,
                "recipient": clean_recipient,
                "phone": safe_phone,
                "message": f"WhatsApp message dispatched to {clean_recipient} ({safe_phone}): '{clean_msg}'"
            }
        else:
            # No phone number resolved: open WhatsApp chat/search with prefilled text
            whatsapp_url = f"https://web.whatsapp.com/send?text={encoded_text}"
            webbrowser.open(whatsapp_url)
            return {
                "success": True,
                "recipient": clean_recipient,
                "message": f"WhatsApp opened with message drafted for {clean_recipient}: '{clean_msg}'"
            }
    except Exception as e:
        return {"success": False, "error": f"Failed to dispatch WhatsApp message: {str(e)}"}
