import os
import time
import requests
from dotenv import load_dotenv
import os

load_dotenv()

qlty_api_url = os.getenv("QLTY_API_URL", "")
qlty_api_token = os.getenv("QLTY_TOKEN", "") 

def get_header(qlty_api_token):
    headers = {
        "Authorization": f"Bearer {qlty_api_token}",
        "Accept": "application/json",
    }
    return headers

def get_project_metrics(qlty_api_token, owner, project):
    url = f"{qlty_api_url}/gh/{owner}/projects/{project}/metrics"
    r = requests.get(url, headers=get_header(qlty_api_token))
    r.raise_for_status()
    return r.json()

def list_project_issues(qlty_api_token, owner, project):
    url = f"{qlty_api_url}/gh/{owner}/projects/{project}/issues"
    r = requests.get(url, headers=get_header(qlty_api_token))
    r.raise_for_status()
    return r.json()

def get_file_metrics(filepath: str, qlty_api_token, owner, project):
    url = f"{qlty_api_url}/gh/{owner}/projects/{project}/files"
    r = requests.get(url, headers=get_header(qlty_api_token), params={"path": filepath})
    r.raise_for_status()
    return r.json()

def get_analysis_status(analysis_id: str, qlty_api_token, owner, project):
    """
    Récupère le statut d'une analyse déclenchée.
    """
    url = f"{qlty_api_url}/gh/{owner}/projects/{project}/analyses/{analysis_id}"
    r = requests.get(url, headers=get_header(qlty_api_token))
    r.raise_for_status()
    return r.json()

def wait_for_analysis_completion(analysis_id: str, timeout: int = 180):
    """
    Attend la fin d'une analyse avec polling.
    """
    start = time.time()
    while time.time() - start < timeout:
        status = get_analysis_status(analysis_id)
        state = status.get("state", status.get("status", "unknown"))
        print(f"⏳ Analyse {analysis_id}: {state}")
        if state in ["completed", "finished", "success"]:
            return status
        elif state in ["failed", "error", "cancelled"]:
            raise RuntimeError(f"Analyse échouée: {state}")
        time.sleep(5)
    raise TimeoutError("Analyse non terminée dans le délai imparti")
