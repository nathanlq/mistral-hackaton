import asyncio
from pathlib import Path
import subprocess
import tempfile
import json
import httpx
import re
import time

SONAR_HOST = "https://ollama.lambdah.ovh"
SONAR_TOKEN = "squ_44a64e04ea7ed4a54789b71def306412f7fcf840"

async def analyze_python_file(file):
    print(f"[DEBUG] Starting analysis for file: {file.filename}")

    if not file.filename.endswith('.py'):
        raise ValueError("[ERROR] Not a Python file!")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Sauvegarder le fichier
        file_path = temp_path / file.filename
        content = await file.read()
        file_path.write_bytes(content)

        # Créer sonar-project.properties
        project_key = file.filename.replace('.py', '')
        props = f"""sonar.projectKey={project_key}
sonar.projectName={file.filename}
sonar.projectVersion=1.0
sonar.sources=.
sonar.python.file.suffixes=.py
sonar.inclusions={file.filename}
"""
        (temp_path / "sonar-project.properties").write_text(props)

        # Lancer l’analyse
        cmd = [
            "sonar-scanner",
            f"-Dsonar.host.url={SONAR_HOST}",
            f"-Dsonar.token={SONAR_TOKEN}"
        ]
        result = subprocess.run(cmd, cwd=temp_path, capture_output=True, text=True)

        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError("[ERROR] sonar-scanner failed")

        # Extraire le taskId depuis la sortie
        match = re.search(r"ce/task\?id=([\w-]+)", result.stdout)
        if not match:
            raise RuntimeError("[ERROR] Impossible de récupérer le taskId depuis les logs sonar-scanner")
        task_id = match.group(1)
        print(f"[DEBUG] Found taskId: {task_id}")

        # Attendre que la tâche soit terminée
        status = await wait_for_task(task_id)
        if status != "SUCCESS":
            raise RuntimeError(f"[ERROR] Task failed with status {status}")

        # Récupérer les résultats via l’API SonarQube
        issues = await get_sonar_issues(project_key)
        return {"filename": file.filename, "issues": issues}


async def wait_for_task(task_id: str, timeout: int = 60, interval: int = 2):
    """Attend que la tâche SonarQube soit terminée"""
    url = f"{SONAR_HOST}/api/ce/task"
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(url, params={"id": task_id}, auth=(SONAR_TOKEN, ""))
            if response.status_code != 200:
                print(f"[WARN] Failed to check task status, code={response.status_code}")
                return "FAILED"

            data = response.json()
            status = data["task"]["status"]
            print(f"[DEBUG] Task {task_id} status: {status}")

            if status in ("SUCCESS", "FAILED", "CANCELED"):
                return status

            if time.time() - start_time > timeout:
                return "TIMEOUT"

            await asyncio.sleep(interval)


async def get_sonar_issues(project_key: str):
    url = f"{SONAR_HOST}/api/issues/search"
    params = {
        "componentKeys": project_key
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, auth=(SONAR_TOKEN, ""))

        if response.status_code != 200:
            print(f"[WARN] Failed to fetch issues, code={response.status_code}")
            return []

        data = response.json()
        return [
            {
                "rule": issue["rule"],
                "severity": issue["severity"],
                "message": issue["message"],
                "line": issue.get("line", 0)
            }
            for issue in data.get("issues", [])
        ]


# --- MAIN ---
class DummyFile:
    def __init__(self, filename: str, content: str):
        self.filename = filename
        self._content = content.encode("utf-8")

    async def read(self):
        return self._content


async def main():
    dummy_code = """
def inefficient_function():
    result = []
    for i in range(1000000):
        result.append(i * 2)
    return result
"""
    dummy_file = DummyFile("test_script.py", dummy_code)
    try:
        analysis_result = await analyze_python_file(dummy_file)
        print("[DEBUG] Final analysis result:")
        print(json.dumps(analysis_result, indent=2))
    except Exception as e:
        print(f"[ERROR] Exception during analysis: {e}")



async def submit_code(code_str: str, filename: str = "submitted_script.py"):
    """Soumettre du code Python donné en chaîne de caractères à SonarQube"""
    f = DummyFile(filename, code_str)
    result = await analyze_python_file(f)
    print("Analysis result:")
    print(json.dumps(result, indent=2))
    return result


