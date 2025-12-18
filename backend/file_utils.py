"""Utility helpers for file aliasing in multi-file plots."""

from __future__ import annotations

import os
import re
from typing import Dict, Iterable

_ALIAS_PATTERN = re.compile(r"[^0-9A-Za-z_]+")


def sanitize_alias(file_path: str) -> str:
    """Return a lowercase, safe alias base derived from a file path."""
    filename = os.path.basename(file_path)
    base_name, _ = os.path.splitext(filename)
    cleaned = _ALIAS_PATTERN.sub("_", base_name).strip("_").lower()
    if not cleaned:
        cleaned = "dataset"
    if cleaned[0].isdigit():
        cleaned = f"data_{cleaned}"
    return cleaned


def build_alias_map(file_paths: Iterable[str], prefix: str = "df") -> Dict[str, str]:
    """Build a deterministic alias-to-path mapping for the provided file paths."""
    alias_map: Dict[str, str] = {}
    base_counts: Dict[str, int] = {}

    for path in file_paths:
        base_alias = sanitize_alias(path)
        alias_base = f"{prefix}_{base_alias}" if prefix else base_alias
        if alias_base not in base_counts:
            base_counts[alias_base] = 1
            alias_map[alias_base] = path
            continue

        count = base_counts[alias_base] + 1
        candidate = f"{alias_base}_{count}"
        while candidate in alias_map:
            count += 1
            candidate = f"{alias_base}_{count}"
        base_counts[alias_base] = count
        alias_map[candidate] = path

    return alias_map
