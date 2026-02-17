"""System control agent – cross-platform system info and guarded command execution."""

from __future__ import annotations

import os
import platform
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult

_ACTIONS: List[str] = [
    "list_processes", "system_info", "disk_usage", "open_app", "execute_command",
]


class SystemAgent(BaseAgent):
    """PC / laptop system control agent."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="system",
            description="PC/laptop system control and information.",
            required_permissions=["system.execute"],
            **kwargs,
        )

    def execute(self, **kwargs: Any) -> AgentResult:
        """Dispatch to the requested system action."""
        action: Optional[str] = kwargs.get("action")
        command: Optional[str] = kwargs.get("command")
        if action and action not in _ACTIONS:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Unknown action '{action}'. Valid: {_ACTIONS}")
        try:
            if action == "list_processes":
                return self._list_processes()
            if action == "system_info":
                return self._system_info()
            if action == "disk_usage":
                return self._disk_usage()
            if action == "open_app":
                return self._open_app(kwargs.get("app_name", ""))
            if action == "execute_command" or command:
                return self._execute_command(command or "")
            return self._system_info()
        except Exception as exc:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"System agent error: {exc}")

    def _list_processes(self) -> AgentResult:
        """Return running process information (cross-platform)."""
        processes: List[Dict[str, Any]] = []
        if platform.system() != "Windows":
            proc_path = Path("/proc")
            if proc_path.exists():
                for entry in proc_path.iterdir():
                    if entry.name.isdigit():
                        try:
                            cmdline = (entry / "cmdline").read_text().replace("\x00", " ").strip()
                            if cmdline:
                                processes.append({"pid": int(entry.name), "command": cmdline})
                        except (OSError, PermissionError):
                            continue
        else:
            processes.append({"note": "Use 'tasklist' via execute_command on Windows."})
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Found {len(processes)} processes.",
                           data={"processes": processes[:100]}, actions_taken=["list_processes"])

    def _system_info(self) -> AgentResult:
        """Return OS, architecture, hostname, and Python version."""
        import sys
        info = {
            "os": platform.system(), "os_release": platform.release(),
            "architecture": platform.machine(), "hostname": platform.node(),
            "python_version": sys.version, "cpu_count": os.cpu_count(),
        }
        return AgentResult(agent_name=self.name, status="success",
                           message="System information retrieved.",
                           data=info, actions_taken=["system_info"])

    def _disk_usage(self) -> AgentResult:
        """Return disk space information for the root partition."""
        root = Path.home().anchor or "/"
        usage = shutil.disk_usage(root)
        data = {
            "total_gb": round(usage.total / (1024 ** 3), 2),
            "used_gb": round(usage.used / (1024 ** 3), 2),
            "free_gb": round(usage.free / (1024 ** 3), 2),
            "usage_percent": round(usage.used / usage.total * 100, 1),
        }
        return AgentResult(agent_name=self.name, status="success",
                           message="Disk usage retrieved.",
                           data=data, actions_taken=["disk_usage"])

    def _open_app(self, app_name: str) -> AgentResult:
        """Return the command that WOULD open an application (placeholder)."""
        if not app_name:
            return AgentResult(agent_name=self.name, status="error",
                               message="No application name provided.")
        system = platform.system()
        if system == "Darwin":
            cmd = f"open -a {app_name}"
        elif system == "Windows":
            cmd = f"start {app_name}"
        else:
            cmd = app_name
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Would run: {cmd} (not executed without explicit permission).",
                           data={"command": cmd, "app_name": app_name},
                           actions_taken=["open_app_placeholder"])

    def _execute_command(self, command: str) -> AgentResult:
        """Run a shell command (shell=False, timeout=30). Requires system.execute permission."""
        if not command:
            return AgentResult(agent_name=self.name, status="error",
                               message="No command provided.")
        if self._permission_manager and not self._permission_manager.check_permission("system.execute"):
            return AgentResult(agent_name=self.name, status="pending_permission",
                               message="system.execute permission required to run commands.",
                               data={"missing_permissions": ["system.execute"]})
        cmd_parts = shlex.split(command)
        result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)
        return AgentResult(
            agent_name=self.name,
            status="success" if result.returncode == 0 else "error",
            message=f"Command exited with code {result.returncode}.",
            data={"stdout": result.stdout, "stderr": result.stderr,
                   "returncode": result.returncode},
            actions_taken=["execute_command"])
