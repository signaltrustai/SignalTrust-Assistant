# SignalTrust Assistant — Architecture

## 1. Overview

SignalTrust Assistant is a modular, layered, multi-agent system designed to orchestrate, document, and automate the entire SignalTrust ecosystem. It acts as a persistent intelligent control plane across all projects — SignalTrust AI, TradingTrust, TrustToken, TrustWallet, and any future initiative.

The architecture prioritizes **separation of concerns**, **extensibility**, and **repository-native storage**. Every module has a single responsibility and communicates with the rest of the system through well-defined interfaces. All state is persisted as version-controlled files, making the assistant fully transparent and auditable.

---

## 2. Global Architecture

### 2.1 Layers

The system is organized into five horizontal layers, from user-facing to infrastructure:

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                    │
│          (CLI / Chat / IDE Integration)              │
├─────────────────────────────────────────────────────┤
│               Orchestration Layer                   │
│        (Agent Router / Task Dispatcher)              │
├───────────┬───────────┬───────────┬─────────────────┤
│  Memory   │   Tasks   │  Scripts  │   Ecosystem     │
│  Module   │   Module  │  Module   │    Module       │
│           │           │           ├─────────────────┤
│           │           │           │   Projects      │
│           │           │           │    Module       │
├───────────┴───────────┴───────────┴─────────────────┤
│                Core Utilities                       │
│      (Config, Logging, File I/O, Templates)          │
├─────────────────────────────────────────────────────┤
│              Storage & Persistence                  │
│      (Markdown, JSON/YAML, Git, File System)         │
└─────────────────────────────────────────────────────┘
```

**User Interface Layer** — The entry point for all interactions. In v1, this is a command-line interface (`assistant/cli/`). Future versions may add chat interfaces, IDE integrations, or messaging bots.

**Orchestration Layer** — The central dispatcher. It receives user requests, determines which module(s) to invoke, coordinates multi-module workflows, and returns consolidated results.

**Module Layer** — Five specialized modules handle distinct domains: memory, tasks, scripts, projects, and ecosystem. Each module operates independently and exposes a clean function-based API.

**Core Utilities Layer** — Shared infrastructure used by all modules: configuration loading, structured logging, file I/O helpers, and template rendering.

**Storage & Persistence Layer** — All data is stored as files within the repository: Markdown documents, JSON/YAML configs, and Git history. No external databases are required.

### 2.2 Module Map

| Module | Package | Responsibility |
|---|---|---|
| Memory | `assistant/memory/` | Long-term context storage and retrieval |
| Tasks | `assistant/tasks/` | Task management, sprint tracking, priorities |
| Scripts | `assistant/scripts/` | Script generation (PowerShell, Python, Git, CI/CD) |
| Projects | `assistant/projects/` | Multi-project ecosystem management |
| Ecosystem | `assistant/ecosystem/` | External integrations (GitHub API, cloud, blockchain) |
| CLI | `assistant/cli/` | Command-line interface and user interaction |

### 2.3 Data Flow

```
User Input (CLI command or natural language)
    │
    ▼
┌──────────────────┐
│   Orchestrator    │──── Parses intent, selects module(s)
└────────┬─────────┘
         │
    ┌────┼────┬──────────┬──────────┐
    ▼    ▼    ▼          ▼          ▼
 Memory Tasks Scripts Projects Ecosystem
    │    │    │          │          │
    └────┼────┴──────────┴──────────┘
         │
         ▼
   Storage Layer (read/write Markdown, JSON, YAML, Git)
         │
         ▼
   Formatted Output → User
