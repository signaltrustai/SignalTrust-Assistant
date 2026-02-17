"""
Adaptive Learning and User Preference System for OmniJARVIS.

Learns from every interaction and adapts behaviour based on user
preferences, past queries, and satisfaction signals.  All state is
persisted to JSON files so it survives restarts.
"""

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIG_ROOT = Path("config")
MEMORY_ROOT = Path("memory")

DEFAULT_PROFILE_PATH = CONFIG_ROOT / "user_profile.json"
DEFAULT_HISTORY_PATH = MEMORY_ROOT / "interaction_history.json"

HIGH_ACTIVITY_THRESHOLD = 20


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class UserProfile:
    """Represents a persistent user profile.

    :param name: Display name of the user.
    :param preferences: Arbitrary key/value preference store.
    :param interaction_count: Total number of recorded interactions.
    :param created_at: ISO-8601 timestamp of when the profile was created.
    :param updated_at: ISO-8601 timestamp of the last profile update.
    """

    name: str = "User"
    preferences: Dict[str, Any] = field(default_factory=dict)
    interaction_count: int = 0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class InteractionRecord:
    """A single recorded interaction between the user and the assistant.

    :param query: The user's original query text.
    :param response_summary: Brief summary of the assistant's response.
    :param agent_used: Identifier for the agent that handled the query.
    :param satisfaction: Optional user satisfaction score (1–5).
    :param timestamp: ISO-8601 timestamp of the interaction.
    :param tags: Descriptive tags for categorisation.
    """

    query: str
    response_summary: str
    agent_used: str
    satisfaction: Optional[int] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# LearningEngine
# ---------------------------------------------------------------------------

