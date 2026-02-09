elif args.module == "agent":
    if args.command == "focus":
        from assistant.agents.focus_agent import FocusAgent
        agent = FocusAgent()
        result = agent.run()
        _print(result, as_json)
