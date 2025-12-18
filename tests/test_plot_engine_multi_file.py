"""Tests for multi-file plot execution."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from file_utils import build_alias_map
from plot_engine import PlotEngine


class TestPlotEngineMultiFile(unittest.TestCase):
    """Ensure PlotEngine can execute code with multiple dataframes."""

    def setUp(self) -> None:
        os.environ["PLOT_EXEC_MEMORY_MB"] = "0"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = PlotEngine()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_execute_with_multiple_files(self) -> None:
        file_one = os.path.join(self.temp_dir.name, "first.csv")
        file_two = os.path.join(self.temp_dir.name, "second.csv")

        with open(file_one, "w") as f:
            f.write("x,y\n1,2\n2,3\n")
        with open(file_two, "w") as f:
            f.write("x,y\n1,4\n2,6\n")

        alias_map = build_alias_map([file_one, file_two])
        aliases = list(alias_map.keys())

        code = "\n".join(
            [
                "import matplotlib.pyplot as plt",
                "plt.figure()",
                f"plt.plot({aliases[0]}['x'], {aliases[0]}['y'], label='A')",
                f"plt.plot({aliases[1]}['x'], {aliases[1]}['y'], label='B')",
                "plt.legend()",
            ]
        )

        result = self.engine.execute_code(code, [file_one, file_two], file_aliases=alias_map)
        self.assertIn("image", result)
        self.assertTrue(result["image"])
