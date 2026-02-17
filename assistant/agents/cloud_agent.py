"""Cloud services agent – sync status, backups, and upload/download intent recording."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult

CONFIG_ROOT = Path("config")
CLOUD_SERVICES_FILE = CONFIG_ROOT / "cloud_services.json"

_ACTIONS: List[str] = [
    "sync_status", "list_services", "backup_files", "upload", "download",
]


class CloudAgent(BaseAgent):
    """Cloud services and file synchronisation agent."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="cloud",
            description="Cloud services, file sync, and backup management.",
            required_permissions=["cloud.sync", "cloud.upload", "cloud.download"],
            **kwargs,
        )

    def execute(self, **kwargs: Any) -> AgentResult:
        """Dispatch to the requested cloud action."""
        action: Optional[str] = kwargs.get("action")
        if action and action not in _ACTIONS:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Unknown action '{action}'. Valid: {_ACTIONS}")
        try:
            if action == "sync_status":
                return self._sync_status()
            if action == "list_services":
                return self._list_services()
            if action == "backup_files":
                return self._backup_files(
                    source_dir=kwargs.get("source_dir", ""),
                    backup_dir=kwargs.get("backup_dir", ""))
            if action == "upload":
                return self._upload(
                    file_path=kwargs.get("file_path", ""),
                    destination=kwargs.get("destination", ""))
            if action == "download":
                return self._download(
                    url=kwargs.get("url", ""),
                    destination=kwargs.get("destination", ""))
            return AgentResult(agent_name=self.name, status="error",
                               message="No action specified.")
        except Exception as exc:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Cloud agent error: {exc}")

    def _sync_status(self) -> AgentResult:
        """Report sync status of configured directories."""
        services = self._load_services()
        statuses: List[Dict[str, Any]] = []
        for svc in services:
            sync_dir = Path(svc.get("sync_dir", ""))
            statuses.append({
                "service": svc.get("name", "unknown"), "sync_dir": str(sync_dir),
                "exists": sync_dir.exists(),
                "status": "synced" if sync_dir.exists() else "not_found",
            })
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Checked {len(statuses)} services.",
                           data={"services": statuses}, actions_taken=["sync_status"])

    def _list_services(self) -> AgentResult:
        """List configured cloud services."""
        services = self._load_services()
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Found {len(services)} cloud services.",
                           data={"services": services}, actions_taken=["list_services"])

    def _backup_files(self, source_dir: str, backup_dir: str) -> AgentResult:
        """Create a backup of *source_dir* in *backup_dir*."""
        if not source_dir or not backup_dir:
            return AgentResult(agent_name=self.name, status="error",
                               message="'source_dir' and 'backup_dir' are required.")
        src = Path(source_dir)
        if not src.exists():
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Source directory does not exist: {source_dir}")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = Path(backup_dir) / f"backup_{timestamp}"
        shutil.copytree(src, dest)
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Backup created at {dest}.",
                           data={"source": str(src), "backup": str(dest)},
                           actions_taken=["backup_files"])

    def _upload(self, file_path: str, destination: str) -> AgentResult:
        """Record upload intent (extensible placeholder)."""
        if not file_path or not destination:
            return AgentResult(agent_name=self.name, status="error",
                               message="'file_path' and 'destination' are required.")
        return AgentResult(
            agent_name=self.name, status="success",
            message=f"Upload intent recorded: {file_path} -> {destination}.",
            data={"file_path": file_path, "destination": destination,
                   "timestamp": datetime.now(timezone.utc).isoformat(), "status": "pending"},
            actions_taken=["upload_intent"])

    def _download(self, url: str, destination: str) -> AgentResult:
        """Record download intent (extensible placeholder)."""
        if not url or not destination:
            return AgentResult(agent_name=self.name, status="error",
                               message="'url' and 'destination' are required.")
        return AgentResult(
            agent_name=self.name, status="success",
            message=f"Download intent recorded: {url} -> {destination}.",
            data={"url": url, "destination": destination,
                   "timestamp": datetime.now(timezone.utc).isoformat(), "status": "pending"},
            actions_taken=["download_intent"])

    def _load_services(self) -> List[Dict[str, Any]]:
        """Load cloud services configuration, creating an empty file if missing."""
        if not CLOUD_SERVICES_FILE.exists():
            CLOUD_SERVICES_FILE.parent.mkdir(parents=True, exist_ok=True)
            CLOUD_SERVICES_FILE.write_text(
                json.dumps({"services": []}, indent=2), encoding="utf-8")
        try:
            return json.loads(CLOUD_SERVICES_FILE.read_text(encoding="utf-8")).get("services", [])
        except (json.JSONDecodeError, OSError):
            return []
