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

    # -------------------------
    # MEMORY COMMANDS
    # -------------------------
    mem_parser = subparsers.add_parser("memory")
    mem_sub = mem_parser.add_subparsers(dest="command", required=True)

    mem_sub.add_parser("list")
    mem_load = mem_sub.add_parser("load")
    mem_load.add_argument("key")
    mem_save = mem_sub.add_parser("save")
    mem_save.add_argument("key")
    mem_save.add_argument("value")

    # -------------------------
    # TASKS COMMANDS
    # -------------------------
    tasks_parser = subparsers.add_parser("tasks")
    tasks_sub = tasks_parser.add_subparsers(dest="command", required=True)

    t_list = tasks_sub.add_parser("list")
    t_list.add_argument("--file", default="todo-v1.md")
    t_next = tasks_sub.add_parser("next")
    t_next.add_argument("--file", default="todo-v1.md")

    # -------------------------
    # SCRIPTS COMMANDS
    # -------------------------
    scripts_parser = subparsers.add_parser("scripts")
    scripts_sub = scripts_parser.add_subparsers(dest="command", required=True)

    s_gen = scripts_sub.add_parser("generate")
    s_gen.add_argument("--type", required=True, choices=["powershell", "python", "git", "actions"])
    s_gen.add_argument("--description", required=True)

    # -------------------------
    # PROJECTS COMMANDS
    # -------------------------
    proj_parser = subparsers.add_parser("projects")
    proj_sub = proj_parser.add_subparsers(dest="command", required=True)

    proj_sub.add_parser("list")
    proj_status = proj_sub.add_parser("status")
    proj_status.add_argument("name")

    # -------------------------
    # ECOSYSTEM COMMANDS
    # -------------------------
    eco_parser = subparsers.add_parser("ecosystem")
    eco_sub = eco_parser.add_subparsers(dest="command", required=True)

    eco_repos = eco_sub.add_parser("repo")
    eco_repos.add_argument("repo")
    eco_issues = eco_sub.add_parser("issues")
    eco_issues.add_argument("repo")
    eco_commits = eco_sub.add_parser("commits")
    eco_commits.add_argument("repo")
    eco_commits.add_argument("--n", type=int, default=10)

    # -------------------------
    # AGENT COMMANDS
    # -------------------------
    agent_parser = subparsers.add_parser("agent")
    agent_sub = agent_parser.add_subparsers(dest="command", required=True)

    agent_sub.add_parser("focus")

    # -------------------------
    # AI COMMANDS
    # -------------------------
    ai_parser = subparsers.add_parser("ai")
    ai_sub = ai_parser.add_subparsers(dest="command", required=True)

    ai_ask = ai_sub.add_parser("ask")
    ai_ask.add_argument("prompt")

    ai_learn = ai_sub.add_parser("learn")
    ai_learn.add_argument("prompt")
    ai_learn.add_argument("response")

    ai_sub.add_parser("improve")

    # -------------------------
    # PARSE ARGS
    # -------------------------
    args = parser.parse_args()
    as_json = getattr(args, "json", False)

    # -------------------------
    # MEMORY EXECUTION
    # -------------------------
    if args.module == "memory":
        if args.command == "list":
            _print(memory.list_contexts(), as_json)
        elif args.command == "load":
            _print(memory.load_context(args.key), as_json)
        elif args.command == "save":
            memory.save_context(args.key, args.value)
            _print({"status": "ok"}, as_json)

    # -------------------------
    # TASKS EXECUTION
    # -------------------------
    elif args.module == "tasks":
        if args.command == "list":
            _print(tasks.list_tasks(args.file), as_json)
        elif args.command == "next":
            _print(tasks.get_next_task(args.file), as_json)

    # -------------------------
    # SCRIPTS EXECUTION
    # -------------------------
    elif args.module == "scripts":
        if args.command == "generate":
            if args.type == "powershell":
                _print(scripts.generate_powershell(args.description))
            elif args.type == "python":
                _print(scripts.generate_python(args.description))
            elif args.type == "git":
                _print("\n".join(scripts.generate_git_commands(args.description)))
            elif args.type == "actions":
                _print(scripts.generate_github_actions(args.description))

    # -------------------------
    # PROJECTS EXECUTION
    # -------------------------
    elif args.module == "projects":
        if args.command == "list":
            _print(projects.list_projects(), as_json)
        elif args.command == "status":
            _print(projects.get_project_status(args.name), as_json)

    # -------------------------
    # ECOSYSTEM EXECUTION
    # -------------------------
    elif args.module == "ecosystem":
        if args.command == "repo":
            _print(ecosystem.get_repo_info(args.repo), as_json)
        elif args.command == "issues":
            _print(ecosystem.list_open_issues(args.repo), as_json)
        elif args.command == "commits":
            _print(ecosystem.list_recent_commits(args.repo, args.n), as_json)

    # -------------------------
    # AGENT EXECUTION
    # -------------------------
    elif args.module == "agent":
        if args.command == "focus":
            from assistant.agents.focus_agent import FocusAgent
            agent = FocusAgent()
            result = agent.run()
            _print(result, as_json)

    # -------------------------
    # AI EXECUTION
    # -------------------------
    elif args.module == "ai":
        if args.command == "ask":
            from assistant.ai.client import ask_ai
            result = ask_ai(args.prompt)
            _print(result, as_json)

        elif args.command == "learn":
            from assistant.ai.evolution import learn_from_interaction
            learn_from_interaction(args.prompt, args.response)
            _print({"status": "learned"}, as_json)

        elif args.command == "improve":
            from assistant.ai.evolution import improve_memory
            result = improve_memory()
            _print(result, as_json)
