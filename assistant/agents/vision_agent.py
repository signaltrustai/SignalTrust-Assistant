"""Vision agent – image analysis, text extraction, and scene description via GPT-4o."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult

_ACTIONS: List[str] = ["analyze_image", "extract_text", "describe_scene"]


def _openai_available() -> bool:
    """Return ``True`` if the ``openai`` package can be imported."""
    try:
        import openai  # noqa: F401
        return bool(openai.api_key)
    except Exception:
        return False


class VisionAgent(BaseAgent):
    """Image analysis and object recognition agent."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="vision",
            description="Image analysis, text extraction, and scene description.",
            required_permissions=["file.read", "network.request"],
            **kwargs,
        )

    def execute(self, **kwargs: Any) -> AgentResult:
        """Dispatch to the requested vision action."""
        action: Optional[str] = kwargs.get("action")
        if action and action not in _ACTIONS:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Unknown action '{action}'. Valid: {_ACTIONS}")
        try:
            if action == "analyze_image":
                return self._analyze_image(kwargs.get("image_path", ""))
            if action == "extract_text":
                return self._extract_text(kwargs.get("image_path", ""))
            if action == "describe_scene":
                return self._describe_scene(kwargs.get("image_path", ""))
            return AgentResult(agent_name=self.name, status="error",
                               message="No action specified.")
        except Exception as exc:
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Vision agent error: {exc}")

    def _validate_image(self, image_path: str) -> Optional[AgentResult]:
        """Return an error result if *image_path* is invalid, else ``None``."""
        if not image_path:
            return AgentResult(agent_name=self.name, status="error",
                               message="No image path provided.")
        if not Path(image_path).exists():
            return AgentResult(agent_name=self.name, status="error",
                               message=f"Image not found: {image_path}")
        return None

    def _analyze_image(self, image_path: str) -> AgentResult:
        """Analyse an image using GPT-4o vision or return a placeholder."""
        err = self._validate_image(image_path)
        if err:
            return err
        if _openai_available():
            return self._call_vision_api(image_path, "Analyze this image in detail.")
        return AgentResult(
            agent_name=self.name, status="success",
            message="Image analysis placeholder (no AI backend configured).",
            data={"image_path": image_path,
                   "file_size_bytes": Path(image_path).stat().st_size,
                   "mime_type": mimetypes.guess_type(image_path)[0],
                   "analysis": "AI analysis unavailable — configure OpenAI API key."},
            actions_taken=["analyze_image_placeholder"])

    def _extract_text(self, image_path: str) -> AgentResult:
        """Extract text from an image."""
        err = self._validate_image(image_path)
        if err:
            return err
        if _openai_available():
            return self._call_vision_api(
                image_path, "Extract all visible text from this image. Return only the text.")
        return AgentResult(
            agent_name=self.name, status="success",
            message="Text extraction placeholder (no AI backend configured).",
            data={"image_path": image_path, "extracted_text": "",
                   "note": "AI text extraction unavailable — configure OpenAI API key."},
            actions_taken=["extract_text_placeholder"])

    def _describe_scene(self, image_path: str) -> AgentResult:
        """Describe what is visible in an image."""
        err = self._validate_image(image_path)
        if err:
            return err
        if _openai_available():
            return self._call_vision_api(
                image_path, "Describe this scene in detail, noting objects, people, and context.")
        return AgentResult(
            agent_name=self.name, status="success",
            message="Scene description placeholder (no AI backend configured).",
            data={"image_path": image_path,
                   "description": "AI scene description unavailable — configure OpenAI API key."},
            actions_taken=["describe_scene_placeholder"])

    def _call_vision_api(self, image_path: str, prompt: str) -> AgentResult:
        """Send an image to the OpenAI GPT-4o vision endpoint."""
        import openai
        path = Path(image_path)
        mime = mimetypes.guess_type(image_path)[0] or "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode()
        data_uri = f"data:{mime};base64,{encoded}"
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_uri}},
            ]}],
            max_tokens=1024,
        )
        result_text = response.choices[0].message.content or ""
        return AgentResult(
            agent_name=self.name, status="success",
            message="Vision analysis complete.",
            data={"image_path": image_path, "result": result_text, "model": "gpt-4o"},
            actions_taken=["vision_api_call"])
