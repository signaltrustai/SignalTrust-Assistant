"""
Memory Agent — Long-term context storage, recall, and session summaries.

Wraps the :class:`MemoryStore` to provide agent-level operations:
storing notes, recalling context, searching memory, and generating
session summaries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult
from assistant.core.memory_store import MemoryStore


class MemoryAgent(BaseAgent):
    """Agent responsible for long-term memory operations.

    Actions: ``store``, ``recall``, ``search``, ``list``, ``summarise``,
    ``delete``.
    """

    def __init__(self, store: Optional[MemoryStore] = None, **kwargs: Any) -> None:
        super().__init__(
            name="memory",
            description=(
                "Stores long-term context: preferences, decisions, "
                "project states. Summarises sessions and maintains "
                "a structured knowledge base."
            ),
            required_permissions=["memory.write"],
            **kwargs,
        )
        self._store = store or MemoryStore()

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> AgentResult:
        action = kwargs.get("action")
        message = kwargs.get("message", "")

        if action == "store" or (not action and message):
            return self._store_note(message, kwargs.get("tags"), kwargs.get("source", "user"))
        if action == "recall":
            return self._recall(kwargs.get("entry_id"))
        if action == "search":
            return self._search(kwargs.get("query", message))
        if action == "list":
            return self._list_entries(kwargs.get("limit", 50), kwargs.get("tags"))
        if action == "summarise" or action == "summarize":
            return self._summarise(kwargs.get("last_n", 10))
        if action == "delete":
            return self._delete(kwargs.get("entry_id"))

        # Default: treat as a note to store
        if message:
            return self._store_note(message)

        return AgentResult(
            agent_name=self.name,
            status="error",
            message="No action or message provided. Use: store, recall, search, list, summarise, delete.",
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _store_note(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        source: str = "user",
    ) -> AgentResult:
        entry = self._store.add_entry(
            {"type": "note", "content": content},
            tags=tags,
            source=source,
        )
        return AgentResult(
            agent_name=self.name,
            status="success",
            message="Note enregistrée dans la mémoire longue durée.",
            data={"entry": entry},
            actions_taken=["store_note"],
        )

    def _recall(self, entry_id: Optional[int] = None) -> AgentResult:
        if entry_id is None:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message="entry_id is required for recall.",
            )
        entry = self._store.get_entry(entry_id)
        if not entry:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message=f"Entry {entry_id} not found.",
            )
        return AgentResult(
            agent_name=self.name,
            status="success",
            message="Entry recalled.",
            data={"entry": entry},
            actions_taken=["recall_entry"],
        )

    def _search(self, query: str) -> AgentResult:
        results = self._store.search(query)
        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Found {len(results)} matching entries.",
            data={"results": results, "query": query},
            actions_taken=["search_memory"],
        )

    def _list_entries(
        self, limit: int = 50, tags: Optional[List[str]] = None,
    ) -> AgentResult:
        entries = self._store.get_entries(limit=limit, tags=tags)
        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Retrieved {len(entries)} entries.",
            data={"entries": entries},
            actions_taken=["list_entries"],
        )

    def _summarise(self, last_n: int = 10) -> AgentResult:
        summary = self._store.summarise_session(last_n)
        return AgentResult(
            agent_name=self.name,
            status="success",
            message="Session summary generated.",
            data={"summary": summary},
            actions_taken=["summarise_session"],
        )

    def _delete(self, entry_id: Optional[int] = None) -> AgentResult:
        if entry_id is None:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message="entry_id is required for deletion.",
            )
        deleted = self._store.delete_entry(entry_id)
        if not deleted:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message=f"Entry {entry_id} not found.",
            )
        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Entry {entry_id} deleted.",
            actions_taken=["delete_entry"],
        )
