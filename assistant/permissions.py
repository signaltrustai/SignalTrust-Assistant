"""
Permission and security system for OmniJARVIS.

Every action must require explicit user authorization before execution.
Provides a centralized permission manager with audit logging, scoped grants,
and persistent storage of standing permissions.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIG_ROOT = Path("config")
PERMISSIONS_FILE = CONFIG_ROOT / "permissions.json"

ACTION_TYPES: List[str] = [
    "system.execute",
    "system.shutdown",
    "system.config",
    "communication.send",
    "communication.read",
    "cloud.sync",
    "cloud.upload",
    "cloud.download",
    "file.read",
    "file.modify",
    "file.delete",
    "network.request",
    "network.listen",
    "agent.spawn",
    "agent.delegate",
    "memory.write",
    "memory.delete",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PermissionScope(str, Enum):
    """Scope that controls how long a granted permission remains active."""

    ONCE = "once"
    SESSION = "session"
    ALWAYS = "always"


class PermissionStatus(str, Enum):
    """Status of a permission request."""

    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"


class AuditDecision(str, Enum):
    """Decision recorded in the audit log."""

    REQUESTED = "requested"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    AUTO_GRANTED = "auto_granted"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PermissionRequest:
    """Represents a single request for user authorization.

    :param action: Action type identifier (e.g. ``"file.modify"``).
    :param description: Human-readable explanation of what will happen.
    :param details: Optional extra context about the action.
    :param timestamp: ISO-8601 timestamp of when the request was created.
    :param status: Current status of the request.
    """

    action: str
    description: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: PermissionStatus = PermissionStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the request to a plain dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class SecurityAuditEntry:
    """Immutable record of a permission decision in the audit trail.

    :param action: Action type that was checked.
    :param description: Human-readable description of the action.
    :param decision: The decision that was made.
    :param timestamp: ISO-8601 timestamp of when the decision was recorded.
    :param scope: Permission scope associated with the decision, if any.
    """

    action: str
    description: str
    decision: AuditDecision
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scope: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entry to a plain dictionary."""
        data = asdict(self)
        data["decision"] = self.decision.value
        return data


# ---------------------------------------------------------------------------
# PermissionManager
# ---------------------------------------------------------------------------

