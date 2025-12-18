"""Deterministic adapters for selected Matplotlib gallery examples.

The plotting sandbox intentionally blocks file/network access and restricts
imports. Many upstream Matplotlib gallery examples rely on external assets or
complex setup. For the UI "Gallery" feature, we provide small, robust adapters
for high-impact examples so they work reliably with user datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class GalleryAdaptation:
    """Result of adapting a gallery example to user data."""

    code: str
    description: str


_GALLERY_PHRASES = (
    "based on this example:",
    "apply example:",
    "example:",
)


def extract_gallery_example_title(query: str) -> Optional[str]:
    """Extract the requested gallery example title from a chat query."""
    normalized = " ".join((query or "").strip().split())
    if not normalized:
        return None

    lowered = normalized.lower()
    for phrase in _GALLERY_PHRASES:
        idx = lowered.find(phrase)
        if idx == -1:
            continue
        remainder = normalized[idx + len(phrase) :].strip()
        if not remainder:
            continue
        title = _split_title(remainder)
        if title:
            return title
    return None


def maybe_adapt_gallery_example(
    example_title: str,
    data_analysis: Optional[Dict[str, object]] = None,
    file_catalog: Optional[List[Dict[str, object]]] = None,
) -> Optional[GalleryAdaptation]:
    """Return adapted plot code for supported examples."""
    normalized_title = _normalize_title(example_title)
    if not normalized_title:
        return None

    analysis = _get_primary_analysis(data_analysis, file_catalog)

    if normalized_title == "curve error band":
        code = _curve_error_band_code(analysis)
        if analysis is None:
            description = "Curve Error Band (synthetic)"
        else:
            x_col, y_col, err_col, _ = _choose_error_band_columns(analysis)
            description = (
                "Curve Error Band"
                f" (x={x_col or 'index'}, y={y_col or 'unknown'}, err={err_col or 'derived'})"
            )
        return GalleryAdaptation(code=code, description=description)

    return None


def generate_gallery_fallback_plot(
    data_analysis: Optional[Dict[str, object]] = None,
    file_catalog: Optional[List[Dict[str, object]]] = None,
) -> Optional[GalleryAdaptation]:
    """Generate a generic plot fallback when an example adaptation fails."""
    analysis = _get_primary_analysis(data_analysis, file_catalog)
    if not analysis:
        return None
    code = _basic_line_plot_code(analysis)
    return GalleryAdaptation(code=code, description="Basic line plot (fallback)")


def _normalize_title(title: str) -> str:
    return " ".join((title or "").strip().lower().split())


def _split_title(text: str) -> str:
    for separator in (".", "\n", "\r"):
        if separator in text:
            text = text.split(separator, 1)[0]
    return text.strip()


def _get_primary_analysis(
    data_analysis: Optional[Dict[str, object]],
    file_catalog: Optional[List[Dict[str, object]]],
) -> Optional[Dict[str, object]]:
    if data_analysis:
        return data_analysis
    if not file_catalog:
        return None
    first = file_catalog[0]
    analysis = first.get("analysis")
    if isinstance(analysis, dict):
        return analysis
    return None


def _curve_error_band_code(analysis: Optional[Dict[str, object]]) -> str:
    """Generate a robust error-band plot for user data (or synthetic fallback)."""
    if not analysis:
        return _curve_error_band_synthetic_code()

    x_col, y_col, err_col, x_kind = _choose_error_band_columns(analysis)

    preamble = [
        "plt.style.use('seaborn-v0_8-whitegrid')",
        "df_local = df.copy()",
    ]

    x_lines: List[str] = []
    y_lines: List[str] = []

    if x_col:
        if x_kind == "datetime":
            x_lines.append(f"x = pd.to_datetime(df_local[{x_col!r}], errors='coerce')")
        else:
            x_lines.append(f"x = pd.to_numeric(df_local[{x_col!r}], errors='coerce')")
    else:
        x_lines.append("x = pd.Series(np.arange(len(df_local)))")

    if y_col:
        y_lines.append(f"y = pd.to_numeric(df_local[{y_col!r}], errors='coerce')")
    else:
        y_lines.append("y = pd.Series(dtype=float)")

    err_lines: List[str] = []
    if err_col:
        err_lines.append(f"y_err = pd.to_numeric(df_local[{err_col!r}], errors='coerce').abs()")
    else:
        err_lines.append("y_err = 0.1 * y.abs()")

    cleanup = [
        "mask = (~x.isna()) & (~y.isna()) & (~y_err.isna())",
        "x = x[mask]",
        "y = y[mask]",
        "y_err = y_err[mask]",
        "df_plot = pd.DataFrame({'x': x, 'y': y, 'y_err': y_err})",
    ]

    plotting = [
        "df_plot = df_plot.sort_values('x')",
        "if df_plot.empty:",
        "    fig, ax = plt.subplots(figsize=(10, 4))",
        "    ax.text(0.5, 0.5, 'No plottable numeric data after cleaning.', ha='center', va='center')",
        "    ax.set_axis_off()",
        "else:",
        "    x = df_plot['x']",
        "    y = df_plot['y']",
        "    y_err = df_plot['y_err']",
        "    fig, ax = plt.subplots(figsize=(10, 4))",
        "    ax.plot(x, y, color='#1f77b4', linewidth=2.0, label='value')",
        "    ax.fill_between(x, y - y_err, y + y_err, color='#1f77b4', alpha=0.22, label='error band')",
        "    ax.set_title('Curve with error band')",
        "    ax.set_xlabel('x')",
        "    ax.set_ylabel('y')",
        "    ax.legend(loc='best')",
    ]

    if x_kind == "datetime":
        plotting.append("    fig.autofmt_xdate()")

    plotting.append("fig.tight_layout()")

    return "\n".join(preamble + x_lines + y_lines + err_lines + cleanup + plotting)


def _curve_error_band_synthetic_code() -> str:
    return "\n".join(
        [
            "plt.style.use('seaborn-v0_8-whitegrid')",
            "x = np.linspace(0, 10, 600)",
            "y = np.sin(2 * np.pi * x / 2.0)",
            "y_err = 0.15 + 0.05 * np.cos(2 * np.pi * x / 1.5)",
            "fig, ax = plt.subplots(figsize=(10, 4))",
            "ax.plot(x, y, color='#1f77b4', linewidth=2.0, label='signal')",
            "ax.fill_between(x, y - y_err, y + y_err, color='#1f77b4', alpha=0.22, label='error band')",
            "ax.set_title('Curve with error band (synthetic)')",
            "ax.set_xlabel('x')",
            "ax.set_ylabel('y')",
            "ax.legend(loc='best')",
            "fig.tight_layout()",
        ]
    )


def _choose_error_band_columns(
    analysis: Dict[str, object],
) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    columns = analysis.get("columns", [])
    numeric_cols = analysis.get("numeric_cols", [])
    datetime_cols = analysis.get("datetime_cols", [])

    resolved_columns = [c for c in columns if isinstance(c, str)]
    resolved_numeric = [c for c in numeric_cols if isinstance(c, str)]
    resolved_datetime = [c for c in datetime_cols if isinstance(c, str)]

    if resolved_datetime and resolved_numeric:
        x_col = resolved_datetime[0]
        y_col = resolved_numeric[0]
        err_col = resolved_numeric[1] if len(resolved_numeric) > 1 else None
        return x_col, y_col, err_col, "datetime"

    if len(resolved_numeric) >= 2:
        x_col = resolved_numeric[0]
        y_col = resolved_numeric[1]
        err_col = resolved_numeric[2] if len(resolved_numeric) > 2 else None
        return x_col, y_col, err_col, "numeric"

    if len(resolved_numeric) == 1:
        y_col = resolved_numeric[0]
        return None, y_col, None, "index"

    y_col = resolved_columns[0] if resolved_columns else None
    return None, y_col, None, "index"


def _basic_line_plot_code(analysis: Dict[str, object]) -> str:
    columns = analysis.get("columns", [])
    numeric_cols = analysis.get("numeric_cols", [])
    datetime_cols = analysis.get("datetime_cols", [])

    resolved_columns = [c for c in columns if isinstance(c, str)]
    resolved_numeric = [c for c in numeric_cols if isinstance(c, str)]
    resolved_datetime = [c for c in datetime_cols if isinstance(c, str)]

    x_expr = "pd.Series(np.arange(len(df_local)))"
    x_label = "index"
    if resolved_datetime:
        x_expr = f"pd.to_datetime(df_local[{resolved_datetime[0]!r}], errors='coerce')"
        x_label = resolved_datetime[0]
    elif len(resolved_numeric) >= 2:
        x_expr = f"pd.to_numeric(df_local[{resolved_numeric[0]!r}], errors='coerce')"
        x_label = resolved_numeric[0]

    y_col = None
    if resolved_datetime and resolved_numeric:
        y_col = resolved_numeric[0]
    elif len(resolved_numeric) >= 2:
        y_col = resolved_numeric[1]
    elif len(resolved_numeric) == 1:
        y_col = resolved_numeric[0]
    elif resolved_columns:
        y_col = resolved_columns[0]

    y_expr = "pd.Series(dtype=float)"
    y_label = "value"
    if y_col:
        y_expr = f"pd.to_numeric(df_local[{y_col!r}], errors='coerce')"
        y_label = y_col

    return "\n".join(
        [
            "plt.style.use('seaborn-v0_8-whitegrid')",
            "df_local = df.copy()",
            f"x = {x_expr}",
            f"y = {y_expr}",
            "mask = (~x.isna()) & (~y.isna())",
            "x = x[mask]",
            "y = y[mask]",
            "df_plot = pd.DataFrame({'x': x, 'y': y}).sort_values('x')",
            "if df_plot.empty:",
            "    fig, ax = plt.subplots(figsize=(10, 4))",
            "    ax.text(0.5, 0.5, 'No plottable numeric data after cleaning.', ha='center', va='center')",
            "    ax.set_axis_off()",
            "else:",
            "    fig, ax = plt.subplots(figsize=(10, 4))",
            "    ax.plot(df_plot['x'], df_plot['y'], color='#1f77b4', linewidth=2.0)",
            "    ax.set_title('Plot')",
            f"    ax.set_xlabel({x_label!r})",
            f"    ax.set_ylabel({y_label!r})",
            "fig.tight_layout()",
        ]
    )
