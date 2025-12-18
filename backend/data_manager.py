"""Data loading, preview, and context utilities for plotting."""

from __future__ import annotations

import io
import os
from typing import Dict, List, Optional

import pandas as pd
from fastapi import UploadFile


class DataManager:
    """Handle saving, loading, and summarizing uploaded datasets."""

    def __init__(self, upload_dir: str = "uploads") -> None:
        self.upload_dir = upload_dir
        self._ensure_dir(self.upload_dir)

    def _ensure_dir(self, directory: str) -> None:
        if not os.path.exists(directory):
            os.makedirs(directory)

    async def save_file(self, file: UploadFile, target_dir: Optional[str] = None) -> str:
        """Save an uploaded file and return its filesystem path."""
        save_dir = target_dir or self.upload_dir
        self._ensure_dir(save_dir)
        file_path = os.path.join(save_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        return file_path

    async def save_text_data(
        self, content: str, filename: str, target_dir: Optional[str] = None
    ) -> str:
        """Save text data (CSV/JSON) and return its filesystem path."""
        save_dir = target_dir or self.upload_dir
        self._ensure_dir(save_dir)
        file_path = os.path.join(save_dir, filename)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from a CSV or JSON file into a DataFrame."""
        if file_path.endswith(".csv"):
            return pd.read_csv(file_path)
        if file_path.endswith(".json"):
            return pd.read_json(file_path)
        raise ValueError("Unsupported file format")

    def get_preview(self, file_path: str) -> List[Dict[str, object]]:
        """Return a preview of the dataset as a list of records."""
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
        else:
            return []

        return df.head().to_dict(orient="records")

    def get_data_context(self, file_path: str, alias: Optional[str] = None) -> str:
        """Build a compact context block for a single dataset."""
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
        else:
            return "No data available."

        buffer = io.StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()
        label = os.path.basename(file_path)
        alias_text = f" (alias: {alias})" if alias else ""

        context = (
            f"File: {label}{alias_text}\n"
            f"Data Columns: {list(df.columns)}\n"
            f"Data Types:\n{info_str}\n"
            f"First 3 rows:\n{df.head(3).to_string()}\n"
        )
        return context

    def get_multi_data_context(self, alias_map: Dict[str, str]) -> str:
        """Build a combined context block for multiple datasets."""
        blocks: List[str] = []
        for alias, path in alias_map.items():
            blocks.append(self.get_data_context(path, alias=alias))
        return "\n".join(blocks)
