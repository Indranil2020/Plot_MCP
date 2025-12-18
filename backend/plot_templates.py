"""Deterministic plot templates for common data-free requests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class TemplatePlot:
    """Result for a template-based plot generation."""

    code: str
    description: str


_PEAK_PATTERN = re.compile(r"(?P<count>\d+)\s*(peaks?|cycles?|periods?)")

_WAVE_HINTS = {
    "sine": ("sine", "sin"),
    "cosine": ("cosine", "cos"),
    "square": ("square", "squarewave", "square-wave"),
    "sawtooth": ("sawtooth", "saw-tooth", "saw tooth", "swattooth", "swat tooth"),
}


def maybe_generate_template_plot(query: str) -> Optional[TemplatePlot]:
    """Return a deterministic template plot for common math-only requests.

    This is intentionally conservative: it triggers only when the request is
    clearly data-free (e.g. sine/cosine waves) and avoids random output unless
    explicitly requested.
    """
    normalized = " ".join((query or "").strip().lower().split())
    if not normalized:
        return None

    waves = _detect_waves(normalized)
    if waves:
        peaks = _extract_peaks(normalized) or 5
        code = _multi_wave_code(waves=waves, peaks=peaks)
        description = _format_wave_description(waves, peaks)
        return TemplatePlot(code=code, description=description)

    return None


def _extract_peaks(normalized_query: str) -> Optional[int]:
    match = _PEAK_PATTERN.search(normalized_query)
    if not match:
        return None
    count_text = match.group("count")
    if not count_text.isdigit():
        return None
    count = int(count_text)
    if count <= 0:
        return None
    return min(count, 50)


def _detect_waves(normalized_query: str) -> List[str]:
    detected: List[str] = []

    for wave_name, hints in _WAVE_HINTS.items():
        if wave_name in {"sine", "cosine"}:
            continue

        if any(hint in normalized_query for hint in hints):
            detected.append(wave_name)

    if "sine" in normalized_query or re.search(r"\bsin\b", normalized_query):
        detected.insert(0, "sine")
    if "cosine" in normalized_query or re.search(r"\bcos\b", normalized_query):
        if "cosine" not in detected:
            detected.append("cosine")

    unique: List[str] = []
    for item in detected:
        if item not in unique:
            unique.append(item)
    return unique


def _format_wave_description(waves: Sequence[str], peaks: int) -> str:
    title = ", ".join(waves)
    return f"Waves: {title} ({peaks} peaks)"


def _multi_wave_code(waves: Sequence[str], peaks: int) -> str:
    color_map = {
        "sine": "#1f77b4",
        "cosine": "#ff7f0e",
        "square": "#22c55e",
        "sawtooth": "#a855f7",
    }

    lines = [
        "plt.style.use('seaborn-v0_8-whitegrid')",
        f"x = np.linspace(0, 2 * np.pi * {peaks}, 2500)",
        "fig, ax = plt.subplots(figsize=(10, 4))",
    ]

    for wave in waves:
        color = color_map.get(wave, "#1f77b4")
        if wave == "sine":
            lines.append(f"ax.plot(x, np.sin(x), linewidth=2.0, color={color!r}, label='sine')")
        elif wave == "cosine":
            lines.append(f"ax.plot(x, np.cos(x), linewidth=2.0, color={color!r}, label='cosine')")
        elif wave == "square":
            lines.append("square = np.where(np.sin(x) >= 0, 1.0, -1.0)")
            lines.append(
                f"ax.plot(x, square, linewidth=2.0, color={color!r}, label='square')"
            )
        elif wave == "sawtooth":
            lines.append("phase = x / (2 * np.pi)")
            lines.append("saw = 2.0 * (phase - np.floor(phase + 0.5))")
            lines.append(
                f"ax.plot(x, saw, linewidth=2.0, color={color!r}, label='sawtooth')"
            )

    lines.extend(
        [
            "ax.set_title('Waves')",
            "ax.set_xlabel('x')",
            "ax.set_ylabel('amplitude')",
            "ax.set_ylim(-1.25, 1.25)",
            "ax.legend(loc='best', ncol=min(4, len(ax.get_lines())))",
            "fig.tight_layout()",
        ]
    )
    return "\n".join(lines)
