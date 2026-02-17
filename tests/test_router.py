"""Tests for the OmniJARVIS intelligent router."""

import pytest

from assistant.core.router import Router, RouteResult


@pytest.fixture
def router():
    return Router()


class TestRouter:
    def test_french_analysis(self, router):
        result = router.route("Analyse ce texte et résume les points clés")
        assert result.agent == "analysis"

    def test_french_memory(self, router):
        result = router.route("Souviens-toi de cette information")
        assert result.agent == "memory"

    def test_french_code(self, router):
        result = router.route("Génère du code Python")
        assert result.agent == "code"

    def test_french_communication(self, router):
        result = router.route("Envoie un message à mon équipe")
        assert result.agent == "communication"

    def test_french_cloud(self, router):
        result = router.route("Synchronise mes sauvegardes cloud")
        assert result.agent == "cloud"

    def test_french_documentation(self, router):
        result = router.route("Documente ce projet")
        assert result.agent == "documentation"

    def test_french_productivity(self, router):
        result = router.route("Automatise ma routine")
        assert result.agent == "productivity"

    def test_french_security(self, router):
        result = router.route("Vérifie les permissions de sécurité")
        assert result.agent == "security"

    def test_french_system(self, router):
        result = router.route("Montre les infos système")
        assert result.agent == "system"

    def test_english_analyze(self, router):
        result = router.route("Analyze this file and explain it")
        assert result.agent == "analysis"

    def test_english_code(self, router):
        result = router.route("Write code for a REST API")
        assert result.agent == "code"

    def test_english_security(self, router):
        result = router.route("Check security audit")
        assert result.agent == "security"

    def test_fallback_executive(self, router):
        result = router.route("Fais quelque chose de cool")
        assert result.agent == "executive"

    def test_confidence_present(self, router):
        result = router.route("Analyse ce code")
        assert result.confidence > 0

    def test_matched_keywords(self, router):
        result = router.route("Analyse et résume")
        assert len(result.matched_keywords) > 0

    def test_original_message_preserved(self, router):
        msg = "Hello world"
        result = router.route(msg)
        assert result.original_message == msg

    def test_route_to_handler(self, router):
        handlers = {
            "executive": lambda m: {"agent": "executive", "message": m},
            "memory": lambda m: {"agent": "memory", "message": m},
        }
        result = router.route_to_handler("Souviens-toi de ça", handlers)
        assert result["agent"] == "memory"
