"""
OmniJARVIS Core Models — Shared data structures for the multi-agent system.

All models are plain dataclasses with JSON serialisation support so they
can be persisted, transmitted, and inspected without external dependencies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskStatus(str, Enum):
    """Lifecycle status of a dispatched task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Task priority levels (highest first)."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class AgentRole(str, Enum):
    """Recognised agent roles in OmniJARVIS."""

    EXECUTIVE = "executive"
    MEMORY = "memory"
    ANALYSIS = "analysis"
    SYSTEM = "system"
    DOCUMENTATION = "documentation"
    CODE = "code"
    COMMUNICATION = "communication"
    CLOUD = "cloud"
    VISION = "vision"
    MOBILITY = "mobility"
    PRODUCTIVITY = "productivity"
    SECURITY = "security"
    FOCUS = "focus"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A discrete unit of work dispatched by the executive agent.

    :param id: Unique task identifier.
    :param description: What needs to be done.
    :param assigned_agent: Agent role responsible for execution.
    :param status: Current lifecycle status.
    :param priority: Urgency / importance level.
    :param result: Outcome data once completed.
    :param created_at: ISO-8601 creation timestamp.
    :param completed_at: ISO-8601 completion timestamp (if finished).
    """

    id: str
    description: str
    assigned_agent: str
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.NORMAL
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        return data


@dataclass
class AgentMessage:
    """A message exchanged between agents via the internal bus.

    :param sender: Name of the sending agent.
    :param recipient: Name of the receiving agent (or ``"broadcast"``).
    :param content: Payload of the message.
    :param message_type: Semantic type (``"request"``, ``"response"``, ``"event"``).
    :param timestamp: ISO-8601 timestamp.
    """

    sender: str
    recipient: str
    content: Dict[str, Any]
    message_type: str = "request"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OmniJARVISResponse:
    """Structured response returned to the user for every request.

    Follows the mandated output format:
    summary → steps → result → suggested next actions.

    :param summary: One-line summary of what happened.
    :param steps: List of ``{"agent": ..., "action": ..., "detail": ...}`` dicts.
    :param result: The main output / payload.
    :param suggestions: Proposed follow-up actions.
    :param timestamp: ISO-8601 timestamp.
    """

    summary: str
    steps: List[Dict[str, str]] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    suggestions: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def format_text(self) -> str:
        """Render the response as human-readable text."""
        lines: List[str] = []
        lines.append(f"📋 Summary: {self.summary}")
        if self.steps:
            lines.append("\n🔧 Steps:")
            for i, step in enumerate(self.steps, 1):
                agent = step.get("agent", "?")
                action = step.get("action", "?")
                detail = step.get("detail", "")
                lines.append(f"  {i}. [{agent}] {action} — {detail}")
        if self.result:
            lines.append(f"\n✅ Result: {self.result}")
        if self.suggestions:
            lines.append("\n💡 Suggested next actions:")
            for s in self.suggestions:
                lines.append(f"  • {s}")
        return "\n".join(lines)
