# SignalTrust Assistant — v1 To-Do List

> Objectif v1 : un assistant **local, modulaire, script‑oriented**, qui gère mémoire, plans, scripts et projets SignalTrust.  
> On vise un noyau solide, simple à étendre.

---

## 🔴 Priority 1 — Foundation & Structure

- [x] Créer la structure du repo (`docs/`, `plans/`, `assistant/`).
- [x] Écrire `docs/vision.md` — vision, rôle, principes.
- [ ] Écrire `docs/architecture.md` — modules, flux de données, responsabilités.
- [ ] Écrire `docs/roadmap.md` — v1, v2, v3, milestones.
- [x] Créer `plans/todo-v1.md` — ce fichier.
- [ ] Créer `plans/sprints.md` — structure de base.
- [ ] Créer `plans/ideas.md` — backlog d’idées.
- [ ] Créer les dossiers de base dans `assistant/` :
  - `assistant/memory/`
  - `assistant/tasks/`
  - `assistant/scripts/`
  - `assistant/projects/`
  - `assistant/ecosystem/`
  - `assistant/cli/`

---

## 🧠 Priority 2 — Memory Module (cœur “second cerveau”)

- [ ] Définir le schéma de mémoire :
  - [ ] Types de contexte (projets, décisions, conventions, roadmaps, idées).
  - [ ] Format (Markdown + JSON index).
  - [ ] Organisation des fichiers (`memory/`).
- [ ] Implémenter `assistant/memory.py` :
  - [ ] `save_context(key, value, meta)` — sauvegarder un contexte.
  - [ ] `load_context(key)` — récupérer un contexte.
  - [ ] `search_context(query)` — rechercher dans tous les contextes.
  - [ ] `list_contexts()` — lister les clés disponibles.
- [ ] Créer le dossier `memory/` avec quelques exemples.
- [ ] Écrire des tests unitaires pour le module mémoire.

---

## ✅ Priority 3 — Task & Planning Module

- [ ] Implémenter `assistant/tasks.py` :
  - [ ] `list_tasks(file)` — parser un fichier Markdown de tâches.
  - [ ] `add_task(file, task, priority)` — ajouter une tâche.
  - [ ] `complete_task(file, task_id)` — marquer comme complétée.
  - [ ] `get_next_task(file)` — renvoyer la tâche prioritaire suivante.
- [ ] Supporter plusieurs fichiers de plan (`todo-v1.md`, `sprints.md`, `ideas.md`).
- [ ] Ajouter quelques tâches d’exemple dans `sprints.md`.
- [ ] Écrire des tests unitaires pour le module tâches.

---

## 🛠 Priority 4 — Script Generation Module (PC & Dev Ops)

- [ ] Implémenter `assistant/scripts.py` :
  - [ ] `generate_powershell(description)` — script PowerShell pour Windows.
  - [ ] `generate_python(description)` — script Python pour automatisation.
  - [ ] `generate_git_commands(workflow)` — séquences Git (init, commit, push, branch, etc.).
  - [ ] `generate_github_actions(workflow_name)` — YAML de base pour CI/CD.
- [ ] Créer un dossier `templates/` pour stocker des modèles de scripts.
- [ ] Ajouter quelques templates de base (backup repo, sync, tests, etc.).
- [ ] Écrire des tests unitaires pour ce module.

---

## 📂 Priority 5 — Project Management Module (éco SignalTrust)

- [ ] Implémenter `assistant/projects.py` :
  - [ ] `list_projects()` — lister tous les projets SignalTrust.
  - [ ] `get_project_status(name)` — statut + notes + liens.
  - [ ] `add_project(name, repo_url, description)` — enregistrer un projet.
- [ ] Créer `config/projects.yaml` avec :
  - [ ] SignalTrust AI
  - [ ] TradingTrust (Lite / Pro)
  - [ ] TrustToken
  - [ ] TrustWallet
  - [ ] SignalTrust Assistant
- [ ] Écrire des tests unitaires pour ce module.

---

## 🌐 Priority 6 — Ecosystem Integration (GitHub d’abord)

- [ ] Implémenter `assistant/ecosystem.py` :
  - [ ] `get_repo_info(repo)` — métadonnées GitHub.
  - [ ] `list_open_issues(repo)` — issues ouvertes.
  - [ ] `list_recent_commits(repo, n)` — derniers commits.
- [ ] Ajouter support token GitHub via variable d’environnement.
- [ ] Mock des appels API pour les tests.
- [ ] Écrire des tests unitaires.

---

## 🧾 Priority 7 — CLI Interface (ton vrai “terminal IA”)

- [ ] Créer `assistant/cli.py` comme point d’entrée.
- [ ] Ajouter commandes :
  - [ ] `memory` (save, load, search, list)
  - [ ] `tasks` (list, add, complete, next)
  - [ ] `scripts` (generate)
  - [ ] `projects` (list, status, add)
  - [ ] `ecosystem` (repos, issues, commits)
- [ ] Créer `run.py` ou `__main__.py` pour exécution rapide :  
  `python -m assistant.cli ...`
- [ ] Ajouter `--help` détaillé.

---

## 📚 Priority 8 — Docs & Qualité

- [ ] Compléter `README.md` (setup, usage, exemples).
- [ ] Remplir `plans/sprints.md` avec Sprint 1 (v1 core).
- [ ] Remplir `plans/ideas.md` avec backlog (LLM, agents, dashboard, etc.).
- [ ] Ajouter des docstrings à tous les modules.
- [ ] Configurer `pytest` + `requirements.txt`.
- [ ] S’assurer que tous les tests passent.

---

## 🚀 Priority 9 — Backlog v2+ (à ne pas attaquer avant v1 stable)

- [ ] Intégration LLM pour commandes en langage naturel.
- [ ] Routage multi‑agents (orchestrateur intelligent).
- [ ] Monitoring en arrière‑plan (repos, marchés, jobs).
- [ ] Système de plugins (extensions custom).
- [ ] Dashboard web (vue globale de l’écosystème).
- [ ] Intégration directe avec SignalTrust AI & TradingTrust (API).

---

> **Règle d’or :** terminer une priorité avant d’ouvrir la suivante.  
> On construit un noyau simple, fiable, extensible — pas un monstre fragile.
