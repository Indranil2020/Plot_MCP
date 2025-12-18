"""Tests for deterministic gallery adapters."""

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from gallery_adapters import extract_gallery_example_title, maybe_adapt_gallery_example


class TestGalleryAdapters(unittest.TestCase):
    """Ensure gallery adapters generate executable code."""

    def test_extracts_gallery_title(self) -> None:
        title = extract_gallery_example_title(
            "Create a plot based on this example: Curve Error Band. Adapt it to my data."
        )
        self.assertEqual(title, "Curve Error Band")

    def test_curve_error_band_adapter_uses_columns(self) -> None:
        analysis = {
            "columns": ["time", "value", "error"],
            "numeric_cols": ["time", "value", "error"],
            "datetime_cols": [],
        }
        adaptation = maybe_adapt_gallery_example("Curve Error Band", data_analysis=analysis)
        self.assertIsNotNone(adaptation)
        assert adaptation is not None
        self.assertIn("fill_between", adaptation.code)
        self.assertIn("'time'", adaptation.code)
        self.assertIn("'value'", adaptation.code)
        self.assertNotIn("...", adaptation.code)

    def test_curve_error_band_adapter_synthetic_fallback(self) -> None:
        adaptation = maybe_adapt_gallery_example("Curve Error Band")
        self.assertIsNotNone(adaptation)
        assert adaptation is not None
        self.assertIn("np.linspace", adaptation.code)
        self.assertIn("fill_between", adaptation.code)
