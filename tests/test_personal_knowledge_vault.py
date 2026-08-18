import unittest
import os
import datetime
from pathlib import Path
from backend.services.knowledge_service import KnowledgeService, knowledge_service
from backend.kernel.planner import planner
from backend.kernel.agent_kernel import agent_kernel

class TestPersonalKnowledgeVault(unittest.TestCase):

    def setUp(self):
        self.service = KnowledgeService()

    def test_01_save_extracted_timetable_knowledge(self):
        """Test committing extracted timetable knowledge into vault."""
        extracted_data = {
            "document_type": "timetable",
            "title": "Semester_Timetable.pdf",
            "summary": "Semester 1 Class Timetable with Monday and Tuesday classes.",
            "profile": {
                "degree": "BICT",
                "year": "2nd Year",
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

        res = self.service.save_extracted_knowledge(
            doc_id="doc_test_timetable_01",
            filename="Semester_Timetable.pdf",
            file_path="storage/vault/Semester_Timetable.pdf",
            extracted_data=extracted_data
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["timetable_count"], 3)
        self.assertEqual(res["facts_count"], 3)

    def test_02_query_monday_lectures(self):
        """Test retrieving Monday lectures from the active timetable."""
        res = self.service.get_today_lectures(target_weekday="Monday")
        self.assertTrue(res["success"])
        self.assertEqual(res["count"], 2)
        classes = res["classes"]
        self.assertEqual(classes[0]["subject"], "Network Switching and Routing")
        self.assertEqual(classes[0]["room"], "Lab 2")
        self.assertEqual(classes[1]["subject"], "Software Engineering")
        self.assertIn("Network Switching and Routing", res["spoken_summary"])
        self.assertIn("Lab 2", res["spoken_summary"])

    def test_03_query_empty_day_lectures(self):
        """Test retrieving lectures for a day with no classes."""
        res = self.service.get_today_lectures(target_weekday="Sunday")
        self.assertTrue(res["success"])
        self.assertEqual(res["count"], 0)
        self.assertIn("no lectures scheduled", res["spoken_summary"].lower())

    def test_04_personal_profile_retrieval(self):
        """Test structured personal profile retrieval."""
        profile = self.service.get_personal_profile()
        self.assertEqual(profile.get("degree"), "BICT")
        self.assertEqual(profile.get("year"), "2nd Year")
        self.assertEqual(profile.get("primary_project"), "AgriMind AI")

    def test_05_timetable_versioning_and_superseding(self):
        """Test that uploading a new timetable supersedes the older timetable."""
        new_extracted_data = {
            "document_type": "timetable",
            "title": "Semester_Timetable_New.pdf",
            "summary": "Revised Timetable with Updated Friday class.",
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

        res = self.service.save_extracted_knowledge(
            doc_id="doc_test_timetable_02",
            filename="Semester_Timetable_New.pdf",
            file_path="storage/vault/Semester_Timetable_New.pdf",
            extracted_data=new_extracted_data
        )

        self.assertTrue(res["success"])

        # Check that active timetable now contains the new Friday class and Monday classes are superseded
        fri_res = self.service.get_today_lectures(target_weekday="Friday")
        self.assertEqual(fri_res["count"], 1)
        self.assertEqual(fri_res["classes"][0]["subject"], "Cyber Defense Operations")

        mon_res = self.service.get_today_lectures(target_weekday="Monday")
        self.assertEqual(mon_res["count"], 0, "Old Monday classes should be superseded.")

    def test_06_planner_knowledge_routing(self):
        """Test planner routes timetable and lecture voice commands to knowledge tools."""
        plan1 = planner.plan_task("What lectures do I have today?")
        self.assertEqual(plan1.steps[0].tool_name, "knowledge.get_today_lectures")

        plan2 = planner.plan_task("When is my next class?")
        self.assertEqual(plan2.steps[0].tool_name, "knowledge.get_next_class")

        plan3 = planner.plan_task("What is my main project?")
        self.assertIn(plan3.steps[0].tool_name, ["knowledge.get_profile", "memory.search"])

    def test_07_agent_kernel_knowledge_synthesis(self):
        """Test agent kernel returns truthful spoken output for profile query."""
        res = agent_kernel.process_command("What is my main project?")
        self.assertIn("reply", res)
        self.assertIn("AgriMind AI", res["reply"])

    def test_08_anti_hallucination_for_unrecorded_facts(self):
        """Test that searching for an unknown fact returns truthful empty result."""
        res = self.service.search_vault("quantum_astrophysics_lab_grade")
        self.assertEqual(res["count"], 0)

    def test_09_forget_knowledge(self):
        """Test forgetting specific memory records."""
        self.service.update_personal_profile({"temporary_secret": "test_token_123"})
        res = self.service.forget_knowledge("test_token_123")
        self.assertTrue(res["success"])

    def test_10_restart_persistence(self):
        """Test that fresh KnowledgeService instance recovers all data from storage."""
        fresh_service = KnowledgeService()
        profile = fresh_service.get_personal_profile()
        self.assertEqual(profile.get("primary_project"), "AgriMind AI")
        fri_res = fresh_service.get_today_lectures(target_weekday="Friday")
        self.assertEqual(fri_res["count"], 1)

if __name__ == "__main__":
    unittest.main()
