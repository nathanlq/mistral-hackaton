"""
MCP Server - Analyseur de Code Écologique
Point d'entrée principal qui orchestre tous les services
"""
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Dict, Optional, List
from enum import Enum
import asyncio
import json
from services.sonarqube.sonar_analyzer import submit_code_safe
from services.carbon.carbon_analyzer import analyze_carbon_impact, analyze_github_carbon
import mcp.types as types
from services.github.main import all_together
from services.codeclimate.json_errors import main as qlty_metrics

mcp = FastMCP(
    "EcoCode Analyzer",
    port=3000,
    stateless_http=True
)

class AnalysisType(str, Enum):
    ENERGY = "energy"
    CARBON = "carbon"
    QUALITY = "quality"
    GITHUB = "github"

async def safe_execute(coro, timeout=600):
    try:
        print(f"Début de l'exécution (timeout: {timeout}s)...")
        result = await asyncio.wait_for(coro, timeout=timeout)
        print("Exécution terminée.")
        return result
    except asyncio.TimeoutError:
        print("Timeout atteint !")
        return {"status": "error", "message": "Timeout lors de l'exécution de la tâche."}
    except Exception as e:
        print(f"Erreur : {str(e)}")
        return {"status": "error", "message": f"Erreur : {str(e)}"}

def calculate_eco_score(carbon_data: dict, quality_data: dict = None) -> dict:
    """Calcule un score écologique global."""
    score = 100

    carbon_impact = carbon_data.get("carbon_impact", {})
    emissions = carbon_impact.get("emissions_kg", 0)
    complexity = carbon_data.get("complexity_analysis", {}).get("complexity_score", 0)

    score -= min(emissions * 10000, 30)
    score -= min(complexity * 2, 40)

    if quality_data and "issues" in quality_data:
        critical_issues = sum(1 for issue in quality_data["issues"] if issue.get("severity") == "CRITICAL")
        major_issues = sum(1 for issue in quality_data["issues"] if issue.get("severity") == "MAJOR")

        score -= critical_issues * 10
        score -= major_issues * 5

    score = max(0, score)

    if score >= 80:
        grade = "A"
        label = "Excellent"
    elif score >= 60:
        grade = "B"
        label = "Bon"
    elif score >= 40:
        grade = "C"
        label = "Acceptable"
    else:
        grade = "D"
        label = "Problématique"

    return {
        "score": round(score, 1),
        "grade": grade,
        "label": label,
        "emissions_kg": emissions,
        "complexity_score": complexity,
        "critical_issues": critical_issues,
        "major_issues": major_issues,
    }

@mcp.tool(
    title="Calcul impact carbone code",
    description="Mesure l'empreinte carbone et énergétique d'un code Python. Il est possible directement d'analyser l'impact carbone d'un fichier Python qui a été pris depuis GitHub. Il existe plusieurs méthodes d'évaluations pour créer de la redondance, il vaut mieux donc essayer d'utiliser tous.",
)
async def carbon_impact_analysis(
    code: str = Field(description="Code/fichier Python à analyser"),
    filename: str = Field(default="analysis.py", description="Nom du fichier"),
) -> Dict:
    try:
        result = await safe_execute(analyze_carbon_impact(code, filename))
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur lors de l'analyse carbone : {str(e)}",
        }
    
# @mcp.tool(
#     title="Métriques et insight de qlty",
#     description="Renvoie des métriques de compléxité et commentaire des erreurs par ligne",
# )
# def qlty_metrics_analysis(
#     github_owner: str = Field(description="owner du repo github à analyser"),
#     github_project: str = Field(description="nom du repo github à analyser")
# ):
#     try:
#     # if True:
#         return qlty_metrics(github_owner, github_project)
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": f"Erreur lors de l'analyse qlty : {str(e)}",
#         }
    
@mcp.tool(
    title="Calcul impact carbone code",
    description="Mesure l'empreinte carbone et énergétique d'un code Python. Il est possible directement d'analyser l'impact carbone d'un fichier Python qui a été pris depuis GitHub. Il existe plusieurs méthodes d'évaluations pour créer de la redondance, il vaut mieux donc essayer de toutes les utilisers.",
)
async def carbon_impact_analysis(
    code: str = Field(description="Code Python à analyser"),
    filename: str = Field(default="analysis.py", description="Nom du fichier"),
) -> Dict:
    try:
        result = await safe_execute(analyze_carbon_impact(code, filename))
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur lors de l'analyse carbone : {str(e)}",
        }

