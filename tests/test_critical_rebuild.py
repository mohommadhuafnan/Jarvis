import unittest
import time
from datetime import datetime, timedelta
from backend.kernel.planner import planner, parse_natural_datetime
from backend.services.scheduler_service import SchedulerService, scheduler_service
from backend.services.google_oauth_service import google_oauth_service
from backend.kernel.agent_kernel import agent_kernel

class TestCriticalReliabilityRebuild(unittest.TestCase):

    def test_01_natural_datetime_parsing_tomorrow_early_morning(self):
        """Test parsing 'Tomorrow I have a meeting at 4:30 AM. Remind me.'"""
        dt = parse_natural_datetime("Tomorrow I have a meeting at 4:30 AM. Remind me.")
        self.assertEqual(dt["display_date"], "tomorrow")
        self.assertEqual(dt["display_time"], "4:30 AM")
        self.assertIn("04:30:00", dt["iso_start"])

    def test_02_natural_datetime_parsing_relative_minutes(self):
        """Test parsing 'Remind me in 10 minutes to review code'"""
        now = datetime.now()
        dt = parse_natural_datetime("Remind me in 10 minutes to review code")
        self.assertTrue(any(d in dt["display_date"].lower() for d in ["today", "tomorrow"]))
        # Should be ~10 minutes from now
        target_dt = datetime.fromisoformat(dt["due_at"])
        diff_sec = abs((target_dt - (now + timedelta(minutes=10))).total_seconds())
        self.assertLess(diff_sec, 5)

    def test_03_planner_compound_calendar_and_reminder(self):
        """Test planner splits 'Tomorrow I have a meeting at 4:30 AM. Remind me.' into both Calendar and Reminder tools."""
        plan = planner.plan_task("Tomorrow I have a meeting at 4:30 AM. Remind me.")
        self.assertTrue(plan.is_multi_step)
        tool_names = [s.tool_name for s in plan.steps]
        self.assertIn("calendar.createEvent", tool_names)
        self.assertIn("tasks.create_reminder", tool_names)

        # Check arguments
        cal_step = next(s for s in plan.steps if s.tool_name == "calendar.createEvent")
        self.assertIn("04:30:00", cal_step.arguments.get("start_time", ""))

        rem_step = next(s for s in plan.steps if s.tool_name == "tasks.create_reminder")
        self.assertIn("4:30 AM", rem_step.arguments.get("reminder_time", ""))

    def test_04_scheduler_daemon_add_and_due_detection(self):
        """Test background scheduler adds reminder, detects when due, and marks delivered."""
        test_sched = SchedulerService()
        past_iso = (datetime.now() - timedelta(seconds=5)).isoformat()
        res = test_sched.add_reminder(
            title="Team Standup",
            reminder_time="4:30 AM",
            due_at=past_iso
        )
        self.assertTrue(res.get("success"))

        # Trigger scheduler check
        test_sched._check_due_reminders()

        # Verify that reminder was detected and marked as delivered
        from backend.database.db import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT delivered FROM scheduled_reminders WHERE id = ?", (res["id"],))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["delivered"], 1)

    def test_05_scheduler_recovery_across_restart(self):
        """Test that pending reminders survive restart by creating a new scheduler instance."""
        future_iso = (datetime.now() + timedelta(hours=5)).isoformat()
        res = scheduler_service.add_reminder(
            title="Design Review",
            reminder_time="Tomorrow at 10 AM",
            due_at=future_iso
        )
        self.assertTrue(res.get("success"))

        # Simulate service restart by instantiating a fresh SchedulerService
        fresh_scheduler = SchedulerService()
        all_reminders = fresh_scheduler.get_all_reminders()
        found = any(r["id"] == res["id"] for r in all_reminders)
        self.assertTrue(found, "Pending reminder must be recovered from persistent database after restart.")

    def test_06_real_gmail_sync_state(self):
        """Test that list_all_or_cached_emails returns structured email items."""
        emails = google_oauth_service.list_all_or_cached_emails()
        self.assertIsInstance(emails, list)
        if emails:
            sample = emails[0]
            self.assertIn("subject", sample)
            self.assertIn("from", sample)

    def test_07_agent_kernel_truthful_stop(self):
        """Test agent kernel emergency stop returns truthful ready response."""
        res = agent_kernel.process_command("Jarvis, stop")
        self.assertIn("reply", res)
        self.assertTrue("Boss" in res["reply"] and any(w in res["reply"].lower() for w in ["halted", "stopped", "ready"]))

if __name__ == "__main__":
    unittest.main()
