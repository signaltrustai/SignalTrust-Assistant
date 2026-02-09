"""
Memory module for SignalTrust Assistant.

Responsible for long-term context storage and retrieval.
Backed by Markdown files + a JSON index in the `memory/` directory.
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

MEMORY_ROOT = Path("memory")
INDEX_FILE = MEMORY_ROOT / "index.json"


def _load_index() -> Dict[str, Any]:
    if not INDEX_FILE.exists():
        return {}
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


def _save_index(index: Dict[str, Any]) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, indent=2), encoding="utf-8")


def save_context(key: str, value: str, meta: Optional[Dict[str, Any]] = None) -> None:
    """
    Save or update a context entry.

    :param key: Unique identifier for the context.
    :param value: Markdown/text content.
    :param meta: Optional metadata (tags, source, etc.).
    """
    meta = meta or {}
    index = _load_index()

    now = datetime.utcnow().isoformat()
    entry = index.get(key, {})
    entry.update(
        {
            "key": key,
            "tags": meta.get("tags", []),
            "source": meta.get("source", "user"),
            "created_at": entry.get("created_at", now),
            "updated_at": now,
            "path": f"{key}.md",
        }
    )
    index[key] = entry

    MEMORY_ROOT.mkdir(parents=True, exist_ok=True)
    (MEMORY_ROOT / entry["path"]).write_text(value, encoding="utf-8")
    _save_index(index)


def load_context(key: str) -> Optional[Dict[str, Any]]:
    """
    Load a context entry by key.

    :return: Dict with metadata + content, or None if not found.
    """
    index = _load_index()
    entry = index.get(key)
    if not entry:
        return None

    path = MEMORY_ROOT / entry["path"]
    if not path.exists():
        return None

    content = path.read_text(encoding="utf-8")
    return {**entry, "content": content}


def list_contexts() -> List[Dict[str, Any]]:
    """
    List all known context entries (metadata only).
    """
    index = _load_index()
    return list(index.values())


def search_context(query: str) -> List[Dict[str, Any]]:
    """
    Naive search across all stored content and metadata.

    :param query: Substring to search for.
    """
    query_lower = query.lower()
    results: List[Dict[str, Any]] = []

    for entry in list_contexts():
        data = load_context(entry["key"])
        if not data:
            continue

        haystack = (data.get("content", "") + " " + " ".join(data.get("tags", []))).lower()
        if query_lower in haystack:
            results.append(data)

    return results
