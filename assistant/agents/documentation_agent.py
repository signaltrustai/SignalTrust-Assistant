"""
Documentation Agent — Writes docs, changelogs, reports, and structured summaries.

Keeps projects and knowledge clean, organised, and always up-to-date.
Uses AI when available for high-quality content generation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult


class DocumentationAgent(BaseAgent):
    """Agent that generates and maintains documentation artifacts.

    Actions: ``generate_readme``, ``generate_changelog``, ``generate_report``,
    ``session_summary``, ``write_doc``, ``update_doc``.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="documentation",
            description=(
                "Writes documentation, changelogs, reports, and "
                "structured summaries. Keeps projects clean and "
                "organised."
            ),
            required_permissions=["file.modify"],
            **kwargs,
        )

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> AgentResult:
        action = kwargs.get("action")
        message = kwargs.get("message", "")

        if action == "generate_readme":
            return self._generate_readme(
                kwargs.get("project_name", ""),
                kwargs.get("description", message),
                kwargs.get("output_path"),
            )
        if action == "generate_changelog":
            return self._generate_changelog(
                kwargs.get("entries", []),
                kwargs.get("output_path"),
            )
        if action == "generate_report":
            return self._generate_report(
                kwargs.get("title", "Report"),
                kwargs.get("content", message),
                kwargs.get("output_path"),
            )
        if action == "session_summary":
            return self._session_summary(kwargs.get("events", []))
        if action == "write_doc":
            return self._write_doc(
                kwargs.get("title", ""),
                kwargs.get("content", message),
                kwargs.get("output_path"),
            )
        if action == "update_doc":
            return self._update_doc(
                kwargs.get("file_path", ""),
                kwargs.get("instruction", message),
            )

        if message:
            return self._write_doc("Auto-generated", message)

        return AgentResult(
            agent_name=self.name,
            status="error",
            message="No action or message. Use: generate_readme, generate_changelog, generate_report, session_summary, write_doc, update_doc.",
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _generate_readme(
        self, project_name: str, description: str, output_path: Optional[str] = None,
    ) -> AgentResult:
        content = self._ai_generate(
            f"Generate a professional README.md for a project named "
            f"'{project_name}'. Description: {description}\n"
            f"Include: overview, features, installation, usage, "
            f"configuration, contributing, and license sections."
        )
        return self._write_output(content, output_path, "README generated.")

    def _generate_changelog(
        self, entries: List[Dict[str, str]], output_path: Optional[str] = None,
    ) -> AgentResult:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if entries:
            entry_text = "\n".join(
                f"- {e.get('type', 'change')}: {e.get('description', '')}"
                for e in entries
            )
        else:
            entry_text = "- Initial release"

        content = (
            f"# Changelog\n\n"
            f"## [{now}]\n\n"
            f"{entry_text}\n"
        )
        return self._write_output(content, output_path, "Changelog generated.")

    def _generate_report(
        self, title: str, content: str, output_path: Optional[str] = None,
    ) -> AgentResult:
        report = self._ai_generate(
            f"Generate a structured professional report.\n"
            f"Title: {title}\n"
            f"Content/Data: {content}\n"
            f"Include: executive summary, findings, analysis, "
            f"recommendations, and conclusion."
        )
        return self._write_output(report, output_path, f"Report '{title}' generated.")

    def _session_summary(self, events: List[Dict[str, Any]]) -> AgentResult:
        if not events:
            summary = "No events recorded in this session."
        else:
            lines = [f"## Session Summary — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"]
            for i, event in enumerate(events, 1):
                agent = event.get("agent", "unknown")
                action = event.get("action", "unknown")
                detail = event.get("detail", "")
                lines.append(f"{i}. **[{agent}]** {action}: {detail}")
            lines.append(f"\n**Total actions:** {len(events)}")
            summary = "\n".join(lines)

        return AgentResult(
            agent_name=self.name,
            status="success",
            message="Session summary generated.",
            data={"summary": summary},
            actions_taken=["generate_session_summary"],
        )

    def _write_doc(
        self, title: str, content: str, output_path: Optional[str] = None,
    ) -> AgentResult:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        doc = f"# {title}\n\n*Generated: {now}*\n\n{content}\n"
        return self._write_output(doc, output_path, f"Document '{title}' created.")

    def _update_doc(self, file_path: str, instruction: str) -> AgentResult:
        if not file_path:
            return AgentResult(
                agent_name=self.name, status="error",
                message="file_path is required for update_doc.",
            )
        path = Path(file_path)
        if not path.is_file():
            return AgentResult(
                agent_name=self.name, status="error",
                message=f"File not found: {file_path}",
            )
        original = path.read_text(encoding="utf-8")
        updated = self._ai_generate(
            f"Update the following document according to this instruction:\n"
            f"{instruction}\n\nOriginal document:\n{original[:8000]}"
        )
        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Document update prepared (review before saving to {file_path}).",
            data={"original": original, "updated": updated, "file_path": file_path},
            actions_taken=["read_doc", "generate_update"],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_output(
        self, content: str, output_path: Optional[str], message: str,
    ) -> AgentResult:
        data: Dict[str, Any] = {"content": content}
        actions = ["generate_content"]

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            data["file_path"] = str(path)
            actions.append("write_file")
            message += f" Written to {path}."

        return AgentResult(
            agent_name=self.name, status="success",
            message=message, data=data, actions_taken=actions,
        )

    def _ai_generate(self, prompt: str) -> str:
        try:
            from assistant.ai.client import ask_ai
            return ask_ai(prompt)
        except Exception:
            return f"[AI unavailable] Prompt: {prompt[:200]}…"
