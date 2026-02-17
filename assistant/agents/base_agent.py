"""
Base agent class for OmniJARVIS specialized agents.

Provides an abstract foundation that every agent inherits from.  Handles
permission checks, interaction recording, and a uniform result format so
that the orchestrator can treat all agents identically.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from assistant.learning import LearningEngine
from assistant.permissions import PermissionManager


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """Uniform result returned by every agent invocation.

    :param agent_name: Identifier of the agent that produced this result.
    :param status: Outcome status — ``"success"``, ``"error"``, or
        ``"pending_permission"``.
    :param message: Human-readable description of the outcome.
    :param data: Optional payload with structured result data.
    :param actions_taken: Log of discrete actions performed during execution.
    :param timestamp: ISO-8601 UTC timestamp of when the result was created.
    """

    agent_name: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    actions_taken: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the result to a plain dictionary."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Abstract base agent
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """Abstract base class for all OmniJARVIS specialized agents.

    Subclasses **must** implement :meth:`execute`.  The public
    :meth:`run` method handles permission verification, delegates to
    ``execute``, and records the interaction via the learning engine.

    Usage::

        class MyAgent(BaseAgent):
            def execute(self, **kwargs) -> AgentResult:
                return AgentResult(
                    agent_name=self.name,
                    status="success",
                    message="Done.",
                )

        agent = MyAgent(
            name="my_agent",
            description="Does something useful.",
            required_permissions=["file.read"],
            permission_manager=pm,
            learning_engine=le,
        )
        result = agent.run(query="hello")
    """

    def __init__(
        self,
        name: str,
        description: str,
        required_permissions: Optional[List[str]] = None,
        permission_manager: Optional[PermissionManager] = None,
        learning_engine: Optional[LearningEngine] = None,
    ) -> None:
        """Initialize the agent.

        :param name: Unique agent identifier.
        :param description: Human-readable summary of what this agent does.
        :param required_permissions: Action types this agent needs (values
            from :data:`assistant.permissions.ACTION_TYPES`).
        :param permission_manager: Optional :class:`PermissionManager` used
            to verify that required permissions have been granted.
        :param learning_engine: Optional :class:`LearningEngine` used to
            record interactions for adaptive learning.
        """
        self._name = name
        self._description = description
        self._required_permissions: List[str] = required_permissions or []
        self._permission_manager = permission_manager
        self._learning_engine = learning_engine

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return the agent identifier."""
        return self._name

    @property
    def description(self) -> str:
        """Return the agent description."""
        return self._description

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, **kwargs: Any) -> AgentResult:
        """Execute the agent with permission checks and interaction logging.

        1. Verify that every required permission is granted (when a
           :class:`PermissionManager` is available).
        2. Delegate to :meth:`execute` for the actual work.
        3. Record the interaction via the :class:`LearningEngine` (when
           available).

        :return: An :class:`AgentResult` describing the outcome.
        """
        # -- Step 1: permission check ----------------------------------
        if self._permission_manager and self._required_permissions:
            missing = [
                perm
                for perm in self._required_permissions
                if not self._permission_manager.check_permission(perm)
            ]
            if missing:
                return AgentResult(
                    agent_name=self._name,
                    status="pending_permission",
                    message=(
                        f"Agent '{self._name}' requires permissions that "
                        f"have not been granted: {', '.join(missing)}"
                    ),
                    data={"missing_permissions": missing},
                )

        # -- Step 2: execute -------------------------------------------
        result = self.execute(**kwargs)

        # -- Step 3: record interaction --------------------------------
        if self._learning_engine:
            self._learning_engine.record_interaction(
                query=str(kwargs) if kwargs else f"{self._name} invoked",
                response_summary=result.message,
                agent_used=self._name,
            )

        return result

    def describe(self) -> Dict[str, Any]:
        """Return a machine-readable description of this agent.

        :return: Dictionary with agent metadata.
        """
        return {
            "name": self._name,
            "description": self._description,
            "required_permissions": list(self._required_permissions),
            "status": "ready",
        }

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def execute(self, **kwargs: Any) -> AgentResult:
        """Perform the agent's core logic.

        Subclasses **must** override this method.  It should return an
        :class:`AgentResult` with ``status="success"`` on success or
        ``status="error"`` on failure.

        :return: An :class:`AgentResult` describing the outcome.
        """
