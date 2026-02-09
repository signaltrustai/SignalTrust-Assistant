# --- AGENT MODULE ---
agent_parser = subparsers.add_parser("agent")
agent_sub = agent_parser.add_subparsers(dest="command", required=True)

agent_focus = agent_sub.add_parser("focus")
