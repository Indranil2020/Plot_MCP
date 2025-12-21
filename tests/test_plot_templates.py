"""Tests for deterministic plot templates."""

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from plot_templates import maybe_generate_template_plot


class TestPlotTemplates(unittest.TestCase):
    """Ensure template plots are generated for common wave requests."""

    def test_generates_sawtooth_wave(self) -> None:
        plot = maybe_generate_template_plot("plot me swattooth wave")
        self.assertIsNotNone(plot)
        assert plot is not None
        self.assertIn("saw", plot.code)
        self.assertIn("np.floor", plot.code)

    def test_generates_multiple_waves(self) -> None:
        plot = maybe_generate_template_plot("sine wave and cos wave and sqaure wave")
        self.assertIsNotNone(plot)
        assert plot is not None
        self.assertIn("np.sin", plot.code)
        self.assertIn("np.cos", plot.code)
        self.assertIn("square", plot.code)
