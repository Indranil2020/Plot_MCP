"""Tests for project manifest persistence."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from project_manifest import ProjectManifestManager
from project_manager import ProjectManager


class TestProjectManifest(unittest.TestCase):
    """Verify dataset registration in project manifest."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_manager = ProjectManager(base_dir=self.temp_dir.name)
        self.manifest_manager = ProjectManifestManager(base_dir=self.temp_dir.name)
        self.project_manager.create_project("Demo")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_register_dataset(self) -> None:
        project_path = self.project_manager.get_project_path("Demo")
        file_path = os.path.join(project_path, "data.csv")
        with open(file_path, "w") as f:
            f.write("x,y\n1,2\n3,4\n")

        manifest = self.manifest_manager.ensure_manifest("Demo")
        self.assertEqual(manifest["project"]["name"], "Demo")

        dataset = self.manifest_manager.register_dataset("Demo", file_path)
        self.assertEqual(dataset["name"], "data.csv")

        updated = self.manifest_manager.load_manifest("Demo")
        self.assertEqual(len(updated["datasets"]), 1)
        self.assertEqual(updated["datasets"][0]["name"], "data.csv")
