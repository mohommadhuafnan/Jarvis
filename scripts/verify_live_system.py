import json
import requests
import time

BASE_URL = "http://localhost:8000/api"

def run_test(name, command):
    print(f"\n==================================================")
    print(f"TEST: {name}")
    print(f"COMMAND: '{command}'")
    print(f"==================================================")
    try:
        start_time = time.time()
        res = requests.post(f"{BASE_URL}/voice/gateway/process", json={
            "audio_or_text": command,
            "conversation_id": "real_live_verification_session",
            "language": "en",
            "voice": "Puck"
        }, timeout=15)
        duration = round(time.time() - start_time, 3)

        if res.status_code == 200:
            data = res.json()
            print(f"[STATUS]: SUCCESS ({duration}s)")
            print(f"[TOOL USED]: {data.get('tool_used')}")
            print(f"[TOOL RESULT]: {json.dumps(data.get('tool_result'), indent=2) if data.get('tool_result') else 'None'}")
            print(f"[JARVIS SPOKEN REPLY]: \"{data.get('reply')}\"")
            print(f"[CONFIRMATION REQUIRED]: {data.get('confirmation_required')}")
            print(f"[ACTION PLAN]: {data.get('action_plan')}")
            return {
                "success": True,
                "tool": data.get("tool_used"),
                "reply": data.get("reply"),
                "result": data.get("tool_result"),
                "confirmation": data.get("confirmation_required")
            }
        else:
            print(f"[STATUS]: HTTP ERROR {res.status_code}")
            print(res.text)
            return {"success": False, "error": res.text}
    except Exception as e:
        print(f"[EXCEPTION]: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    results = {}

    # 1. Wake / Greeting
    results["1_greeting"] = run_test("Wake Greeting", "Hello Jarvis")

    # 2. Open Chrome
    results["2_open_chrome"] = run_test("Open Chrome", "Open Chrome")

    # 3. Open WhatsApp
    results["3_open_whatsapp"] = run_test("Open WhatsApp", "Open WhatsApp")

    # 4. WhatsApp Message Send Intent
    results["4_whatsapp_message"] = run_test("WhatsApp Message", "Send a WhatsApp message to John saying Hello")

    # 5. Check Emails
    results["5_check_emails"] = run_test("Check Emails", "Check my emails")

    # 6. Calendar Check
    results["6_calendar_today"] = run_test("Calendar Today", "What's on my calendar today?")

    # 7. Schedule Meeting
    results["7_schedule_meeting"] = run_test("Schedule Meeting", "Schedule a test meeting tomorrow at 3 PM")

    # 8. Set Reminder
    results["8_set_reminder"] = run_test("Set Reminder", "Remind me tomorrow at 8 AM to check my project")

    # 9. Store Memory
    results["9_store_memory"] = run_test("Store Memory", "Remember that my main project is AgriMind AI")

    # 10. Recall Memory
    results["10_recall_memory"] = run_test("Recall Memory", "What is my main project?")

    # 11. Emergency Stop
    results["11_emergency_stop"] = run_test("Emergency Stop", "Jarvis, stop")

    print("\n\n##################################################")
    print("ALL REAL LIVE TESTS COMPLETED")
    print("##################################################")
