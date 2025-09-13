from services.codeclimate.api.client import get_project_metrics, list_project_issues
import json
from dotenv import load_dotenv
import os

load_dotenv()

qlty_api_url = os.getenv("QLTY_API_URL", "")
qlty_api_token = os.getenv("QLTY_TOKEN", "") 


def main(owner, project):
    # try:
    if True:
        metrics = get_project_metrics(qlty_api_token, owner, project)
        print(f"✅ Metrics globales récupérées : {len(metrics.get('data', []))} items")
    # except Exception as e:
    #     print("❌ Erreur lors de la récupération des metrics :", e)
    #     metrics = {}

    # Récupération des issues
    try:
        issues = list_project_issues(qlty_api_token, owner, project)
        issue_count = len(issues.get("data", [])) if issues else 0
        print(f"✅ Issues récupérées : {issue_count}")
    except Exception as e:
        print("❌ Erreur lors de la récupération des issues :", e)
        issues = {}

    # Génération du JSON
    project_data = {
        "metrics": metrics,
        "issues": issues
    }

    filename = "qlty_project_data.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2)
    print(f"✅ JSON projet généré : {filename}")
    return project_data

if __name__ == "__main__":
    main()
