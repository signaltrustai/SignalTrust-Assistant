# SignalTrust Assistant — Architecture

## Overview

SignalTrust Assistant follows a modular, layered architecture. Each layer has a clear responsibility and communicates through well-defined interfaces.

```
┌─────────────────────────────────────────────┐
│              User Interface                 │
│     (CLI / Chat / IDE Integration)          │
├─────────────────────────────────────────────┤
│            Orchestration Layer              │
│    (Agent Router / Task Dispatcher)         │
├──────────┬──────────┬──────────┬────────────┤
│  Memory  │  Tasks   │ Scripts  │ Ecosystem  │
│  Module  │  Module  │ Module   │  Module    │
├──────────┴──────────┴──────────┴────────────┤
│           Core Utilities                    │
│   (Config, Logging, File I/O, Templates)    │
├─────────────────────────────────────────────┤
│         Storage & Persistence               │
│   (Markdown docs, JSON/YAML configs, Git)   │
└─────────────────────────────────────────────┘
```

## Modules

### Memory (`assistant/memory.py`)
- Stores and retrieves long-term context: decisions, preferences, project state.
- Backed by structured Markdown and config files in the repository.
- Supports tagging, search, and time-based recall.

### Task Orchestration (`assistant/tasks.py`)
- Manages to-do items, sprints, milestones, and priorities.
- Reads from and writes to `plans/` directory.
- Tracks task status, dependencies, and deadlines.

### Project Management (`assistant/projects.py`)
- Maintains awareness of all SignalTrust ecosystem projects.
- Tracks repository status, open issues, deployment state.
- Provides cross-project dependency mapping.

### Script Generation (`assistant/scripts.py`)
- Generates executable scripts for PowerShell, Python, Bash, and Git.
- Templates for common workflows: repo setup, CI/CD, deployment, data pipelines.
- Output is always ready-to-run with no manual editing required.

### Ecosystem Integration (`assistant/ecosystem.py`)
- Connects to GitHub API, CI/CD pipelines, cloud providers.
- Monitors repository activity, build status, deployment health.
- Future: blockchain network integration for TrustToken and TrustWallet.

## Data Flow

1. User sends a request (natural language or structured command).
2. Orchestration layer routes the request to the appropriate module(s).
3. Module(s) execute the task, reading/writing to storage as needed.
4. Results are returned to the user as actionable output.

## Configuration

- All configuration lives in the repository as version-controlled files.
- No external databases required for v1.
- Git history serves as an audit trail for all changes.

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| CLI | argparse / click (future) |
| Storage | Markdown, JSON, YAML, Git |
| Scripting | PowerShell, Python, Bash |
| Integration | GitHub API, REST APIs |
| Testing | pytest |

---

*Architecture is designed to be simple enough to start today and flexible enough to scale tomorrow.*
