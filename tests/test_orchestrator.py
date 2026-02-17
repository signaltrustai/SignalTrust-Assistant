"""Tests for the OmniJARVIS orchestrator."""

import pytest

from assistant.orchestrator import OmniJARVIS


@pytest.fixture
def jarvis(tmp_path, monkeypatch):
    """Create an OmniJARVIS instance with temp storage."""
    monkeypatch.chdir(tmp_path)
    return OmniJARVIS()


class TestOmniJARVIS:
    def test_initialization(self, jarvis):
        assert jarvis.INIT_MESSAGE == "OmniJARVIS operational. Ready to orchestrate your personal OS."

    def test_list_agents(self, jarvis):
        agents = jarvis.list_agents()
        assert len(agents) == 12
        names = [a["name"] for a in agents]
        assert "executive" in names
        assert "memory" in names
        assert "code" in names
        assert "system" in names

    def test_handle_routes_message(self, jarvis):
        response = jarvis.handle("Hello world")
        assert response.summary
        assert response.steps
        assert len(response.steps) >= 1

    def test_handle_format_text(self, jarvis):
        response = jarvis.handle("test")
        text = response.format_text()
        assert "Summary" in text

    def test_grant_and_check_permission(self, jarvis):
        jarvis.grant_permission("system.execute", "session")
        perms = jarvis.list_permissions()
        assert any(p["action"] == "system.execute" for p in perms)

    def test_revoke_permission(self, jarvis):
        jarvis.grant_permission("file.read", "session")
        jarvis.revoke_permission("file.read")
        perms = jarvis.list_permissions()
        assert not any(p["action"] == "file.read" for p in perms)

    def test_audit_log(self, jarvis):
        jarvis.grant_permission("file.read", "session")
        log = jarvis.audit_log()
        assert len(log) > 0

    def test_session_summary(self, jarvis):
        summary = jarvis.session_summary()
        assert "No interactions" in summary or "Session" in summary

    def test_get_profile(self, jarvis):
        profile = jarvis.get_profile()
        assert "name" in profile

    def test_get_stats(self, jarvis):
        stats = jarvis.get_stats()
        assert "total_interactions" in stats

    def test_handle_direct_system(self, jarvis):
        jarvis.grant_permission("system.execute", "session")
        result = jarvis.handle_direct("system", action="system_info", message="info")
        assert result.status == "success"
        assert "os" in result.data

    def test_handle_direct_unknown_agent(self, jarvis):
        result = jarvis.handle_direct("nonexistent")
        assert result.status == "error"

    def test_permission_enforcement(self, jarvis):
        # Memory agent needs memory.write
        result = jarvis.handle_direct("memory", action="store", message="test note")
        assert result.status == "pending_permission"

    def test_permission_enforcement_after_grant(self, jarvis):
        jarvis.grant_permission("memory.write", "session")
        result = jarvis.handle_direct("memory", action="store", message="test note")
        assert result.status == "success"

    def test_suggestions_on_permission_denied(self, jarvis):
        response = jarvis.handle("Souviens-toi de ça")
        assert any("grant" in s.lower() or "permission" in s.lower() for s in response.suggestions)


class TestOmniJARVISModels:
    def test_response_to_dict(self, jarvis):
        response = jarvis.handle("test")
        d = response.to_dict()
        assert "summary" in d
        assert "steps" in d
        assert "suggestions" in d
