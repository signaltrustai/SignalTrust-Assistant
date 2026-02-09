"""
Tasks module for SignalTrust Assistant.

Parses and manipulates Markdown-based planning files in `plans/`.
"""

from pathlib import Path
from typing import List, Dict, Optional

PLANS_ROOT = Path("plans")


def list_tasks(file: str) -> List[Dict]:
    """
    Parse a Markdown plan file and return a list of tasks.

    Very simple v1: lines starting with '- [ ]' or '- [x]'.
    """
    path = PLANS_ROOT / file
    if not path.exists():
        return []

    tasks: List[Dict] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.rstrip()
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            status = "completed" if line.startswith("- [x]") else "pending"
            title = line[5:].strip()
            tasks.append(
                {
                    "id": f"{file}:{i}",
                    "title": title,
                    "status": status,
                    "priority": "normal",
                    "line_number": i,
                    "file": file,
                }
            )
    return tasks


def add_task(file: str, task: str, priority: str = "normal") -> None:
    """
    Append a new task at the end of the file.
    """
    path = PLANS_ROOT / file
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(f"- [ ] {task}\n")


def complete_task(file: str, task_id: str) -> bool:
    """
    Mark a task as completed by its id (file:line_number).

    :return: True if updated, False otherwise.
    """
    path = PLANS_ROOT / file
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8").splitlines()
    updated = False

    for i, line in enumerate(content, start=1):
        if f"{file}:{i}" == task_id and line.startswith("- [ ]"):
            content[i - 1] = line.replace("- [ ]", "- [x]", 1)
            updated = True
            break

    if updated:
        path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return updated


def get_next_task(file: str) -> Optional[Dict]:
    """
    Return the first pending task in the file.
    """
    tasks = list_tasks(file)
    for t in tasks:
        if t["status"] == "pending":
            return t
    return None
