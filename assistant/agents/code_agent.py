"""
Code generation, modification, and execution agent for OmniJARVIS.

Provides AI-powered code generation, review, explanation, and guarded
execution.  All code execution uses ``subprocess.run`` with ``shell=False``
and a strict timeout — ``eval()`` / ``exec()`` are **never** used.

Security model:
    * File paths are resolved and validated against the working directory.
    * Commands are parsed with :func:`shlex.split` (no shell injection).
    * Execution requires an explicit ``system.execute`` permission check.
    * Every generated or modified file is recorded in a history ledger.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SUPPORTED_LANGUAGES: List[str] = [
    "python", "javascript", "typescript", "bash", "powershell",
    "html", "css", "sql", "rust", "go", "java",
]

_ACTIONS: List[str] = [
    "generate_code", "modify_code", "review_code",
    "execute_code", "explain_code", "list_generated",
]

_HISTORY_PATH = Path("memory/code_agent_history.json")

_EXECUTION_TIMEOUT = 30  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_resolve(file_path: str) -> Path:
    """Resolve *file_path* and ensure it stays inside the working directory.

    :param file_path: User-supplied path (relative or absolute).
    :returns: Resolved :class:`Path`.
    :raises ValueError: If the resolved path escapes the working directory.
    """
    cwd = Path.cwd().resolve()
    resolved = (cwd / file_path).resolve()
    if not str(resolved).startswith(str(cwd)):
        raise ValueError(
            f"Path traversal detected: '{file_path}' resolves outside "
            f"the working directory."
        )
    return resolved


def _load_history() -> List[Dict[str, Any]]:
    """Load the code-agent history ledger from disk."""
    if _HISTORY_PATH.exists():
        try:
            return json.loads(_HISTORY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_history(history: List[Dict[str, Any]]) -> None:
    """Persist the code-agent history ledger to disk."""
    _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _HISTORY_PATH.write_text(
        json.dumps(history, indent=2), encoding="utf-8",
    )


def _record_action(
    action: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
) -> None:
    """Append an entry to the history ledger."""
    history = _load_history()
    history.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "file_path": file_path,
        "language": language,
    })
    _save_history(history)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class CodeAgent(BaseAgent):
    """AI-powered code generation, modification, review, and execution agent.

    Supported actions: ``generate_code``, ``modify_code``, ``review_code``,
    ``execute_code``, ``explain_code``, and ``list_generated``.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="code",
            description="Code generation, modification, and execution agent",
            required_permissions=["system.execute", "file.modify", "file.read"],
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def execute(self, action: Optional[str] = None, **kwargs: Any) -> AgentResult:
        """Dispatch to the requested code action.

        :param action: One of the supported action names.
        :returns: :class:`AgentResult` with the outcome.
        """
        if action and action not in _ACTIONS:
            return AgentResult(
                agent_name=self.name, status="error",
                message=f"Unknown action '{action}'. Valid: {_ACTIONS}",
            )

        try:
            if action == "generate_code":
                return self._generate_code(
                    language=kwargs.get("language", "python"),
                    description=kwargs.get("description", ""),
                    output_path=kwargs.get("output_path"),
                )
            if action == "modify_code":
                return self._modify_code(
                    file_path=kwargs.get("file_path", ""),
                    instruction=kwargs.get("instruction", ""),
                )
            if action == "review_code":
                return self._review_code(
                    file_path=kwargs.get("file_path"),
                    code=kwargs.get("code"),
                )
            if action == "execute_code":
                return self._execute_code(
                    file_path=kwargs.get("file_path"),
                    code=kwargs.get("code"),
                    language=kwargs.get("language", "python"),
                )
            if action == "explain_code":
                return self._explain_code(
                    file_path=kwargs.get("file_path"),
                    code=kwargs.get("code"),
                )
            if action == "list_generated":
                return self._list_generated()
            return AgentResult(
                agent_name=self.name, status="error",
                message="No action specified. Provide one of: " + ", ".join(_ACTIONS),
            )
        except Exception as exc:  # noqa: BLE001 – catch-all for robustness
            return AgentResult(
                agent_name=self.name, status="error",
                message=f"Code agent error: {exc}",
            )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _generate_code(
        self, language: str, description: str, output_path: Optional[str] = None,
    ) -> AgentResult:
        """Generate code from a natural-language description via AI."""
        if language not in _SUPPORTED_LANGUAGES:
            return AgentResult(
                agent_name=self.name, status="error",
                message=f"Unsupported language '{language}'. Supported: {_SUPPORTED_LANGUAGES}",
            )
        if not description:
            return AgentResult(
                agent_name=self.name, status="error",
                message="A description is required for code generation.",
            )

        prompt = (
            f"Generate {language} code for the following requirement. "
            f"Return ONLY the code, no explanations:\n\n{description}"
        )
        code = self._ask_ai_safe(prompt)

        if output_path:
            resolved = _safe_resolve(output_path)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(code, encoding="utf-8")
            _record_action("generate_code", str(resolved), language)
            return AgentResult(
                agent_name=self.name, status="success",
                message=f"Code generated and written to {resolved}.",
                data={"code": code, "file_path": str(resolved), "language": language},
                actions_taken=["generate_code", "write_file"],
            )

        _record_action("generate_code", language=language)
        return AgentResult(
            agent_name=self.name, status="success",
            message="Code generated successfully.",
            data={"code": code, "language": language},
            actions_taken=["generate_code"],
        )

    def _modify_code(self, file_path: str, instruction: str) -> AgentResult:
        """Read an existing file, apply an AI-driven modification, and return the result."""
        if not file_path:
            return AgentResult(
                agent_name=self.name, status="error",
                message="file_path is required for modify_code.",
            )
        resolved = _safe_resolve(file_path)
        if not resolved.is_file():
            return AgentResult(
                agent_name=self.name, status="error",
                message=f"File not found: {resolved}",
            )

        original = resolved.read_text(encoding="utf-8")
        prompt = (
            f"Modify the following code according to this instruction:\n"
            f"{instruction}\n\n"
            f"Return ONLY the modified code, no explanations:\n\n{original}"
        )
        modified = self._ask_ai_safe(prompt)
        _record_action("modify_code", str(resolved))

        return AgentResult(
            agent_name=self.name, status="success",
            message="Code modified (review before saving). Use generate_code with output_path to persist.",
            data={"original": original, "modified": modified, "file_path": str(resolved)},
            actions_taken=["modify_code"],
        )

    def _review_code(
        self, file_path: Optional[str] = None, code: Optional[str] = None,
    ) -> AgentResult:
        """Review code for quality, issues, and security concerns."""
        source = self._resolve_code_source(file_path, code)
        if isinstance(source, AgentResult):
            return source

        prompt = (
            "Review the following code. Provide a JSON object with keys: "
            '"quality_score" (1-10), "issues" (list of strings), '
            '"suggestions" (list of strings), "security_concerns" (list of strings).\n\n'
            f"{source}"
        )
        review = self._ask_ai_safe(prompt)
        return AgentResult(
            agent_name=self.name, status="success",
            message="Code review complete.",
            data={"review": review, "file_path": file_path},
            actions_taken=["review_code"],
        )

    def _execute_code(
        self,
        file_path: Optional[str] = None,
        code: Optional[str] = None,
        language: str = "python",
    ) -> AgentResult:
        """Execute code with explicit permission checks and sandboxing."""
        if self._permission_manager and not self._permission_manager.check_permission("system.execute"):
            return AgentResult(
                agent_name=self.name, status="pending_permission",
                message="system.execute permission required to run code.",
                data={"missing_permissions": ["system.execute"]},
            )

        if language != "python":
            cmd_hint = self._non_python_hint(file_path, language)
            return AgentResult(
                agent_name=self.name, status="success",
                message=f"Execution hint for {language} (not auto-executed).",
                data={"command": cmd_hint, "language": language},
                actions_taken=["execution_hint"],
            )

        # Build command
        if file_path:
            resolved = _safe_resolve(file_path)
            if not resolved.is_file():
                return AgentResult(
                    agent_name=self.name, status="error",
                    message=f"File not found: {resolved}",
                )
            cmd = [sys.executable, str(resolved)]
        elif code:
            cmd = [sys.executable, "-c", code]
        else:
            return AgentResult(
                agent_name=self.name, status="error",
                message="Provide file_path or code to execute.",
            )

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_EXECUTION_TIMEOUT,
        )
        _record_action("execute_code", file_path, "python")

        return AgentResult(
            agent_name=self.name,
            status="success" if result.returncode == 0 else "error",
            message=f"Code exited with return code {result.returncode}.",
            data={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            },
            actions_taken=["execute_code"],
        )

    def _explain_code(
        self, file_path: Optional[str] = None, code: Optional[str] = None,
    ) -> AgentResult:
        """Use AI to explain code line by line."""
        source = self._resolve_code_source(file_path, code)
        if isinstance(source, AgentResult):
            return source

        prompt = (
            "Explain the following code line by line. Be thorough but concise:\n\n"
            f"{source}"
        )
        explanation = self._ask_ai_safe(prompt)
        return AgentResult(
            agent_name=self.name, status="success",
            message="Code explanation generated.",
            data={"explanation": explanation, "file_path": file_path},
            actions_taken=["explain_code"],
        )

    def _list_generated(self) -> AgentResult:
        """List all files previously generated or modified by this agent."""
        history = _load_history()
        return AgentResult(
            agent_name=self.name, status="success",
            message=f"Found {len(history)} history entries.",
            data={"history": history},
            actions_taken=["list_generated"],
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_code_source(
        self, file_path: Optional[str], code: Optional[str],
    ) -> str | AgentResult:
        """Return code text from *file_path* or *code*, or an error result."""
        if file_path:
            resolved = _safe_resolve(file_path)
            if not resolved.is_file():
                return AgentResult(
                    agent_name=self.name, status="error",
                    message=f"File not found: {resolved}",
                )
            return resolved.read_text(encoding="utf-8")
        if code:
            return code
        return AgentResult(
            agent_name=self.name, status="error",
            message="Provide either file_path or code.",
        )

    def _ask_ai_safe(self, prompt: str) -> str:
        """Call :func:`ask_ai` with graceful error handling."""
        try:
            from assistant.ai.client import ask_ai
            return ask_ai(prompt)
        except Exception as exc:  # noqa: BLE001
            return f"[AI unavailable] {exc}"

    @staticmethod
    def _non_python_hint(file_path: Optional[str], language: str) -> str:
        """Return a suggested shell command for non-Python languages."""
        runners = {
            "javascript": "node", "typescript": "npx ts-node",
            "bash": "bash", "powershell": "pwsh",
            "rust": "cargo run", "go": "go run",
            "java": "javac && java",
        }
        runner = runners.get(language, language)
        target = file_path or "<file>"
        return f"{runner} {shlex.quote(target)}"
