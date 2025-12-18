"""Session persistence for threaded chat history."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


class SessionManager:
    """Persist and retrieve chat sessions as JSON files."""

    DEFAULT_TITLE = "New chat"

    def __init__(self, base_dir: str = "backend/sessions") -> None:
        self.base_dir = base_dir
        self.index_path = os.path.join(self.base_dir, "index.json")
        self._ensure_dir(self.base_dir)

    def _ensure_dir(self, directory: str) -> None:
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _session_path(self, session_id: str) -> str:
        return os.path.join(self.base_dir, f"{session_id}.json")

    def _load_index(self) -> List[Dict[str, object]]:
        if not os.path.exists(self.index_path):
            return []
        with open(self.index_path, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []

    def _save_index(self, sessions: List[Dict[str, object]]) -> None:
        with open(self.index_path, "w") as f:
            json.dump(sessions, f, indent=2)

    def _read_session(self, session_id: str) -> Dict[str, object]:
        session_path = self._session_path(session_id)
        if not os.path.exists(session_path):
            raise ValueError(f"Session '{session_id}' does not exist")
        with open(session_path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        raise ValueError("Invalid session data")

    def _write_session(self, session_data: Dict[str, object]) -> None:
        session_id = session_data.get("id", "")
        if not session_id:
            raise ValueError("Session data missing id")
        session_path = self._session_path(session_id)
        with open(session_path, "w") as f:
            json.dump(session_data, f, indent=2)

    def create_session(
        self, title: Optional[str] = None, project_name: Optional[str] = None
    ) -> Dict[str, object]:
        """Create a new chat session."""
        session_id = uuid.uuid4().hex
        now = self._now_iso()
        display_title = title.strip() if title and title.strip() else self.DEFAULT_TITLE
        session_data: Dict[str, object] = {
            "id": session_id,
            "title": display_title,
            "created_at": now,
            "updated_at": now,
            "project_name": project_name,
            "selected_files": [],
            "last_message": "",
            "messages": [],
            "plots": [],
        }
        self._write_session(session_data)

        index = self._load_index()
        index.append(
            {
                "id": session_id,
                "title": display_title,
                "created_at": now,
                "updated_at": now,
                "project_name": project_name,
                "selected_files": [],
                "last_message": "",
            }
        )
        self._save_index(index)
        return session_data

    def list_sessions(self, project_name: Optional[str] = None) -> List[Dict[str, object]]:
        """List session metadata, optionally filtered by project name."""
        sessions = self._load_index()
        if project_name:
            sessions = [
                session
                for session in sessions
                if session.get("project_name") == project_name
            ]
        return sorted(
            sessions,
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )

    def get_session(self, session_id: str) -> Dict[str, object]:
        """Return the full session object."""
        return self._read_session(session_id)

    def get_messages(self, session_id: str) -> List[Dict[str, object]]:
        """Return message history for a session."""
        session = self._read_session(session_id)
        messages = session.get("messages", [])
        if isinstance(messages, list):
            return messages
        return []

    def append_message(
        self, session_id: str, role: str, content: str, code: Optional[str] = None
    ) -> None:
        """Append a message to a session and update its metadata."""
        session = self._read_session(session_id)
        now = self._now_iso()
        message: Dict[str, object] = {
            "role": role,
            "content": content,
            "timestamp": now,
        }
        if code:
            message["code"] = code

        messages = session.get("messages", [])
        if not isinstance(messages, list):
            messages = []
        messages.append(message)
        session["messages"] = messages
        session["updated_at"] = now
        session["last_message"] = content[:160] if content else ""

        if role == "user":
            existing_title = str(session.get("title", "") or "").strip()
            if self._should_auto_title(existing_title):
                session["title"] = self._derive_title(content)

        self._write_session(session)

        index = self._load_index()
        for item in index:
            if item.get("id") == session_id:
                item["updated_at"] = now
                item["last_message"] = session["last_message"]
                item["title"] = session.get("title", item.get("title", ""))
                if "project_name" in session:
                    item["project_name"] = session.get("project_name")
                if "selected_files" in session:
                    item["selected_files"] = session.get("selected_files", [])
        self._save_index(index)

    def append_plot(self, session_id: str, plot_entry: Dict[str, object]) -> None:
        """Record a plot entry against a session."""
        session = self._read_session(session_id)
        plots = session.get("plots", [])
        if not isinstance(plots, list):
            plots = []
        plots.append(plot_entry)
        session["plots"] = plots
        session["updated_at"] = self._now_iso()
        self._write_session(session)

    def update_session_context(
        self,
        session_id: str,
        project_name: Optional[str],
        selected_files: Optional[List[str]],
    ) -> None:
        """Update the session context fields without adding a message."""
        session = self._read_session(session_id)
        if project_name is not None:
            session["project_name"] = project_name
        if selected_files is not None:
            session["selected_files"] = selected_files
        session["updated_at"] = self._now_iso()
        self._write_session(session)

        index = self._load_index()
        for item in index:
            if item.get("id") == session_id:
                if project_name is not None:
                    item["project_name"] = project_name
                if selected_files is not None:
                    item["selected_files"] = selected_files
                item["updated_at"] = session["updated_at"]
        self._save_index(index)

    def _should_auto_title(self, existing_title: str) -> bool:
        if not existing_title:
            return True
        if existing_title == self.DEFAULT_TITLE:
            return True
        return existing_title.startswith("Chat ")

    def _derive_title(self, content: str, max_length: int = 48) -> str:
        title = " ".join((content or "").strip().split())
        if not title:
            return self.DEFAULT_TITLE
        if len(title) <= max_length:
            return title
        return f"{title[: max_length - 1].rstrip()}…"
