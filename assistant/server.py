"""
OmniJARVIS — FastAPI app re-export.

This module re-exports the app from assistant.web.server for backward
compatibility.
"""

from assistant.web.server import app  # noqa: F401
