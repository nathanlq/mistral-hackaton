from fastmcp import FastMCP
from src.services.sonarqube_client import SonarQubeClient
from src.services.dependency_track_client import DependencyTrackClient
from src.core.optimizer import CodeOptimizer
from src.core.metrics import EnergyMetrics
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Initialisation du serveur MCP
mcp = FastMCP("EcoOptimizer")

# Clients de services
sonar_client = SonarQubeClient()
dependency_client = DependencyTrackClient()
optimizer = CodeOptimizer()
metrics_calculator = EnergyMetrics()

@mcp.tool(description="Analyse un repository GitHub pour l'optimisation énergétique. Retourne un analysis_id pour les étapes suivantes.")
async def analyze_repository(
    repo_url: str  # Format: "https://github.com/owner/repo"
) -> str:
    """
    Lance l'analyse complète d'un repository.
    
    Args:
        repo_url: URL complète du repository GitHub
        
    Returns:
        analysis_id (format: eco_YYYYMMDD_HHMMSS)
    """
    # Note: GitHub est déjà disponible via Le Chat
    # On se contente de déclencher les analyses externes
    
    analysis_id = f"eco_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Déclenchement analyses asynchrones
    await sonar_client.trigger_analysis(repo_url)
    await dependency_client.analyze_repository(repo_url)
    
    # Stockage minimal de l'état
    await store_analysis_state(analysis_id, {"repo_url": repo_url, "status": "running"})
    
    return analysis_id

@mcp.tool(description="Calcule les métriques énergétiques d'une analyse. Retourne score énergie, estimation CO2 et coût.")
async def get_energy_metrics(
    analysis_id: str  # Format: eco_YYYYMMDD_HHMMSS
) -> dict:
    """
    Calcule métriques énergétiques à partir des données collectées.
    
    Args:
        analysis_id: ID retourné par analyze_repository
        
    Returns:
        {
            "energy_score": 0-100,
            "co2_estimate_kg": float,
            "cost_estimate_eur": float,
            "metrics_date": "YYYY-MM-DD HH:MM:SS"
        }
    """
    # Récupération des données d'analyse
    sonar_metrics = await sonar_client.get_quality_metrics(analysis_id)
    deps_issues = await dependency_client.get_vulnerabilities(analysis_id)
    
    # Calculs énergétiques
    energy_score = await metrics_calculator.calculate_energy_score(
        complexity=sonar_metrics.get("complexity", 0),
        code_smells=sonar_metrics.get("code_smells", 0),
        outdated_deps=len(deps_issues.get("outdated", []))
    )
    
    co2_estimate = await metrics_calculator.estimate_co2_impact(energy_score)
    cost_estimate = await metrics_calculator.calculate_cost_impact(energy_score)
    
    return {
        "energy_score": round(energy_score, 1),
        "co2_estimate_kg": round(co2_estimate, 3),
        "cost_estimate_eur": round(cost_estimate, 2),
        "metrics_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@mcp.tool(description="Génère des suggestions d'optimisation énergétique basées sur l'analyse. Utilise l'IA pour des recommandations personnalisées.")
async def suggest_optimizations(
    analysis_id: str,  # Format: eco_YYYYMMDD_HHMMSS
    max_suggestions: int = 5  # Nombre max de suggestions (1-10)
) -> dict:
    """
    Génère suggestions d'optimisation via l'IA Mistral.
    
    Args:
        analysis_id: ID retourné par analyze_repository
        max_suggestions: Nombre max de suggestions à retourner
        
    Returns:
        {
            "suggestions": [
                {
                    "title": str,
                    "description": str,
                    "impact_energy": "low|medium|high",
                    "effort": "low|medium|high",
                    "files_affected": [str],
                    "energy_savings_percent": int
                }
            ],
            "generated_date": "YYYY-MM-DD HH:MM:SS"
        }
    """
    # Récupération des données pour le prompt
    analysis_data = await get_analysis_summary(analysis_id)
    
    # Construction du prompt pour Mistral (via Le Chat)
    context = f"""
    Données d'analyse énergétique:
    - Complexité cyclomatique: {analysis_data.get('complexity')}
    - Code smells: {analysis_data.get('code_smells')}
    - Dépendances obsolètes: {analysis_data.get('outdated_deps')}
    - Score énergétique: {analysis_data.get('energy_score')}/100
    
    Génère {max_suggestions} optimisations concrètes pour réduire la consommation énergétique.
    """
    
    # Note: Le Chat/Mistral traitera ce contexte
    suggestions = await optimizer.generate_suggestions(context, max_suggestions)
    
    return {
        "suggestions": suggestions,
        "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@mcp.tool(description="Vérifie les dépendances obsolètes et vulnérabilités d'un projet. Retourne audit complet.")
async def audit_dependencies(
    analysis_id: str  # Format: eco_YYYYMMDD_HHMMSS
) -> dict:
    """
    Audit complet des dépendances pour sécurité et performance.
    
    Args:
        analysis_id: ID retourné par analyze_repository
        
    Returns:
        {
            "total_dependencies": int,
            "outdated": [{"name": str, "current": str, "latest": str, "energy_impact": str}],
            "vulnerabilities": [{"name": str, "severity": str, "cve": str}],
            "audit_date": "YYYY-MM-DD HH:MM:SS"
        }
    """
    deps_data = await dependency_client.get_full_audit(analysis_id)
    
    return {
        "total_dependencies": deps_data["total"],
        "outdated": deps_data["outdated"],
        "vulnerabilities": deps_data["vulnerabilities"],
        "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }