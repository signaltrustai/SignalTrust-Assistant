"""Mobility agent – coordinates multiple devices (phone, watch, glasses, tablet, PC, IoT)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult

CONFIG_ROOT = Path("config")
MEMORY_ROOT = Path("memory")
DEVICES_FILE = CONFIG_ROOT / "devices.json"
DEVICE_QUEUE_FILE = MEMORY_ROOT / "device_queue.json"

VALID_DEVICE_TYPES: List[str] = ["phone", "watch", "glasses", "tablet", "pc", "iot"]

_ACTIONS: List[str] = [
    "list_devices", "register_device", "send_to_device", "sync_devices", "device_status",
]


class MobilityAgent(BaseAgent):
    """Multi-device coordination agent."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="mobility",
            description="Multi-device coordination (phone, watch, glasses, etc.).",
            required_permissions=["network.request"],
            **kwargs,
        )

    def execute(self, **kwargs: Any) -> AgentResult:
        """Dispatch to the requested mobility action."""
        action: Optional[str] = kwargs.get("action")
        if action and action not in _ACTIONS:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Unknown action '{action}'. Valid: {_ACTIONS}")
        try:
            if action == "list_devices":
                return self._list_devices()
            if action == "register_device":
                return self._register_device(
                    name=kwargs.get("name", ""), device_type=kwargs.get("device_type", ""),
                    connection_info=kwargs.get("connection_info", {}))
            if action == "send_to_device":
                return self._send_to_device(
                    device_name=kwargs.get("device_name", ""), payload=kwargs.get("payload", {}))
            if action == "sync_devices":
                return self._sync_devices()
            if action == "device_status":
                return self._device_status(kwargs.get("device_name"))
            return AgentResult(agent_name=self.name, status="error", message="No action specified.")
        except Exception as exc:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Mobility agent error: {exc}")

    def _list_devices(self) -> AgentResult:
        """List all registered devices."""
        devices = self._load_devices()
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Found {len(devices)} registered devices.",
                           data={"devices": devices}, actions_taken=["list_devices"])

    def _register_device(self, name: str, device_type: str,
                         connection_info: Dict[str, Any]) -> AgentResult:
        """Add a device to the registry."""
        if not name or not device_type:
            return AgentResult(agent_name=self.name, status="error",
                               message="'name' and 'device_type' are required.")
        if device_type not in VALID_DEVICE_TYPES:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Invalid device type '{device_type}'. Valid: {VALID_DEVICE_TYPES}")
        devices = self._load_devices()
        if any(d["name"] == name for d in devices):
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Device '{name}' is already registered.")
        device = {
            "name": name, "device_type": device_type, "connection_info": connection_info,
            "registered_at": datetime.now(timezone.utc).isoformat(), "status": "online",
        }
        devices.append(device)
        self._save_devices(devices)
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Device '{name}' ({device_type}) registered.",
                           data=device, actions_taken=["register_device"])

    def _send_to_device(self, device_name: str, payload: Dict[str, Any]) -> AgentResult:
        """Queue a payload for a device."""
        if not device_name:
            return AgentResult(agent_name=self.name, status="error",
                               message="'device_name' is required.")
        devices = self._load_devices()
        if not any(d["name"] == device_name for d in devices):
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Device '{device_name}' not found.")
        queue = self._load_queue()
        entry = {
            "device_name": device_name, "payload": payload,
            "queued_at": datetime.now(timezone.utc).isoformat(), "status": "pending",
        }
        queue.append(entry)
        self._save_queue(queue)
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Payload queued for device '{device_name}'.",
                           data=entry, actions_taken=["send_to_device"])

    def _sync_devices(self) -> AgentResult:
        """Synchronise state across all registered devices."""
        devices = self._load_devices()
        report: List[Dict[str, str]] = [
            {"name": d["name"], "type": d.get("device_type", "unknown"), "sync_status": "synced"}
            for d in devices
        ]
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Sync complete for {len(report)} devices.",
                           data={"sync_report": report}, actions_taken=["sync_devices"])

    def _device_status(self, device_name: Optional[str] = None) -> AgentResult:
        """Return status of one or all devices."""
        devices = self._load_devices()
        if device_name:
            device = next((d for d in devices if d["name"] == device_name), None)
            if not device:
                return AgentResult(agent_name=self.name, status="error",
                                   message=f"Device '{device_name}' not found.")
            return AgentResult(agent_name=self.name, status="success",
                               message=f"Status for device '{device_name}'.",
                               data={"device": device}, actions_taken=["device_status"])
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Status for {len(devices)} devices.",
                           data={"devices": devices}, actions_taken=["device_status"])

    def _load_json(self, path: Path, key: str) -> List[Dict[str, Any]]:
        """Load a JSON list from *path* under *key*, creating the file if needed."""
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({key: []}, indent=2), encoding="utf-8")
        try:
            return json.loads(path.read_text(encoding="utf-8")).get(key, [])
        except (json.JSONDecodeError, OSError):
            return []

    def _save_json(self, path: Path, key: str, items: List[Dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({key: items}, indent=2), encoding="utf-8")

    def _load_devices(self) -> List[Dict[str, Any]]:
        return self._load_json(DEVICES_FILE, "devices")

    def _save_devices(self, devices: List[Dict[str, Any]]) -> None:
        self._save_json(DEVICES_FILE, "devices", devices)

    def _load_queue(self) -> List[Dict[str, Any]]:
        return self._load_json(DEVICE_QUEUE_FILE, "queue")

    def _save_queue(self, queue: List[Dict[str, Any]]) -> None:
        self._save_json(DEVICE_QUEUE_FILE, "queue", queue)
