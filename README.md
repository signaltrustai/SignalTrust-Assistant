# 🧠 OmniJARVIS — L'Assistante Personnelle AI Ultime

> **"OmniJARVIS operational. Ready to orchestrate your personal OS."**

OmniJARVIS est une assistante personnelle AI de nouvelle génération, conçue pour agir comme un véritable **cerveau numérique personnel**. Elle comprend, planifie, exécute et optimise toutes les tâches autorisées par l'utilisateur, en orchestrant l'ensemble de son écosystème numérique.

---

## 🚀 Vision

Offrir une expérience fluide, intelligente et proactive — le **top du top mondial** — en respectant trois principes fondamentaux :

1. **L'utilisateur garde toujours le contrôle**
2. **Chaque action nécessite une permission explicite**
3. **Sécurité et transparence sont prioritaires**

---

## 🎯 Mission

| Capacité | Description |
|---|---|
| 🗣️ Langage naturel | Comprend des instructions en français et anglais, même complexes ou vagues |
| 🤖 Multi-agents | 12 agents spécialisés coordonnés par un orchestrateur intelligent |
| ⚡ Automatisation | Workflows multi-étapes, routines personnalisées, actions contextuelles |
| 🧠 Apprentissage | Apprend les préférences de l'utilisateur et évolue chaque jour |
| 🔐 Sécurité | Permissions explicites, audit trail, transparence totale |
| 💻 Code | Génère, modifie, review et exécute du code sur demande |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Interface Utilisateur                 │
│              (CLI / Web API / Chat naturel)              │
├─────────────────────────────────────────────────────────┤
│                  🧠 Orchestrateur OmniJARVIS             │
│          (Routing intelligent FR/EN + Permissions)       │
├──────┬──────┬──────┬──────┬──────┬──────┬──────┬───────┤
│ Exec │ Mem  │ Anal │ Sys  │ Doc  │ Code │ Comm │ Cloud │
│ utif │ oire │ yse  │ tème │ umen │      │ unic │       │
├──────┴──────┴──────┴──────┴──────┴──────┴──────┴───────┤
│  Vision │ Mobilité │ Productivité │ Sécurité │ Focus   │
├─────────────────────────────────────────────────────────┤
│              Moteur d'Apprentissage Adaptatif            │
├─────────────────────────────────────────────────────────┤
│         Stockage (Markdown, JSON, YAML, Git)            │
└─────────────────────────────────────────────────────────┘
```

---

## 🧩 Les 12 Agents Spécialisés

| # | Agent | Rôle |
|---|---|---|
| 1 | **Executive** | Interprète les requêtes, décompose en tâches, assigne aux agents |
| 2 | **Memory** | Mémoire longue durée : préférences, décisions, contexte |
| 3 | **Analysis** | Analyse de fichiers, code, documents, données |
| 4 | **System** | Contrôle système : processus, disque, apps, commandes |
| 5 | **Documentation** | Rédaction de docs, changelogs, rapports, résumés |
| 6 | **Code** | Génération, modification, review et exécution de code |
| 7 | **Communication** | Messages, emails, réunions, contacts |
| 8 | **Cloud** | Services cloud, synchronisation, sauvegardes |
| 9 | **Vision** | Analyse d'images, reconnaissance de texte et scènes |
| 10 | **Mobility** | Coordination multi-appareils (téléphone, montre, lunettes, IoT) |
| 11 | **Productivity** | Routines, workflows, automatisation, résumé quotidien |
| 12 | **Security** | Audit, monitoring, scan de configuration, alertes |

---

## 🚀 Démarrage Rapide

### Installation

```bash
git clone https://github.com/signaltrustai/SignalTrust-Assistant.git
cd SignalTrust-Assistant
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
export GROQ_API_KEY="your-key-here"  # Optionnel, pour les fonctionnalités IA
```

### Utilisation CLI

```bash
# Initialisation
python -m assistant.cli jarvis
# → 🧠 OmniJARVIS operational. Ready to orchestrate your personal OS.

# Requête en langage naturel (routage automatique FR/EN)
python -m assistant.cli jarvis "Analyse ce fichier pour moi"
python -m assistant.cli jarvis "Souviens-toi que le déploiement est vendredi"
python -m assistant.cli jarvis "Génère du code Python pour une API REST"

# Appel direct d'un agent
python -m assistant.cli jarvis --agent system --action system_info "info"
python -m assistant.cli jarvis --agent code --action generate_code "script"

# Gestion des permissions
python -m assistant.cli permissions grant system.execute --scope session
python -m assistant.cli permissions grant file.modify --scope always
python -m assistant.cli permissions list
python -m assistant.cli permissions audit

# Gestion des agents
python -m assistant.cli agent list
python -m assistant.cli agent status
python -m assistant.cli agent stats
python -m assistant.cli agent profile
```

### API Web

```bash
python run_web.py
# GET  /              → Statut et message d'initialisation
# POST /chat          → Requête en langage naturel
# GET  /agents        → Liste des agents
# GET  /status        → Résumé de session
# GET  /stats         → Statistiques d'utilisation
# GET  /permissions   → Permissions actives
# POST /permissions/grant   → Accorder une permission
# POST /permissions/revoke  → Révoquer une permission
# GET  /audit         → Journal d'audit de sécurité
```

---

## 🔐 Système de Permissions

OmniJARVIS ne fait **rien** sans votre autorisation explicite.

### Types d'actions protégées

| Action | Description |
|---|---|
| `system.execute` | Exécuter des commandes système |
| `file.read` / `file.modify` / `file.delete` | Opérations fichiers |
| `memory.write` / `memory.delete` | Opérations mémoire |
| `communication.send` / `communication.read` | Communication |
| `cloud.sync` / `cloud.upload` / `cloud.download` | Cloud |
| `network.request` / `network.listen` | Réseau |
| `agent.spawn` / `agent.delegate` | Agents |

### Portées : `once` (une fois) · `session` (session) · `always` (persistant)

---

## 🧠 Apprentissage Adaptatif

- **Profil utilisateur** avec préférences persistantes
- **Historique des interactions** pour recommandation d'agents
- **Suggestions intelligentes** basées sur les patterns d'usage

---

## 💻 Agent Code

Génère, modifie, review et exécute du code dans 11 langages (Python, JS, TS, Bash, PowerShell, HTML, CSS, SQL, Rust, Go, Java). Exécution sandboxée, timeout 30s, aucun `eval()`/`exec()`.

---

## 📌 Philosophie

- ✅ Penser étape par étape, sorties concises et structurées
- ✅ Clarifier l'intention quand c'est ambigu
- ✅ Proposer des améliorations et prochaines étapes
- ✅ Documenter les décisions importantes
- ✅ Moins de chaos, plus de clarité

---

*OmniJARVIS — Votre OS personnel IA, le meilleur du meilleur, prêt à l'emploi.* 🚀
