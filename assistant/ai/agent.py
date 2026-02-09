"""
AI agent module for SignalTrust Assistant.

Provides high-level AI-powered helper functions.
"""

from assistant.ai.client import ask_ai


def summarize(text: str) -> str:
    """
    Summarize the given text using AI.

    :param text: The text to summarize.
    :return: A concise summary.
    """
    prompt = f"Summarize the following text concisely:\n\n{text}"
    return ask_ai(prompt)


def analyze(text: str) -> str:
    """
    Analyze the given text and provide insights using AI.

    :param text: The text to analyze.
    :return: An analytical response.
    """
    prompt = f"Analyze the following text and provide key insights:\n\n{text}"
    return ask_ai(prompt)


def generate_code(description: str) -> str:
    """
    Generate code based on a description using AI.

    :param description: A description of the desired code.
    :return: Generated source code.
    """
    prompt = (
        f"Generate clean, well-documented code for the following requirement. "
        f"Return only the code with comments, no extra explanation:\n\n{description}"
    )
    return ask_ai(prompt)


def improve_memory_entry(key: str, content: str) -> str:
    """
    Improve a memory entry using AI.

    :param key: The memory entry key (for context).
    :param content: The current content of the memory entry.
    :return: An improved version of the content.
    """
    prompt = (
        f"Improve the following memory entry (key: '{key}'). "
        f"Make it clearer, more structured, and more useful:\n\n{content}"
    )
    return ask_ai(prompt)
