from assistant import tasks, memory
from assistant.ai.agent import analyze
from datetime import datetime
from pathlib import Path

class FocusAgent:
    def run(self):
        # 1. Trouver la prochaine tâche
        task = tasks.get_next_task("todo-v1.md")
        if not task:
            return {"status": "no_tasks"}

        title = task["title"]

        # 2. Analyse IA
        analysis = analyze(f"Analyse cette tâche et propose un plan d'action : {title}")

        # 3. Générer un plan simple
        plan = f"Plan généré pour la tâche '{title}':\n{analysis}"

        # 4. Sauvegarder un log
        log_dir = Path("memory/agent-logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_key = f"focus_agent_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        memory.save_context(log_key, plan, {"tags": ["agent", "focus"]})

        return {
            "status": "done",
            "task": title,
            "analysis": analysis,
            "memory_key": log_key
        }
