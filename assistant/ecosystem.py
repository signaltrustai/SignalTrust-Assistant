"""
Ecosystem module for SignalTrust Assistant.

Handles external integrations, starting with GitHub API.
"""

from typing import Any, Dict, List
import os

import requests


GITHUB_API_BASE = "https://api.github.com"


def _github_headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_repo_info(repo: str) -> Dict[str, Any]:
    """
    Get metadata for a GitHub repository (owner/repo).
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}"
    resp = requests.get(url, headers=_github_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def list_open_issues(repo: str) -> List[Dict[str, Any]]:
    """
    List open issues for a repository.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/issues"
    resp = requests.get(url, headers=_github_headers(), timeout=15, params={"state": "open"})
    resp.raise_for_status()
    return resp.json()


def list_recent_commits(repo: str, n: int = 10) -> List[Dict[str, Any]]:
    """
    List the last n commits for a repository.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/commits"
    resp = requests.get(url, headers=_github_headers(), timeout=15, params={"per_page": n})
    resp.raise_for_status()
    return resp.json()
