"""
MCP Server - Analyseur de Code Écologique
Point d'entrée principal qui orchestre tous les services
"""
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import List, Dict, Optional
from enum import Enum
import mcp.types as types
from services.sonarqube.sonar_analyzer import submit_code_safe
from services.carbon.carbon_analyzer import analyze_carbon_impact, analyze_github_carbon
import asyncio
import json

mcp = FastMCP("EcoCode Analyzer", port=3000, stateless_http=True, debug=True)

class AnalysisType(str, Enum):
    ENERGY = "energy" 
    CARBON = "carbon"
    QUALITY = "quality"
    GITHUB = "github"

@mcp.tool(
    title="Calcul impact carbone code",
    description="Mesure l'empreinte carbone et énergétique d'un code Python"
)
async def carbon_impact_analysis(
    code: str = Field(description="Code Python à analyser"),
    filename: str = Field(default="analysis.py", description="Nom du fichier")
) -> Dict:
    pass


@mcp.tool(
    title="Analyse GitHub écologique", 
    description="Analyse l'impact carbone et la complexité d'un repo GitHub"
)
async def github_eco_analysis(
    repo_url: str = Field(description="URL du repository GitHub"),
    analysis_type: AnalysisType = Field(default=AnalysisType.CARBON, description="Type d'analyse")
) -> Dict:
    pass


@mcp.tool(
    title="Analyse complète écologique",
    description="Combine analyse carbone + qualité code + recommandations"
)
async def full_eco_analysis(
    code: str,
    filename: str = "analysis.py",
    include_sonar: bool = True
) -> dict:
    pass


def calculate_eco_score(carbon_data: dict, quality_data: dict = None) -> dict:
    """Calcule un score écologique global"""
    
    score = 100  # Score de base
    
    # Pénalités carbone
    carbon_impact = carbon_data.get("carbon_impact", {})
    emissions = carbon_impact.get("emissions_kg", 0)
    complexity = carbon_data.get("complexity_analysis", {}).get("complexity_score", 0)
    
    score -= min(emissions * 10000, 30)  # Max -30 pour carbone
    score -= min(complexity * 2, 40)     # Max -40 pour complexité
    
    # Pénalités qualité
    if quality_data and "issues" in quality_data:
        critical_issues = sum(1 for i in quality_data["issues"] if i.get("severity") == "CRITICAL")
        major_issues = sum(1 for i in quality_data["issues"] if i.get("severity") == "MAJOR")
        
        score -= critical_issues * 10  
        score -= major_issues * 5
    
    score = max(0, score)  # Minimum 0
    
    # Classification
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
        "complexity_score": complexity
    }

@mcp.tool(
    title="Submit Code for SonarQube Analysis",
    description="Soumet un fichier de code à SonarQube via SSH et retourne les problèmes détectés"
)
async def run_sonarqube_analysis(
    code: str = Field(description="Code source à analyser"),
    filename: str = Field(default="analysis.py", description="Nom du fichier")
) -> Dict:
    pass


@mcp.prompt("Analyse de repo github")
def github_analyse_prompt(lien_repo: str = Field(description="lien d'un repo github à analyser") ):
    return f"""
    You are an automated code auditor. Your primary goal is to analyze a GitHub repository to detect **computational complexity issues**, identify hotspots, and produce a structured and prioritized efficiency report on Python code.  
### Instructions  
0. **Extraction of the github repositery**
   - The github repository is located in this prompt  "Hello, I want you to analyse this github project {lien_repo}". Extract it and use it for the next operations
1. **Repository Access**  
   - Connect to the given GitHub repository via Github 
   - Parse the repository contents (only the Python code), and locate the main file/function. 
2. **Libraries and Dependencies**  
   - Identify all external libraries and their versions.  
   - Check across `requirements.txt`, `setup.py`, `pyproject.toml`, etc.  
   - Also scan the code directly for library usage.  
   - For each library, report:  
     - Version (if specified)  
     - Frequency of usage in the repository  
   - Rank libraries by frequency of usage.  
3. **Intra-Repository Imports**  
   - Detect imports of internal modules and scripts dynamically within the repository.  
   - Report which internal scripts or modules are used the most.  
4. **Computational Complexity & Code Efficiency Improvements**  
   - Perform static analysis to detect parts of the code with high computational cost on the most called file, with emphasis on:  
     - Nested loops (O(n²), O(n³), etc.)  
     - Deep recursion and potential stack overflows  
     - Heavy data structure operations (e.g., repeated list scans, inefficient sorts, unnecessary recomputations)  
     - Excessive I/O inside loops causing CPU or memory strain  
   - For each identified case, estimate the complexity class and assess its potential impact.  
   - Where applicable, suggest optimizations or existing library functions that provide more efficient alternatives.  
   - Rank recommended improvements by priority (High, Medium, Low) based on operation frequency and risk of performance degradation.  
6. **Output Report**  
   - Return results in **Markdown format**.  
   - Divide the report into the following sections:  
     - Dependencies and Libraries  
     - Internal Code Usage  
     - Complexity Analysis and Efficiency Opportunities  
     - Bottlenecks and Hotspots  
   - Inside each section, findings should be **ranked and numbered by priority**.  
   - Make the Markdown structured and readable for both humans and LLMs.  
---
### Structure Examples (Tables for Each Section)
#### Dependencies and Libraries
| Rank | Library | Version | Frequency of Usage | Notes |
|------|----------|---------|--------------------|-------|
| 1    | numpy    | 1.22.0  | 15 files           | Core dependency |
| 2    | pandas   | 1.4.2   | 10 files           | Data processing |
---
#### Internal Code Usage
| Rank | Module/Script         | Import Frequency | Notes |
|------|-----------------------|------------------|-------|
| 1    | utils/data_loader.py  | 8 imports        | Centralized data handling |
| 2    | core/parser.py        | 5 imports        | Tightly coupled with `main.py` |
---
Most used file :
#### Complexity Analysis and Efficiency Opportunities
| Rank  | Function      | Operation Detected | Est. Complexity | Recommended Optimization | Priority |
|------|------------------------|-------------------|-----------------|--------------------------|----------|
| 1    |  brute_force_search() | Nested loops | O(n²) | Replace with set/dict lookup | High |
| 2    | custom_sort() | Bubble sort | O(n²) | Use built-in `sort()` | High |

Don't add any more comments than wanted. Be concise.
"""

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
