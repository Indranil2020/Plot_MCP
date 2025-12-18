"""Sandboxed plot execution runner (spawned in a subprocess)."""

from __future__ import annotations

import json
import os
import sys
import warnings
from typing import Dict

warnings.filterwarnings("ignore", message="Unable to import Axes3D.*")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ALLOWED_IMPORTS = {
    "matplotlib",
    "matplotlib.pyplot",
    "pandas",
    "numpy",
    "seaborn",
}


def main() -> None:
    payload_path = _get_payload_path()
    with open(payload_path, "r") as f:
        payload = json.load(f)

    code = payload.get("code", "")
    data_paths = payload.get("data_paths", {})
    output_image = payload.get("output_image")
    output_metadata = payload.get("output_metadata")
    dpi = int(payload.get("dpi", 300))
    image_format = payload.get("format", "png")
    memory_limit_mb = int(payload.get("memory_limit_mb", 512))

    _apply_resource_limits(memory_limit_mb)
    _setup_fonts()

    dataframes = _load_dataframes(data_paths)
    default_df = next(iter(dataframes.values()), pd.DataFrame())

    safe_globals = {
        "__builtins__": _safe_builtins(),
        "plt": plt,
        "pd": pd,
        "sns": sns,
        "np": np,
    }
    local_vars = {
        "df": default_df,
        "dfs": dataframes,
        "dataframes": dataframes,
    }
    local_vars.update(dataframes)

    exec(code, safe_globals, local_vars)

    fig = plt.gcf()
    if os.getenv("PLOT_ENFORCE_STYLE", "0") == "1":
        _apply_styling_to_figure(fig)
    plt.savefig(output_image, format=image_format, dpi=dpi, bbox_inches="tight")

    metadata = _extract_plot_metadata(fig)
    with open(output_metadata, "w") as f:
        json.dump(metadata, f)


def _get_payload_path() -> str:
    if "--payload" in sys.argv:
        idx = sys.argv.index("--payload")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    raise ValueError("Missing payload path")


def _apply_resource_limits(memory_limit_mb: int) -> None:
    if os.name == "nt":
        return
    import resource

    if memory_limit_mb <= 0:
        return

    bytes_limit = memory_limit_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))


def _safe_builtins() -> Dict[str, object]:
    allowed = {
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "list": list,
        "dict": dict,
        "set": set,
        "float": float,
        "int": int,
        "str": str,
        "print": print,
    }
    allowed["__import__"] = _safe_import
    return allowed


def _safe_import(name: str, globals=None, locals=None, fromlist=(), level: int = 0):
    if name not in ALLOWED_IMPORTS:
        raise ValueError(f"Import not allowed: {name}")
    import importlib

    return importlib.import_module(name)


def _load_dataframes(data_paths: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    dataframes: Dict[str, pd.DataFrame] = {}
    for alias, path in data_paths.items():
        if path.endswith(".csv"):
            dataframes[alias] = pd.read_csv(path)
        elif path.endswith(".json"):
            dataframes[alias] = pd.read_json(path)
        else:
            dataframes[alias] = pd.DataFrame()
    return dataframes


def _setup_fonts() -> None:
    from matplotlib import font_manager

    font_files = [
        "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Italic.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold_Italic.ttf",
    ]

    fonts_found = False
    for font_file in font_files:
        if os.path.exists(font_file):
            font_manager.fontManager.addfont(font_file)
            fonts_found = True

    plt.rcParams["font.family"] = "Times New Roman" if fonts_found else "serif"

    line_width = 1.5
    font_size = 12

    plt.rcParams.update(
        {
            "axes.linewidth": line_width,
            "xtick.major.width": line_width,
            "ytick.major.width": line_width,
            "xtick.minor.width": 1.0,
            "ytick.minor.width": 1.0,
            "xtick.major.size": 6,
            "ytick.major.size": 6,
            "xtick.minor.size": 3,
            "ytick.minor.size": 3,
            "xtick.labelsize": font_size,
            "ytick.labelsize": font_size,
            "axes.labelsize": font_size,
            "legend.fontsize": font_size,
            "axes.titlesize": font_size,
            "figure.titlesize": font_size,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "xtick.bottom": True,
            "ytick.left": True,
            "ytick.right": True,
            "axes.grid.which": "both",
            "axes.spines.left": True,
            "axes.spines.bottom": True,
            "axes.spines.top": True,
            "axes.spines.right": True,
        }
    )


def _apply_styling_to_figure(fig):
    for ax in fig.axes:
        ax.minorticks_on()
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(plt.rcParams.get("axes.linewidth", 1.5))
        label_size = int(plt.rcParams.get("xtick.labelsize", 12))
        ax.tick_params(
            axis="both",
            which="major",
            direction="in",
            length=6,
            width=plt.rcParams.get("xtick.major.width", 1.5),
            labelsize=label_size,
        )
        ax.tick_params(
            axis="both",
            which="minor",
            direction="in",
            length=3,
            width=plt.rcParams.get("xtick.minor.width", 1.0),
        )
        ax.tick_params(top=True, bottom=True, left=True, right=True, labeltop=False, labelbottom=True, labelleft=True, labelright=False)


def _extract_plot_metadata(fig):
    metadata = []
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def get_relative_bbox(artist, label_type):
        bbox = artist.get_window_extent(renderer)
        inv = fig.transFigure.inverted()
        bbox_fig = bbox.transformed(inv)
        return {
            "type": label_type,
            "text": artist.get_text() if hasattr(artist, "get_text") else "",
            "bbox": [bbox_fig.x0, bbox_fig.y0, bbox_fig.width, bbox_fig.height],
        }

    for ax in fig.axes:
        if ax.get_title():
            metadata.append(get_relative_bbox(ax.title, "title"))
        if ax.get_xlabel():
            metadata.append(get_relative_bbox(ax.xaxis.label, "xlabel"))
        if ax.get_ylabel():
            metadata.append(get_relative_bbox(ax.yaxis.label, "ylabel"))
        legend = ax.get_legend()
        if legend:
            bbox = legend.get_window_extent(renderer)
            inv = fig.transFigure.inverted()
            bbox_fig = bbox.transformed(inv)
            metadata.append(
                {
                    "type": "legend",
                    "text": "Legend",
                    "bbox": [bbox_fig.x0, bbox_fig.y0, bbox_fig.width, bbox_fig.height],
                }
            )

    return metadata


if __name__ == "__main__":
    main()
