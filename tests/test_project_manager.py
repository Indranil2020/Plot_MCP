"""Tests for the ProjectManager helper."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from project_manager import ProjectManager


class TestProjectManager(unittest.TestCase):
    """Validate project creation and file listing."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = ProjectManager(base_dir=self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_project_and_list_files(self) -> None:
        project = self.manager.create_project("Experiment")
        file_path = os.path.join(project["path"], "data.csv")
        with open(file_path, "w") as f:
            f.write("x,y\n1,2\n3,4\n")

        projects = self.manager.list_projects()
        self.assertIn("Experiment", projects)

        entries = self.manager.list_entries("Experiment", include_dirs=True)
        files = [entry for entry in entries if entry.get("type") == "file"]
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["name"], "data.csv")
