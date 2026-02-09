"""
CLI entrypoint for SignalTrust Assistant.

Usage:
    python -m assistant.cli <module> <command> [options]
"""

import argparse
import json
from typing import Any

from assistant import memory, tasks, scripts, projects, ecosystem


def _print(obj: Any, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    else:
        print(obj)


def main() -> None:
    parser = argparse.ArgumentParser(prog="signaltrust-assistant")
    parser.add_argument("--json", action="store_true", help="Output JSON where applicable")

    subparsers = parser.add_subparsers(dest="module", required=True)

    # memory
    mem_parser = subparsers.add_parser("memory")
    mem_sub = mem_parser.add_subparsers(dest="command", required=True)

    mem_list = mem_sub.add_parser("list")
    mem_load = mem_sub.add_parser("load")
    mem_load.add_argument("key")
    mem_save = mem_sub.add_parser("save")
    mem_save.add_argument("key")
    mem_save.add_argument("value")

    # tasks
    tasks_parser = subparsers.add_parser("tasks")
    tasks_sub = tasks_parser.add_subparsers(dest="command", required=True)

    t_list = tasks_sub.add_parser("list")
    t_list.add_argument("--file", default="todo-v1.md")
    t_next = tasks_sub.add_parser("next")
    t_next.add_argument("--file", default="todo-v1.md")

    # scripts
    scripts_parser = subparsers.add_parser("scripts")
    scripts_sub = scripts_parser.add_subparsers(dest="command", required=True)

    s_gen = scripts_sub.add_parser("generate")
    s_gen.add_argument("--type", required=True, choices=["powershell", "python", "git", "actions"])
    s_gen.add_argument("--description", required=True)

    # projects
    proj_parser = subparsers.add_parser("projects")
    proj_sub = proj_parser.add_subparsers(dest="command", required=True)

    proj_list = proj_sub.add_parser("list")
    proj_status = proj_sub.add_parser("status")
    proj_status.add_argument("name")

    # ecosystem
    eco_parser = subparsers.add_parser("ecosystem")
    eco_sub = eco_parser.add_subparsers(dest="command", required=True)

    eco_repos = eco_sub.add_parser("repo")
    eco_repos.add_argument("repo")
    eco_issues = eco_sub.add_parser("issues")
    eco_issues.add_argument("repo")
    eco_commits = eco_sub.add_parser("commits")
    eco_commits.add_argument("repo")
    eco_commits.add_argument("--n", type=int, default=10)

    args = parser.parse_args()
    as_json = getattr(args, "json", False)

    if args.module == "memory":
        if args.command == "list":
            _print(memory.list_contexts(), as_json)
        elif args.command == "load":
            _print(memory.load_context(args.key), as_json)
        elif args.command == "save":
            memory.save_context(args.key, args.value)
            _print({"status": "ok"}, as_json)

    elif args.module == "tasks":
        if args.command == "list":
            _print(tasks.list_tasks(args.file), as_json)
        elif args.command == "next":
            _print(tasks.get_next_task(args.file), as_json)

    elif args.module == "scripts":
        if args.command == "generate":
            if args.type == "powershell":
                _print(scripts.generate_powershell(args.description), as_json=False)
            elif args.type == "python":
                _print(scripts.generate_python(args.description), as_json=False)
            elif args.type == "git":
                _print("\n".join(scripts.generate_git_commands(args.description)), as_json=False)
            elif args.type == "actions":
                _print(scripts.generate_github_actions(args.description), as_json=False)

    elif args.module == "projects":
        if args.command == "list":
            _print(projects.list_projects(), as_json)
        elif args.command == "status":
            _print(projects.get_project_status(args.name), as_json)

    elif args.module == "ecosystem":
        if args.command == "repo":
            _print(ecosystem.get_repo_info(args.repo), as_json)
        elif args.command == "issues":
            _print(ecosystem.list_open_issues(args.repo), as_json)
        elif args.command == "commits":
            _print(ecosystem.list_recent_commits(args.repo, args.n), as_json)


if __name__ == "__main__":
    main()
