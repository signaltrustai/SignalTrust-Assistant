"""
OmniJARVIS Web API — FastAPI-based HTTP interface.

Provides REST endpoints for the full OmniJARVIS system:
natural-language chat, agent management, permissions, and statistics.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from assistant.orchestrator import OmniJARVIS


# ---------------------------------------------------------------------------
# Application & state
# ---------------------------------------------------------------------------

app = FastAPI(
    title="OmniJARVIS API",
    description="🧠 L'Assistante Personnelle AI Ultime — REST API",
    version="1.0.0",
)

# Single shared instance for the lifetime of the server
_jarvis = OmniJARVIS()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    prompt: str
    agent: Optional[str] = None
    action: Optional[str] = None


class ChatResponse(BaseModel):
    summary: str
    steps: List[Dict[str, str]] = []
    result: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []


class PermissionRequest(BaseModel):
    action: str
    scope: str = "session"


class PermissionResponse(BaseModel):
    status: str
    action: str
    scope: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> Dict[str, str]:
    """Health check & init message."""
    return {"status": "online", "message": _jarvis.INIT_MESSAGE}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Send a natural-language request to OmniJARVIS."""
    if req.agent:
        result = _jarvis.handle_direct(req.agent, action=req.action, message=req.prompt)
        return ChatResponse(
            summary=result.message,
            result=result.data,
            suggestions=[],
        )

    response = _jarvis.handle(req.prompt)
    return ChatResponse(
        summary=response.summary,
        steps=response.steps,
        result=response.result,
        suggestions=response.suggestions,
    )


@app.get("/agents")
def list_agents() -> List[Dict[str, Any]]:
    """List all registered agents."""
    return _jarvis.list_agents()


@app.get("/status")
def session_status() -> Dict[str, str]:
    """Get session summary."""
    return {"summary": _jarvis.session_summary()}


@app.get("/stats")
def usage_stats() -> Dict[str, Any]:
    """Get usage statistics."""
    return _jarvis.get_stats()


@app.get("/profile")
def user_profile() -> Dict[str, Any]:
    """Get user profile."""
    return _jarvis.get_profile()


@app.get("/permissions")
def list_permissions() -> List[Dict[str, Any]]:
    """List active permissions."""
    return _jarvis.list_permissions()


@app.post("/permissions/grant", response_model=PermissionResponse)
def grant_permission(req: PermissionRequest) -> PermissionResponse:
    """Grant a permission."""
    _jarvis.grant_permission(req.action, req.scope)
    return PermissionResponse(status="granted", action=req.action, scope=req.scope)


@app.post("/permissions/revoke", response_model=PermissionResponse)
def revoke_permission(req: PermissionRequest) -> PermissionResponse:
    """Revoke a permission."""
    _jarvis.revoke_permission(req.action)
    return PermissionResponse(status="revoked", action=req.action)


@app.get("/audit")
def audit_log() -> List[Dict[str, Any]]:
    """Get security audit trail."""
    return _jarvis.audit_log()
