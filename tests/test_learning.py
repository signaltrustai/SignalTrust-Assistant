"""Tests for the OmniJARVIS learning engine."""

import json
from pathlib import Path

import pytest

from assistant.learning import LearningEngine


@pytest.fixture
def engine(tmp_path):
    """Create a LearningEngine backed by temp files."""
    return LearningEngine(
        profile_path=tmp_path / "profile.json",
        history_path=tmp_path / "history.json",
    )


class TestLearningEngine:
    def test_record_interaction(self, engine):
        rec = engine.record_interaction(
            query="test query",
            response_summary="test response",
            agent_used="system",
            satisfaction=5,
            tags=["test"],
        )
        assert rec.query == "test query"
        assert rec.agent_used == "system"

    def test_get_set_preference(self, engine):
        engine.set_preference("language", "fr")
        assert engine.get_preference("language") == "fr"
        assert engine.get_preference("missing", "default") == "default"

    def test_interaction_history(self, engine):
        engine.record_interaction("q1", "r1", "system")
        engine.record_interaction("q2", "r2", "code")
        history = engine.get_interaction_history(limit=10)
        assert len(history) == 2
        # Most recent first
        assert history[0]["query"] == "q2"

    def test_filter_by_agent(self, engine):
        engine.record_interaction("q1", "r1", "system")
        engine.record_interaction("q2", "r2", "code")
        history = engine.get_interaction_history(agent="code")
        assert len(history) == 1
        assert history[0]["agent_used"] == "code"

    def test_usage_stats(self, engine):
        engine.record_interaction("q1", "r1", "system", satisfaction=4)
        engine.record_interaction("q2", "r2", "system", satisfaction=5)
        stats = engine.get_usage_stats()
        assert stats["total_interactions"] == 2
        assert stats["favorite_agent"] == "system"
        assert stats["avg_satisfaction"] == 4.5

    def test_preferred_agent(self, engine):
        for _ in range(5):
            engine.record_interaction("github issues", "done", "system", satisfaction=5, tags=["github"])
        engine.record_interaction("github issues", "done", "code", satisfaction=2, tags=["github"])
        best = engine.get_preferred_agent(["github"])
        assert best == "system"

    def test_get_suggestions_empty(self, engine):
        suggestions = engine.get_suggestions()
        assert any("haven't recorded" in s for s in suggestions)

    def test_update_profile(self, engine):
        engine.update_profile(name="TestUser")
        profile = engine.get_profile()
        assert profile["name"] == "TestUser"

    def test_persistence(self, tmp_path):
        pf = tmp_path / "profile.json"
        hf = tmp_path / "history.json"
        e1 = LearningEngine(profile_path=pf, history_path=hf)
        e1.set_preference("lang", "fr")
        e1.record_interaction("q", "r", "test")

        e2 = LearningEngine(profile_path=pf, history_path=hf)
        assert e2.get_preference("lang") == "fr"
        assert len(e2.get_interaction_history()) == 1
