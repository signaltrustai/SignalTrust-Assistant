"""
Executive Agent (Commander) — The brain of OmniJARVIS.

Interprets user requests, decomposes them into tasks, assigns tasks
to specialised agents, ensures completion, and reports back with a
structured response following the mandated output format.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult
from assistant.core.models import OmniJARVISResponse, Task, TaskStatus


class ExecutiveAgent(BaseAgent):
    """Top-level orchestrator that interprets intent and delegates work.

    The Executive Agent is the fallback handler when no specialised
    agent matches the user's intent.  It can also decompose complex
    multi-step requests into sub-tasks.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="executive",
            description=(
                "Interprets requests, decomposes them into tasks, "
                "assigns them to specialised agents, and reports results."
            ),
            required_permissions=[],
            **kwargs,
        )
        self._task_log: List[Task] = []

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> AgentResult:
        action = kwargs.get("action")
        if action == "decompose":
            return self._decompose(kwargs.get("request", ""))
        if action == "status":
            return self._task_status()
        # Default: interpret a raw message
        return self._interpret(kwargs.get("message", kwargs.get("request", "")))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _interpret(self, message: str) -> AgentResult:
        """Interpret a free-form user message and produce a plan."""
        if not message:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message="No message provided to interpret.",
            )

        # Use AI if available for deeper understanding
        analysis = self._ai_interpret(message)

        return AgentResult(
            agent_name=self.name,
            status="success",
            message="Request interpreted and plan generated.",
            data={
                "original_request": message,
                "interpretation": analysis,
                "plan": self._generate_plan(message, analysis),
            },
            actions_taken=["interpret_request", "generate_plan"],
        )

    def _decompose(self, request: str) -> AgentResult:
        """Break a complex request into discrete assignable tasks."""
        if not request:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message="No request provided to decompose.",
            )

        tasks = self._create_tasks(request)
        self._task_log.extend(tasks)

        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Request decomposed into {len(tasks)} task(s).",
            data={"tasks": [t.to_dict() for t in tasks]},
            actions_taken=["decompose_request"],
        )

    def _task_status(self) -> AgentResult:
        """Report on all tracked tasks."""
        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Tracking {len(self._task_log)} task(s).",
            data={"tasks": [t.to_dict() for t in self._task_log]},
            actions_taken=["report_status"],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ai_interpret(self, message: str) -> str:
        """Use AI for deeper semantic understanding (graceful fallback)."""
        try:
            from assistant.ai.client import ask_ai
            prompt = (
                "You are OmniJARVIS, a personal AI assistant. "
                "Interpret the following user request concisely. "
                "Identify the intent, required agents, and key actions:\n\n"
                f"{message}"
            )
            return ask_ai(prompt)
        except Exception:
            return f"Direct interpretation: {message}"

    def _generate_plan(self, message: str, analysis: str) -> List[Dict[str, str]]:
        """Generate a step-by-step execution plan."""
        msg = message.lower()
        steps: List[Dict[str, str]] = []

        step_map = [
            (["code", "program", "coder", "génère"], "code", "Generate / modify code"),
            (["analyse", "analyze", "review"], "analysis", "Analyse content"),
            (["fichier", "file", "dossier"], "system", "File system operation"),
            (["souviens", "remember", "note"], "memory", "Store in memory"),
            (["document", "rapport", "readme"], "documentation", "Generate documentation"),
            (["message", "email", "meeting"], "communication", "Handle communication"),
            (["cloud", "backup", "sync"], "cloud", "Cloud operation"),
            (["routine", "workflow", "automate"], "productivity", "Automate workflow"),
        ]

        for keywords, agent, action in step_map:
            if any(kw in msg for kw in keywords):
                steps.append({"agent": agent, "action": action, "detail": message})

        if not steps:
            steps.append({
                "agent": "executive",
                "action": "General processing",
                "detail": message,
            })

        return steps

    def _create_tasks(self, request: str) -> List[Task]:
        """Create Task objects from a request."""
        plan = self._generate_plan(request, "")
        tasks: List[Task] = []
        for step in plan:
            tasks.append(Task(
                id=str(uuid.uuid4())[:8],
                description=step.get("detail", request),
                assigned_agent=step.get("agent", "executive"),
            ))
        return tasks