```

1. The user sends a request via the CLI (structured command or, in future versions, natural language).
2. The orchestrator parses the intent and routes the request to the appropriate module(s).
3. The target module(s) execute the task, reading from and writing to the storage layer as needed.
4. Results are aggregated and returned to the user as actionable output (text, files, or scripts).
5. Side effects (file writes, config updates) are committed to Git for full traceability.

---

## 3. Orchestrator Core

The orchestrator is the central nervous system of the assistant. It is responsible for:

- **Intent Parsing** — Interpreting user commands and mapping them to module actions. In v1, this is based on explicit CLI subcommands. In future versions, an LLM-powered router will handle natural language intent detection.
- **Module Dispatch** — Calling the appropriate module function(s) with the correct parameters. Simple requests target a single module; complex workflows may chain multiple modules.
- **Context Injection** — Loading relevant memory entries before dispatching to a module, so each module operates with full context awareness.
- **Result Aggregation** — Collecting outputs from one or more modules and formatting them for the user.
- **Error Handling** — Catching module-level errors, logging them, and returning meaningful feedback to the user.

### Orchestrator Design Principles

1. **Stateless dispatch** — The orchestrator does not hold state between requests. All persistent state lives in the storage layer.
2. **Single entry point** — All user interactions pass through the orchestrator, ensuring consistent logging and error handling.
3. **Composable workflows** — Multi-step operations (e.g., "create a task, generate a script for it, and track the project") are composed by chaining module calls within the orchestrator.

---

## 4. Memory Module

**Package:** `assistant/memory/`

The memory module is the "second brain" of the assistant. It enables long-term context persistence across sessions, allowing the assistant to remember decisions, preferences, conventions, and project history.

### 4.1 Structure

Each memory entry is a structured unit containing:

| Field | Type | Description |
|---|---|---|
| `key` | string | Unique identifier for the context entry |
| `value` | string | The content of the memory (plain text or Markdown) |
| `tags` | list | Categorization tags (e.g., `decision`, `convention`, `roadmap`) |
| `created_at` | ISO 8601 | Timestamp of creation |
| `updated_at` | ISO 8601 | Timestamp of last update |
| `source` | string | Origin of the context (e.g., `user`, `agent`, `import`) |

### 4.2 Storage

Memory entries are persisted in the repository under a dedicated `memory/` directory:

```
memory/
├── index.json          # Master index of all entries (key → metadata)
├── decisions/          # Architecture and product decisions
│   ├── use-python.md
│   └── storage-format.md
├── conventions/        # Coding and workflow conventions
│   └── commit-style.md
├── projects/           # Per-project context
│   ├── signaltrust-ai.md
│   └── tradingtrust.md
└── roadmaps/           # Roadmap snapshots and evolution
    └── v1-plan.md
