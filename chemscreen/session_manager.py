"""Session management for persistent storage and history."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from chemscreen.config import Config, get_config
from chemscreen.models import BatchSearchSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session persistence and history."""

    def __init__(
        self, session_dir: Optional[Path] = None, config: Optional[Config] = None
    ):
        """
        Initialize session manager.

        Args:
            session_dir: Directory for session storage (uses config if None)
            config: Configuration instance (uses global if None)
        """
        self.config = config or get_config()
        self.session_dir = session_dir or self.config.sessions_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.session_dir / "index.json"

    def save_session(self, session: BatchSearchSession) -> Path:
        """
        Save a session to persistent storage.

        Args:
            session: BatchSearchSession to save

        Returns:
            Path to saved session file
        """
        # Create filename with timestamp and batch ID
        timestamp = session.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}_{session.batch_id}.json"
        filepath = self.session_dir / filename

        try:
            # Convert session to dict and save
            session_data = session.model_dump()

            # Handle datetime serialization
            def serialize_datetime(obj: Any) -> str:
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, default=serialize_datetime)

            # Update session index
            self._update_session_index(session, filepath)

            logger.info(f"Session {session.batch_id} saved to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save session {session.batch_id}: {e}")
            raise

    def load_session(self, session_id: str) -> Optional[BatchSearchSession]:
        """
        Load a session from persistent storage.

        Args:
            session_id: Batch ID of session to load

        Returns:
            BatchSearchSession or None if not found
        """
        try:
            # Find session file
            session_files = list(self.session_dir.glob(f"session_*_{session_id}.json"))

            if not session_files:
                logger.warning(f"Session {session_id} not found")
                return None

            filepath = session_files[0]

            with open(filepath, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Convert back to BatchSearchSession
            session = BatchSearchSession.model_validate(session_data)

            logger.info(f"Session {session_id} loaded from {filepath}")
            return session

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """
        List all available sessions.

        Returns:
            List of session metadata dictionaries
        """
        try:
            if not self.index_file.exists():
                return []

            with open(self.index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)

            sessions: list[dict[str, Any]] = index_data.get("sessions", [])

            # Sort by creation date (newest first)
            sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from storage.

        Args:
            session_id: Batch ID of session to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find and delete session file
            session_files = list(self.session_dir.glob(f"session_*_{session_id}.json"))

            if not session_files:
                logger.warning(f"Session {session_id} not found for deletion")
                return False

            filepath = session_files[0]
            filepath.unlink()

            # Remove from index
            self._remove_from_index(session_id)

            logger.info(f"Session {session_id} deleted")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def _update_session_index(self, session: BatchSearchSession, filepath: Path) -> None:
        """Update the session index with new session metadata."""
        try:
            # Load existing index
            if self.index_file.exists():
                with open(self.index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
            else:
                index_data = {"sessions": [], "last_updated": None}

            # Create session metadata
            session_metadata = {
                "session_id": session.batch_id,
                "created_at": session.created_at.isoformat(),
                "chemical_count": len(session.chemicals),
                "session_name": getattr(session, "session_name", ""),
                "status": session.status,
                "file_path": filepath.name,
                "result_count": len(session.results) if session.results else 0,
            }

            # Remove existing entry if updating
            index_data["sessions"] = [
                s
                for s in index_data["sessions"]
                if s.get("session_id") != session.batch_id
            ]

            # Add new entry
            index_data["sessions"].append(session_metadata)
            index_data["last_updated"] = datetime.now().isoformat()

            # Save updated index atomically
            temp_filepath = self.index_file.with_suffix(".json.tmp")
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
            temp_filepath.rename(self.index_file)

        except Exception as e:
            logger.error(f"Failed to update session index: {e}")

    def _remove_from_index(self, session_id: str) -> None:
        """Remove session from index."""
        try:
            if not self.index_file.exists():
                return

            with open(self.index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)

            # Remove session
            index_data["sessions"] = [
                s for s in index_data["sessions"] if s.get("session_id") != session_id
            ]
            index_data["last_updated"] = datetime.now().isoformat()

            # Save updated index atomically
            temp_filepath = self.index_file.with_suffix(".json.tmp")
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
            temp_filepath.rename(self.index_file)

        except Exception as e:
            logger.error(f"Failed to remove session from index: {e}")

    def cleanup_old_sessions(self, days_to_keep: Optional[int] = None) -> int:
        """
        Clean up sessions older than specified days.

        Args:
            days_to_keep: Number of days to keep sessions (uses config if None)

        Returns:
            Number of sessions deleted
        """
        try:
            days_to_keep = days_to_keep or self.config.session_cleanup_days
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0

            sessions = self.list_sessions()

            for session_meta in sessions:
                session_date = datetime.fromisoformat(session_meta["created_at"])

                if session_date.timestamp() < cutoff_date:
                    if self.delete_session(session_meta["session_id"]):
                        deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
