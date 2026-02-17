"""
Analysis Agent — Deep analysis of files, code, documents, and data.

Extracts patterns, risks, opportunities, and actionable recommendations
using AI when available, with deterministic fallbacks for offline use.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult


class AnalysisAgent(BaseAgent):
    """Agent that analyses content and produces structured insights.

    Actions: ``analyze_text``, ``analyze_file``, ``analyze_code``,
    ``compare``, ``extract_patterns``.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="analysis",
            description=(
                "Analyses files, code, documents, and data. "
                "Extracts patterns, risks, opportunities, and "
                "recommendations."
            ),
            required_permissions=["file.read"],
            **kwargs,
        )

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> AgentResult:
        action = kwargs.get("action")
        message = kwargs.get("message", "")

        if action == "analyze_text" or (not action and message):
            return self._analyze_text(message)
        if action == "analyze_file":
            return self._analyze_file(kwargs.get("file_path", ""))
        if action == "analyze_code":
            return self._analyze_code(
                kwargs.get("file_path"), kwargs.get("code")
            )
        if action == "compare":
            return self._compare(kwargs.get("text_a", ""), kwargs.get("text_b", ""))
        if action == "extract_patterns":
            return self._extract_patterns(kwargs.get("text", message))

        if message:
            return self._analyze_text(message)

        return AgentResult(
            agent_name=self.name,
            status="error",
            message="No action or message. Use: analyze_text, analyze_file, analyze_code, compare, extract_patterns.",
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _analyze_text(self, text: str) -> AgentResult:
        """Analyse free-form text and provide insights."""
        if not text:
            return AgentResult(
                agent_name=self.name, status="error",
                message="No text provided for analysis.",
            )
        analysis = self._ai_analyze(
            f"Analyze the following text and provide key insights, risks, "
            f"opportunities, and recommendations:\n\n{text}"
        )
        return AgentResult(
            agent_name=self.name, status="success",
            message="Text analysis complete.",
            data={"analysis": analysis, "input_length": len(text)},
            actions_taken=["analyze_text"],
        )

    def _analyze_file(self, file_path: str) -> AgentResult:
        """Read and analyse a file."""
        if not file_path:
            return AgentResult(
                agent_name=self.name, status="error",
                message="file_path is required.",
            )
        path = Path(file_path)
        if not path.is_file():
            return AgentResult(
                agent_name=self.name, status="error",
                message=f"File not found: {file_path}",
            )
        content = path.read_text(encoding="utf-8")
        analysis = self._ai_analyze(
            f"Analyze this file ({path.name}) and provide a structured "
            f"summary with key findings:\n\n{content[:8000]}"
        )
        return AgentResult(
            agent_name=self.name, status="success",
            message=f"File '{path.name}' analysed.",
            data={
                "analysis": analysis,
                "file_path": str(path),
                "file_size": len(content),
            },
            actions_taken=["read_file", "analyze_content"],
        )

    def _analyze_code(
        self, file_path: Optional[str] = None, code: Optional[str] = None,
    ) -> AgentResult:
        """Perform a deep code analysis."""
        source = ""
        if file_path:
            path = Path(file_path)
            if not path.is_file():
                return AgentResult(
                    agent_name=self.name, status="error",
                    message=f"File not found: {file_path}",
                )
            source = path.read_text(encoding="utf-8")
        elif code:
            source = code
        else:
            return AgentResult(
                agent_name=self.name, status="error",
                message="Provide file_path or code for analysis.",
            )

        analysis = self._ai_analyze(
            "Perform a deep code analysis. Cover: architecture, "
            "quality, potential bugs, security, performance, and "
            f"improvement suggestions:\n\n{source[:8000]}"
        )
        return AgentResult(
            agent_name=self.name, status="success",
            message="Code analysis complete.",
            data={"analysis": analysis, "file_path": file_path},
            actions_taken=["analyze_code"],
        )

    def _compare(self, text_a: str, text_b: str) -> AgentResult:
        """Compare two texts and highlight differences."""
        if not text_a or not text_b:
            return AgentResult(
                agent_name=self.name, status="error",
                message="Both text_a and text_b are required.",
            )
        analysis = self._ai_analyze(
            f"Compare these two texts. Highlight differences, "
            f"similarities, and provide recommendations:\n\n"
            f"--- Text A ---\n{text_a[:4000]}\n\n"
            f"--- Text B ---\n{text_b[:4000]}"
        )
        return AgentResult(
            agent_name=self.name, status="success",
            message="Comparison complete.",
            data={"analysis": analysis},
            actions_taken=["compare_texts"],
        )

    def _extract_patterns(self, text: str) -> AgentResult:
        """Extract recurring patterns from text."""
        if not text:
            return AgentResult(
                agent_name=self.name, status="error",
                message="No text provided.",
            )
        analysis = self._ai_analyze(
            f"Extract recurring patterns, themes, and key data points "
            f"from the following text:\n\n{text[:8000]}"
        )
        return AgentResult(
            agent_name=self.name, status="success",
            message="Pattern extraction complete.",
            data={"patterns": analysis},
            actions_taken=["extract_patterns"],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ai_analyze(self, prompt: str) -> str:
        """Call AI with graceful fallback."""
        try:
            from assistant.ai.client import ask_ai
            return ask_ai(prompt)
        except Exception:
            return f"[Offline analysis] Input received ({len(prompt)} chars). Connect AI for deeper insights."
