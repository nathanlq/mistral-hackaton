"""
Service SonarQube via SSH - évite l'installation locale
"""
import asyncio
import tempfile
import zipfile
from pathlib import Path
import json
import re
from uuid import uuid4
import asyncssh
import os
from dotenv import load_dotenv

load_dotenv()

SSH_CONFIG = {
    "host": os.getenv("SSH_HOST", "localhost"),
    "username": os.getenv("SSH_USERNAME"),
    "password": os.getenv("SSH_PASSWORD"),
    "port": int(os.getenv("SSH_PORT", "22")),
}

if os.getenv("SSH_KEY_PATH"):
    SSH_CONFIG["client_keys"] = [os.getenv("SSH_KEY_PATH")]
    SSH_CONFIG.pop("password", None)

SONAR_HOST = os.getenv("SONAR_HOST", "https://ollama.lambdah.ovh") 
SONAR_TOKEN = os.getenv("SONAR_TOKEN")


async def analyze_code_via_ssh(code: str, filename: str = "analysis.py") -> dict:
    """Analyse SonarQube en uploadant le code vers le serveur SSH"""
    
    with tempfile.TemporaryDirectory() as local_temp:
        local_path = Path(local_temp)
        project_dir = local_path / "project" 
        project_dir.mkdir()
        code_file = project_dir / filename
        code_file.write_text(code)
        
        project_key = f"remote_analysis_{uuid4().hex[:8]}"
        sonar_props = f"""sonar.projectKey={project_key}
sonar.projectName={filename}
sonar.projectVersion=1.0
sonar.sources=.
sonar.python.file.suffixes=.py
sonar.python.version=3.8,3.9,3.10,3.11
sonar.inclusions={filename}
sonar.scm.disabled=true
sonar.scanner.skipSystemTruststore=true
"""
        (project_dir / "sonar-project.properties").write_text(sonar_props)
        
        archive_path = local_path / "project.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            for file in project_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(project_dir))
    
        return await execute_remote_analysis(archive_path, project_key, filename)


async def execute_remote_analysis(archive_path: Path, project_key: str, filename: str) -> dict:
    """Exécute l'analyse sur le serveur distant"""
    try:
        async with asyncssh.connect(**SSH_CONFIG) as conn:
            remote_archive = f"/tmp/sonar_{uuid4().hex}.zip"
            remote_dir = f"/tmp/sonar_project_{uuid4().hex}"
            
            cleanup_result = await conn.run(f"rm -rf {remote_dir}")
            
            async with conn.start_sftp_client() as sftp:
                await sftp.put(str(archive_path), remote_archive)
            
            decompress_cmd = f"mkdir -p {remote_dir} && cd {remote_dir} && unzip -q {remote_archive}"
            result = await conn.run(decompress_cmd)
            if result.exit_status != 0:
                raise RuntimeError(f"Décompression échouée: {result.stderr}")
            
            sonar_cmd = f"""
                cd {remote_dir} && 
                sonar-scanner \
                    -Dsonar.host.url={SONAR_HOST} \
                    -Dsonar.token={SONAR_TOKEN} \
                    -Dsonar.log.level=DEBUG \
                    -X
            """
            result = await conn.run(sonar_cmd)
            
            if result.exit_status != 0:
                return {
                    "filename": filename,
                    "error": "SonarQube analysis failed",
                    "exit_code": result.exit_status,
                    "stderr": result.stderr,
                    "stdout": result.stdout
                }
            
            match = re.search(r"ce/task\?id=([\w-]+)", result.stdout)
            if not match:
                raise RuntimeError("Impossible de récupérer le taskId")
            
            task_id = match.group(1)
            
            from .sonar import wait_for_task, get_sonar_issues
            status = await wait_for_task(task_id)
            issues = get_sonar_issues(project_key)
            
            return {
                "filename": filename,
                "project_key": project_key,
                "issues": issues,
                "task_id": task_id,
                "analysis_method": "ssh_remote"
            }
                
    finally:
        async with asyncssh.connect(**SSH_CONFIG) as conn:
            await conn.run(f"rm -f {remote_archive} && rm -rf {remote_dir}")


async def analyze_code_rsync(code: str, filename: str = "analysis.py") -> dict:
    """Alternative avec rsync - plus simple"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        local_path = Path(temp_dir)
        project_dir = local_path / "project"
        project_dir.mkdir()
        (project_dir / filename).write_text(code)
        
        project_key = f"rsync_analysis_{uuid4().hex[:8]}"
        sonar_props = f"""sonar.projectKey={project_key}
sonar.projectName={filename}
sonar.sources=.
sonar.inclusions={filename}
"""
        (project_dir / "sonar-project.properties").write_text(sonar_props)
        
        remote_path = f"/tmp/sonar_rsync_{uuid4().hex}"
        rsync_cmd = [
            "rsync", "-avz", "--delete",
            f"{project_dir}/",
            f"{SSH_CONFIG['username']}@{SSH_CONFIG['host']}:{remote_path}/"
        ]
        
        import subprocess
        result = subprocess.run(rsync_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": f"Rsync failed: {result.stderr}"}
        
        async with asyncssh.connect(**SSH_CONFIG) as conn:
            sonar_cmd = f"""
                cd {remote_path} && 
                sonar-scanner -Dsonar.host.url={SONAR_HOST} -Dsonar.token={SONAR_TOKEN}
            """
            result = await conn.run(sonar_cmd)
            
            match = re.search(r"ce/task\?id=([\w-]+)", result.stdout)
            if match:
                task_id = match.group(1)
                from .sonar import wait_for_task, get_sonar_issues
                status = await wait_for_task(task_id)
                if status == "SUCCESS":
                    issues = await get_sonar_issues(project_key)
                    return {"filename": filename, "issues": issues}
            
            return {"error": "Analysis failed", "output": result.stdout}


async def submit_code(code: str):    
    try:
        result = await analyze_code_via_ssh(code, "test_security_issues.py")
        if "error" in result:
            result = await analyze_code_rsync(code, "test_security_issues.py")
        return result.get("issues", [])
    except Exception as e:
        import traceback
        traceback.print_exc()


async def submit_code_safe(code: str, filename: str = "analysis.py") -> dict:
    """Wrapper autour de submit_code pour toujours renvoyer un dict"""
    try:
        result = await submit_code(code)
        if not isinstance(result, dict):
            return {"error": "SonarQube analysis returned no result"}
        result.setdefault("issues", [])
        if isinstance(result.get("issues"), dict):
            result["issues"] = result["issues"].get("issues", [])
        return result
    except Exception as e:
        return {"error": f"SonarQube analysis failed: {str(e)}", "issues": []}


if __name__ == "__main__":
    test_code = """
import os
import subprocess

def bad_security_practice():
    user_input = input("Enter filename: ")
    os.system(f"cat {user_input}")
    
def poor_code_quality():
    unused_var = "this is never used"
    x = 1
    y = 2
    z = 3
    if x > 0:
        if y > 0:
            if z > 0:
                print("nested conditions")
            else:
                print("z negative")
        else:
            print("y negative") 
    else:
        print("x negative")
        
def duplicate_code():
    data = []
    for i in range(10):
        data.append(i * 2)
    more_data = []
    for i in range(10):
        more_data.append(i * 2)
    return data, more_data

def sql_injection_risk():
    user_id = input("User ID: ")
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query

if __name__ == "__main__":
    bad_security_practice()
    poor_code_quality() 
    duplicate_code()
    sql_injection_risk()
"""
    import asyncio
    res = asyncio.run(submit_code_safe(test_code))
    print(res)
