"""
OmniJARVIS Orchestrator — The central nervous system.

Receives user requests, routes them to the correct agent(s) via the
intelligent Router, coordinates multi-agent workflows, enforces
permissions, records interactions for learning, and returns structured
responses following the mandated output format.

This is the single entry-point for all OmniJARVIS interactions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from assistant.core.memory_store import MemoryStore
from assistant.core.models import OmniJARVISResponse
from assistant.core.router import Router
from assistant.learning import LearningEngine
from assistant.permissions import PermissionManager

from assistant.agents.base_agent import AgentResult
from assistant.agents.executive_agent import ExecutiveAgent
from assistant.agents.memory_agent import MemoryAgent
from assistant.agents.analysis_agent import AnalysisAgent
from assistant.agents.system_agent import SystemAgent
from assistant.agents.documentation_agent import DocumentationAgent
from assistant.agents.code_agent import CodeAgent
from assistant.agents.communication_agent import CommunicationAgent
from assistant.agents.cloud_agent import CloudAgent
from assistant.agents.vision_agent import VisionAgent
from assistant.agents.mobility_agent import MobilityAgent
from assistant.agents.productivity_agent import ProductivityAgent
from assistant.agents.security_agent import SecurityAgent


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class OmniJARVIS:
    """Central orchestrator for the OmniJARVIS multi-agent system.

    Wires together the router, permission manager, learning engine,
    memory store, and all specialised agents into a single unified
    entry-point.

    Usage::

        jarvis = OmniJARVIS()
        response = jarvis.handle("Analyse ce fichier pour moi")
        print(response.format_text())
    """

    INIT_MESSAGE = "OmniJARVIS operational. Ready to orchestrate your personal OS."

    def __init__(self) -> None:
        # Core infrastructure
        self._permissions = PermissionManager()
        self._learning = LearningEngine()
        self._memory_store = MemoryStore()
        self._router = Router()

        # Shared kwargs for every agent
        agent_kwargs: Dict[str, Any] = {
            "permission_manager": self._permissions,
            "learning_engine": self._learning,
        }

        # Instantiate all agents
        self._agents: Dict[str, Any] = {
            "executive": ExecutiveAgent(**agent_kwargs),
            "memory": MemoryAgent(store=self._memory_store, **agent_kwargs),
            "analysis": AnalysisAgent(**agent_kwargs),
            "system": SystemAgent(**agent_kwargs),
            "documentation": DocumentationAgent(**agent_kwargs),
            "code": CodeAgent(**agent_kwargs),
            "communication": CommunicationAgent(**agent_kwargs),
            "cloud": CloudAgent(**agent_kwargs),
            "vision": VisionAgent(**agent_kwargs),
            "mobility": MobilityAgent(**agent_kwargs),
            "productivity": ProductivityAgent(**agent_kwargs),
            "security": SecurityAgent(**agent_kwargs),
        }

        # Session event log (for session summaries)
        self._session_events: List[Dict[str, str]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle(self, message: str) -> OmniJARVISResponse:
        """Process a user message through the full OmniJARVIS pipeline.

        Workflow:
        1. Identify intent via the Router.
        2. Dispatch to the matched agent.
        3. Record the interaction for learning.
        4. Update memory when relevant.
        5. Return a structured :class:`OmniJARVISResponse`.

        :param message: Raw user input (French or English).
        :return: Structured response with summary, steps, result, and
            suggestions.
        """
        # 1. Route
        route = self._router.route(message)
        agent_name = route.agent
        agent = self._agents.get(agent_name, self._agents["executive"])

        # 2. Execute
        steps: List[Dict[str, str]] = []
        steps.append({
            "agent": "router",
            "action": "Intent detection",
            "detail": f"Matched '{agent_name}' (confidence: {route.confidence:.2f})",
        })

        result = self._dispatch(agent_name, agent, message)
        steps.append({
            "agent": agent_name,
            "action": result.message,
            "detail": ", ".join(result.actions_taken) if result.actions_taken else "—",
        })

        # 3. Record session event
        self._session_events.append({
            "agent": agent_name,
            "action": result.message,
            "detail": message[:100],
        })

        # 4. Auto-store important decisions/notes in memory
        if agent_name != "memory" and result.status == "success":
            self._memory_store.add_entry(
                {"type": "interaction", "agent": agent_name, "query": message[:200]},
                tags=[agent_name, "auto"],
                source="orchestrator",
            )

        # 5. Generate suggestions
        suggestions = self._generate_suggestions(agent_name, message, result)

        # 6. Build response
        return OmniJARVISResponse(
            summary=result.message,
            steps=steps,
            result=result.data,
            suggestions=suggestions,
        )

    def handle_direct(
        self,
        agent_name: str,
        action: Optional[str] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Directly invoke a specific agent by name (bypasses routing).

        :param agent_name: Registered agent identifier.
        :param action: Agent action to execute.
        :return: Raw :class:`AgentResult`.
        """
        agent = self._agents.get(agent_name)
        if agent is None:
            return AgentResult(
                agent_name="orchestrator",
                status="error",
                message=f"Unknown agent: {agent_name}. Available: {list(self._agents.keys())}",
            )
        message = kwargs.pop("message", "")
        return self._dispatch(agent_name, agent, message, action=action, **kwargs)

    def grant_permission(self, action: str, scope: str = "session") -> None:
        """Grant a permission through the orchestrator.

        :param action: Action type (e.g. ``"system.execute"``).
        :param scope: ``"once"``, ``"session"``, or ``"always"``.
        """
        self._permissions.grant_permission(action, scope)

    def revoke_permission(self, action: str) -> None:
        """Revoke a permission."""
        self._permissions.revoke_permission(action)

    def list_permissions(self) -> List[Dict[str, Any]]:
        """List all active permissions."""
        return self._permissions.list_permissions()

    def audit_log(self) -> List[Dict[str, Any]]:
        """Return the security audit trail."""
        return self._permissions.audit_log()

    def list_agents(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered agents."""
        result: List[Dict[str, Any]] = []
        for name, agent in self._agents.items():
            if hasattr(agent, "describe"):
                result.append(agent.describe())
            else:
                result.append({"name": name, "status": "ready"})
        return result

    def session_summary(self) -> str:
        """Generate a summary of the current session."""
        if not self._session_events:
            return "No interactions in this session yet."
        lines = [f"📊 Session Summary ({len(self._session_events)} interactions)\n"]
        for i, event in enumerate(self._session_events, 1):
            lines.append(
                f"  {i}. [{event['agent']}] {event['action']}: {event['detail']}"
            )
        stats = self._learning.get_usage_stats()
        lines.append(f"\n📈 Total all-time interactions: {stats['total_interactions']}")
        if stats["favorite_agent"]:
            lines.append(f"⭐ Favourite agent: {stats['favorite_agent']}")
        return "\n".join(lines)

    def get_profile(self) -> Dict[str, Any]:
        """Return the user profile."""
        return self._learning.get_profile()

    def update_profile(self, name: Optional[str] = None, **prefs: Any) -> None:
        """Update the user profile."""
        self._learning.update_profile(name=name, preferences=prefs if prefs else None)

    def get_stats(self) -> Dict[str, Any]:
        """Return usage statistics."""
        return self._learning.get_usage_stats()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _dispatch(
        self,
        agent_name: str,
        agent: Any,
        message: str,
        action: Optional[str] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Call an agent's run/handle method with proper arguments."""
        try:
            # BaseAgent subclasses
            if hasattr(agent, "run") and hasattr(agent, "execute"):
                return agent.run(message=message, action=action, **kwargs)
            # Legacy agents (FocusAgent)
            if hasattr(agent, "run"):
                raw = agent.run()
                return AgentResult(
                    agent_name=agent_name,
                    status=raw.get("status", "success"),
                    message=str(raw),
                    data=raw,
                )
            # Simple handle() pattern
            if hasattr(agent, "handle"):
                raw = agent.handle(message)
                return AgentResult(
                    agent_name=agent_name,
                    status=raw.get("status", "success"),
                    message=raw.get("message", str(raw)),
                    data=raw,
                )
        except Exception as exc:
            return AgentResult(
                agent_name=agent_name,
                status="error",
                message=f"Agent '{agent_name}' raised an error: {exc}",
            )

        return AgentResult(
            agent_name=agent_name,
            status="error",
            message=f"Agent '{agent_name}' has no compatible interface.",
        )

    def _generate_suggestions(
        self, agent_name: str, message: str, result: AgentResult,
    ) -> List[str]:
        """Generate context-aware follow-up suggestions."""
        suggestions: List[str] = []

        if result.status == "pending_permission":
            missing = (result.data or {}).get("missing_permissions", [])
            for perm in missing:
                suggestions.append(
                    f"Grant permission: jarvis.grant_permission('{perm}', 'session')"
                )

        if result.status == "error":
            suggestions.append("Retry with more details or try a different agent.")

        # Agent-specific suggestions
        suggestion_map: Dict[str, List[str]] = {
            "code": [
                "Review the generated code before execution.",
                "Use 'execute_code' to run with permission.",
            ],
            "analysis": [
                "Store important findings in memory.",
                "Generate a report from the analysis.",
            ],
            "memory": [
                "Search memory for related context.",
                "Generate a session summary.",
            ],
            "system": [
                "Check disk usage or system info.",
                "Create an automation routine.",
            ],
            "documentation": [
                "Update the project README.",
                "Generate a changelog.",
            ],
        }
        if agent_name in suggestion_map and result.status == "success":
            suggestions.extend(suggestion_map[agent_name])

        # Learning-based suggestions
        learned = self._learning.get_suggestions(message[:50] if message else None)
        suggestions.extend(learned[:2])

        return suggestions[:5]  # Cap at 5
