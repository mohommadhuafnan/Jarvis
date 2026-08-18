import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def run_knowledge_vault_audit():
    print("==================================================")
    print("RUNNING JARVIS PERSONAL KNOWLEDGE VAULT LIVE AUDIT")
    print("==================================================")

    # 1. Ingest Semester Timetable
    print("\n--- 1. Ingesting Semester Timetable ---")
    tt_payload = {
        "doc_id": "doc_semester_timetable_v1",
        "filename": "Semester_Timetable.pdf",
        "file_path": "storage/vault/Semester_Timetable.pdf",
        "extracted_data": {
            "document_type": "timetable",
            "title": "BICT 2nd Year Semester Timetable",
            "summary": "Official Faculty Timetable for BICT 2nd Year with Network Routing and Digital Systems.",
            "profile": {
                "degree": "BICT",
                "year": "2nd Year",
                "university": "Faculty of Technology",
                "primary_project": "AgriMind AI"
            },
            "timetable_entries": [
                {
                    "weekday": "Monday",
                    "start_time": "09:00",
                    "end_time": "11:00",
                    "subject": "Network Switching and Routing",
                    "code": "NST201",
                    "room": "Lab 2",
                    "lecturer": "Dr. Perera"
                },
                {
                    "weekday": "Monday",
                    "start_time": "13:00",
                    "end_time": "15:00",
                    "subject": "Software Engineering",
                    "code": "SE202",
                    "room": "E301",
                    "lecturer": "Prof. Silva"
                },
                {
                    "weekday": "Tuesday",
                    "start_time": "13:00",
                    "end_time": "15:00",
                    "subject": "Digital Electronic Systems",
                    "code": "DES203",
                    "room": "Lab 1",
                    "lecturer": "Dr. Fernando"
                }
            ],
            "facts": [
                {"category": "education", "key": "degree", "value": "BICT", "confidence": 1.0},
                {"category": "education", "key": "year", "value": "2nd Year", "confidence": 1.0},
                {"category": "project", "key": "primary_project", "value": "AgriMind AI", "confidence": 1.0}
            ]
        }
    }

    res_save = requests.post(f"{BASE_URL}/knowledge/confirm-save", json=tt_payload, timeout=10)
    print(f"Ingestion Commit Status: {res_save.status_code}")
    print(f"Ingestion Result: {res_save.json()}")

    # 2. Query Spoken Voice: "What lectures do I have on Monday?"
    print("\n--- 2. Voice Query: 'What lectures do I have on Monday?' ---")
    res_v1 = requests.post(f"{BASE_URL}/voice/gateway/process", json={
        "audio_or_text": "What lectures do I have on Monday?",
        "conversation_id": "knowledge_audit_session"
    }, timeout=15)
    d_v1 = res_v1.json()
    print(f"Tool Used: {d_v1.get('tool_used')}")
    print(f"Spoken Output: \"{d_v1.get('reply')}\"")

    # 3. Query Spoken Voice: "When is my next class?"
    print("\n--- 3. Voice Query: 'When is my next class?' ---")
    res_v2 = requests.post(f"{BASE_URL}/voice/gateway/process", json={
        "audio_or_text": "When is my next class?",
        "conversation_id": "knowledge_audit_session"
    }, timeout=15)
    d_v2 = res_v2.json()
    print(f"Tool Used: {d_v2.get('tool_used')}")
    print(f"Spoken Output: \"{d_v2.get('reply')}\"")

    # 4. Query Spoken Voice: "What is my main project?"
    print("\n--- 4. Voice Query: 'What is my main project?' ---")
    res_v3 = requests.post(f"{BASE_URL}/voice/gateway/process", json={
        "audio_or_text": "What is my main project?",
        "conversation_id": "knowledge_audit_session"
    }, timeout=15)
    d_v3 = res_v3.json()
    print(f"Tool Used: {d_v3.get('tool_used')}")
    print(f"Spoken Output: \"{d_v3.get('reply')}\"")

    # 5. Query Spoken Voice: "What do you know about me?"
    print("\n--- 5. Voice Query: 'What do you know about me?' ---")
    res_v4 = requests.post(f"{BASE_URL}/voice/gateway/process", json={
        "audio_or_text": "What do you know about me?",
        "conversation_id": "knowledge_audit_session"
    }, timeout=15)
    d_v4 = res_v4.json()
    print(f"Tool Used: {d_v4.get('tool_used')}")
    print(f"Spoken Output: \"{d_v4.get('reply')}\"")

    # 6. Versioning: Ingest New Timetable
    print("\n--- 6. Timetable Versioning: Ingesting 'Semester_Timetable_New.pdf' ---")
    new_tt_payload = {
        "doc_id": "doc_semester_timetable_v2",
        "filename": "Semester_Timetable_New.pdf",
        "file_path": "storage/vault/Semester_Timetable_New.pdf",
        "extracted_data": {
            "document_type": "timetable",
            "title": "Semester Timetable Revised",
            "summary": "Superseded older schedule with new Friday Cyber Operations lecture.",
            "profile": {},
            "timetable_entries": [
                {
                    "weekday": "Friday",
                    "start_time": "10:00",
                    "end_time": "12:00",
                    "subject": "Cyber Defense Operations",
                    "code": "CDO204",
                    "room": "Security Lab",
                    "lecturer": "Dr. Jay"
                }
            ],
            "facts": []
        }
    }
    res_new_tt = requests.post(f"{BASE_URL}/knowledge/confirm-save", json=new_tt_payload, timeout=10)
    print(f"New Timetable Commit: {res_new_tt.json()}")

    # Check that Friday now has classes and Monday is superseded
    res_friday = requests.get(f"{BASE_URL}/knowledge/today-lectures?weekday=Friday", timeout=8)
    print(f"Friday Lectures Count (New Timetable): {res_friday.json().get('count')}")
    print(f"Friday Spoken: \"{res_friday.json().get('spoken_summary')}\"")

    res_monday = requests.get(f"{BASE_URL}/knowledge/today-lectures?weekday=Monday", timeout=8)
    print(f"Monday Lectures Count (Old Timetable Superseded): {res_monday.json().get('count')}")

    # 7. Anti-Hallucination Test: Ask for unrecorded knowledge
    print("\n--- 7. Anti-Hallucination Check for Unrecorded Knowledge ---")
    res_v5 = requests.post(f"{BASE_URL}/voice/gateway/process", json={
        "audio_or_text": "What is my quantum mechanics test score?",
        "conversation_id": "knowledge_audit_session"
    }, timeout=15)
    d_v5 = res_v5.json()
    print(f"Spoken Output for Unrecorded Fact: \"{d_v5.get('reply')}\"")

    # 8. Check HUD Summary Endpoint
    print("\n--- 8. HUD Summary Endpoint Verification ---")
    res_summary = requests.get(f"{BASE_URL}/knowledge/summary", timeout=8)
    d_summary = res_summary.json()
    print(f"Active Document: {d_summary.get('active_document')}")
    print(f"Total Classes: {d_summary.get('total_classes')}")
    print(f"User Degree: {d_summary.get('profile', {}).get('degree')}")
    print(f"User Primary Project: {d_summary.get('profile', {}).get('primary_project')}")

    print("\n==================================================")
    print("JARVIS KNOWLEDGE VAULT LIVE AUDIT COMPLETED")
    print("==================================================")

if __name__ == "__main__":
    run_knowledge_vault_audit()
