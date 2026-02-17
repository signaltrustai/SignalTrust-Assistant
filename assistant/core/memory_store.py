"""
OmniJARVIS Memory Store — Unified long-term context storage.

Wraps the existing ``assistant.memory`` module with higher-level
operations used by the Memory Agent and the Orchestrator.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


MEMORY_ROOT = Path("memory")
STORE_FILE = MEMORY_ROOT / "omnijarvis_store.json"


class MemoryStore:
    """JSON-backed long-term memory for OmniJARVIS.

    Supports tagged entries, chronological retrieval, search, and
    session summaries.

    Usage::

        store = MemoryStore()
        store.add_entry({"type": "note", "content": "Remember to deploy v2."})
        entries = store.search("deploy")
    """

    def __init__(self, store_file: Optional[Path] = None) -> None:
        self._store_file: Path = store_file or STORE_FILE
        self._entries: List[Dict[str, Any]] = self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_entry(
        self,
        data: Dict[str, Any],
        tags: Optional[List[str]] = None,
        source: str = "user",
    ) -> Dict[str, Any]:
        """Add a new entry to long-term memory.

        :param data: Arbitrary payload (must be JSON-serialisable).
        :param tags: Optional categorisation tags.
        :param source: Origin of the entry (``"user"``, ``"agent"``, etc.).
        :return: The stored entry with generated metadata.
        """
        entry: Dict[str, Any] = {
            "id": len(self._entries) + 1,
            "data": data,
            "tags": tags or [],
            "source": source,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._entries.append(entry)
        self._save()
        return entry

    def get_entries(
        self,
        limit: int = 50,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve entries with optional filters, most-recent first.

        :param limit: Maximum number of entries to return.
        :param tags: If given, only return entries containing *all* tags.
        :param source: If given, filter by source.
        """
        results = list(reversed(self._entries))
        if tags:
            tag_set = set(tags)
            results = [e for e in results if tag_set.issubset(set(e.get("tags", [])))]
        if source:
            results = [e for e in results if e.get("source") == source]
        return results[:limit]

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Full-text search across all entry data and tags.

        :param query: Case-insensitive substring to search for.
        """
        q = query.lower()
        results: List[Dict[str, Any]] = []
        for entry in self._entries:
            haystack = json.dumps(entry, ensure_ascii=False).lower()
            if q in haystack:
                results.append(entry)
        return results

    def get_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single entry by its numeric ID."""
        for entry in self._entries:
            if entry.get("id") == entry_id:
                return entry
        return None

    def delete_entry(self, entry_id: int) -> bool:
        """Remove an entry by ID.

        :return: ``True`` if the entry was found and removed.
        """
        for i, entry in enumerate(self._entries):
            if entry.get("id") == entry_id:
                self._entries.pop(i)
                self._save()
                return True
        return False

    def count(self) -> int:
        """Return the total number of stored entries."""
        return len(self._entries)

    def summarise_session(self, last_n: int = 10) -> str:
        """Return a plain-text summary of the most recent entries."""
        recent = list(reversed(self._entries))[:last_n]
        if not recent:
            return "No entries in memory."
        lines = [f"Memory summary ({len(recent)} most recent entries):"]
        for entry in recent:
            content = entry.get("data", {}).get("content", str(entry.get("data", "")))
            preview = content[:120] + ("…" if len(content) > 120 else "")
            tags = ", ".join(entry.get("tags", [])) or "—"
            lines.append(f"  • [{tags}] {preview}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> List[Dict[str, Any]]:
        if not self._store_file.exists():
            return []
        try:
            data = json.loads(self._store_file.read_text(encoding="utf-8"))
            return data.get("entries", [])
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self) -> None:
        self._store_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"entries": self._entries}
        self._store_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
