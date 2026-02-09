# SignalTrust Assistant — v1 To-Do List

## Priority 1: Project Foundation
- [x] Create repository structure (`docs/`, `plans/`, `assistant/`).
- [x] Write `docs/vision.md` — define what SignalTrust Assistant is and why it exists.
- [x] Write `docs/architecture.md` — define the modular architecture and data flow.
- [x] Write `docs/roadmap.md` — define phased development plan.
- [x] Write `plans/todo-v1.md` — this file.
- [x] Create placeholder modules in `assistant/`.

## Priority 2: Memory Module
- [ ] Design memory schema (what gets stored, in what format).
- [ ] Implement `assistant/memory.py`:
  - [ ] `save_context(key, value)` — persist a piece of context to a file.
  - [ ] `load_context(key)` — retrieve stored context.
  - [ ] `search_context(query)` — find relevant context across all stored data.
  - [ ] `list_contexts()` — list all stored context keys.
- [ ] Store memory as structured Markdown or JSON files in a `memory/` directory.
- [ ] Write unit tests for memory module.

## Priority 3: Task Orchestration Module
- [ ] Implement `assistant/tasks.py`:
  - [ ] `list_tasks(file)` — parse a Markdown to-do file and return structured tasks.
  - [ ] `add_task(file, task, priority)` — add a new task to a plan file.
  - [ ] `complete_task(file, task_id)` — mark a task as done.
  - [ ] `get_next_task(file)` — return the highest-priority incomplete task.
- [ ] Support multiple plan files (`todo-v1.md`, `sprints.md`, etc.).
- [ ] Write unit tests for tasks module.

## Priority 4: Script Generation Module
- [ ] Implement `assistant/scripts.py`:
  - [ ] `generate_powershell(command_description)` — produce a PowerShell script.
  - [ ] `generate_python(task_description)` — produce a Python script.
  - [ ] `generate_git_commands(workflow)` — produce Git command sequences.
  - [ ] `generate_github_actions(workflow_name)` — produce a GitHub Actions YAML.
- [ ] Create a `templates/` directory for script templates.
- [ ] Write unit tests for script generation.

## Priority 5: Project Management Module
- [ ] Implement `assistant/projects.py`:
  - [ ] `list_projects()` — return all known SignalTrust ecosystem projects.
  - [ ] `get_project_status(project_name)` — return current status and key metrics.
  - [ ] `add_project(name, repo_url, description)` — register a new project.
- [ ] Create a `config/projects.yaml` to store project definitions.
- [ ] Write unit tests for project management.

## Priority 6: Ecosystem Integration Module
- [ ] Implement `assistant/ecosystem.py`:
  - [ ] `get_repo_info(repo)` — fetch GitHub repository metadata.
  - [ ] `list_open_issues(repo)` — list open issues for a project.
  - [ ] `list_recent_commits(repo, n)` — list the last N commits.
- [ ] Implement GitHub API client with token-based authentication.
- [ ] Write unit tests with mocked API responses.

## Priority 7: CLI Interface
- [ ] Create `assistant/cli.py` as the main entry point.
- [ ] Support commands: `memory`, `tasks`, `scripts`, `projects`, `ecosystem`.
- [ ] Add `--help` documentation for all commands.
- [ ] Create a `run.py` or `__main__.py` for easy execution.

## Priority 8: Documentation & Polish
- [ ] Write a comprehensive `README.md` with setup and usage instructions.
- [ ] Fill `plans/sprints.md` with the first sprint plan.
- [ ] Fill `plans/ideas.md` with a backlog of future ideas.
- [ ] Add inline code documentation (docstrings) to all modules.
- [ ] Set up `pytest` and ensure all tests pass.

## Priority 9: Future Enhancements (Backlog)
- [ ] LLM integration for natural language task processing.
- [ ] Agent routing and multi-agent collaboration.
- [ ] Background monitoring and notifications.
- [ ] Plugin system for extensibility.
- [ ] Web dashboard for visual project overview.

---

*Work top-down by priority. Each priority level should be fully complete before moving to the next.*
