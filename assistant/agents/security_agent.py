"""Security agent – monitoring, permission auditing, config scanning, and alert management."""

from __future__ import annotations

import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult

CONFIG_ROOT = Path("config")
MEMORY_ROOT = Path("memory")
ALERTS_FILE = MEMORY_ROOT / "security_alerts.json"

_ACTIONS: List[str] = [
    "audit_report", "check_permissions", "scan_config", "list_alerts", "security_status",
]

_SECRET_PATTERNS: List[str] = [
    "password", "secret", "api_key", "apikey", "token", "private_key",
]


class SecurityAgent(BaseAgent):
    """Security monitoring and audit logging agent."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="security",
            description="Security monitoring, auditing, and alert management.",
            required_permissions=[],
            **kwargs,
        )

    def execute(self, **kwargs: Any) -> AgentResult:
        """Dispatch to the requested security action."""
        action: Optional[str] = kwargs.get("action")
        if action and action not in _ACTIONS:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Unknown action '{action}'. Valid: {_ACTIONS}")
        try:
            if action == "audit_report":
                return self._audit_report()
            if action == "check_permissions":
                return self._check_permissions()
            if action == "scan_config":
                return self._scan_config()
            if action == "list_alerts":
                return self._list_alerts()
            if action == "security_status":
                return self._security_status()
            return AgentResult(agent_name=self.name, status="error",
                               message="No action specified.")
        except Exception as exc:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Security agent error: {exc}")

    def _audit_report(self) -> AgentResult:
        """Generate an audit report from the permission manager's log."""
        if not self._permission_manager:
            return AgentResult(agent_name=self.name, status="success",
                               message="No permission manager configured — audit log empty.",
                               data={"audit_log": []}, actions_taken=["audit_report"])
        log = self._permission_manager.audit_log()
        return AgentResult(
            agent_name=self.name, status="success",
            message=f"Audit report: {len(log)} entries.",
            data={"total_entries": len(log), "audit_log": log,
                   "generated_at": datetime.now(timezone.utc).isoformat()},
            actions_taken=["audit_report"])

    def _check_permissions(self) -> AgentResult:
        """List all currently active permissions."""
        if not self._permission_manager:
            return AgentResult(agent_name=self.name, status="success",
                               message="No permission manager configured.",
                               data={"permissions": []}, actions_taken=["check_permissions"])
        permissions = self._permission_manager.list_permissions()
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Active permissions: {len(permissions)}.",
                           data={"permissions": permissions}, actions_taken=["check_permissions"])

    def _scan_config(self) -> AgentResult:
        """Scan the config directory for potential security issues."""
        issues: List[Dict[str, str]] = []
        if not CONFIG_ROOT.exists():
            return AgentResult(agent_name=self.name, status="success",
                               message="Config directory does not exist — nothing to scan.",
                               data={"issues": []}, actions_taken=["scan_config"])
        for config_file in CONFIG_ROOT.rglob("*"):
            if not config_file.is_file():
                continue
            try:
                mode = config_file.stat().st_mode
                if mode & stat.S_IROTH or mode & stat.S_IWOTH:
                    issues.append({"file": str(config_file),
                                   "issue": "world-readable or world-writable",
                                   "severity": "medium"})
            except OSError:
                pass
            if config_file.suffix in (".json", ".yaml", ".yml"):
                try:
                    content = config_file.read_text(encoding="utf-8").lower()
                    for pattern in _SECRET_PATTERNS:
                        if pattern in content:
                            issues.append({"file": str(config_file),
                                           "issue": f"Possible exposed secret ('{pattern}' found)",
                                           "severity": "high"})
                            break
                except OSError:
                    pass
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Config scan complete: {len(issues)} issues found.",
                           data={"issues": issues}, actions_taken=["scan_config"])

    def _list_alerts(self) -> AgentResult:
        """Return security alerts from ``memory/security_alerts.json``."""
        alerts = self._load_alerts()
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Found {len(alerts)} security alerts.",
                           data={"alerts": alerts}, actions_taken=["list_alerts"])

    def _security_status(self) -> AgentResult:
        """Overall security health summary."""
        alerts = self._load_alerts()
        open_alerts = [a for a in alerts if a.get("status") != "resolved"]
        perm_count = 0
        if self._permission_manager:
            perm_count = len(self._permission_manager.list_permissions())
        health = "healthy"
        if open_alerts:
            high = [a for a in open_alerts if a.get("severity") == "high"]
            health = "critical" if high else "warning"
        summary = {
            "health": health, "active_permissions": perm_count,
            "open_alerts": len(open_alerts), "total_alerts": len(alerts),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Security status: {health}.",
                           data=summary, actions_taken=["security_status"])

    @staticmethod
    def _load_alerts() -> List[Dict[str, Any]]:
        """Load security alerts, creating the file if needed."""
        if not ALERTS_FILE.exists():
            ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            ALERTS_FILE.write_text(json.dumps({"alerts": []}, indent=2), encoding="utf-8")
        try:
            return json.loads(ALERTS_FILE.read_text(encoding="utf-8")).get("alerts", [])
        except (json.JSONDecodeError, OSError):
            return []
