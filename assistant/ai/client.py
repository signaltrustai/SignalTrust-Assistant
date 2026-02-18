"""
AI client for SignalTrust Assistant.

Handles communication with the Groq API.
"""

import os
from typing import Optional

from groq import Groq, GroqError


def load_api_key() -> str:
    """
    Read the API key from the environment variable GROQ_API_KEY.

    :return: The API key string.
    :raises RuntimeError: If the environment variable is not set.
    """
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is not set. "
            "Please set it before using AI features."
        )
    return key


def ask_ai(prompt: str, model: str = "llama3-70b-8192", temperature: float = 0.7) -> str:
    """
    Send a prompt to the Groq API and return the response text.

    :param prompt: The user prompt to send.
    :param model: The model to use (default: llama3-70b-8192).
    :param temperature: Sampling temperature (default: 0.7).
    :return: The assistant's response text.
    """
    api_key = load_api_key()
    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are SignalTrust Assistant, an AI helper for software development."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
    except GroqError as exc:
        raise RuntimeError(f"Groq API request failed: {exc}") from exc

    if not response.choices:
        raise RuntimeError("Groq API returned an empty response.")

    return response.choices[0].message.content or ""
