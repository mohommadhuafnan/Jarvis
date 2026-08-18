import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_live_workflow():
    print("==================================================")
    print("RUNNING LIVE REAL-WORLD RELIABILITY AUDIT")
    print("==================================================")

    # 1. Natural Language Calendar + Reminder Compound Intent
    print("\n--- TEST D: 'Tomorrow I have a meeting at 4:30 AM. Remind me.' ---")
    res1 = requests.post(f"{BASE_URL}/voice/gateway/process", json={
        "audio_or_text": "Tomorrow I have a meeting at 4:30 AM. Remind me.",
        "conversation_id": "daily_use_audit_session"
    }, timeout=15)
    print(f"Status: {res1.status_code}")
    d1 = res1.json()
    print(f"Tool Used: {d1.get('tool_used')}")
    print(f"Spoken Reply: \"{d1.get('reply')}\"")
    print(f"Action Plan: {d1.get('action_plan')}")

    # 2. Real Gmail Sync & Retrieval
    print("\n--- TEST B: 'Check my emails.' & Dashboard Sync ---")
    res2 = requests.post(f"{BASE_URL}/voice/gateway/process", json={
        "audio_or_text": "Check my emails.",
        "conversation_id": "daily_use_audit_session"
    }, timeout=15)
    print(f"Status: {res2.status_code}")
    d2 = res2.json()
    print(f"Spoken Reply: \"{d2.get('reply')}\"")
    
    # Check what /api/email/list returns for the dashboard
    res_emails = requests.get(f"{BASE_URL}/email/list", timeout=8)
    d_emails = res_emails.json()
    print(f"Dashboard Real Email Count: {d_emails.get('count')}")
    if d_emails.get("emails"):
        print(f"Sample First Email Sender: {d_emails['emails'][0].get('from')}")
        print(f"Sample First Email Subject: {d_emails['emails'][0].get('subject')}")

    # 3. Real Calendar Query
    print("\n--- TEST C: 'What's on my calendar tomorrow?' ---")
    res3 = requests.post(f"{BASE_URL}/voice/gateway/process", json={
        "audio_or_text": "What's on my calendar tomorrow?",
        "conversation_id": "daily_use_audit_session"
    }, timeout=15)
    print(f"Status: {res3.status_code}")
    d3 = res3.json()
    print(f"Spoken Reply: \"{d3.get('reply')}\"")

    # 4. Background Reminder Daemon Execution & Due Push
    print("\n--- TEST F: Reminder Daemon Automatic Due Notification ---")
    # Schedule a reminder due in 2 seconds
    res_rem = requests.post(f"{BASE_URL}/reminders/create", json={
        "title": "Check AgriMind Pipeline",
        "reminder_time": "Now (Live Test)",
        "due_at": "2020-01-01T00:00:00"  # Instant due
    }, timeout=8)
    print(f"Created Test Reminder: {res_rem.json()}")

    # Wait 4 seconds for scheduler daemon loop to process
    time.sleep(4)

    # Query /api/reminders/due
    res_due = requests.get(f"{BASE_URL}/reminders/due", timeout=8)
    d_due = res_due.json()
    print(f"Scheduler Popped Due Count: {d_due.get('count')}")
    if d_due.get("due_reminders"):
        print(f"Spoken Voice Alert Dispatched: \"{d_due['due_reminders'][0].get('spoken_notification')}\"")

    print("\n==================================================")
    print("LIVE REAL-WORLD AUDIT FINISHED")
    print("==================================================")

if __name__ == "__main__":
    test_live_workflow()
