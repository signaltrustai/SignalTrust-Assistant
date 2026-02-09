"""
FocusAgent — the first autonomous agent for SignalTrust Assistant.

Loads the next pending task, analyzes it with the AI module,
generates an execution plan, logs the action, and saves context to memory.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from assistant import memory, tasks
from assistant.ai import agent as ai_agent

AGENT_LOGS_DIR = Path("memory/agent-logs")


class FocusAgent:
    """
    An autonomous agent that focuses on the next pending task.

    Workflow:
        1. Load the next task from the plan file.
        2. Analyze the task using the AI module.
        3. Generate a short execution plan.
        4. Write a log entry to ``memory/agent-logs/``.
        5. Save a memory entry via ``memory.save_context()``.
        6. Return a structured report.
    """

    def __init__(self, task_file: str = "todo-v1.md") -> None:
        self.task_file = task_file

    def run(self) -> Dict[str, Any]:
        """Execute the agent workflow and return a structured report."""

        # 1. Load the next pending task
        task = tasks.get_next_task(self.task_file)
        if task is None:
            return {
                "status": "no_task",
                "message": "No pending tasks found.",
            }

        # 2. Analyze the task with the AI module
        analysis = ai_agent.analyze(task["title"])

        # 3. Generate a short execution plan
        plan = self._build_plan(task, analysis)

        # 4. Write a log entry
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_path = self._write_log(task, analysis, plan, timestamp)

        # 5. Save a memory entry
        memory_key = f"agent-focus-{timestamp}"
        memory.save_context(
            memory_key,
            f"# FocusAgent Report\n\n"
            f"**Task:** {task['title']}\n\n"
            f"**Analysis:**\n{analysis}\n\n"
            f"**Plan:**\n{plan}\n",
            meta={"tags": ["agent", "focus"], "source": "focus-agent"},
        )

        # 6. Return structured report
        return {
            "status": "completed",
            "task": task,
            "analysis": analysis,
            "plan": plan,
            "log_file": str(log_path),
            "memory_key": memory_key,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_plan(task: Dict[str, Any], analysis: str) -> str:
        """Create a simple textual execution plan."""
        return (
            f"1. Review task: {task['title']}\n"
            f"2. Apply insights from analysis\n"
            f"3. Execute required changes\n"
            f"4. Verify completion"
        )

    @staticmethod
    def _write_log(
        task: Dict[str, Any],
        analysis: str,
        plan: str,
        timestamp: str,
    ) -> Path:
        """Persist a log file in ``memory/agent-logs/``."""
        AGENT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_path = AGENT_LOGS_DIR / f"focus-{timestamp}.md"
        log_path.write_text(
            f"# FocusAgent Log — {timestamp}\n\n"
            f"## Task\n{task['title']}\n\n"
            f"## Analysis\n{analysis}\n\n"
            f"## Plan\n{plan}\n",
            encoding="utf-8",
        )
        return log_path
