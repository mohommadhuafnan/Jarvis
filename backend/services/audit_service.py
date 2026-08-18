import re
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.database.collections import get_audit_logs_col, get_agent_runs_col, get_tool_executions_col

logger = logging.getLogger("JARVIS.Services.Audit")

def sanitize_payload(payload: Any) -> Any:
    """
    Recursively redact sensitive keys, tokens, passwords, and connection strings from payloads.
    """
    if isinstance(payload, dict):
        clean = {}
        for k, v in payload.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ["password", "secret", "token", "key", "uri", "auth", "credential"]):
                clean[k] = "[REDACTED]"
            else:
                clean[k] = sanitize_payload(v)
        return clean
    elif isinstance(payload, list):
        return [sanitize_payload(x) for x in payload]
    elif isinstance(payload, str):
        # Redact any mongodb srv or auth patterns in string
        if "mongodb+srv://" in payload or "mongodb://" in payload:
            return "[REDACTED_MONGODB_URI]"
        if re.search(r'GOCSPX-[a-zA-Z0-9_\-]+', payload):
            return "[REDACTED_OAUTH_SECRET]"
        if re.search(r'AQ\.[a-zA-Z0-9_\-]+', payload):
            return "[REDACTED_GEMINI_KEY]"
        return payload
    return payload

class AuditService:
    """
    Audit & Agent Run Telemetry Logging Service.
    Guarantees full observability and compliance without leaking sensitive credentials.
    """

    def log_agent_run(
        self,
        task_id: str,
        agent: str,
        tool: str,
        arguments_summary: Any,
        status: str,
        started_at: str,
        completed_at: Optional[str] = None,
        result_summary: Any = None,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record an agent's tool execution run in MongoDB.
        """
        col = get_agent_runs_col()
        rid = run_id or f"run_{uuid.uuid4().hex[:8]}"
        doc = {
            "runId": rid,
            "taskId": task_id,
            "agent": agent,
            "tool": tool,
            "argumentsSummary": sanitize_payload(arguments_summary),
            "status": status,
            "startedAt": started_at,
            "completedAt": completed_at or datetime.now().isoformat(),
            "resultSummary": sanitize_payload(result_summary)
        }

        if col is not None:
            try:
                col.insert_one(doc)
            except Exception as e:
                logger.error(f"Error logging agent run: {e}")

        # Also log to tool_executions
        tool_col = get_tool_executions_col()
        if tool_col is not None:
            try:
                tool_col.insert_one({
                    "runId": rid,
                    "taskId": task_id,
                    "tool": tool,
                    "timestamp": started_at,
                    "status": status
                })
            except Exception:
                pass

        return {k: v for k, v in doc.items() if k != "_id"}

    def log_audit(
        self,
        task_id: str,
        agent: str,
        tool: str,
        risk_level: str,
        permission_decision: str,
        status: str = "success",
        details: Any = None
    ) -> Dict[str, Any]:
        """
        Record a permission-checked action in the audit log collection.
        """
        col = get_audit_logs_col()
        now = datetime.now().isoformat()
        doc = {
            "timestamp": now,
            "taskId": task_id,
            "agent": agent,
            "tool": tool,
            "riskLevel": str(risk_level).upper(),
            "permissionDecision": str(permission_decision).upper(),
            "status": status,
            "details": sanitize_payload(details) if details else ""
        }

        if col is not None:
            try:
                col.insert_one(doc)
            except Exception as e:
                logger.error(f"Error writing to audit log: {e}")

        return {k: v for k, v in doc.items() if k != "_id"}

    def get_audit_logs(self, task_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve recent audit logs.
        """
        col = get_audit_logs_col()
        if col is None:
            return []

        filter_q = {"taskId": task_id} if task_id else {}
        try:
            cursor = col.find(filter_q, {"_id": 0}).sort("timestamp", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error fetching audit logs: {e}")
            return []

    def get_agent_runs(self, task_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve agent run histories.
        """
        col = get_agent_runs_col()
        if col is None:
            return []

        filter_q = {"taskId": task_id} if task_id else {}
        try:
            cursor = col.find(filter_q, {"_id": 0}).sort("startedAt", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error fetching agent runs: {e}")
            return []

audit_service = AuditService()
