"""Tests for the OmniJARVIS permission system."""

import json
import tempfile
from pathlib import Path

import pytest

from assistant.permissions import (
    AuditDecision,
    PermissionManager,
    PermissionRequest,
    PermissionScope,
    PermissionStatus,
    SecurityAuditEntry,
)


@pytest.fixture
def pm(tmp_path):
    """Create a PermissionManager backed by a temp file."""
    return PermissionManager(permissions_file=tmp_path / "perms.json")


class TestPermissionManager:
    def test_grant_once(self, pm):
        pm.grant_permission("file.read", scope="once")
        # "once" does not create a standing grant
        assert not pm.check_permission("file.read")

    def test_grant_session(self, pm):
        pm.grant_permission("file.read", scope="session")
        assert pm.check_permission("file.read")

    def test_grant_always_persists(self, tmp_path):
        pf = tmp_path / "perms.json"
        pm1 = PermissionManager(permissions_file=pf)
        pm1.grant_permission("file.read", scope="always")
        assert pm1.check_permission("file.read")

        # New instance reads from disk
        pm2 = PermissionManager(permissions_file=pf)
        assert pm2.check_permission("file.read")

    def test_revoke_permission(self, pm):
        pm.grant_permission("file.read", scope="session")
        assert pm.check_permission("file.read")
        pm.revoke_permission("file.read")
        assert not pm.check_permission("file.read")

    def test_deny_permission(self, pm):
        pm.deny_permission("file.read")
        log = pm.audit_log()
        assert any(e["decision"] == "denied" for e in log)

    def test_unknown_action_raises(self, pm):
        with pytest.raises(ValueError, match="Unknown action type"):
            pm.check_permission("fake.action")

    def test_request_auto_grants_when_standing(self, pm):
        pm.grant_permission("file.read", scope="session")
        req = pm.request_permission("file.read", "Read config")
        assert req.status == PermissionStatus.GRANTED

    def test_request_pending_when_no_standing(self, pm):
        req = pm.request_permission("file.read", "Read config")
        assert req.status == PermissionStatus.PENDING

    def test_list_permissions(self, pm):
        pm.grant_permission("file.read", scope="session")
        pm.grant_permission("memory.write", scope="session")
        perms = pm.list_permissions()
        actions = [p["action"] for p in perms]
        assert "file.read" in actions
        assert "memory.write" in actions

    def test_audit_trail(self, pm):
        pm.grant_permission("file.read", scope="session")
        pm.revoke_permission("file.read")
        log = pm.audit_log()
        assert len(log) >= 2
        decisions = [e["decision"] for e in log]
        assert "granted" in decisions
        assert "revoked" in decisions


class TestPermissionRequest:
    def test_to_dict(self):
        req = PermissionRequest(
            action="file.read", description="test", status=PermissionStatus.GRANTED
        )
        d = req.to_dict()
        assert d["status"] == "granted"
        assert d["action"] == "file.read"


class TestSecurityAuditEntry:
    def test_to_dict(self):
        entry = SecurityAuditEntry(
            action="file.read",
            description="test",
            decision=AuditDecision.GRANTED,
        )
        d = entry.to_dict()
        assert d["decision"] == "granted"