```

- **Markdown files** store the human-readable content of each entry.
- **`index.json`** provides a fast-lookup index mapping keys to metadata (tags, timestamps, file paths) without requiring a full filesystem scan.

### 4.3 Indexing

The index supports three access patterns:

1. **Key lookup** — Fast direct retrieval by unique key via JSON index.
2. **Tag-based filtering** — List all entries matching one or more tags.
3. **Full-text search** — Substring and keyword search across all stored content. Future versions will support semantic search via embeddings and a vector store.

### 4.4 Core Functions

| Function | Description |
|---|---|
| `save_context(key, value, meta)` | Persist a new context entry or update an existing one |
| `load_context(key)` | Retrieve a context entry by key |
| `search_context(query)` | Search entries by keyword or tag |
| `list_contexts()` | Return all available context keys with metadata |

---

## 5. Tasks Module

**Package:** `assistant/tasks/`

The tasks module manages to-do lists, sprints, milestones, and priorities. It operates on Markdown-based plan files stored in the `plans/` directory.

### 5.1 Planning

The module understands multiple plan file formats:

- **To-do lists** (`plans/todo-v1.md`) — Flat or grouped task lists with checkbox syntax (`- [ ]` / `- [x]`).
- **Sprint plans** (`plans/sprints.md`) — Time-boxed groups of tasks with goals and status tracking.
- **Idea backlogs** (`plans/ideas.md`) — Unstructured idea capture for future prioritization.

### 5.2 Parsing

The Markdown parser extracts structured task objects from plan files:

| Field | Type | Description |
|---|---|---|
| `id` | string | Auto-generated or section-based task identifier |
| `title` | string | Task description text |
| `status` | enum | `pending`, `in_progress`, `completed` |
| `priority` | enum | `critical`, `high`, `normal`, `low` |
| `section` | string | Parent section or sprint name |
| `file` | string | Source file path |

The parser handles nested lists, priority markers (emoji or text-based), and grouped sections.

### 5.3 Priorities

Task prioritization follows a simple, explicit model:

1. **Priority markers** — Tasks in higher-priority sections (e.g., `Priority 1`) rank above those in lower sections.
2. **Status-based ordering** — `pending` tasks are surfaced before `in_progress` tasks.
3. **FIFO within a priority** — Among tasks at the same priority level, the first listed task is next.

The `get_next_task()` function returns the single highest-priority pending task, enabling a focused, one-task-at-a-time workflow.

### 5.4 Core Functions

| Function | Description |
|---|---|
| `list_tasks(file)` | Parse a Markdown file and return all tasks |
| `add_task(file, task, priority)` | Append a new task to the appropriate section |
| `complete_task(file, task_id)` | Mark a task as completed (`- [x]`) |
| `get_next_task(file)` | Return the highest-priority pending task |

---

## 6. Scripts Module

**Package:** `assistant/scripts/`

The scripts module generates ready-to-run scripts and automation workflows. All output is immediately executable with no manual editing required.

### 6.1 PowerShell

Generates Windows-native scripts for system administration and automation tasks:

- Backup and sync operations
- Environment setup and configuration
- Service management
- File and directory operations

Generated scripts follow PowerShell best practices: `param()` blocks, `Set-StrictMode`, proper error handling with `try/catch`, and inline documentation via comment-based help.

### 6.2 Python

Generates Python scripts for data processing, API interaction, and automation:

- Data transformation and analysis pipelines
- API client scripts
- File processing utilities
- Testing and validation scripts

Generated scripts include `if __name__ == "__main__":` guards, type hints, docstrings, and proper argument parsing via `argparse`.

### 6.3 Git

Generates Git command sequences for common workflows:

- Repository initialization and configuration
- Branching strategies (feature branches, release branches)
- Commit, push, and merge sequences
- Tag management and release workflows

Output is provided as executable shell commands with explanatory comments.

### 6.4 GitHub Actions

Generates YAML workflow definitions for CI/CD pipelines:

- Build and test workflows
- Deployment pipelines
- Scheduled jobs (e.g., nightly builds, data sync)
- Multi-environment matrices

Generated workflows follow GitHub Actions best practices and include proper trigger configuration, job dependencies, and secret management.

### 6.5 Template System

Scripts are generated from composable templates stored in a `templates/` directory. Each template defines:

- **Structure** — The skeleton of the script (imports, main block, error handling).
- **Variables** — Placeholders filled in by the generator based on user input.
- **Documentation** — Inline comments and usage instructions.

### 6.6 Core Functions

| Function | Description |
|---|---|
| `generate_powershell(description)` | Generate a PowerShell script from a task description |
| `generate_python(description)` | Generate a Python script from a task description |
| `generate_git_commands(workflow)` | Generate a Git command sequence for a workflow |
| `generate_github_actions(workflow_name)` | Generate a GitHub Actions YAML workflow |

---

## 7. Projects Module

**Package:** `assistant/projects/`

The projects module maintains awareness of all repositories and initiatives in the SignalTrust ecosystem.

### 7.1 Ecosystem Management

The module tracks:

| Project | Description |
|---|---|
| **SignalTrust AI** | Core AI/ML platform for signal detection and trust scoring |
| **TradingTrust** | Algorithmic trading strategies powered by SignalTrust signals |
| **TrustToken** | Tokenized trust and reputation systems on blockchain |
| **TrustWallet** | Secure wallet infrastructure for digital assets |
| **SignalTrust Assistant** | This project — the orchestration and automation layer |

Each project is registered in `config/projects.yaml` with metadata:

```yaml
projects:
  - name: SignalTrust AI
    repo: signaltrustai/SignalTrust-AI
    description: Core AI/ML platform
    status: active
    language: Python
  - name: TradingTrust
    repo: signaltrustai/TradingTrust
    description: Algorithmic trading strategies
    status: active
    language: Python