class PermissionManager:
    """Centralized manager for action permissions and security auditing.

    Maintains an in-memory table of standing permissions (session and
    persistent), an audit trail of every permission decision, and persists
    ``"always"``-scoped grants to ``config/permissions.json``.

    Usage::

        pm = PermissionManager()
        req = pm.request_permission("file.modify", "Overwrite config file")
        # ... present *req* to the user for approval ...
        pm.grant_permission("file.modify", scope="session")
        if pm.check_permission("file.modify"):
            # proceed with action
            ...
    """

    def __init__(self, permissions_file: Optional[Path] = None) -> None:
        """Initialize the permission manager.

        :param permissions_file: Path to the JSON file used for persistent
            ``"always"``-scoped permissions.  Defaults to
            ``config/permissions.json``.
        """
        self._permissions_file: Path = permissions_file or PERMISSIONS_FILE
        self._session_permissions: Dict[str, str] = {}
        self._audit_trail: List[SecurityAuditEntry] = []
        self._persistent_permissions: Dict[str, str] = {}
        self._load_persistent_permissions()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_permission(
        self,
        action: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> PermissionRequest:
        """Create a new permission request for the given action.

        If a standing permission already exists (session or persistent) the
        returned request is automatically marked as granted and an
        ``auto_granted`` audit entry is recorded.

        :param action: Action type identifier (e.g. ``"system.execute"``).
        :param description: Human-readable explanation of the action.
        :param details: Optional additional context.
        :return: A :class:`PermissionRequest` representing the request.
        """
        self._validate_action(action)
        request = PermissionRequest(
            action=action,
            description=description,
            details=details,
        )

        if self.check_permission(action):
            request.status = PermissionStatus.GRANTED
            self._record_audit(
                action=action,
                description=description,
                decision=AuditDecision.AUTO_GRANTED,
                scope=self._resolve_scope(action),
            )
        else:
            self._record_audit(
                action=action,
                description=description,
                decision=AuditDecision.REQUESTED,
            )

        return request

    def check_permission(self, action: str) -> bool:
        """Check whether a standing permission exists for *action*.

        :param action: Action type identifier.
        :return: ``True`` if there is an active session or persistent grant.
        """
        self._validate_action(action)
        return (
            action in self._session_permissions
            or action in self._persistent_permissions
        )

    def grant_permission(self, action: str, scope: str = "once") -> None:
        """Grant a permission for *action* with the specified *scope*.

        :param action: Action type identifier.
        :param scope: One of ``"once"``, ``"session"``, or ``"always"``.
            * ``"once"``    – no standing grant is stored; a single audit
              entry is recorded.
            * ``"session"`` – the grant persists in memory for the current
              session.
            * ``"always"``  – the grant is persisted to disk and survives
              restarts.
        :raises ValueError: If *scope* is not a recognised value.
        """
        self._validate_action(action)
        permission_scope = PermissionScope(scope)

        if permission_scope == PermissionScope.SESSION:
            self._session_permissions[action] = scope
        elif permission_scope == PermissionScope.ALWAYS:
            self._persistent_permissions[action] = scope
            self._save_persistent_permissions()

        self._record_audit(
            action=action,
            description=f"Permission granted ({scope})",
            decision=AuditDecision.GRANTED,
            scope=scope,
        )

    def deny_permission(self, action: str) -> None:
        """Deny (and record) a permission request for *action*.

        :param action: Action type identifier.
        """
        self._validate_action(action)
        self._record_audit(
            action=action,
            description="Permission denied",
            decision=AuditDecision.DENIED,
        )

    def revoke_permission(self, action: str) -> None:
        """Revoke any standing permission for *action*.

        Removes both session and persistent grants and records an audit
        entry.

        :param action: Action type identifier.
        """
        self._validate_action(action)
        self._session_permissions.pop(action, None)
        if action in self._persistent_permissions:
            del self._persistent_permissions[action]
            self._save_persistent_permissions()

        self._record_audit(
            action=action,
            description="Permission revoked",
            decision=AuditDecision.REVOKED,
        )

    def list_permissions(self) -> List[Dict[str, Any]]:
        """Return all currently active standing permissions.

        :return: A list of dicts, each with ``"action"`` and ``"scope"``
            keys.
        """
        permissions: List[Dict[str, Any]] = []
        for action, scope in self._session_permissions.items():
            permissions.append({"action": action, "scope": scope})
        for action, scope in self._persistent_permissions.items():
            permissions.append({"action": action, "scope": scope})
        return permissions

    def audit_log(self) -> List[Dict[str, Any]]:
        """Return the full in-memory audit trail.

        :return: A list of serialized :class:`SecurityAuditEntry` dicts,
            ordered chronologically.
        """
        return [entry.to_dict() for entry in self._audit_trail]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_action(self, action: str) -> None:
        """Raise if *action* is not a registered action type.

        :param action: Action type identifier.
        :raises ValueError: If the action is unknown.
        """
        if action not in ACTION_TYPES:
            raise ValueError(
                f"Unknown action type: {action!r}. "
                f"Registered types: {', '.join(ACTION_TYPES)}"
            )

    def _resolve_scope(self, action: str) -> Optional[str]:
        """Return the scope string for an existing standing permission.

        :param action: Action type identifier.
        :return: The scope string, or ``None`` if no standing grant exists.
        """
        if action in self._session_permissions:
            return self._session_permissions[action]
        if action in self._persistent_permissions:
            return self._persistent_permissions[action]
        return None

    def _record_audit(
        self,
        action: str,
        description: str,
        decision: AuditDecision,
        scope: Optional[str] = None,
    ) -> None:
        """Append an entry to the in-memory audit trail.

        :param action: Action type identifier.
        :param description: Human-readable description.
        :param decision: The audit decision.
        :param scope: Optional scope associated with the decision.
        """
        entry = SecurityAuditEntry(
            action=action,
            description=description,
            decision=decision,
            scope=scope,
        )
        self._audit_trail.append(entry)

    def _load_persistent_permissions(self) -> None:
        """Load persistent permissions from the JSON file on disk."""
        if not self._permissions_file.exists():
            self._persistent_permissions = {}
            return
        try:
            data = json.loads(
                self._permissions_file.read_text(encoding="utf-8")
            )
            self._persistent_permissions = data.get("permissions", {})
        except (json.JSONDecodeError, OSError):
            self._persistent_permissions = {}

    def _save_persistent_permissions(self) -> None:
        """Persist ``"always"``-scoped permissions to the JSON file."""
        self._permissions_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"permissions": self._persistent_permissions}
        self._permissions_file.write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
