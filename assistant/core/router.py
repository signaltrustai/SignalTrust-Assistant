"""
OmniJARVIS Intelligent Router — Intent detection and agent dispatch.

Analyses incoming natural-language messages (French and English) and
routes them to the most appropriate specialised agent.  When no clear
match is found the Executive Agent acts as the fallback decision-maker.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Intent keywords (French + English, case-insensitive)
# ---------------------------------------------------------------------------

_INTENT_MAP: Dict[str, List[str]] = {
    "memory": [
        # French
        "souviens-toi", "souviens", "retiens", "retenir", "note", "mémorise",
        "mémoire", "rappelle", "contexte", "enregistre",
        # English
        "remember", "store", "memory", "save context", "note down", "recall",
    ],
    "analysis": [
        "analyse", "analyser", "explique", "expliquer", "comprends",
        "résume", "résumer", "résumé", "évalue", "diagnostique",
        "analyze", "explain", "understand", "summarize", "summarise",
        "evaluate", "diagnose", "review", "inspect", "assess",
    ],
    "system": [
        "fichier", "dossier", "script", "automation", "automatisation",
        "exécute", "processus", "disque", "système", "commande", "terminal",
        "file", "folder", "directory", "process", "disk", "execute",
        "command", "run script", "shell", "open app",
    ],
    "documentation": [
        "documente", "documentation", "rapport", "changelog",
        "résumé de session", "readme", "guide", "rédige",
        "document", "report", "write docs", "session summary",
        "write guide", "changelog", "update docs",
    ],
    "code": [
        "code", "coder", "programmer", "génère du code", "générer",
        "modifier le code", "refactoriser", "déboguer", "compiler",
        "generate code", "write code", "modify code", "refactor",
        "debug", "compile", "program", "develop", "coding",
    ],
    "communication": [
        "message", "email", "courriel", "réunion", "meeting",
        "envoie", "envoyer", "contact", "appel", "appeler",
        "send", "call", "schedule", "meeting", "mail",
    ],
    "cloud": [
        "cloud", "sauvegarde", "backup", "synchronise", "synchroniser",
        "upload", "télécharge", "télécharger", "download",
        "sync", "storage", "drive", "s3", "bucket",
    ],
    "vision": [
        "image", "photo", "vision", "voir", "regarde", "caméra",
        "lunettes", "reconnaître", "identifier", "scanner",
        "see", "look", "camera", "glasses", "recognize", "scan",
        "screenshot", "capture",
    ],
    "mobility": [
        "appareil", "téléphone", "montre connectée", "tablette", "wearable",
        "connecté", "bluetooth", "iot", "smartphone", "smartwatch",
        "device", "phone", "watch", "tablet", "wearable", "gadget",
    ],
    "productivity": [
        "routine", "workflow", "automatise", "tâche", "planifie",
        "planning", "agenda", "productivité", "habitude",
        "routine", "workflow", "automate", "task", "schedule",
        "plan", "habit", "productivity", "daily",
    ],
    "security": [
        "sécurité", "permission", "audit", "alerte", "protection",
        "chiffrement", "mot de passe", "accès", "menace",
        "security", "permission", "audit", "alert", "protect",
        "encrypt", "password", "access", "threat", "vulnerability",
    ],
}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

@dataclass
class RouteResult:
    """Result of the routing decision.

    :param agent: The chosen agent identifier.
    :param confidence: Score (0.0–1.0) indicating match strength.
    :param matched_keywords: Keywords that triggered the match.
    :param original_message: The user message that was analysed.
    """

    agent: str
    confidence: float
    matched_keywords: List[str] = field(default_factory=list)
    original_message: str = ""


class Router:
    """Intent-based router that dispatches messages to OmniJARVIS agents.

    The router scores each agent by counting keyword hits in the message
    and picks the highest-scoring one.  If no agent scores above the
    threshold the ``executive`` agent acts as the fallback.

    Usage::

        router = Router()
        route = router.route("Analyse ce fichier pour moi")
        print(route.agent)  # → "analysis"
    """

    def __init__(
        self,
        intent_map: Optional[Dict[str, List[str]]] = None,
        threshold: float = 0.1,
    ) -> None:
        """
        :param intent_map: Custom keyword map (agent → keywords).
            Defaults to the built-in bilingual map.
        :param threshold: Minimum normalised score to accept a match
            (below this the executive fallback is used).
        """
        self._intent_map = intent_map or _INTENT_MAP
        self._threshold = threshold

    def route(self, message: str) -> RouteResult:
        """Determine which agent should handle *message*.

        :param message: The user's raw input text.
        :return: A :class:`RouteResult` with the chosen agent and metadata.
        """
        msg_lower = message.lower()
        scores: Dict[str, Tuple[float, List[str]]] = {}

        for agent, keywords in self._intent_map.items():
            matched: List[str] = []
            for kw in keywords:
                if kw in msg_lower:
                    matched.append(kw)
            if matched:
                # Score combines match count with keyword density.
                # More matches = higher score; long keyword lists don't
                # penalise agents unfairly.
                score = len(matched) * (1.0 + len(matched) / len(keywords))
                scores[agent] = (score, matched)

        if not scores:
            return RouteResult(
                agent="executive",
                confidence=0.0,
                original_message=message,
            )

        best_agent = max(scores, key=lambda a: scores[a][0])
        best_score, best_keywords = scores[best_agent]

        if best_score < self._threshold:
            return RouteResult(
                agent="executive",
                confidence=best_score,
                matched_keywords=best_keywords,
                original_message=message,
            )

        return RouteResult(
            agent=best_agent,
            confidence=best_score,
            matched_keywords=best_keywords,
            original_message=message,
        )

    def route_to_handler(
        self,
        message: str,
        handlers: Dict[str, Callable[..., Any]],
    ) -> Dict[str, Any]:
        """Route *message* and immediately call the matching handler.

        :param message: User's input.
        :param handlers: Map of agent name → callable.
        :return: The handler's return value, or an error dict.
        """
        result = self.route(message)
        handler = handlers.get(result.agent)
        if handler is None:
            handler = handlers.get("executive")
        if handler is None:
            return {
                "agent": result.agent,
                "status": "error",
                "message": f"No handler registered for agent '{result.agent}'.",
            }
        return handler(message)
