"""Project manifest persistence for datasets, plots, and UI state."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd

from data_manager import DataManager
from data_validator import get_validator


class ProjectManifestManager:
    """Maintain per-project manifest metadata on disk."""

    def __init__(self, base_dir: str = "backend/projects") -> None:
        self.base_dir = os.getenv("PROJECTS_DIR", base_dir)
        self.data_manager = DataManager()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _get_project_path(self, project_name: str) -> str:
        return os.path.join(self.base_dir, project_name)

    def _get_manifest_path(self, project_name: str) -> str:
        return os.path.join(self._get_project_path(project_name), "project.json")

    def ensure_manifest(self, project_name: str) -> Dict[str, object]:
        """Create a manifest if missing and return its contents."""
        manifest_path = self._get_manifest_path(project_name)
        if os.path.exists(manifest_path):
            return self.load_manifest(project_name)

        project_path = self._get_project_path(project_name)
        if not os.path.exists(project_path):
            raise ValueError("Project directory does not exist")

        now = self._now_iso()
        manifest: Dict[str, object] = {
            "project": {
                "name": project_name,
                "created_at": now,
                "updated_at": now,
            },
            "datasets": [],
            "plots": [],
            "ui_state": {
                "selected_files": [],
                "last_session_id": None,
                "plot_history_index": 0,
            },
        }
        self.save_manifest(project_name, manifest)
        return manifest

    def load_manifest(self, project_name: str) -> Dict[str, object]:
        """Load the manifest from disk."""
        manifest_path = self._get_manifest_path(project_name)
        if not os.path.exists(manifest_path):
            raise ValueError("Project manifest does not exist")
        with open(manifest_path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        raise ValueError("Invalid manifest format")

    def save_manifest(self, project_name: str, manifest: Dict[str, object]) -> None:
        """Persist the manifest to disk."""
        manifest_path = self._get_manifest_path(project_name)
        project_path = self._get_project_path(project_name)
        if not os.path.exists(project_path):
            raise ValueError("Project directory does not exist")

        manifest.setdefault("project", {})
        manifest["project"]["updated_at"] = self._now_iso()
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def register_dataset(self, project_name: str, file_path: str) -> Dict[str, object]:
        """Register a dataset in the manifest and return the entry."""
        manifest = self.ensure_manifest(project_name)
        project_path = self._get_project_path(project_name)
        if not os.path.isfile(file_path):
            raise ValueError("Dataset file not found")

        relative_path = os.path.relpath(file_path, project_path)
        df = self.data_manager.load_data(file_path)
        validator = get_validator()
        analysis = validator.analyze_data(df)
        schema = {
            "shape": analysis.get("shape", df.shape),
            "columns": analysis.get("columns", list(df.columns)),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "numeric_cols": analysis.get("numeric_cols", []),
            "categorical_cols": analysis.get("categorical_cols", []),
            "datetime_cols": analysis.get("datetime_cols", []),
            "warnings": analysis.get("warnings", []),
        }
        sample_rows = df.head(5).to_dict(orient="records")

        existing = self._find_dataset_by_path(manifest.get("datasets", []), relative_path)
        if existing:
            existing["size"] = os.path.getsize(file_path)
            existing["hash"] = self._hash_file(file_path)
            existing["path"] = os.path.abspath(file_path)
            existing["schema"] = schema
            existing["sample_rows"] = sample_rows
            existing["updated_at"] = self._now_iso()
            self.save_manifest(project_name, manifest)
            return existing

        dataset_entry: Dict[str, object] = {
            "id": uuid.uuid4().hex,
            "name": os.path.basename(file_path),
            "relative_path": relative_path,
            "path": os.path.abspath(file_path),
            "size": os.path.getsize(file_path),
            "hash": self._hash_file(file_path),
            "schema": schema,
            "sample_rows": sample_rows,
            "created_at": self._now_iso(),
        }

        datasets = manifest.get("datasets", [])
        if not isinstance(datasets, list):
            datasets = []
        datasets.append(dataset_entry)
        manifest["datasets"] = datasets
        self.save_manifest(project_name, manifest)
        return dataset_entry

    def update_ui_state(self, project_name: str, updates: Dict[str, object]) -> Dict[str, object]:
        """Update the UI state block in the manifest."""
        manifest = self.ensure_manifest(project_name)
        ui_state = manifest.get("ui_state", {})
        if not isinstance(ui_state, dict):
            ui_state = {}
        ui_state.update(updates)
        manifest["ui_state"] = ui_state
        self.save_manifest(project_name, manifest)
        return ui_state

    def register_plot(
        self,
        project_name: str,
        code: str,
        selected_files: List[str],
        image_path: str,
        thumbnail_path: Optional[str],
        session_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, object]:
        """Register a plot entry in the manifest."""
        manifest = self.ensure_manifest(project_name)
        project_path = self._get_project_path(project_name)
        plot_entry: Dict[str, object] = {
            "id": uuid.uuid4().hex,
            "created_at": self._now_iso(),
            "session_id": session_id,
            "description": description or "",
            "code": code,
            "selected_files": [
                os.path.relpath(path, project_path) for path in selected_files
            ],
            "image_path": os.path.relpath(image_path, project_path),
            "thumbnail_path": os.path.relpath(thumbnail_path, project_path)
            if thumbnail_path
            else None,
        }

        plots = manifest.get("plots", [])
        if not isinstance(plots, list):
            plots = []
        plots.append(plot_entry)
        manifest["plots"] = plots
        self.save_manifest(project_name, manifest)
        return plot_entry

    def get_plot_history(self, project_name: str) -> List[Dict[str, object]]:
        """Return plot history for a project."""
        manifest = self.ensure_manifest(project_name)
        plots = manifest.get("plots", [])
        if isinstance(plots, list):
            return plots
        return []

    def get_plot_by_id(
        self, project_name: str, plot_id: str
    ) -> Optional[Dict[str, object]]:
        """Find a plot entry by id."""
        plots = self.get_plot_history(project_name)
        for plot in plots:
            if plot.get("id") == plot_id:
                return plot
        return None

    def set_plot_thumbnail_path(
        self, project_name: str, plot_id: str, thumbnail_path: str
    ) -> Optional[Dict[str, object]]:
        """Persist a thumbnail path update for an existing plot entry."""
        manifest = self.ensure_manifest(project_name)
        plots = manifest.get("plots", [])
        if not isinstance(plots, list):
            return None

        for plot in plots:
            if plot.get("id") == plot_id:
                plot["thumbnail_path"] = thumbnail_path
                manifest["plots"] = plots
                self.save_manifest(project_name, manifest)
                return plot

        return None

    def _hash_file(self, file_path: str) -> str:
        """Compute a SHA256 hash for the file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _find_dataset_by_path(
        self, datasets: List[Dict[str, object]], relative_path: str
    ) -> Optional[Dict[str, object]]:
        for dataset in datasets:
            if dataset.get("relative_path") == relative_path:
                return dataset
        return None
