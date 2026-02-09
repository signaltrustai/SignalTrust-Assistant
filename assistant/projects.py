"""
Projects module for SignalTrust Assistant.

Keeps track of all SignalTrust ecosystem projects via config/projects.yaml.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

CONFIG_ROOT = Path("config")
PROJECTS_FILE = CONFIG_ROOT / "projects.yaml"


def _load_projects() -> List[Dict[str, Any]]:
    if not PROJECTS_FILE.exists():
        return []
    data = yaml.safe_load(PROJECTS_FILE.read_text(encoding="utf-8")) or {}
    return data.get("projects", [])


def list_projects() -> List[Dict[str, Any]]:
    """
    Return all registered projects with metadata.
    """
    return _load_projects()


def get_project_status(name: str) -> Optional[Dict[str, Any]]:
    """
    Return metadata for a given project name.
    """
    for project in _load_projects():
        if project.get("name") == name:
            return project
    return None


def add_project(name: str, repo_url: str, description: str) -> None:
    """
    Register a new project in config/projects.yaml.
    """
    CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
    projects = _load_projects()

    projects = [p for p in projects if p.get("name") != name]
    projects.append(
        {
            "name": name,
            "repo": repo_url,
            "description": description,
            "status": "active",
        }
    )

    PROJECTS_FILE.write_text(
        yaml.safe_dump({"projects": projects}, sort_keys=False),
        encoding="utf-8",
    )