```

### 7.2 Cross-Project Awareness

The module provides:

- **Dependency mapping** — Which projects depend on which others.
- **Status aggregation** — Consolidated view of build status, open issues, and deployment state across all projects.
- **Impact analysis** — When a change is planned in one project, identify which other projects may be affected.

### 7.3 Core Functions

| Function | Description |
|---|---|
| `list_projects()` | List all registered projects with metadata |
| `get_project_status(name)` | Return detailed status for a specific project |
| `add_project(name, repo_url, description)` | Register a new project in the ecosystem |

---

## 8. Ecosystem Module

**Package:** `assistant/ecosystem/`

The ecosystem module connects the assistant to external services, starting with the GitHub API.

### 8.1 GitHub API Integration

The module wraps the GitHub REST API to provide:

| Capability | Endpoint | Description |
|---|---|---|
| Repository info | `GET /repos/{owner}/{repo}` | Metadata, stars, forks, language |
| Open issues | `GET /repos/{owner}/{repo}/issues` | Issue list with labels and assignees |
| Recent commits | `GET /repos/{owner}/{repo}/commits` | Commit history with messages and authors |
| Pull requests | `GET /repos/{owner}/{repo}/pulls` | PR status, reviews, merge state |
| Workflow runs | `GET /repos/{owner}/{repo}/actions/runs` | CI/CD pipeline status |

Authentication is handled via a GitHub personal access token stored in the `GITHUB_TOKEN` environment variable. Planned capabilities include proper error handling, rate-limit awareness, and response caching.

### 8.2 Future Integrations

The module is designed to be extended with additional integrations:

- **CI/CD pipelines** — Monitor and trigger builds across providers.
- **Cloud providers** — Query deployment status on AWS, GCP, or Azure.
- **Blockchain networks** — Monitor on-chain activity for TrustToken and TrustWallet.
- **Notification services** — Send alerts via Telegram, Discord, or email.

### 8.3 Core Functions

| Function | Description |
|---|---|
| `get_repo_info(repo)` | Retrieve repository metadata from GitHub |
| `list_open_issues(repo)` | List open issues for a repository |
| `list_recent_commits(repo, n)` | Return the last `n` commits for a repository |

---

## 9. CLI Interface

**Package:** `assistant/cli/`

The CLI is the primary user interface for v1 of SignalTrust Assistant. It provides a structured command-line experience for interacting with all modules.

### 9.1 Command Structure

```
python -m assistant.cli <module> <command> [options]
```

| Module | Commands |
|---|---|
| `memory` | `save`, `load`, `search`, `list` |
| `tasks` | `list`, `add`, `complete`, `next` |
| `scripts` | `generate` (with `--type` flag for PowerShell/Python/Git/Actions) |
| `projects` | `list`, `status`, `add` |
| `ecosystem` | `repos`, `issues`, `commits` |

### 9.2 Design Principles

- **Explicit subcommands** — Every action is a clear verb (`save`, `list`, `generate`).
- **Consistent flags** — Common options (`--file`, `--format`, `--verbose`) behave identically across modules.
- **Machine-readable output** — Optional `--json` flag for programmatic consumption.
- **Help at every level** — `--help` is available on the root command, each module, and each subcommand.

### 9.3 Entry Point

The CLI entry point is `assistant/cli/__init__.py` (or a dedicated `__main__.py`), invoked via:

```bash
python -m assistant.cli --help
python -m assistant.cli memory list
python -m assistant.cli tasks next --file plans/todo-v1.md
python -m assistant.cli scripts generate --type python --description "backup script"
```

---

## 10. Storage & Configuration Layer

### 10.1 Storage Strategy

All persistent data is stored as files within the Git repository. This provides:

- **Version control** — Full history of every change, with diffs and rollback capability.
- **Transparency** — All state is human-readable and inspectable.
- **Portability** — Clone the repo and the entire assistant state comes with it.
- **Collaboration** — Standard Git workflows (branches, PRs, reviews) apply to assistant data.

### 10.2 File Organization

```
SignalTrust-Assistant/
├── assistant/          # Source code (modules, CLI, utilities)
│   ├── __init__.py
│   ├── memory/         # Memory module package
│   ├── tasks/          # Tasks module package
│   ├── scripts/        # Scripts module package
│   ├── projects/       # Projects module package
│   ├── ecosystem/      # Ecosystem module package
│   └── cli/            # CLI interface package
├── config/             # Configuration files (YAML/JSON)
│   └── projects.yaml   # Project registry
├── docs/               # Documentation
│   ├── architecture.md # This document
│   ├── vision.md       # Vision and principles
│   └── roadmap.md      # Phased roadmap
├── memory/             # Persisted memory entries
│   ├── index.json      # Memory index
│   └── ...             # Context files (Markdown)
├── plans/              # Planning documents
│   ├── todo-v1.md      # v1 to-do list
│   ├── sprints.md      # Sprint plans
│   └── ideas.md        # Idea backlog
├── templates/          # Script and output templates
└── tests/              # Test suite
```

### 10.3 Configuration

Configuration is managed through YAML and JSON files in the `config/` directory:

- **`config/projects.yaml`** — Project registry with metadata.
- **`config/settings.yaml`** (future) — User preferences, default behaviors, API keys reference.

All configuration is version-controlled. Sensitive values (API tokens) are stored in environment variables, never in config files. For production and autonomous operation, a dedicated secret management solution (e.g., encrypted environment files, vault services) is recommended.

---

## 11. Evolution Toward Multi-Agent and Autonomous Behavior

The architecture is designed to evolve from a structured CLI tool into a fully autonomous multi-agent system. This evolution follows a deliberate, phased approach.

### 11.1 Phase 1 — Structured CLI (Current)

- Single-user, single-thread operation.
- Explicit commands drive all behavior.
- Modules operate independently with manual orchestration.
- Memory is file-based with simple key-value access.

### 11.2 Phase 2 — Intelligent Routing

- Integration of a language model (LLM) for natural language intent parsing.
- The orchestrator becomes an **agent router** that automatically dispatches requests to the correct module based on semantic understanding.
- Memory gains tag-based and keyword-based search for richer context retrieval.

### 11.3 Phase 3 — Specialized Agents

Each module evolves into a **specialized agent** with domain expertise:

| Agent | Capability |
|---|---|
| **Memory Agent** | Proactively surfaces relevant context during conversations |
| **Task Agent** | Suggests next actions, detects blockers, auto-prioritizes |
| **Script Agent** | Generates and validates scripts, proposes optimizations |
| **Project Agent** | Monitors project health, alerts on issues, tracks progress |
| **Ecosystem Agent** | Watches repositories, pipelines, and deployments in real time |
| **Code Review Agent** | Reviews pull requests and suggests improvements |
| **Documentation Agent** | Keeps docs in sync with code changes automatically |

### 11.4 Phase 4 — Multi-Agent Collaboration

- Agents communicate with each other through an internal message bus.
- Complex tasks are decomposed into sub-tasks and distributed across agents.
- A **supervisor agent** monitors agent activity, resolves conflicts, and ensures coherence.
- Background agents run on schedules (e.g., nightly repo scans, daily standup summaries).

### 11.5 Phase 5 — Autonomous Operation

- The assistant proposes and executes multi-step workflows with minimal human oversight.
- Self-improving memory: the assistant learns from interaction patterns and refines its behavior.
- Plugin system allows community-contributed agents to extend capabilities.
- The system can autonomously build, test, deploy, and monitor across the entire ecosystem.

### 11.6 Design for Autonomy

Key architectural decisions that enable this evolution:

1. **Module isolation** — Each module can be upgraded to an agent independently.
2. **Storage-as-source-of-truth** — All state is in the repository, so agents can operate asynchronously without shared in-memory state.
3. **Composable orchestration** — The dispatcher pattern naturally extends to multi-agent routing.
4. **Transparent operation** — Every action is logged and version-controlled, enabling human review at any point.

---

## 12. Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| CLI | `argparse` (v1), `click` (planned) |
| Storage | Markdown, JSON, YAML, Git |
| Scripting targets | PowerShell, Python, Bash, GitHub Actions |
| API integration | GitHub REST API, `requests` / `httpx` |
| Testing | `pytest` |
| Future: LLM | Groq API (llama3-70b-8192), local models (llama.cpp) |
| Future: Search | Vector embeddings, FAISS or ChromaDB |

---

*This architecture is designed to be simple enough to start today and flexible enough to scale into a fully autonomous multi-agent system tomorrow.*
