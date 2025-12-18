"""Tests for code safety validator."""

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from code_safety import CodeSafetyValidator


class TestCodeSafetyValidator(unittest.TestCase):
    """Validate linting behavior for unsafe constructs."""

    def setUp(self) -> None:
        self.validator = CodeSafetyValidator()

    def test_allows_simple_plot(self) -> None:
        code = "plt.plot([1,2], [3,4])"
        result = self.validator.lint(code)
        self.assertTrue(result.ok)

    def test_blocks_os_import(self) -> None:
        code = "import os\nos.listdir('.')"
        result = self.validator.lint(code)
        self.assertFalse(result.ok)
        self.assertTrue(any("Import not allowed" in error for error in result.errors))

    def test_blocks_read_csv(self) -> None:
        code = "pd.read_csv('data.csv')"
        result = self.validator.lint(code)
        self.assertFalse(result.ok)

    def test_blocks_ellipsis_placeholder(self) -> None:
        code = "x = ...\nplt.plot(x, [1, 2, 3])"
        result = self.validator.lint(code)
        self.assertFalse(result.ok)
        self.assertTrue(any("Placeholder" in error for error in result.errors))
