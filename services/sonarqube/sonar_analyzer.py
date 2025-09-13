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

# Charger variables d'environnement
load_dotenv()

# Configuration SSH depuis .env
SSH_CONFIG = {
    "host": os.getenv("SSH_HOST", "localhost"),
    "username": os.getenv("SSH_USERNAME"),
    "password": os.getenv("SSH_PASSWORD"),  # optionnel si clé SSH
    "port": int(os.getenv("SSH_PORT", "22")),
}

# Si clé SSH spécifiée, l'utiliser à la place du mot de passe
if os.getenv("SSH_KEY_PATH"):
    SSH_CONFIG["client_keys"] = [os.getenv("SSH_KEY_PATH")]
    SSH_CONFIG.pop("password", None)

SONAR_HOST = os.getenv("SONAR_HOST", "https://ollama.lambdah.ovh") 
SONAR_TOKEN = os.getenv("SONAR_TOKEN")


async def analyze_code_via_ssh(code: str, filename: str = "analysis.py") -> dict:
    """Analyse SonarQube en uploadant le code vers le serveur SSH"""
    
    # Préparer archive locale
    with tempfile.TemporaryDirectory() as local_temp:
        local_path = Path(local_temp)
        
        # Créer structure projet
        project_dir = local_path / "project" 
        project_dir.mkdir()
        
        # Fichier de code
        code_file = project_dir / filename
        code_file.write_text(code)
        
        # Configuration Sonar
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
        
        # Créer archive
        archive_path = local_path / "project.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            for file in project_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(project_dir))
    
        # Upload et analyse via SSH
        return await execute_remote_analysis(archive_path, project_key, filename)


