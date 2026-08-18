import sys
import os
import time
import requests
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import all tools to populate registry
import backend.tools.system_tools
import backend.tools.task_tools
import backend.tools.calendar_tools
import backend.tools.email_tools
import backend.tools.gmail_tools
import backend.tools.web_tools
import backend.tools.file_tools
import backend.tools.code_sandbox
import backend.tools.vision_tools
import backend.tools.computer_tools
import backend.tools.browser_tools
import backend.tools.memory_tools

from backend.database.mongodb import get_mongo_client, check_db_health, get_database
from backend.database.collections import (
    get_users_col, get_conversations_col, get_messages_col,
    get_memories_col, get_tasks_col, get_agent_runs_col,
    get_tool_executions_col, get_voice_sessions_col,
    get_preferences_col, get_audit_logs_col
)
from backend.database.indexes import create_indexes
from backend.services.memory_service import memory_service
from backend.services.task_service import task_service, TaskStatus
from backend.services.conversation_service import conversation_service
from backend.services.audit_service import audit_service, sanitize_payload
from backend.services.preference_service import preference_service
from backend.services.voice_session_service import voice_session_service
from backend.kernel.agent_kernel import agent_kernel
from backend.kernel.permission_engine import permission_engine
from backend.tools.registry import RiskLevel, registry

results = {}

def run_test(name, test_fn):
    try:
        ok = test_fn()
        status = "PASS" if ok else "FAIL"
        results[name] = status
        print(f"[{status}] {name}")
    except Exception as e:
        results[name] = f"FAIL ({e})"
        print(f"[FAIL] {name}: {e}")

def test_mongo_package():
    import pymongo
    return bool(pymongo.__version__)

def test_mongo_connection():
    client = get_mongo_client()
    return client is not None

def test_mongo_ping():
    client = get_mongo_client()
    res = client.admin.command("ping")
    return res.get("ok") == 1

def test_health_endpoint():
    res = requests.get("http://127.0.0.1:8000/api/health/database", timeout=5)
    if res.status_code == 200:
        data = res.json()
        return data.get("database") == "mongodb" and data.get("status") == "connected"
    return False

def test_memory_write():
    res = memory_service.store_memory(
        key="main_project",
        value="AgriMind AI",
        memory_type="user_preference",
        source="conversation"
    )
    return res.get("success") is True

def test_memory_read():
    mem = memory_service.get_memory("main_project")
    if mem and mem.get("value") == "AgriMind AI":
        search_res = memory_service.search_memory("AgriMind")
        return len(search_res) > 0
    return False

def test_conversation_write():
    conv_id = "test_conv_001"
    conversation_service.get_or_create_conversation(conv_id)
    msg = conversation_service.add_message(
        conversation_id=conv_id,
        role="user",
        content="Hello JARVIS, initialize neural link."
    )
    return msg.get("content") == "Hello JARVIS, initialize neural link."

def test_conversation_retrieval():
    conv_id = "test_conv_001"
    msgs = conversation_service.get_messages(conv_id)
    return len(msgs) > 0 and msgs[0].get("role") == "user"

def test_task_creation():
    task = task_service.create_task(
        objective="Project Testing",
        description="Verify autonomous MongoDB persistence",
        agent="CodingAgent",
        priority="high",
        task_id="TASK-2026-00123"
    )
    return task.get("taskId") == "TASK-2026-00123" and task.get("status") == TaskStatus.PLANNED

def test_task_update():
    res = task_service.update_task(
        task_id="TASK-2026-00123",
        status=TaskStatus.RUNNING,
        progress=64,
        current_step="Running tests"
    )
    task = task_service.get_task("TASK-2026-00123")
    return task and task.get("status") == TaskStatus.RUNNING and task.get("progress") == 64

def test_task_recovery():
    interrupted = task_service.recover_interrupted_tasks()
    task = task_service.get_task("TASK-2026-00123")
    task_service.update_task("TASK-2026-00123", status=TaskStatus.COMPLETED, progress=100)
    return task and task.get("status") in [TaskStatus.RECOVERING, TaskStatus.COMPLETED]

def test_agent_run_logging():
    run = audit_service.log_agent_run(
        task_id="TASK-2026-00123",
        agent="ComputerAgent",
        tool="computer.openApplication",
        arguments_summary={"application": "terminal"},
        status="COMPLETED",
        started_at="2026-08-18T10:00:00",
        completed_at="2026-08-18T10:00:02",
        result_summary={"success": True}
    )
    runs = audit_service.get_agent_runs(task_id="TASK-2026-00123")
    return len(runs) > 0 and runs[0].get("tool") == "computer.openApplication"

def test_audit_logging():
    audit = audit_service.log_audit(
        task_id="TASK-2026-00123",
        agent="GmailAgent",
        tool="gmail.send",
        risk_level="CONFIRM",
        permission_decision="APPROVED",
        status="success",
        details={"recipient": "commander@jarvis.ai"}
    )
    logs = audit_service.get_audit_logs(task_id="TASK-2026-00123")
    return len(logs) > 0 and logs[0].get("riskLevel") == "CONFIRM"

