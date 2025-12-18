"""API flow tests using direct endpoint calls."""

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path


class FakeUploadFile:
    """Minimal async upload file stub for tests."""

    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


class TestApiFlows(unittest.TestCase):
    """Verify project and multi-file API workflows."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["PROJECTS_DIR"] = self.temp_dir.name
        sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))
        if "main" in sys.modules:
            del sys.modules["main"]
        import main

        self.main = main

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_project_upload_and_join(self) -> None:
        create_request = self.main.ProjectRequest(name="Demo")
        asyncio.run(self.main.create_project(create_request))

        file_a = FakeUploadFile("a.csv", b"id,value\n1,10\n2,20\n")
        file_b = FakeUploadFile("b.csv", b"id,score\n1,5\n2,6\n")

        asyncio.run(self.main.upload_to_project("Demo", file_a))
        asyncio.run(self.main.upload_to_project("Demo", file_b))

        files_response = asyncio.run(self.main.list_project_files("Demo", recursive=False))
        datasets = files_response.get("datasets", [])
        self.assertEqual(len(datasets), 2)

        file_paths = [entry["path"] for entry in datasets]
        join_request = self.main.JoinRequest(selected_files=file_paths)
        join_payload = asyncio.run(self.main.join_suggestions(join_request))
        self.assertTrue(join_payload.get("suggestions"))

    def test_execute_plot_saves_history(self) -> None:
        create_request = self.main.ProjectRequest(name="Demo")
        asyncio.run(self.main.create_project(create_request))

        file_a = FakeUploadFile("a.csv", b"id,value\n1,10\n2,20\n")
        upload_response = asyncio.run(self.main.upload_to_project("Demo", file_a))
        file_path = upload_response["path"]

        code = "\n".join(
            [
                "fig, ax = plt.subplots(figsize=(6, 4))",
                "ax.plot(df['id'], df['value'], marker='o')",
                "ax.set_xlabel('id')",
                "ax.set_ylabel('value')",
                "ax.set_title('Demo plot')",
                "fig.tight_layout()",
            ]
        )

        request = self.main.ExecutePlotRequest(
            code=code,
            selected_files=[file_path],
            project_name="Demo",
            description="Unit test plot",
        )
        result = asyncio.run(self.main.execute_plot(request))
        self.assertFalse(result.get("error", False))
        self.assertTrue(result.get("plot"))
        self.assertTrue(result.get("plot_entry"))

        files_response = asyncio.run(self.main.list_project_files("Demo", recursive=False))
        plots = files_response.get("plots", [])
        self.assertEqual(len(plots), 1)
