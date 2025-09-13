"""
MCP Server - Analyseur de Code Écologique
Point d'entrée principal qui orchestre tous les services
"""
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import List, Dict, Optional
from enum import Enum
import mcp.types as types

from services.sonarqube.sonar import submit_code

mcp = FastMCP("EcoCode Analyzer", port=3000, stateless_http=True, debug=True)

class AnalysisType(str, Enum):
    ENERGY = "energy"
    PERFORMANCE = "performance"
    DEPENDENCIES = "dependencies"
    SECURITY = "security"
    BUNDLE = "bundle"
    CARBON = "carbon"
    FULL = "full"

class ReportFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"

@mcp.tool(
    title="Submit Code for SonarQube Analysis",
    description="Soumet un fichier de code à SonarQube et retourne les problèmes détectés"
)
async def run_sonarqube_analysis(
    code: str = Field(description="Code source à analyser"),
    timeout=600
) -> Dict:
    return await submit_code(code, filename="bad_code.py")

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
