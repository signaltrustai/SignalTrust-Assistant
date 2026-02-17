"""Productivity agent – manages routines, workflows, and daily activity summaries."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult

CONFIG_ROOT = Path("config")
MEMORY_ROOT = Path("memory")
ROUTINES_FILE = CONFIG_ROOT / "routines.json"
WORKFLOWS_FILE = CONFIG_ROOT / "workflows.json"
HISTORY_FILE = MEMORY_ROOT / "interaction_history.json"

_ACTIONS: List[str] = [
    "create_routine", "list_routines", "run_routine",
    "create_workflow", "list_workflows", "daily_summary",
]


class ProductivityAgent(BaseAgent):
    """Workflow automation and routine management agent."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="productivity",
            description="Workflow automation, routines, and daily summaries.",
            required_permissions=["system.execute", "file.modify"],
            **kwargs,
        )

    def execute(self, **kwargs: Any) -> AgentResult:
        """Dispatch to the requested productivity action."""
        action: Optional[str] = kwargs.get("action")
        if action and action not in _ACTIONS:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Unknown action '{action}'. Valid: {_ACTIONS}")
        try:
            if action == "create_routine":
                return self._create_routine(
                    name=kwargs.get("name", ""), steps=kwargs.get("steps", []),
                    schedule=kwargs.get("schedule"))
            if action == "list_routines":
                return self._list_routines()
            if action == "run_routine":
                return self._run_routine(kwargs.get("name", ""))
            if action == "create_workflow":
                return self._create_workflow(
                    name=kwargs.get("name", ""), steps=kwargs.get("steps", []),
                    triggers=kwargs.get("triggers"))
            if action == "list_workflows":
                return self._list_workflows()
            if action == "daily_summary":
                return self._daily_summary()
            return AgentResult(agent_name=self.name, status="error", message="No action specified.")
        except Exception as exc:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Productivity agent error: {exc}")

    def _create_routine(self, name: str, steps: List[str],
                        schedule: Optional[str] = None) -> AgentResult:
        """Save a named routine (list of steps)."""
        if not name or not steps:
            return AgentResult(agent_name=self.name, status="error",
                               message="'name' and 'steps' are required.")
        routines = self._load_json(ROUTINES_FILE, "routines")
        routine = {"name": name, "steps": steps, "schedule": schedule,
                    "created_at": datetime.now(timezone.utc).isoformat()}
        routines = [r for r in routines if r.get("name") != name]
        routines.append(routine)
        self._save_json(ROUTINES_FILE, "routines", routines)
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Routine '{name}' saved with {len(steps)} steps.",
                           data=routine, actions_taken=["create_routine"])

    def _list_routines(self) -> AgentResult:
        """List all saved routines."""
        routines = self._load_json(ROUTINES_FILE, "routines")
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Found {len(routines)} routines.",
                           data={"routines": routines}, actions_taken=["list_routines"])

    def _run_routine(self, name: str) -> AgentResult:
        """Execute a routine step-by-step (dry-run)."""
        if not name:
            return AgentResult(agent_name=self.name, status="error",
                               message="Routine 'name' is required.")
        routines = self._load_json(ROUTINES_FILE, "routines")
        routine = next((r for r in routines if r.get("name") == name), None)
        if not routine:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Routine '{name}' not found.")
        execution: List[Dict[str, str]] = [
            {"step": idx, "action": step, "status": "would_execute"}
            for idx, step in enumerate(routine.get("steps", []), start=1)
        ]
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Dry-run of routine '{name}' ({len(execution)} steps).",
                           data={"routine": name, "execution": execution},
                           actions_taken=["run_routine"])

    def _create_workflow(self, name: str, steps: List[str],
                         triggers: Optional[List[str]] = None) -> AgentResult:
        """Create a multi-step workflow definition."""
        if not name or not steps:
            return AgentResult(agent_name=self.name, status="error",
                               message="'name' and 'steps' are required.")
        workflows = self._load_json(WORKFLOWS_FILE, "workflows")
        workflow = {"name": name, "steps": steps, "triggers": triggers or [],
                     "created_at": datetime.now(timezone.utc).isoformat()}
        workflows = [w for w in workflows if w.get("name") != name]
        workflows.append(workflow)
        self._save_json(WORKFLOWS_FILE, "workflows", workflows)
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Workflow '{name}' created with {len(steps)} steps.",
                           data=workflow, actions_taken=["create_workflow"])

    def _list_workflows(self) -> AgentResult:
        """List all workflows."""
        workflows = self._load_json(WORKFLOWS_FILE, "workflows")
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Found {len(workflows)} workflows.",
                           data={"workflows": workflows}, actions_taken=["list_workflows"])

    def _daily_summary(self) -> AgentResult:
        """Generate a daily activity summary from interaction history."""
        today = datetime.now(timezone.utc).date().isoformat()
        interactions: List[Dict[str, Any]] = []
        if HISTORY_FILE.exists():
            try:
                data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                interactions = [e for e in data.get("interactions", [])
                                if e.get("timestamp", "").startswith(today)]
            except (json.JSONDecodeError, OSError):
                pass
        summary = {
            "date": today, "total_interactions": len(interactions),
            "agents_used": list({i.get("agent_used", "unknown") for i in interactions}),
            "queries": [i.get("query", "") for i in interactions[:20]],
        }
        return AgentResult(agent_name=self.name, status="success",
                           message=f"Daily summary for {today}: {len(interactions)} interactions.",
                           data=summary, actions_taken=["daily_summary"])

    @staticmethod
    def _load_json(path: Path, key: str) -> List[Dict[str, Any]]:
        """Load a JSON list from *path* under *key*, creating the file if needed."""
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({key: []}, indent=2), encoding="utf-8")
        try:
            return json.loads(path.read_text(encoding="utf-8")).get(key, [])
        except (json.JSONDecodeError, OSError):
            return []

    @staticmethod
    def _save_json(path: Path, key: str, items: List[Dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({key: items}, indent=2), encoding="utf-8")
