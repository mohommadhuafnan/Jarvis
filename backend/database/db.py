import sqlite3
import json
from datetime import datetime
from backend.config import DB_PATH

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'pending',
        deadline TEXT,
        tags TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Calendar Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calendar_events (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        location TEXT,
        reminder_minutes INTEGER DEFAULT 15,
        created_at TEXT NOT NULL
    );
    """)

    # Long-term Memory Vault Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory_vault (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        tags TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Activity & Tool Execution Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id TEXT PRIMARY KEY,
        module TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        status TEXT DEFAULT 'success',
        created_at TEXT NOT NULL
    );
    """)

    # Conversations & Chat History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        tool_calls TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Google OAuth Tokens Table (Server-side Encrypted Store)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS oauth_tokens (
        service TEXT PRIMARY KEY,
        access_token TEXT NOT NULL,
        refresh_token TEXT,
        token_uri TEXT,
        client_id TEXT,
        scopes TEXT,
        expiry TEXT,
        updated_at TEXT NOT NULL
    );
    """)

    # Local Email Cache Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id TEXT PRIMARY KEY,
        thread_id TEXT,
        sender TEXT NOT NULL,
        recipient TEXT,
        subject TEXT NOT NULL,
        snippet TEXT,
        body TEXT,
        is_unread INTEGER DEFAULT 1,
        labels TEXT,
        received_at TEXT NOT NULL
    );
    """)

    # Personal Profiles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personal_profiles (
        user_id TEXT PRIMARY KEY,
        profile_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Knowledge Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_hash TEXT,
        mime_type TEXT,
        doc_type TEXT DEFAULT 'general',
        summary TEXT,
        extracted_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        uploaded_at TEXT NOT NULL
    );
    """)

    # Knowledge Facts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_facts (
        id TEXT PRIMARY KEY,
        document_id TEXT,
        category TEXT NOT NULL,
        fact_type TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        source_type TEXT DEFAULT 'manual',
        source_name TEXT,
        page INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );
    """)

    # Structured Timetables Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timetables (
        id TEXT PRIMARY KEY,
        document_id TEXT,
        semester TEXT,
        weekday TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        subject TEXT NOT NULL,
        code TEXT,
        room TEXT,
        lecturer TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );
    """)


    # Seed initial system logs and demo data if empty
    cursor.execute("SELECT COUNT(*) as count FROM activity_logs")
    if cursor.fetchone()["count"] == 0:
        now = datetime.now().strftime("%H:%M")
        initial_logs = [
            ("act_1", "System", "JARVIS AI initialized successfully", "All systems are operational", "success", "20:53"),
            ("act_2", "Camera System", "Connected to 5 cameras", "Monitoring and recording active", "success", "20:51"),
            ("act_3", "Presentation Generated", "New presentation created", "Jarvis_Project_Overview.pptx", "success", "20:50"),
            ("act_4", "Email Summary", "12 unread emails found", "Priority: 3 High, 2 Medium, 7 Low", "success", "20:48"),
            ("act_5", "Task Updated", "'Project Report' marked as complete", "Great work!", "success", "20:45"),
        ]
        cursor.executemany(
            "INSERT INTO activity_logs (id, module, action, details, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            initial_logs
        )

    # Seed initial sample tasks if empty
    cursor.execute("SELECT COUNT(*) as count FROM tasks")
    if cursor.fetchone()["count"] == 0:
        sample_tasks = [
            ("task_1", "Finish AgriMind AI neural training", "Train model with 50k agricultural images", "high", "pending", "2026-08-20", "ai,project", datetime.now().isoformat(), datetime.now().isoformat()),
            ("task_2", "Inspect camera feeds & security perimeter", "Run vision scan across all nodes", "medium", "completed", "2026-08-18", "security", datetime.now().isoformat(), datetime.now().isoformat()),
            ("task_3", "Review quarterly system telemetry report", "Audit memory usage and API quota", "low", "pending", "2026-08-22", "telemetry", datetime.now().isoformat(), datetime.now().isoformat()),
        ]
        cursor.executemany(
            "INSERT INTO tasks (id, title, description, priority, status, deadline, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_tasks
        )

    # Seed sample memory if empty
    cursor.execute("SELECT COUNT(*) as count FROM memory_vault")
    if cursor.fetchone()["count"] == 0:
        sample_memories = [
            ("mem_1", "user_profile", "Primary Project", "AgriMind AI & Cyber Defense Command Center", "project,ai", datetime.now().isoformat(), datetime.now().isoformat()),
            ("mem_2", "preferences", "Coding Language", "Python & TypeScript", "dev,pref", datetime.now().isoformat(), datetime.now().isoformat()),
            ("mem_3", "preferences", "Theme", "Cyberpunk Crimson HUD", "ui,pref", datetime.now().isoformat(), datetime.now().isoformat()),
        ]
        cursor.executemany(
            "INSERT INTO memory_vault (id, category, key, value, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_memories
        )

    conn.commit()
    conn.close()