async def execute_remote_analysis(archive_path: Path, project_key: str, filename: str) -> dict:
    """Exécute l'analyse sur le serveur distant"""
    
    print(f"[DEBUG] Tentative connexion SSH vers {SSH_CONFIG['host']}:{SSH_CONFIG['port']}")
    print(f"[DEBUG] Utilisateur: {SSH_CONFIG['username']}")
    print(f"[DEBUG] Auth: {'Clé SSH' if 'client_keys' in SSH_CONFIG else 'Mot de passe'}")
    
    try:
        async with asyncssh.connect(**SSH_CONFIG) as conn:
            print(f"[DEBUG] ✅ Connexion SSH établie")
            
            # Paths distants
            remote_archive = f"/tmp/sonar_{uuid4().hex}.zip"
            remote_dir = f"/tmp/sonar_project_{uuid4().hex}"
            
            print(f"[DEBUG] Paths distants:")
            print(f"[DEBUG]   Archive: {remote_archive}")
            print(f"[DEBUG]   Projet: {remote_dir}")
            
            try:
                # Vérification espace disque et permissions
                print(f"[DEBUG] Vérification serveur...")
                disk_check = await conn.run("df -h /tmp && ls -la /tmp | head -5")
                print(f"[DEBUG] Espace /tmp: {disk_check.stdout[:200]}")
                
                # Vérification sonar-scanner
                sonar_check = await conn.run("which sonar-scanner && sonar-scanner --version")
                if sonar_check.exit_status == 0:
                    print(f"[DEBUG] ✅ sonar-scanner disponible")
                    print(f"[DEBUG] Version: {sonar_check.stdout.strip()}")
                else:
                    print(f"[DEBUG] ❌ sonar-scanner introuvable")
                    print(f"[DEBUG] Erreur: {sonar_check.stderr}")
                
                # Nettoyage préalable
                print(f"[DEBUG] Nettoyage préalable...")
                cleanup_result = await conn.run(f"rm -rf {remote_dir}")
                print(f"[DEBUG] Nettoyage: {'OK' if cleanup_result.exit_status == 0 else 'FAILED'}")
                
                # Upload archive
                print(f"[DEBUG] Upload archive ({archive_path.stat().st_size} bytes)...")
                async with conn.start_sftp_client() as sftp:
                    await sftp.put(str(archive_path), remote_archive)
                print(f"[DEBUG] ✅ Upload terminé")
                
                # Vérification upload
                check_upload = await conn.run(f"ls -la {remote_archive}")
                if check_upload.exit_status == 0:
                    print(f"[DEBUG] ✅ Archive présente: {check_upload.stdout.strip()}")
                else:
                    raise RuntimeError(f"Archive non trouvée après upload")
                
                # Décompresser
                print(f"[DEBUG] Décompression...")
                decompress_cmd = f"mkdir -p {remote_dir} && cd {remote_dir} && unzip -q {remote_archive}"
                result = await conn.run(decompress_cmd)
                
                if result.exit_status != 0:
                    print(f"[DEBUG] ❌ Décompression échouée")
                    print(f"[DEBUG] Stderr: {result.stderr}")
                    print(f"[DEBUG] Stdout: {result.stdout}")
                    raise RuntimeError(f"Décompression échouée: {result.stderr}")
                
                print(f"[DEBUG] ✅ Décompression OK")
                
                # Vérification contenu
                ls_result = await conn.run(f"ls -la {remote_dir}")
                print(f"[DEBUG] Contenu projet: {ls_result.stdout}")
                
                # Vérification sonar-project.properties
                props_check = await conn.run(f"cat {remote_dir}/sonar-project.properties")
                if props_check.exit_status == 0:
                    print(f"[DEBUG] ✅ Fichier config sonar:")
                    print(f"[DEBUG] {props_check.stdout}")
                else:
                    print(f"[DEBUG] ❌ Fichier config sonar manquant")
                
                # Exécuter sonar-scanner avec plus de logs
                print(f"[DEBUG] Lancement sonar-scanner...")
                sonar_cmd = f"""
                    cd {remote_dir} && 
                    sonar-scanner \
                        -Dsonar.host.url={SONAR_HOST} \
                        -Dsonar.token={SONAR_TOKEN} \
                        -Dsonar.log.level=DEBUG \
                        -X
                """
                
                print(f"[DEBUG] Commande: {sonar_cmd.strip()}")
                result = await conn.run(sonar_cmd)
                
                print(f"[DEBUG] Exit code: {result.exit_status}")
                print(f"[DEBUG] Stdout (1000 premiers chars):")
                print(f"[DEBUG] {result.stdout[:1000]}")
                
                if result.stderr:
                    print(f"[DEBUG] Stderr (500 premiers chars):")
                    print(f"[DEBUG] {result.stderr[:500]}")
                
                if result.exit_status != 0:
                    return {
                        "filename": filename,
                        "error": "SonarQube analysis failed",
                        "exit_code": result.exit_status,
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                
                # Extraire taskId
                print(f"[DEBUG] Recherche taskId dans output...")
                match = re.search(r"ce/task\?id=([\w-]+)", result.stdout)
                if not match:
                    print(f"[DEBUG] ❌ TaskId non trouvé")
                    print(f"[DEBUG] Recherche dans: {result.stdout[-500:]}")
                    raise RuntimeError("Impossible de récupérer le taskId")
                
                task_id = match.group(1)
                print(f"[DEBUG] ✅ TaskId trouvé: {task_id}")
                
                # Attendre completion (réutilise fonction existante)
                print(f"[DEBUG] Attente completion task...")
                from .sonar import wait_for_task, get_sonar_issues
                
                status = await wait_for_task(task_id)
                print(f"[DEBUG] Status final: {status}")

                print(f"[DEBUG] ✅ Task terminée avec succès")
                
                # Récupérer résultats
                print(f"[DEBUG] Récupération issues...")
                issues = get_sonar_issues(project_key)
                print(f"[DEBUG] ✅ {len(issues)} issues récupérées")
                
                return {
                    "filename": filename,
                    "project_key": project_key,
                    "issues": issues,
                    "task_id": task_id,
                    "analysis_method": "ssh_remote"
                }
                
            finally:
                # Nettoyage
                print(f"[DEBUG] Nettoyage final...")
                cleanup_final = await conn.run(f"rm -f {remote_archive} && rm -rf {remote_dir}")
                print(f"[DEBUG] Nettoyage: {'OK' if cleanup_final.exit_status == 0 else 'FAILED'}")
                
    except asyncssh.PermissionDenied as e:
        print(f"[DEBUG] ❌ Permission SSH refusée")
        print(f"[DEBUG] Erreur: {e}")
        print(f"[DEBUG] Suggestions de debug:")
        print(f"[DEBUG]   1. Tester: ssh {SSH_CONFIG['username']}@{SSH_CONFIG['host']}")
        print(f"[DEBUG]   2. Vérifier: ~/.ssh/authorized_keys sur le serveur")
        print(f"[DEBUG]   3. Vérifier: /var/log/auth.log sur le serveur")
        print(f"[DEBUG]   4. Tester auth: ssh-copy-id {SSH_CONFIG['username']}@{SSH_CONFIG['host']}")
        raise
        
    except Exception as e:
        print(f"[DEBUG] ❌ Erreur générale: {e}")
        print(f"[DEBUG] Type: {type(e).__name__}")
        raise


# Version simplifiée avec rsync (alternative)
async def analyze_code_rsync(code: str, filename: str = "analysis.py") -> dict:
    """Alternative avec rsync - plus simple"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        local_path = Path(temp_dir)
        
        # Préparer projet
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
        
        # Rsync vers serveur
        remote_path = f"/tmp/sonar_rsync_{uuid4().hex}"
        rsync_cmd = [
            "rsync", "-avz", "--delete",
            f"{project_dir}/",
            f"{SSH_CONFIG['username']}@{SSH_CONFIG['host']}:{remote_path}/"
        ]
        
        print(f"[DEBUG] Commande rsync: {' '.join(rsync_cmd)}")
        
        import subprocess
        result = subprocess.run(rsync_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[DEBUG] ❌ Rsync failed: {result.stderr}")
            return {"error": f"Rsync failed: {result.stderr}"}
        
        print(f"[DEBUG] ✅ Rsync OK")
        
        # SSH pour exécuter sonar-scanner  
        async with asyncssh.connect(**SSH_CONFIG) as conn:
            sonar_cmd = f"""
                cd {remote_path} && 
                sonar-scanner -Dsonar.host.url={SONAR_HOST} -Dsonar.token={SONAR_TOKEN}
            """
            print(f"[DEBUG] Commande sonar: {sonar_cmd.strip()}")
            result = await conn.run(sonar_cmd)
            
            print(f"[DEBUG] Sonar exit code: {result.exit_status}")
            
            # Parser et récupérer résultats comme avant
            match = re.search(r"ce/task\?id=([\w-]+)", result.stdout)
            if match:
                task_id = match.group(1)
                print(f"[DEBUG] TaskId trouvé: {task_id}")
                from .sonar import wait_for_task, get_sonar_issues
                status = await wait_for_task(task_id)
                if status == "SUCCESS":
                    issues = await get_sonar_issues(project_key)
                    return {"filename": filename, "issues": issues}
            
            return {"error": "Analysis failed", "output": result.stdout}


async def submit_code(code: str):    
    try:
        # Test méthode SSH
        print("\n🚀 Lancement analyse SSH...")
        result = await analyze_code_via_ssh(code, "test_security_issues.py")
        if "error" in result:
            print(f"❌ Erreur SSH: {result['error']}")
            if "stderr" in result:
                print(f"   Détail: {result['stderr']}")
            
            # Fallback vers rsync si SSH échoue
            print("\n🔄 Tentative avec rsync...")
            result = await analyze_code_rsync(code, "test_security_issues.py")
        
        if "error" not in result:
            print(f"✅ Analyse terminée!")
            print(f"📁 Fichier: {result['filename']}")
            print(f"🔑 Projet: {result.get('project_key', 'N/A')}")
            
            issues = result.get('issues', [])
            print(f"\n📊 Issues détectées: {len(issues)}")
        return issues
    except Exception as e:
        print(f"💥 Exception: {e}")
        import traceback
        traceback.print_exc()

async def submit_code_safe(code: str, filename: str = "analysis.py") -> dict:
    """Wrapper autour de submit_code pour toujours renvoyer un dict"""
    try:
        result = await submit_code(code)
        print(result)
        if not isinstance(result, dict):
            return {"error": "SonarQube analysis returned no result"}
        
        # Assurer que 'issues' est toujours une liste
        result.setdefault("issues", [])
        if isinstance(result.get("issues"), dict):
            result["issues"] = result["issues"].get("issues", [])
        print(result)
        return result

    except Exception as e:
        return {"error": f"SonarQube analysis failed: {str(e)}", "issues": []}


if __name__ == "__main__":
    test_code = """
import os
import subprocess

def bad_security_practice():
    # Injection de commande - CRITIQUE
    user_input = input("Enter filename: ")
    os.system(f"cat {user_input}")  # Vulnérabilité critique
    
def poor_code_quality():
    # Variables inutilisées, complexité cyclomatique
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
    # Code dupliqué
    data = []
    for i in range(10):
        data.append(i * 2)
    
    more_data = []
    for i in range(10):
        more_data.append(i * 2)  # Duplication
    
    return data, more_data

def sql_injection_risk():
    # Simulation injection SQL
    user_id = input("User ID: ")
    query = f"SELECT * FROM users WHERE id = {user_id}"  # Vulnérable
    return query

# Exécution
if __name__ == "__main__":
    bad_security_practice()
    poor_code_quality() 
    duplicate_code()
    sql_injection_risk()
"""
    import asyncio
    res = asyncio.run(submit_code_safe(test_code))
    print(res)