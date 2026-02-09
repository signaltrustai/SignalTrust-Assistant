# Agents

## What is an Agent?

An **agent** in SignalTrust Assistant is an autonomous module that can independently load a task, reason about it using the AI module, execute actions, and persist results to memory. Agents operate in a loop-friendly fashion — each invocation picks up the next piece of work, processes it, and returns a structured report.

## FocusAgent

`FocusAgent` is the first autonomous agent shipped with the assistant.

### How it works

1. **Load task** — reads the next pending task from the plan file (default `plans/todo-v1.md`) via `tasks.get_next_task()`.
2. **Analyze** — sends the task title to the AI module (`assistant.ai.agent.analyze()`) for insights.
3. **Plan** — generates a short, numbered execution plan based on the task and analysis.
4. **Log** — writes a timestamped Markdown log to `memory/agent-logs/`.
5. **Remember** — saves a memory entry through `memory.save_context()` so insights are available to future runs.
6. **Report** — returns a structured dictionary containing the task, analysis, plan, log path, and memory key.

### Running FocusAgent

Use the CLI:

```bash
python -m assistant agent focus
```

Pass `--json` to get the report as formatted JSON:

```bash
python -m assistant agent focus --json
```

## Adding Future Agents

To add a new agent:

1. Create a new file in `assistant/agents/` (e.g., `review_agent.py`).
2. Implement a class with a `run()` method that returns a structured report (dict).
3. Register a CLI sub-command under the `agent` module in `assistant/__init__.py`.
4. Document the new agent in this file.
