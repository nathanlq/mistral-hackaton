"""
MCP Server - Analyseur de Code Écologique
Point d'entrée principal qui orchestre tous les services
"""
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import List, Dict, Optional
from enum import Enum
import mcp.types as types

from services.sonarqube.api import submit_code

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
def run_sonarqube_analysis(
    code: str = Field(description="Code source à analyser"),
    filename: str = Field(description="Nom du fichier, ex: bad_code.py"),
    project_key: str = Field(description="Clé unique du projet", default="mcp-project")
) -> Dict:
    return submit_code(code, filename, project_key)

@mcp.prompt("Analyse de repo github")
def github_analyse_prompt():
    return """
You are an automated code auditor. Your primary goal is to analyze a GitHub repository to detect **computational complexity issues**, identify hotspots, and produce a structured and prioritized efficiency report.
### Instructions
1. **Repository Access**
   - Connect to the given GitHub repository via GitHub.
   - Parse the repository contents.
2. **Libraries and Dependencies**
   - Identify all external libraries and their versions.
   - Check across `requirements.txt`, `setup.py`, `pyproject.toml`, `package.json`, or other language-specific dependency files.
   - Also scan the code directly for library usage.
   - For each library, report:
     - Version (if specified)
     - Frequency of usage in the repository
   - Rank libraries by frequency of usage.
3. **Intra-Repository Imports**
   - Detect imports of internal modules and scripts dynamically within the repository.
   - Report which internal scripts or modules are used the most.
   - Rank them based on frequency of usage.
4. **Computational Complexity & Code Efficiency Improvements**
   - Perform static analysis to detect parts of the code with high computational cost, with emphasis on:
     - Nested loops (O(n²), O(n³), etc.)
     - Deep recursion and potential stack overflows
     - Heavy data structure operations (e.g., repeated list scans, inefficient sorts, unnecessary recomputations)
     - Excessive I/O inside loops causing CPU or memory strain
   - For each identified case, estimate the complexity class and assess its potential impact.
   - Where applicable, suggest optimizations or existing library functions that provide more efficient alternatives.
   - Rank recommended improvements by priority (High, Medium, Low) based on operation frequency and risk of performance degradation.
5. **Potential Bottlenecks**
   - Identify functions, scripts, or modules that are invoked frequently and may become runtime bottlenecks.
   - Highlight code components that concentrate too many calls, computations, or dependencies.
   - Cross-reference bottlenecks with complexity analysis to highlight *critical inefficiencies*.
   - Rank bottlenecks by risk level (High, Medium, Low).
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
#### Complexity Analysis and Efficiency Opportunities
| Rank | File & Function        | Operation Detected | Est. Complexity | Recommended Optimization | Priority |
|------|------------------------|-------------------|-----------------|--------------------------|----------|
| 1    | core/search.py → brute_force_search() | Nested loops | O(n²) | Replace with set/dict lookup | High |
| 2    | utils/sorting.py → custom_sort() | Bubble sort | O(n²) | Use built-in `sort()` | High |
---
#### Bottlenecks and Hotspots
| Rank | File & Function        | Description | Risk Level | Notes |
|------|------------------------|-------------|------------|-------|
| 1    | main.py → run_pipeline() | Calls brute_force_search() repeatedly | High | Causes potential O(n³) runtime |
| 2    | data_loader.py → CSVLoader | Reads disk on every iteration | Medium | Should batch or preload data
"""

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
