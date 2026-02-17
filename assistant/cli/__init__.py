"""
OmniJARVIS CLI — Command-line interface for the personal AI OS.

Provides both structured sub-commands (legacy compatibility) and a
natural-language ``jarvis`` command that routes through the orchestrator.

Usage::

    python -m assistant.cli jarvis "Analyse ce fichier"
    python -m assistant.cli agent list
    python -m assistant.cli memory list
    python -m assistant.cli ai ask "What is Python?"
"""

import argparse
import json
import sys
from typing import Any

from assistant import memory, tasks, scripts, projects, ecosystem
from assistant.ai import agent as ai_agent
from assistant.ai.client import ask_ai
from assistant.agents.focus_agent import FocusAgent


def _print(obj: Any, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    else:
        print(obj)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnijarvis",
        description="🧠 OmniJARVIS — L'Assistante Personnelle AI Ultime",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")

    sub = parser.add_subparsers(dest="module", required=True)

    # ── jarvis (natural language) ──────────────────────────────────
    j = sub.add_parser("jarvis", help="Send a natural-language request to OmniJARVIS")
    j.add_argument("message", nargs="?", default="", help="Your request")
    j.add_argument("--agent", help="Force a specific agent")
    j.add_argument("--action", help="Agent action to invoke")
    j.add_argument("--grant", help="Grant a permission (action type)")
    j.add_argument("--revoke", help="Revoke a permission (action type)")
    j.add_argument("--scope", default="session", choices=["once", "session", "always"])

    # ── agent ──────────────────────────────────────────────────────
    ag = sub.add_parser("agent", help="Manage OmniJARVIS agents")
    ag_sub = ag.add_subparsers(dest="command", required=True)
    ag_sub.add_parser("list", help="List all agents")
    ag_sub.add_parser("status", help="Session summary")
    ag_sub.add_parser("stats", help="Usage statistics")
    ag_sub.add_parser("profile", help="User profile")
    ag_focus = ag_sub.add_parser("focus", help="Run FocusAgent")
    ag_focus.add_argument("--file", default="todo-v1.md")

    # ── permissions ────────────────────────────────────────────────
    perm = sub.add_parser("permissions", help="Manage permissions")
    perm_sub = perm.add_subparsers(dest="command", required=True)
    perm_sub.add_parser("list", help="List active permissions")
    perm_sub.add_parser("audit", help="Show audit log")
    pg = perm_sub.add_parser("grant", help="Grant a permission")
    pg.add_argument("action")
    pg.add_argument("--scope", default="session", choices=["once", "session", "always"])
    pr = perm_sub.add_parser("revoke", help="Revoke a permission")
    pr.add_argument("action")

    # ── memory (legacy) ────────────────────────────────────────────
    mem = sub.add_parser("memory")
    mem_sub = mem.add_subparsers(dest="command", required=True)
    mem_sub.add_parser("list")
    ml = mem_sub.add_parser("load")
    ml.add_argument("key")
    ms = mem_sub.add_parser("save")
    ms.add_argument("key")
    ms.add_argument("value")

    # ── tasks (legacy) ─────────────────────────────────────────────
    tk = sub.add_parser("tasks")
    tk_sub = tk.add_subparsers(dest="command", required=True)
    tl = tk_sub.add_parser("list")
    tl.add_argument("--file", default="todo-v1.md")
    tn = tk_sub.add_parser("next")
    tn.add_argument("--file", default="todo-v1.md")

    # ── scripts (legacy) ──────────────────────────────────────────
    sc = sub.add_parser("scripts")
    sc_sub = sc.add_subparsers(dest="command", required=True)
    sg = sc_sub.add_parser("generate")
    sg.add_argument("--type", required=True, choices=["powershell", "python", "git", "actions"])
    sg.add_argument("--description", required=True)

    # ── projects (legacy) ─────────────────────────────────────────
    pj = sub.add_parser("projects")
    pj_sub = pj.add_subparsers(dest="command", required=True)
    pj_sub.add_parser("list")
    ps = pj_sub.add_parser("status")
    ps.add_argument("name")

    # ── ecosystem (legacy) ────────────────────────────────────────
    ec = sub.add_parser("ecosystem")
    ec_sub = ec.add_subparsers(dest="command", required=True)
    er = ec_sub.add_parser("repo")
    er.add_argument("repo")
    ei = ec_sub.add_parser("issues")
    ei.add_argument("repo")
    ecc = ec_sub.add_parser("commits")
    ecc.add_argument("repo")
    ecc.add_argument("--n", type=int, default=10)

    # ── ai (legacy) ───────────────────────────────────────────────
    ai = sub.add_parser("ai")
    ai_sub = ai.add_subparsers(dest="command", required=True)
    aa = ai_sub.add_parser("ask")
    aa.add_argument("prompt")
    asu = ai_sub.add_parser("summarize")
    asu.add_argument("text")
    aan = ai_sub.add_parser("analyze")
    aan.add_argument("text")
    acg = ai_sub.add_parser("codegen")
    acg.add_argument("description")
    aim = ai_sub.add_parser("improve-memory")
    aim.add_argument("key")
    aim.add_argument("content")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    as_json = getattr(args, "json", False)

    # ── OmniJARVIS orchestrator commands ──────────────────────────
    if args.module == "jarvis":
        from assistant.orchestrator import OmniJARVIS
        jarvis = OmniJARVIS()

        # Permission management shortcuts
        if args.grant:
            jarvis.grant_permission(args.grant, args.scope)
            _print({"status": "granted", "action": args.grant, "scope": args.scope}, as_json)
            return 0
        if args.revoke:
            jarvis.revoke_permission(args.revoke)
            _print({"status": "revoked", "action": args.revoke}, as_json)
            return 0

        if not args.message:
            print(f"\n🧠 {jarvis.INIT_MESSAGE}\n")
            return 0

        # Direct agent call or routed message
        if args.agent:
            result = jarvis.handle_direct(args.agent, action=args.action, message=args.message)
            _print(result.to_dict() if as_json else result.to_dict(), as_json)
        else:
            response = jarvis.handle(args.message)
            if as_json:
                _print(response.to_dict(), as_json=True)
            else:
                print(response.format_text())
        return 0

    if args.module == "agent":
        from assistant.orchestrator import OmniJARVIS
        jarvis = OmniJARVIS()

        if args.command == "list":
            _print(jarvis.list_agents(), as_json)
        elif args.command == "status":
            print(jarvis.session_summary())
        elif args.command == "stats":
            _print(jarvis.get_stats(), as_json)
        elif args.command == "profile":
            _print(jarvis.get_profile(), as_json)
        elif args.command == "focus":
            agent = FocusAgent(task_file=args.file)
            result = agent.run()
            _print(result, as_json)
        return 0

    if args.module == "permissions":
        from assistant.orchestrator import OmniJARVIS
        jarvis = OmniJARVIS()

        if args.command == "list":
            _print(jarvis.list_permissions(), as_json)
        elif args.command == "audit":
            _print(jarvis.audit_log(), as_json)
        elif args.command == "grant":
            jarvis.grant_permission(args.action, args.scope)
            _print({"status": "granted", "action": args.action, "scope": args.scope}, as_json)
        elif args.command == "revoke":
            jarvis.revoke_permission(args.action)
            _print({"status": "revoked", "action": args.action}, as_json)
        return 0

    # ── Legacy commands ───────────────────────────────────────────
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

    elif args.module == "ai":
        if args.command == "ask":
            _print(ask_ai(args.prompt), as_json=False)
        elif args.command == "summarize":
            _print(ai_agent.summarize(args.text), as_json=False)
        elif args.command == "analyze":
            _print(ai_agent.analyze(args.text), as_json=False)
        elif args.command == "codegen":
            _print(ai_agent.generate_code(args.description), as_json=False)
        elif args.command == "improve-memory":
            _print(ai_agent.improve_memory_entry(args.key, args.content), as_json=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
