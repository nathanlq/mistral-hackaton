import requests
import time
import asyncio
from typing import Dict, List, Optional

SONAR_HOST = "https://ollama.lambdah.ovh"
SONAR_TOKEN = "squ_44a64e04ea7ed4a54789b71def306412f7fcf840"

async def wait_for_task(task_id: str, timeout: int = 300) -> bool:
    """Attend que la tâche SonarQube soit terminée"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"{SONAR_HOST}/api/ce/task",
                params={"id": task_id},
                auth=(SONAR_TOKEN, "")
            )
            
            if response.status_code == 200:
                task_data = response.json()
                status = task_data.get("task", {}).get("status")
                
                if status == "SUCCESS":
                    return True
                elif status == "FAILED":
                    raise Exception(f"SonarQube task failed: {task_data}")
                
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Erreur lors de l'attente: {e}")
            await asyncio.sleep(5)
    
    return "TIMEOUT"

def get_sonar_issues(project_key: str) -> Dict:
    """Récupère les issues SonarQube pour un projet"""
    
    eco_rules = [
        "python:S1066",  # Complexité cognitive
        "python:S3776",  # Complexité cyclomatique
    ]
    
    try:
        response = requests.get(
            f"{SONAR_HOST}/api/issues/search",
            params={
                "componentKeys": project_key
            },
            auth=(SONAR_TOKEN, "")
        )
        
        if response.status_code != 200:
            raise Exception(f"Erreur API SonarQube: {response.status_code} - {response.text}")
        
        all_issues = response.json()
        
        eco_issues = []
        for issue in all_issues.get("issues", []):
            rule_key = issue.get("rule", "")
            
            is_eco = (
                rule_key in eco_rules or
                any(keyword in issue.get("message", "").lower() 
                    for keyword in ["performance", "memory", "cpu", "complexity", "unused", "duplicate"])
            )
            
            if is_eco:
                eco_issues.append(issue)
        
        return {
            "total_issues": len(all_issues.get("issues", [])),
            "eco_issues": len(eco_issues),
            "issues": eco_issues,
            "project_key": project_key
        }
        
    except Exception as e:
        print(f"Erreur lors de la récupération des issues: {e}")
        return {"error": str(e)}

def calculate_eco_score(issues_data: Dict) -> Dict:
    """Calcule un score écologique basé sur les issues"""
    
    if "error" in issues_data:
        return {"error": issues_data["error"]}
    
    eco_issues = issues_data.get("issues", [])
    impact_count = {"high": 0, "medium": 0, "low": 0}
    
    detailed_issues = []
    
    for issue in eco_issues:
        severity = issue.get("severity", "INFO")
        rule_key = issue.get("rule", "")
        message = issue.get("message", "")
        line = issue.get("line", 0)
        
        if severity in ["BLOCKER", "CRITICAL"]:
            impact = "high"
            impact_count["high"] += 1
        elif severity == "MAJOR":
            impact = "medium" 
            impact_count["medium"] += 1
        else:
            impact = "low"
            impact_count["low"] += 1
        
        detailed_issues.append({
            "rule": rule_key,
            "message": message,
            "line": line,
            "severity": severity,
            "eco_impact": impact,
            "component": issue.get("component", "")
        })
    
    total_issues = sum(impact_count.values())
    if total_issues == 0:
        eco_score = 100
    else:
        penalty = impact_count["high"] * 15 + impact_count["medium"] * 8 + impact_count["low"] * 3
        eco_score = max(0, 100 - penalty)
    
    return {
        "eco_score": eco_score,
        "total_issues": issues_data.get("total_issues", 0),
        "eco_issues_count": len(eco_issues),
        "impact_breakdown": impact_count,
        "detailed_issues": detailed_issues,
        "project_key": issues_data.get("project_key")
    }