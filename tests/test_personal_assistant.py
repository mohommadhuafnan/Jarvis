import unittest
from backend.services.google_oauth_service import google_oauth_service
from backend.kernel.planner import planner
from backend.kernel.agent_kernel import agent_kernel
from backend.services.memory_service import memory_service

class TestJarvisPersonalAssistant(unittest.TestCase):

    def test_01_google_oauth_status(self):
        """Test that Google OAuth status is configured and reports truthfully."""
        status = google_oauth_service.get_status()
        self.assertIn("configured", status)
        self.assertIn("connected", status)
        self.assertIn("account", status)

    def test_02_truthful_gmail_disconnected_state(self):
        """Test that unread emails report truthfully when not yet authorized."""
        if not google_oauth_service.is_connected():
            res = google_oauth_service.list_unread_emails()
            self.assertFalse(res.get("connected", True))
            self.assertIn("not connected", res.get("message", "").lower())

    def test_03_planner_emergency_stop(self):
        """Test that 'Jarvis, stop' generates Emergency Stop plan."""
        plan = planner.plan_task("Jarvis, stop")
        self.assertEqual(plan.title, "Emergency Stop")

    def test_04_planner_memory_store(self):
        """Test that 'Jarvis, remember that my main project is AgriMind AI' maps to memory.store."""
        plan = planner.plan_task("Jarvis, remember that my main project is AgriMind AI")
        self.assertEqual(plan.steps[0].tool_name, "memory.store")
        self.assertEqual(plan.steps[0].arguments.get("key"), "main_project")
        self.assertEqual(plan.steps[0].arguments.get("value"), "AgriMind AI")

    def test_05_planner_memory_recall(self):
        """Test that 'What is my main project?' maps to memory.search."""
        plan = planner.plan_task("What is my main project?")
        self.assertEqual(plan.steps[0].tool_name, "memory.search")

    def test_06_memory_service_store_and_search(self):
        """Test storing and searching memory via MemoryService."""
        store_res = memory_service.store_memory(
            key="main_project",
            value="AgriMind AI",
            memory_type="projects"
        )
        self.assertTrue(store_res.get("success", False))

        search_res = memory_service.search_memory(query="main_project")
        self.assertTrue(len(search_res) > 0)
        self.assertEqual(search_res[0].get("value"), "AgriMind AI")

    def test_07_agent_kernel_memory_store_execution(self):
        """Test full Agent Kernel process of memory store command."""
        res = agent_kernel.process_command("Jarvis, remember that my main project is AgriMind AI")
        self.assertIn("reply", res)
        self.assertEqual(res.get("tool_used"), "memory.store")

    def test_08_agent_kernel_memory_recall_execution(self):
        """Test full Agent Kernel recall of stored memory."""
        res = agent_kernel.process_command("What is my main project?")
        self.assertIn("reply", res)
        self.assertIn("AgriMind AI", res["reply"])

    def test_09_agent_kernel_honest_gmail_response(self):
        """Test that Agent Kernel produces honest, non-fake response for email check."""
        res = agent_kernel.process_command("Jarvis, check my email")
        self.assertIn("reply", res)
        self.assertNotIn("12 unread emails", res["reply"])

    def test_10_agent_kernel_honest_calendar_response(self):
        """Test that Agent Kernel produces honest response for calendar check."""
        res = agent_kernel.process_command("What's on my calendar?")
        self.assertIn("reply", res)

    def test_11_planner_open_chrome(self):
        """Test that 'Open Chrome' maps to computer.openApplication."""
        plan = planner.plan_task("Open Chrome")
        self.assertEqual(plan.steps[1].tool_name, "computer.openApplication")
        self.assertEqual(plan.steps[1].arguments.get("application"), "chrome")

    def test_12_planner_open_whatsapp(self):
        """Test that 'Open WhatsApp' maps to whatsapp.open."""
        plan = planner.plan_task("Open WhatsApp")
        self.assertEqual(plan.steps[0].tool_name, "whatsapp.open")

    def test_13_planner_whatsapp_message(self):
        """Test that 'Send a WhatsApp message to John saying I will arrive at 5' maps to whatsapp.send_message."""
        plan = planner.plan_task("Send a WhatsApp message to John saying I'll be there at 5")
        self.assertEqual(plan.steps[1].tool_name, "whatsapp.send_message")
        self.assertEqual(plan.steps[1].arguments.get("recipient"), "John")

    def test_14_planner_reminder_at_time(self):
        """Test that 'Remind me at 8 PM to work on AgriMind' maps to tasks.create_reminder."""
        plan = planner.plan_task("Remind me at 8 PM to work on AgriMind")
        self.assertEqual(plan.steps[0].tool_name, "tasks.create_reminder")
        self.assertIn("8 PM", plan.steps[0].arguments.get("reminder_time", ""))

    def test_15_agent_kernel_reminder_execution(self):
        """Test Agent Kernel sets reminder and speaks confirmation."""
        res = agent_kernel.process_command("Remind me at 8 PM to work on AgriMind")
        self.assertIn("reply", res)
        self.assertIn("reminder", res["reply"].lower())

if __name__ == "__main__":
    unittest.main()