class LearningEngine:
    """Adaptive learning engine that tracks interactions and preferences.

    Persists a :class:`UserProfile` and a list of
    :class:`InteractionRecord` entries to JSON files so that the
    assistant improves over time.

    Usage::

        engine = LearningEngine()
        engine.record_interaction(
            query="List open issues",
            response_summary="Returned 12 issues from SignalTrust repo.",
            agent_used="ecosystem",
            satisfaction=4,
            tags=["github", "issues"],
        )
        print(engine.get_usage_stats())
    """

    def __init__(
        self,
        profile_path: Optional[Path] = None,
        history_path: Optional[Path] = None,
    ) -> None:
        """Initialize the engine, loading existing data from disk.

        :param profile_path: Path to the user profile JSON file.
            Defaults to ``config/user_profile.json``.
        :param history_path: Path to the interaction history JSON file.
            Defaults to ``memory/interaction_history.json``.
        """
        self._profile_path: Path = profile_path or DEFAULT_PROFILE_PATH
        self._history_path: Path = history_path or DEFAULT_HISTORY_PATH
        self._profile: UserProfile = self._load_profile()
        self._history: List[InteractionRecord] = self._load_history()

    # ------------------------------------------------------------------
    # Interaction recording
    # ------------------------------------------------------------------

    def record_interaction(
        self,
        query: str,
        response_summary: str,
        agent_used: str,
        satisfaction: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> InteractionRecord:
        """Record a new interaction and persist it to disk.

        :param query: The user's query text.
        :param response_summary: Brief summary of the response.
        :param agent_used: Agent identifier that handled the query.
        :param satisfaction: Optional satisfaction score (1–5).
        :param tags: Optional list of descriptive tags.
        :return: The created :class:`InteractionRecord`.
        """
        record = InteractionRecord(
            query=query,
            response_summary=response_summary,
            agent_used=agent_used,
            satisfaction=satisfaction,
            tags=tags or [],
        )
        self._history.append(record)
        self._profile.interaction_count += 1
        self._profile.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_history()
        self._save_profile()
        return record

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Retrieve a user preference by key.

        :param key: Preference key.
        :param default: Value returned when the key does not exist.
        :return: The stored preference value, or *default*.
        """
        return self._profile.preferences.get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference and persist the profile.

        :param key: Preference key.
        :param value: Preference value (must be JSON-serialisable).
        """
        self._profile.preferences[key] = value
        self._profile.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_profile()

    # ------------------------------------------------------------------
    # Agent recommendation
    # ------------------------------------------------------------------

    def get_preferred_agent(self, query_keywords: List[str]) -> Optional[str]:
        """Suggest the best agent for a query based on past interactions.

        Examines historical interactions whose queries or tags overlap
        with *query_keywords* and returns the agent with the highest
        weighted score (frequency × average satisfaction).

        :param query_keywords: Keywords describing the incoming query.
        :return: Agent identifier, or ``None`` if no history matches.
        """
        if not query_keywords:
            return None

        keywords_lower = [kw.lower() for kw in query_keywords]
        agent_scores: Dict[str, List[int]] = {}

        for record in self._history:
            haystack = (
                record.query.lower()
                + " "
                + " ".join(t.lower() for t in record.tags)
            )
            if any(kw in haystack for kw in keywords_lower):
                agent_scores.setdefault(record.agent_used, []).append(
                    record.satisfaction if record.satisfaction is not None else 3
                )

        if not agent_scores:
            return None

        # Score = number of matches × average satisfaction
        best_agent: Optional[str] = None
        best_score: float = -1.0
        for agent, scores in agent_scores.items():
            score = len(scores) * (sum(scores) / len(scores))
            if score > best_score:
                best_score = score
                best_agent = agent

        return best_agent

    # ------------------------------------------------------------------
    # History retrieval
    # ------------------------------------------------------------------

    def get_interaction_history(
        self,
        limit: int = 50,
        agent: Optional[str] = None,
        min_satisfaction: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return filtered interaction history.

        :param limit: Maximum number of records to return.
        :param agent: If given, only return records handled by this agent.
        :param min_satisfaction: If given, only return records with at
            least this satisfaction score.
        :return: A list of interaction record dicts, most recent first.
        """
        filtered: List[InteractionRecord] = list(reversed(self._history))
        if agent is not None:
            filtered = [r for r in filtered if r.agent_used == agent]
        if min_satisfaction is not None:
            filtered = [
                r
                for r in filtered
                if r.satisfaction is not None
                and r.satisfaction >= min_satisfaction
            ]
        return [asdict(r) for r in filtered[:limit]]

    # ------------------------------------------------------------------
    # Usage statistics
    # ------------------------------------------------------------------

    def get_usage_stats(self) -> Dict[str, Any]:
        """Compute aggregate usage statistics.

        :return: Dictionary with ``total_interactions``,
            ``favorite_agent``, ``avg_satisfaction``, ``most_used_tags``,
            and ``interactions_today``.
        """
        total = len(self._history)

        # Favorite agent
        agent_counter: Counter[str] = Counter(
            r.agent_used for r in self._history
        )
        favorite_agent: Optional[str] = (
            agent_counter.most_common(1)[0][0] if agent_counter else None
        )

        # Average satisfaction (only scored records)
        scored = [
            r.satisfaction
            for r in self._history
            if r.satisfaction is not None
        ]
        avg_satisfaction: Optional[float] = (
            round(sum(scored) / len(scored), 2) if scored else None
        )

        # Most-used tags
        tag_counter: Counter[str] = Counter(
            tag for r in self._history for tag in r.tags
        )
        most_used_tags: List[str] = [
            tag for tag, _ in tag_counter.most_common(10)
        ]

        # Interactions today
        today = datetime.now(timezone.utc).date().isoformat()
        interactions_today = sum(
            1 for r in self._history if r.timestamp.startswith(today)
        )

        return {
            "total_interactions": total,
            "favorite_agent": favorite_agent,
            "avg_satisfaction": avg_satisfaction,
            "most_used_tags": most_used_tags,
            "interactions_today": interactions_today,
        }

    # ------------------------------------------------------------------
    # Suggestions
    # ------------------------------------------------------------------

    def get_suggestions(
        self, context: Optional[str] = None
    ) -> List[str]:
        """Generate actionable suggestions based on usage patterns.

        :param context: Optional context string to tailor suggestions.
        :return: A list of human-readable suggestion strings.
        """
        suggestions: List[str] = []

        stats = self.get_usage_stats()
        total = stats["total_interactions"]

        if total == 0:
            suggestions.append(
                "You haven't recorded any interactions yet — start by "
                "asking a question to build your learning profile."
            )
            return suggestions

        # Suggest exploring under-used agents
        agent_counts: Counter[str] = Counter(
            r.agent_used for r in self._history
        )
        if len(agent_counts) == 1:
            sole_agent = list(agent_counts.keys())[0]
            suggestions.append(
                f"All your interactions used the '{sole_agent}' agent. "
                "Try exploring other agents for a broader experience."
            )

        # Satisfaction-based suggestions
        avg_sat = stats["avg_satisfaction"]
        if avg_sat is not None and avg_sat < 3.0:
            suggestions.append(
                "Your average satisfaction is below 3 — consider "
                "adjusting your preferences or trying different agents."
            )

        # Tag-based context suggestions
        if context:
            context_lower = context.lower()
            related = [
                r for r in self._history
                if context_lower in r.query.lower()
                or any(context_lower in t.lower() for t in r.tags)
            ]
            if related:
                recent = related[-1]
                suggestions.append(
                    f"You've previously asked about '{context}' — "
                    f"the '{recent.agent_used}' agent handled it last."
                )
            else:
                suggestions.append(
                    f"'{context}' is a new topic for you — it could be "
                    "a great opportunity to explore!"
                )

        # Activity-based suggestion
        if stats["interactions_today"] >= HIGH_ACTIVITY_THRESHOLD:
            suggestions.append(
                "You've been very active today! Consider taking a short "
                "break to recharge."
            )

        # Encourage tagging
        untagged = sum(1 for r in self._history if not r.tags)
        if untagged > total * 0.5:
            suggestions.append(
                "Over half of your interactions have no tags. Adding "
                "tags helps the engine learn your interests faster."
            )

        return suggestions

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    def update_profile(
        self,
        name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update the user profile.

        :param name: New display name, if changing.
        :param preferences: Dict of preferences to merge into the
            existing set.
        """
        if name is not None:
            self._profile.name = name
        if preferences is not None:
            self._profile.preferences.update(preferences)
        self._profile.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_profile()

    def get_profile(self) -> Dict[str, Any]:
        """Return the current user profile as a dictionary.

        :return: Serialized :class:`UserProfile`.
        """
        return asdict(self._profile)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load_profile(self) -> UserProfile:
        """Load the user profile from disk, or create a fresh one."""
        if not self._profile_path.exists():
            return UserProfile()
        try:
            data = json.loads(
                self._profile_path.read_text(encoding="utf-8")
            )
            return UserProfile(
                name=data.get("name", "User"),
                preferences=data.get("preferences", {}),
                interaction_count=data.get("interaction_count", 0),
                created_at=data.get(
                    "created_at",
                    datetime.now(timezone.utc).isoformat(),
                ),
                updated_at=data.get(
                    "updated_at",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        except (json.JSONDecodeError, OSError):
            return UserProfile()

    def _save_profile(self) -> None:
        """Persist the current user profile to disk."""
        self._profile_path.parent.mkdir(parents=True, exist_ok=True)
        self._profile_path.write_text(
            json.dumps(asdict(self._profile), indent=2),
            encoding="utf-8",
        )

    def _load_history(self) -> List[InteractionRecord]:
        """Load interaction history from disk, or return an empty list."""
        if not self._history_path.exists():
            return []
        try:
            data = json.loads(
                self._history_path.read_text(encoding="utf-8")
            )
            records: List[InteractionRecord] = []
            for entry in data.get("interactions", []):
                records.append(
                    InteractionRecord(
                        query=entry.get("query", ""),
                        response_summary=entry.get("response_summary", ""),
                        agent_used=entry.get("agent_used", "unknown"),
                        satisfaction=entry.get("satisfaction"),
                        timestamp=entry.get(
                            "timestamp",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        tags=entry.get("tags", []),
                    )
                )
            return records
        except (json.JSONDecodeError, OSError):
            return []

    def _save_history(self) -> None:
        """Persist the full interaction history to disk."""
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "interactions": [asdict(r) for r in self._history],
        }
        self._history_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
