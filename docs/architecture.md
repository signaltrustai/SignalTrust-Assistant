# Architecture (initial draft)

## High-level layout
- **Memory layer (assistant/memory):** Markdown-based knowledge base for projects, decisions, preferences, and reusable snippets.
- **Orchestrator (assistant/orchestrator):** Coordinates agents, routes intents, and stitches memory + task outputs into actionable plans.
- **Task runners (assistant/tasks):** Specialized executors for planning, coding, documentation, and verification workflows.
- **Script library (assistant/scripts):** Parameterized PowerShell/Python/Git automation generated or curated by the assistant.

## Data flow (first iteration)
1. User intent or goal is captured and stored with references to related memory.
2. Orchestrator decomposes intent into tasks and selects runners or script templates.
3. Task outputs and decisions are written back to memory as markdown for traceability.
4. Generated scripts/commands are offered with review/dry-run defaults before execution.