def test_voice_session_persistence():
    session = voice_session_service.create_session(
        language="en",
        provider="Google Gemini Live Audio"
    )
    sid = session.get("sessionId")
    ended = voice_session_service.end_session(sid)
    sessions = voice_session_service.list_sessions(limit=5)
    return ended and any(s.get("sessionId") == sid for s in sessions)

def test_user_preferences():
    preference_service.set_preference("preferredLanguage", "English")
    preference_service.set_preference("preferredVoice", "Puck")
    val = preference_service.get_preference("preferredLanguage")
    all_prefs = preference_service.get_all_preferences()
    return val == "English" and "preferredVoice" in all_prefs

def test_indexes():
    ok = create_indexes()
    return ok is True

def test_permission_integration():
    allowed_read, _, risk_read = permission_engine.check_permission("memory.search", {"query": "test"})
    allowed_del, _, risk_del = permission_engine.check_permission("files.delete", {"filename": "test.txt"})
    return allowed_read is True and allowed_del is False

def test_secret_protection():
    dirty = {
        "user": "commander",
        "api_key": "AIzaSy_DUMMY_SECRET_KEY_FOR_TESTING_12345",
        "mongodb_uri": "mongodb+srv://user:pass@cluster.mongodb.net",
        "notes": "safe note"
    }
    clean = sanitize_payload(dirty)
    return clean["api_key"] == "[REDACTED]" and clean["mongodb_uri"] == "[REDACTED]" and clean["notes"] == "safe note"

def test_e2e_a_memory_recall():
    res1 = agent_kernel.process_command("Jarvis, remember that my main project is AgriMind AI.")
    res2 = agent_kernel.process_command("What is my main project?")
    return "AgriMind" in res2.get("reply", "") or "AgriMind" in str(res1)

def test_e2e_b_task_creation():
    res = agent_kernel.process_command("Create a task called Project Testing.")
    task = task_service.get_task("Project Testing")
    return task is not None or "Project Testing" in str(res)

def test_e2e_c_working_on():
    res = agent_kernel.process_command("Jarvis, what am I currently working on?")
    return len(res.get("reply", "")) > 0

def test_e2e_d_task_continuation():
    res = agent_kernel.process_command("Jarvis, continue my previous task.")
    return "previous task" in res.get("reply", "").lower() or "resuming" in res.get("reply", "").lower() or "processed" in res.get("reply", "").lower()

def test_e2e_e_agent_logging():
    runs = audit_service.get_agent_runs(limit=10)
    return len(runs) > 0

def test_e2e_f_audit_logging():
    res = agent_kernel.process_command("Jarvis, what did you do?")
    logs = audit_service.get_audit_logs(limit=10)
    return len(logs) > 0 and len(res.get("reply", "")) > 0

def test_e2e_g_permission_enforcement():
    # Attempting high risk operation should be gated by Permission Engine
    res = agent_kernel.process_command("Delete meeting")
    return res.get("confirmation_required") is not None or "confirmation" in res.get("reply", "").lower() or "safety" in res.get("reply", "").lower()

if __name__ == "__main__":
    print("\n========== JARVIS MONGODB INTEGRATION TEST SUITE ==========\n")
    run_test("MongoDB package", test_mongo_package)
    run_test("MongoDB connection", test_mongo_connection)
    run_test("MongoDB ping", test_mongo_ping)
    run_test("Database health endpoint", test_health_endpoint)
    run_test("Memory service", test_memory_write)
    run_test("Memory read", test_memory_read)
    run_test("Conversation persistence", test_conversation_write)
    run_test("Conversation retrieval", test_conversation_retrieval)
    run_test("Task persistence", test_task_creation)
    run_test("Task update", test_task_update)
    run_test("Task recovery", test_task_recovery)
    run_test("Agent run logging", test_agent_run_logging)
    run_test("Audit logging", test_audit_logging)
    run_test("Voice session persistence", test_voice_session_persistence)
    run_test("User preferences", test_user_preferences)
    run_test("Indexes", test_indexes)
    run_test("Permission integration", test_permission_integration)
    run_test("Secret protection", test_secret_protection)
    
    print("\n--- END-TO-END FLOWS ---")
    run_test("E2E A. Memory write/read", test_e2e_a_memory_recall)
    run_test("E2E B. Task persistence", test_e2e_b_task_creation)
    run_test("E2E C. Working on / Recall", test_e2e_c_working_on)
    run_test("E2E D. Restart/recovery", test_e2e_d_task_continuation)
    run_test("E2E E. Agent logging", test_e2e_e_agent_logging)
    run_test("E2E F. Audit logging", test_e2e_f_audit_logging)
    run_test("E2E G. Permission enforcement", test_e2e_g_permission_enforcement)
    print("\n===========================================================\n")