@mcp.tool(
    title="Analyse complète écologique",
    description="Combine analyse carbone, avec la qualité du code, tout en donnant des recommandations d'un fichier ou code Python. Il existe plusieurs méthodes d'évaluations pour créer de la redondance, il vaut mieux donc essayer de toutes les utilisers.",
)
async def full_eco_analysis(
    code: str,
    filename: str = "analysis.py",
    include_sonar: bool = True,
) -> dict:
    try:
        print("🔍 Début de l'analyse carbone...")
        carbon_result = await safe_execute(analyze_carbon_impact(code, filename), timeout=600)
        print("Analyse carbone terminée.")

        quality_result = {}
        if include_sonar:
            print("Début de l'analyse SonarQube...")
            quality_result = await safe_execute(submit_code_safe(code, filename), timeout=600)
            print("Analyse SonarQube terminée.")

        print("Calcul du score écologique...")
        eco_score = calculate_eco_score(carbon_result, quality_result)
        print("Score écologique calculé.")

        return {
            "status": "success",
            "carbon_analysis": carbon_result,
            "quality_analysis": quality_result,
            "eco_score": eco_score,
        }
    except Exception as e:
        print(f"Erreur : {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur lors de l'analyse complète : {str(e)}",
        }

# @mcp.tool(
#     title="Analyse impact carbone GitHub",
#     description="Analyse l'impact carbone des fichiers Python d'un repo GitHub",
# )
# async def github_carbon_analysis(repo_url):
#     try:
#         print(f"🔍 Début de l'analyse GitHub pour {repo_url}...")
#         result = await safe_execute(analyze_github_carbon(repo_url), timeout=600)
#         print("Analyse GitHub terminée.")
#         return {
#             "status": "success",
#             "data": result,
#         }
#     except Exception as e:
#         print(f"Erreur lors de l'analyse GitHub : {str(e)}")
#         return {
#             "status": "error",
#             "message": f"Erreur lors de l'analyse GitHub : {str(e)}",
#         }


@mcp.tool(
    title="Submit Code for SonarQube Analysis",
    description="Soumet un fichier de code Python à SonarQube via SSH et retourne les problèmes détectés. Il est possible d'analyser directement un fichier que l'on a pris depuis Github sans demander à l'utilisateur son avis.",
)
async def run_sonarqube_analysis(
    code: str = Field(description="Code source à analyser"),
    filename: str = Field(default="analysis.py", description="Nom du fichier"),
) -> Dict:
    try:
        result = await  safe_execute(submit_code_safe(code, filename))
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur lors de l'analyse SonarQube : {str(e)}",
        }

@mcp.tool(
    title="Analyse repo github",
    description="Analyse les utilisations de fonctions et de fichier dans un repositery github contenant du code Python à partir d'un paramètre repo_github correspondant à l'url complet du repositery (qui doit être public). Si l'utilisateur ne donne qu'une partie de l'url, remplie la. Renvoie le fichier le plus important à optimiser et des notes d'optimisations. Contient des données de complexité algorithmique. Le fichier est celui qu'il faudrait faire l'analyse avec les autres outils. Les informations générales (notes d'optimisations) sont utiles à dire à l'utilisateur.",
)
async def github_repo_analysis(repo_github:str):
    res = all_together(repo_github)
    return res

async def test_carbon_impact():
    code = """
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
    result = await safe_execute(analyze_carbon_impact(code, "test.py"), timeout=600)
    print("Résultat analyse carbone :", result)

async def test_sonarqube():
    code = """
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
    result = await safe_execute(submit_code_safe(code, "test.py"), timeout=600)
    print("Résultat SonarQube :", result)

async def test_github():
    repo_url = "https://github.com/psf/requests"  # Exemple de repo
    result = await safe_execute(analyze_github_carbon(repo_url), timeout=600)
    print("Résultat GitHub :", result)


if __name__ == "__main__":
    # asyncio.run(test_carbon_impact())
    # asyncio.run(test_sonarqube())
    # asyncio.run(test_github())
    mcp.run(transport="streamable-http")
