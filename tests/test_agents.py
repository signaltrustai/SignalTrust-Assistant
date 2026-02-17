"""Tests for OmniJARVIS specialized agents."""

import pytest

from assistant.agents.base_agent import BaseAgent, AgentResult
from assistant.agents.system_agent import SystemAgent
from assistant.agents.security_agent import SecurityAgent
from assistant.agents.executive_agent import ExecutiveAgent
from assistant.agents.memory_agent import MemoryAgent
from assistant.agents.analysis_agent import AnalysisAgent
from assistant.agents.documentation_agent import DocumentationAgent
from assistant.core.memory_store import MemoryStore
from assistant.permissions import PermissionManager
from assistant.learning import LearningEngine


@pytest.fixture
def pm(tmp_path):
    return PermissionManager(permissions_file=tmp_path / "perms.json")


@pytest.fixture
def le(tmp_path):
    return LearningEngine(
        profile_path=tmp_path / "profile.json",
        history_path=tmp_path / "history.json",
    )


class TestBaseAgent:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseAgent(name="test", description="test")

    def test_subclass_with_execute(self, pm, le):
        class DummyAgent(BaseAgent):
            def execute(self, **kwargs):
                return AgentResult(
                    agent_name=self.name, status="success", message="done"
                )

        agent = DummyAgent(
            name="dummy", description="test agent",
            permission_manager=pm, learning_engine=le,
        )
        result = agent.run()
        assert result.status == "success"

    def test_describe(self, pm, le):
        class DummyAgent(BaseAgent):
            def execute(self, **kwargs):
                return AgentResult(
                    agent_name=self.name, status="success", message="done"
                )

        agent = DummyAgent(name="dummy", description="test agent")
        desc = agent.describe()
        assert desc["name"] == "dummy"
        assert desc["status"] == "ready"


class TestSystemAgent:
    def test_system_info(self, pm, le):
        pm.grant_permission("system.execute", scope="session")
        agent = SystemAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(action="system_info")
        assert result.status == "success"
        assert "os" in result.data

    def test_disk_usage(self, pm, le):
        pm.grant_permission("system.execute", scope="session")
        agent = SystemAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(action="disk_usage")
        assert result.status == "success"

    def test_requires_permission(self, pm, le):
        agent = SystemAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(action="system_info")
        assert result.status == "pending_permission"


class TestSecurityAgent:
    def test_security_status(self, pm, le):
        agent = SecurityAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(action="security_status")
        assert result.status == "success"

    def test_check_permissions(self, pm, le):
        pm.grant_permission("file.read", scope="session")
        agent = SecurityAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(action="check_permissions")
        assert result.status == "success"


class TestExecutiveAgent:
    def test_interpret(self, pm, le):
        agent = ExecutiveAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(message="Deploy the app")
        assert result.status == "success"
        assert "plan" in result.data

    def test_decompose(self, pm, le):
        agent = ExecutiveAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(action="decompose", request="Build and deploy")
        assert result.status == "success"
        assert "tasks" in result.data

    def test_status(self, pm, le):
        agent = ExecutiveAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(action="status")
        assert result.status == "success"


class TestMemoryAgent:
    def test_store_note(self, pm, le, tmp_path):
        pm.grant_permission("memory.write", scope="session")
        store = MemoryStore(store_file=tmp_path / "store.json")
        agent = MemoryAgent(store=store, permission_manager=pm, learning_engine=le)
        result = agent.run(action="store", message="Important note")
        assert result.status == "success"
        assert "entry" in result.data

    def test_search(self, pm, le, tmp_path):
        pm.grant_permission("memory.write", scope="session")
        store = MemoryStore(store_file=tmp_path / "store.json")
        agent = MemoryAgent(store=store, permission_manager=pm, learning_engine=le)
        agent.run(action="store", message="Deploy on Friday")
        result = agent.run(action="search", query="Friday")
        assert result.status == "success"
        assert len(result.data["results"]) >= 1


class TestAnalysisAgent:
    def test_analyze_text(self, pm, le):
        pm.grant_permission("file.read", scope="session")
        agent = AnalysisAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(action="analyze_text", message="The system is performing well")
        assert result.status == "success"


class TestDocumentationAgent:
    def test_session_summary(self, pm, le):
        pm.grant_permission("file.modify", scope="session")
        agent = DocumentationAgent(permission_manager=pm, learning_engine=le)
        result = agent.run(action="session_summary", events=[
            {"agent": "system", "action": "info", "detail": "Got system info"}
        ])
        assert result.status == "success"
        assert "summary" in result.data
