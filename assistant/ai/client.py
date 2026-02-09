"""
AI client for SignalTrust Assistant.

Handles communication with the OpenAI API.
"""

import os
from typing import Optional

import openai


def load_api_key() -> str:
    """
    Read the API key from the environment variable OPENAI_API_KEY.

    :return: The API key string.
    :raises RuntimeError: If the environment variable is not set.
    """
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it before using AI features."
        )
    return key


def ask_ai(prompt: str, model: str = "gpt-4o", temperature: float = 0.7) -> str:
    """
    Send a prompt to the OpenAI API and return the response text.

    :param prompt: The user prompt to send.
    :param model: The model to use (default: gpt-4o).
    :param temperature: Sampling temperature (default: 0.7).
    :return: The assistant's response text.
    """
    api_key = load_api_key()
    client = openai.OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are SignalTrust Assistant, an AI helper for software development."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
    except openai.OpenAIError as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc}") from exc

    if not response.choices:
        raise RuntimeError("OpenAI API returned an empty response.")

    return response.choices[0].message.content or ""
