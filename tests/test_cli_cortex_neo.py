import subprocess
import sys
import os
from pathlib import Path

def test_list_workflows():
    # Bevorzugt das venv-Python, fällt auf aktuelles Python zurück
    repo_root = Path(__file__).resolve().parent.parent
    venv_python = repo_root / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    env = os.environ.copy()
    env.setdefault("NEO4J_URI", "bolt://localhost:7687")
    env.setdefault("NEO4J_USER", "neo4j")
    env.setdefault("NEO4J_PASSWORD", "neo4jtest")

    # Create a workflow before listing
    subprocess.run([
        python_exec, "cortex_neo/cortex_cli.py", "create-workflow", "TestWorkflow"],
        capture_output=True, text=True, env=env, cwd=repo_root
    )
    result = subprocess.run([
        python_exec, "cortex_neo/cortex_cli.py", "list-workflows"
    ], capture_output=True, text=True, env=env, cwd=repo_root)
    assert result.returncode == 0, f"Fehler beim Ausführen: {result.stderr}"
    assert "Workflow" in result.stdout or result.stdout.strip() != "", "Keine Workflows gefunden oder Ausgabe leer."
    print("[OK] list-workflows gibt Workflows aus:")
    print(result.stdout)

if __name__ == "__main__":
    test_list_workflows()
