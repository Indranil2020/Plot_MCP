"""Tests for SessionManager persistence."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from session_manager import SessionManager


class TestSessionManager(unittest.TestCase):
    """Validate session creation and message storage."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = SessionManager(base_dir=self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_session_lifecycle(self) -> None:
        session = self.manager.create_session("Test Chat", "ProjectA")
        session_id = session["id"]

        self.manager.append_message(session_id, "user", "Hello")
        self.manager.append_message(session_id, "assistant", "Hi there")

        messages = self.manager.get_messages(session_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], "Hello")

        self.manager.update_session_context(session_id, "ProjectB", ["/tmp/data.csv"])
        session_data = self.manager.get_session(session_id)
        self.assertEqual(session_data["project_name"], "ProjectB")
        self.assertEqual(session_data["selected_files"], ["/tmp/data.csv"])

        sessions = self.manager.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["id"], session_id)

    def test_auto_titles_from_first_user_message(self) -> None:
        session = self.manager.create_session(project_name="ProjectA")
        session_id = session["id"]
        self.assertEqual(session["title"], SessionManager.DEFAULT_TITLE)

        self.manager.append_message(session_id, "user", "Plot sine wave with 5 peaks")
        session_data = self.manager.get_session(session_id)
        self.assertEqual(session_data["title"], "Plot sine wave with 5 peaks")
