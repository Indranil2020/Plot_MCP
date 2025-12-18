"""Tests for join assistant suggestions."""

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from join_assistant import JoinAssistant


class TestJoinAssistant(unittest.TestCase):
    """Ensure join suggestions are produced for common keys."""

    def setUp(self) -> None:
        self.assistant = JoinAssistant()

    def test_suggests_join_on_shared_key(self) -> None:
        left = pd.DataFrame({"id": [1, 2], "value": [10, 20]})
        right = pd.DataFrame({"id": [1, 2], "score": [5, 6]})
        suggestions = self.assistant.suggest_joins({"df_left": left, "df_right": right})
        self.assertTrue(suggestions["suggestions"])
        self.assertEqual(suggestions["suggestions"][0]["key"], "id")
