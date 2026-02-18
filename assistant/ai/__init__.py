"""
AI integration module for SignalTrust Assistant.

Provides AI-powered features using the Groq API.
"""

from assistant.ai.client import ask_ai, load_api_key
from assistant.ai.agent import summarize, analyze, generate_code, improve_memory_entry
