import os
import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import CORS_ORIGINS, HOST, PORT, USER_NAME, WAKE_WORD, ASSISTANT_NAME, LANGUAGE, GEMINI_API_KEY
from backend.database.db import init_db, get_db
from backend.database.mongodb import get_mongo_client, check_db_health, close_mongo_connection
from backend.database.indexes import create_indexes
from backend.database.migration import run_sqlite_to_mongodb_migration
from backend.services.memory_service import memory_service
from backend.services.task_service import task_service, TaskStatus
from backend.services.conversation_service import conversation_service
from backend.services.audit_service import audit_service
from backend.services.preference_service import preference_service
from backend.services.voice_session_service import voice_session_service

from backend.voice.voice_gateway import voice_gateway
from backend.voice import get_voice_provider
from backend.ai.gemini_service import ai_service
from backend.tools.registry import registry, RiskLevel
from backend.tools.system_tools import get_diagnostics, get_time

app = FastAPI(title="JARVIS AI Command Center API", version="2.5.1")

# Enable CORS for Next.js / Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.services.scheduler_service import scheduler_service
from backend.services.google_oauth_service import google_oauth_service

@app.on_event("startup")
def startup_event():
    # 1. Initialize local SQLite (Phase 1/2 retention for OAuth and local caches)
    init_db()
    
    # 2. Connect to MongoDB Atlas, create indexes, and run migration
    client = get_mongo_client()
    if client is not None:
        create_indexes()
        run_sqlite_to_mongodb_migration()
        task_service.recover_interrupted_tasks()
        print(f"[{ASSISTANT_NAME}] Connected to MongoDB Atlas. Indexes verified. Tasks recovered.")
    else:
        print(f"[{ASSISTANT_NAME}] WARNING: MongoDB connection pending or offline.")

    # 3. Start background reminder scheduler daemon
    scheduler_service.start()

    print(f"[{ASSISTANT_NAME}] AI Command Center Backend Online.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler_service.stop()
    close_mongo_connection()
    print(f"[{ASSISTANT_NAME}] Services & MongoDB gracefully closed.")

# --- Reminder Scheduler Endpoints ---
@app.get("/api/reminders/due")
def get_due_reminders():
    """Pop and return due notifications to be spoken immediately by frontend."""
    notifications = scheduler_service.pop_due_notifications()
    return {
        "count": len(notifications),
        "due_reminders": notifications
    }

@app.get("/api/reminders/all")
def get_all_reminders():
    """Return all scheduled reminders."""
    reminders = scheduler_service.get_all_reminders()
    return {
        "count": len(reminders),
        "reminders": reminders
    }

class ReminderCreateRequest(BaseModel):
    title: str
    reminder_time: str
    due_at: Optional[str] = None

@app.post("/api/reminders/create")
def create_reminder_endpoint(req: ReminderCreateRequest):
    return scheduler_service.add_reminder(req.title, req.reminder_time, req.due_at)

# --- Gmail / Email Synchronization Endpoints ---
@app.get("/api/gmail/emails")
@app.get("/api/email/list")
def list_emails_endpoint():
    """Returns real Gmail messages from authenticated account or stored cache."""
    emails = google_oauth_service.list_all_or_cached_emails()
    return {
        "count": len(emails),
        "emails": emails
    }

# --- System & Telemetry Endpoints ---
@app.get("/api/health")
def health_check():
    return {
        "status": "ONLINE",
        "assistant": ASSISTANT_NAME,
        "version": "2.5.1",
        "ai_core": "Gemini 2.5/2.0 Flash",
        "voice_gateway": "VALSEA & Gemini Live Core Active",
        "timestamp": time.time()
    }

@app.get("/api/health/database")
def database_health_check():
    """
    Real-time live health ping to MongoDB verifying connection status and latency.
    """
    health = check_db_health()
    if health.get("status") != "connected":
        return health
    return {
        "database": "mongodb",
        "status": "connected",
        "latency_ms": health.get("latency_ms", 0),
        "database_name": health.get("database_name", "jarvis")
    }

@app.get("/api/system/stats")
def system_stats():
    diag = get_diagnostics()
    time_info = get_time()
    
    # Fetch recent audit logs from MongoDB
    audit_logs = audit_service.get_audit_logs(limit=10)
    voice_telemetry = voice_gateway.get_live_telemetry()
    
    return {
        "telemetry": diag,
        "clock": time_info,
        "user_name": USER_NAME,
        "logs": audit_logs,
        "connection": "SECURE",
        "memory_status": "MongoDB Atlas Active",
        "voice_telemetry": voice_telemetry,
        "uptime": diag["uptime"],
        "status": "ALL SYSTEMS OPERATIONAL"
    }

from backend.kernel import agent_kernel, planner, permission_engine

# --- AI Chat & Agent Kernel Execution ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"
    history: Optional[List[Dict[str, str]]] = []

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    result = agent_kernel.process_command(req.message, context={"conversation_id": req.session_id})
    return result

@app.post("/api/kernel/stop")
def emergency_stop_endpoint():
    voice_gateway.interrupt()
    return agent_kernel.trigger_emergency_stop()

@app.post("/api/kernel/plan")
def get_plan_endpoint(req: ChatRequest):
    plan = planner.plan_task(req.message)
    return plan.dict()

# --- Voice Gateway REST Endpoints ---
class VoiceProcessRequest(BaseModel):
    audio_or_text: str
    conversation_id: Optional[str] = "default_session"
    language: Optional[str] = "en"
    voice: Optional[str] = "Puck"

@app.post("/api/voice/gateway/process")
def process_voice_gateway_endpoint(req: VoiceProcessRequest):
    """
    Execute full voice conversational turn:
    Transcript/Audio -> STT -> Multi-turn Context -> Gemini -> Kernel -> Tools -> TTS -> Audio
    """
    result = voice_gateway.process_voice_turn(
        audio_or_text=req.audio_or_text,
        conversation_id=req.conversation_id or "default_session",
        language=req.language or "en",
        voice=req.voice or "Puck"
    )
    return result

@app.post("/api/voice/gateway/interrupt")
def interrupt_voice_gateway_endpoint():
    """
    Instant Barge-In Interruption Endpoint.
    Halt active speech output and reset speech pipeline.
    """
    return voice_gateway.interrupt()

@app.get("/api/voice/gateway/telemetry")
def get_voice_gateway_telemetry_endpoint():
    """
    Retrieve live turn latencies: STT, Gemini, Agent, TTS, Total.
    """
    return voice_gateway.get_live_telemetry()

# --- MongoDB Task Management Endpoints ---
@app.get("/api/tasks")
def get_tasks(status: Optional[str] = "all"):
    tasks = task_service.list_tasks(status=status if status != "all" else None, limit=50)
    return {
        "count": len(tasks),
        "tasks": tasks
    }

@app.post("/api/tasks")
def add_task(payload: Dict[str, Any] = Body(...)):
    res = task_service.create_task(
        objective=payload.get("title", payload.get("objective", "Untitled Task")),
        description=payload.get("description", ""),
        priority=payload.get("priority", "medium"),
        deadline=payload.get("deadline"),
        agent=payload.get("agent", "CodingAgent")
    )
    return {"success": True, "task": res}

@app.put("/api/tasks/{task_id}")
def update_task_endpoint(task_id: str, payload: Dict[str, Any] = Body(...)):
    res = task_service.update_task(
        task_id=task_id,
        status=payload.get("status"),
        progress=payload.get("progress"),
        current_step=payload.get("current_step")
    )
    return res

@app.put("/api/tasks/{task_id}/complete")
def complete_task_endpoint(task_id: str):
    res = registry.execute("tasks.complete", {"task_id": task_id})
    return res

# --- MongoDB Long-term Memory Endpoints ---
@app.get("/api/memory")
@app.get("/api/memories")
def get_memory(query: Optional[str] = None, type: Optional[str] = None):
    if query:
        memories = memory_service.search_memory(query=query)
    else:
        memories = memory_service.list_memories(memory_type=type)
    return {
        "total": len(memories),
        "memories": memories
    }

@app.post("/api/memory")
@app.post("/api/memories")
def add_memory(payload: Dict[str, Any] = Body(...)):
    key = payload.get("key", payload.get("subject", "User Note"))
    val = payload.get("value", payload.get("detail", ""))
    cat = payload.get("category", payload.get("type", "user_preference"))
    res = memory_service.store_memory(key=key, value=val, memory_type=cat)
    return res

@app.delete("/api/memories/{key_or_id}")
def delete_memory_endpoint(key_or_id: str):
    deleted = memory_service.delete_memory(key_or_id)
    return {"success": deleted, "key": key_or_id}

# --- MongoDB Audit & Telemetry Endpoints ---
@app.get("/api/audit/logs")
def get_audit_logs_endpoint(task_id: Optional[str] = None, limit: int = 50):
    logs = audit_service.get_audit_logs(task_id=task_id, limit=limit)
    return {"count": len(logs), "logs": logs}

@app.get("/api/audit/agent-runs")
def get_agent_runs_endpoint(task_id: Optional[str] = None, limit: int = 50):
    runs = audit_service.get_agent_runs(task_id=task_id, limit=limit)
    return {"count": len(runs), "agent_runs": runs}

# --- MongoDB Conversation History Endpoints ---
@app.get("/api/conversations")
def list_conversations_endpoint():
    convs = conversation_service.list_conversations()
    return {"conversations": convs}

@app.get("/api/conversations/{conv_id}/messages")
def get_conversation_messages_endpoint(conv_id: str):
    msgs = conversation_service.get_messages(conversation_id=conv_id)
    return {"conversation_id": conv_id, "messages": msgs}

# --- MongoDB User Preferences Endpoints ---
@app.get("/api/preferences")
def get_user_preferences_endpoint():
    prefs = preference_service.get_all_preferences()
    return {"preferences": prefs}

@app.post("/api/preferences")
def set_user_preference_endpoint(payload: Dict[str, Any] = Body(...)):
    key = payload.get("key")
    val = payload.get("value")
    if not key:
        raise HTTPException(status_code=400, detail="Missing key")
    res = preference_service.set_preference(key=key, value=val)
    return res

# --- Calendar ---
@app.get("/api/calendar")
def get_calendar():
    res = registry.execute("calendar.getEvents", {"days_ahead": 7})
    return res.get("result", {})

@app.post("/api/calendar")
def add_calendar_event(payload: Dict[str, Any] = Body(...)):
    res = registry.execute("calendar.createEvent", payload)
    return res

# --- Email ---
@app.get("/api/emails")
def get_emails(unread_only: bool = False):
    res = registry.execute("email.read", {"unread_only": unread_only})
    return res.get("result", {})

@app.post("/api/emails/draft")
def draft_email_endpoint(payload: Dict[str, Any] = Body(...)):
    res = registry.execute("email.draft", payload)
    return res

@app.post("/api/emails/send")
def send_email_endpoint(payload: Dict[str, Any] = Body(...)):
    res = registry.execute("email.send", payload)
    return res

# --- Filesystem Sandbox ---
@app.get("/api/files")
def get_files():
    res = registry.execute("files.list", {})
    return res.get("result", {})

@app.post("/api/files/read")
def read_workspace_file(payload: Dict[str, str] = Body(...)):
    res = registry.execute("files.read", {"filename": payload.get("filename", "")})
    return res

@app.post("/api/files/write")
def write_workspace_file(payload: Dict[str, str] = Body(...)):
    res = registry.execute("files.create", {
        "filename": payload.get("filename", ""),
        "content": payload.get("content", "")
    })
    return res

# --- Code Execution Sandbox ---
@app.post("/api/code/run")
def run_code_sandbox(payload: Dict[str, str] = Body(...)):
    res = registry.execute("code.run", {
        "language": payload.get("language", "python"),
        "code": payload.get("code", "")
    })
    return res

# --- Google OAuth Endpoints ---
from backend.services.google_oauth_service import google_oauth_service
from fastapi.responses import HTMLResponse

@app.get("/api/auth/google/status")
def google_auth_status():
    return google_oauth_service.get_status()

@app.get("/api/auth/google/login")
def google_auth_login():
    try:
        url = google_oauth_service.get_auth_url()
        return {"auth_url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/google/callback")
def google_auth_callback(code: Optional[str] = None):
    if not code:
        return HTMLResponse("<h3>Authorization error: No authorization code received.</h3>", status_code=400)
    try:
        res = google_oauth_service.exchange_code_for_tokens(code)
        email = res.get("user_email") or "Your Google Account"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <title>JARVIS Google OAuth Success</title>
          <style>
            body {{ background: #050508; color: #F5F5F5; font-family: monospace; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
            .card {{ background: #0D0B0E; border: 1px solid #FF1E42; padding: 2rem; border-radius: 8px; text-align: center; box-shadow: 0 0 20px rgba(255,30,66,0.3); }}
            h2 {{ color: #FF1E42; margin-top: 0; }}
          </style>
        </head>
        <body>
          <div class="card">
            <h2>JARVIS AI — GOOGLE CONNECTED</h2>
            <p>Successfully linked account: <b>{email}</b></p>
            <p>You may close this window and return to the JARVIS Command Center.</p>
            <script>
              setTimeout(() => {{
                if (window.opener) {{
                  window.opener.postMessage({{ type: 'GOOGLE_AUTH_SUCCESS', email: '{email}' }}, '*');
                  window.close();
                }} else {{
                  window.location.href = 'http://localhost:5173';
                }}
              }}, 2000);
            </script>
          </div>
        </body>
        </html>
        """
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f"<h3>Google OAuth Token Exchange Failed: {e}</h3>", status_code=500)

# --- Multi-Agent Orchestrator & Registry ---
from backend.kernel.agent_registry import agent_registry
from backend.kernel.orchestrator import orchestrator

@app.get("/api/agents")
def list_registered_agents():
    return {
        "success": True,
        "count": len(agent_registry.list_agents()),
        "agents": agent_registry.list_agents()
    }

@app.post("/api/orchestrator/execute")
def execute_orchestrated_task(payload: Dict[str, Any] = Body(...)):
    prompt = payload.get("task", "")
    plan = planner.plan_task(prompt)
    res = orchestrator.orchestrate_plan(plan)
    return res

# --- Voice & Gemini Audio Endpoints ---
@app.get("/api/voice/voices")
def get_available_voices():
    return {
        "provider": "VALSEA & Google Gemini Voice Core",
        "voices": [
            {"id": "Puck", "name": "Puck (Energetic & Futuristic)", "gender": "Male"},
            {"id": "Charon", "name": "Charon (Deep & Tactical)", "gender": "Male"},
            {"id": "Kore", "name": "Kore (Smooth & Sophisticated)", "gender": "Female"},
            {"id": "Fenrir", "name": "Fenrir (Authoritative)", "gender": "Male"},
            {"id": "Aoede", "name": "Aoede (Warm & Intelligent)", "gender": "Female"}
        ],
        "default": "Puck"
    }

@app.post("/api/voice/speak")
def generate_voice_speech(payload: Dict[str, Any] = Body(...)):
    text = payload.get("text", "")
    voice_name = payload.get("voice", "Puck")
    provider = get_voice_provider()
    result = provider.synthesize(text, voice_name=voice_name)
    return result

@app.post("/api/voice/transcribe")
def transcribe_audio_stream(payload: Dict[str, Any] = Body(...)):
    audio_base64 = payload.get("audio", "")
    provider = get_voice_provider()
    result = provider.transcribe(audio_base64)
    return result

@app.get("/api/voice/sessions")
def get_voice_sessions_endpoint():
    sessions = voice_session_service.list_sessions()
    return {"sessions": sessions}

# --- Settings ---
@app.get("/api/settings")
def get_settings():
    return {
        "assistant_name": ASSISTANT_NAME,
        "user_name": USER_NAME,
        "wake_word": WAKE_WORD,
        "language": LANGUAGE,
        "has_gemini_key": bool(ai_service.api_key),
        "model": ai_service.model_name
    }

@app.post("/api/settings")
def update_settings(payload: Dict[str, Any] = Body(...)):
    global USER_NAME, WAKE_WORD, LANGUAGE
    if "user_name" in payload:
        USER_NAME = payload["user_name"]
    if "wake_word" in payload:
        WAKE_WORD = payload["wake_word"]
    if "language" in payload:
        LANGUAGE = payload["language"]
    if "gemini_api_key" in payload and payload["gemini_api_key"]:
        ai_service.update_key(payload["gemini_api_key"])
    
    return {"success": True, "message": "Settings updated successfully."}

# --- Real-time WebSocket Connection ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/assistant")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send initial connection handshake
    await websocket.send_json({
        "type": "SYSTEM_CONNECTED",
        "state": "IDLE",
        "message": f"Connected to {ASSISTANT_NAME} AI Core & Voice Gateway.",
        "telemetry": get_diagnostics(),
        "voice_telemetry": voice_gateway.get_live_telemetry()
    })

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type", "CHAT_MESSAGE")

            if event_type == "WAKE_WORD_TRIGGERED":
                await websocket.send_json({
                    "type": "STATE_CHANGE",
                    "state": "LISTENING",
                    "action_status": "Wake word recognized. Listening..."
                })

            elif event_type == "VOICE_INPUT_START":
                # Instant Barge-In on user speech start
                voice_gateway.interrupt()
                await websocket.send_json({
                    "type": "STATE_CHANGE",
                    "state": "LISTENING",
                    "action_status": "Capturing audio input..."
                })

            elif event_type == "VOICE_INPUT_STOP":
                await websocket.send_json({
                    "type": "STATE_CHANGE",
                    "state": "THINKING",
                    "action_status": "Analyzing audio stream..."
                })

            elif event_type == "PROCESS_VOICE_GATEWAY":
                # Full bidirectional turn via Voice Gateway
                raw_input = data.get("message", data.get("audio", ""))
                lang = data.get("language", "en")
                conv_id = data.get("session_id", "default_session")

                await websocket.send_json({
                    "type": "STATE_CHANGE",
                    "state": "THINKING",
                    "action_status": "Voice Gateway: Neural processing & intent classification..."
                })

                vg_res = voice_gateway.process_voice_turn(
                    audio_or_text=raw_input,
                    conversation_id=conv_id,
                    language=lang
                )

                tool = vg_res.get("tool_used")
                if tool:
                    await websocket.send_json({
                        "type": "STATE_CHANGE",
                        "state": "EXECUTING",
                        "current_tool": tool,
                        "action_status": f"Executing {tool}..."
                    })
                    await asyncio.sleep(0.2)

                await websocket.send_json({
                    "type": "AI_RESPONSE",
                    "state": "SPEAKING",
                    "reply": vg_res.get("reply", ""),
                    "transcript": vg_res.get("transcript", ""),
                    "tool_used": tool,
                    "tool_result": vg_res.get("tool_result"),
                    "audio_data": vg_res.get("audio_data"),
                    "telemetry": vg_res.get("telemetry", {}),
                    "action_status": "Speaking response..."
                })

            elif event_type == "PROCESS_COMMAND":
                user_msg = data.get("message", "")
                
                # 1. State -> THINKING
                await websocket.send_json({
                    "type": "STATE_CHANGE",
                    "state": "THINKING",
                    "action_status": "Neural processing & intent classification..."
                })
                await asyncio.sleep(0.1)

                # 2. Run agent AI brain through kernel
                result = agent_kernel.process_command(user_msg)
                tool = result.get("tool_used")

                # If tool execution
                if tool:
                    await websocket.send_json({
                        "type": "STATE_CHANGE",
                        "state": "EXECUTING",
                        "current_tool": tool,
                        "action_status": f"Executing {tool}...",
                        "action_plan": result.get("action_plan", [])
                    })
                    await asyncio.sleep(0.2)

                # 3. State -> SPEAKING
                await websocket.send_json({
                    "type": "AI_RESPONSE",
                    "state": "SPEAKING",
                    "reply": result.get("reply", ""),
                    "tool_used": tool,
                    "tool_result": result.get("tool_result"),
                    "action_plan": result.get("action_plan", []),
                    "action_status": "Speaking response..."
                })

            elif event_type == "INTERRUPT_SPEECH":
                voice_gateway.interrupt()
                await websocket.send_json({
                    "type": "STATE_CHANGE",
                    "state": "LISTENING",
                    "action_status": "Speech halted (Barge-In). Listening to command..."
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=True)
