"""Project directory management for multi-file plotting."""

from __future__ import annotations

import os
from typing import Dict, List


class ProjectManager:
    """Manage project folders and their contents on disk."""

    def __init__(self, base_dir: str = "backend/projects") -> None:
        self.base_dir = os.getenv("PROJECTS_DIR", base_dir)
        self._ensure_dir(self.base_dir)

    def _ensure_dir(self, directory: str) -> None:
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _validate_project_name(self, project_name: str) -> str:
        name = project_name.strip()
        if not name:
            raise ValueError("Project name cannot be empty")
        if name.startswith("."):
            raise ValueError("Project name cannot start with a dot")
        if os.path.sep in name or (os.path.altsep and os.path.altsep in name):
            raise ValueError("Project name must not contain path separators")
        return name

    def _get_project_path(self, project_name: str) -> str:
        name = self._validate_project_name(project_name)
        return os.path.join(self.base_dir, name)

    def list_projects(self) -> List[str]:
        """Return a list of all project directory names."""
        if not os.path.exists(self.base_dir):
            return []
        projects = [
            entry
            for entry in os.listdir(self.base_dir)
            if os.path.isdir(os.path.join(self.base_dir, entry))
        ]
        return sorted(projects)

    def create_project(self, project_name: str) -> Dict[str, str]:
        """Create a new project directory."""
        name = self._validate_project_name(project_name)
        project_path = os.path.join(self.base_dir, name)
        if os.path.exists(project_path):
            raise ValueError(f"Project '{name}' already exists")

        os.makedirs(project_path)
        return {"name": name, "path": project_path}

    def list_entries(
        self, project_name: str, include_dirs: bool = True, recursive: bool = False
    ) -> List[Dict[str, object]]:
        """List files (and optionally folders) within a project."""
        project_path = self._get_project_path(project_name)
        if not os.path.exists(project_path):
            raise ValueError(f"Project '{project_name}' does not exist")

        entries: List[Dict[str, object]] = []

        if recursive:
            for root, dirs, files in os.walk(project_path):
                for name in sorted(dirs):
                    if name.startswith("."):
                        continue
                    path = os.path.join(root, name)
                    rel_path = os.path.relpath(path, project_path)
                    if include_dirs:
                        entries.append(
                            {
                                "name": name,
                                "path": os.path.abspath(path),
                                "relative_path": rel_path,
                                "type": "dir",
                            }
                        )
                for name in sorted(files):
                    if name.startswith("."):
                        continue
                    path = os.path.join(root, name)
                    rel_path = os.path.relpath(path, project_path)
                    stats = os.stat(path)
                    entries.append(
                        {
                            "name": name,
                            "path": os.path.abspath(path),
                            "relative_path": rel_path,
                            "type": "file",
                            "size": stats.st_size,
                            "created": stats.st_ctime,
                            "modified": stats.st_mtime,
                        }
                    )
            return entries

        for name in sorted(os.listdir(project_path)):
            if name.startswith("."):
                continue
            path = os.path.join(project_path, name)
            rel_path = os.path.relpath(path, project_path)
            if os.path.isdir(path):
                if include_dirs:
                    entries.append(
                        {
                            "name": name,
                            "path": os.path.abspath(path),
                            "relative_path": rel_path,
                            "type": "dir",
                        }
                    )
            elif os.path.isfile(path):
                stats = os.stat(path)
                entries.append(
                    {
                        "name": name,
                        "path": os.path.abspath(path),
                        "relative_path": rel_path,
                        "type": "file",
                        "size": stats.st_size,
                        "created": stats.st_ctime,
                        "modified": stats.st_mtime,
                    }
                )

        return entries

    def list_files(self, project_name: str) -> List[Dict[str, object]]:
        """List files in a project (directories excluded)."""
        return [
            entry
            for entry in self.list_entries(project_name, include_dirs=False)
            if entry.get("type") == "file"
        ]

    def get_project_path(self, project_name: str) -> str:
        """Return the absolute path for a project directory."""
        return os.path.abspath(self._get_project_path(project_name))

    def get_file_path(self, project_name: str, filename: str) -> str:
        """Return the absolute path for a file within a project."""
        project_path = self._get_project_path(project_name)
        return os.path.abspath(os.path.join(project_path, filename))
