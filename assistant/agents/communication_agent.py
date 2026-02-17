"""
Communication agent for OmniJARVIS.

Manages messaging, email drafting, meeting scheduling, and contacts.
All operations are local-first: messages and meetings are persisted as
structured records that downstream plugins can deliver.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from assistant.agents.base_agent import BaseAgent, AgentResult


CONFIG_ROOT = Path("config")
CONTACTS_FILE = CONFIG_ROOT / "contacts.json"

_ACTIONS: List[str] = [
    "send_message",
    "draft_email",
    "schedule_meeting",
    "list_contacts",
]


class CommunicationAgent(BaseAgent):
    """Messaging and meeting management agent."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="communication",
            description="Messaging, email drafting, and meeting management.",
            required_permissions=["communication.send", "communication.read"],
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> AgentResult:
        """Dispatch to the requested communication action."""
        action: Optional[str] = kwargs.get("action")

        if action and action not in _ACTIONS:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message=f"Unknown action '{action}'. Valid: {_ACTIONS}",
            )

        try:
            if action == "send_message":
                return self._send_message(
                    recipient=kwargs.get("recipient", ""),
                    message=kwargs.get("message", ""),
                    channel=kwargs.get("channel", "default"),
                )
            if action == "draft_email":
                return self._draft_email(
                    to=kwargs.get("to", ""),
                    subject=kwargs.get("subject", ""),
                    body=kwargs.get("body", ""),
                )
            if action == "schedule_meeting":
                return self._schedule_meeting(
                    title=kwargs.get("title", ""),
                    participants=kwargs.get("participants", []),
                    datetime_str=kwargs.get("datetime_str", ""),
                    duration_minutes=kwargs.get("duration_minutes", 60),
                )
            if action == "list_contacts":
                return self._list_contacts()
            return AgentResult(
                agent_name=self.name,
                status="error",
                message="No action specified.",
            )
        except Exception as exc:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message=f"Communication agent error: {exc}",
            )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _send_message(
        self, recipient: str, message: str, channel: str = "default"
    ) -> AgentResult:
        """Create a message record (extensible via plugins)."""
        if not recipient or not message:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message="Recipient and message are required.",
            )

        record = {
            "recipient": recipient,
            "message": message,
            "channel": channel,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "queued",
        }
        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Message queued for {recipient} on '{channel}'.",
            data=record,
            actions_taken=["send_message"],
        )

    def _draft_email(self, to: str, subject: str, body: str) -> AgentResult:
        """Generate a formatted email draft."""
        if not to or not subject:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message="'to' and 'subject' are required.",
            )

        draft = {
            "to": to,
            "subject": subject,
            "body": body,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "formatted": f"To: {to}\nSubject: {subject}\n\n{body}",
        }
        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Email draft created for {to}.",
            data=draft,
            actions_taken=["draft_email"],
        )

    def _schedule_meeting(
        self,
        title: str,
        participants: List[str],
        datetime_str: str,
        duration_minutes: int = 60,
    ) -> AgentResult:
        """Create a meeting record."""
        if not title or not datetime_str:
            return AgentResult(
                agent_name=self.name,
                status="error",
                message="'title' and 'datetime_str' are required.",
            )

        meeting = {
            "title": title,
            "participants": participants,
            "datetime": datetime_str,
            "duration_minutes": duration_minutes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "scheduled",
        }
        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Meeting '{title}' scheduled for {datetime_str}.",
            data=meeting,
            actions_taken=["schedule_meeting"],
        )

    def _list_contacts(self) -> AgentResult:
        """Return contacts from ``config/contacts.json`` (creates empty if missing)."""
        if not CONTACTS_FILE.exists():
            CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            CONTACTS_FILE.write_text(
                json.dumps({"contacts": []}, indent=2), encoding="utf-8"
            )

        try:
            data = json.loads(CONTACTS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {"contacts": []}

        contacts = data.get("contacts", [])
        return AgentResult(
            agent_name=self.name,
            status="success",
            message=f"Found {len(contacts)} contacts.",
            data={"contacts": contacts},
            actions_taken=["list_contacts"],
        )
