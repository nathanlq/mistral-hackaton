# EcoOptimizer MCP

Serveur MCP pour l'optimisation écologique du code - Analyse automatique de la performance énergétique et suggestions d'optimisation.

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python src/main.py
```

## Configuration

Copiez `.env.example` vers `.env` et configurez :
- GitHub token
- SonarQube URL/token  
- Dependency Track URL/token

## Architecture

- **Core** : Logique MCP et moteur d'optimisation
- **Services** : Intégrations externes (GitHub, SonarQube, etc.)
- **Models** : Structures de données
- **Utils** : Outils transversaux

## Fonctionnalités

- Analyse énergétique du code
- Détection de dépendances obsolètes
- Suggestions d'optimisation automatiques
- Métriques CO2 et coût énergétique
- Intégration GitHub seamless

## Hackathon Mistral MCP 2024

Projet développé pour le hackathon Mistral AI MCP - Focus sur l'impact environnemental du développement logiciel.

## Exemple technique

Utilisateur dans Le Chat: "Analyse mon repo https://github.com/user/project"

↓

Le Chat (GitHub déjà connecté) → HTTP → votre serveur MCP exposé via ngrok

↓

@mcp.tool analyze_repository(repo_url)
   ├── SonarQubeClient.trigger_analysis() 
   ├── DependencyTrackClient.analyze_repository()
   └── Retourne analysis_id = "eco_20240913_143022"

↓

"Calcule les métriques énergétiques"

↓

@mcp.tool get_energy_metrics(analysis_id)
   └── Retourne {"energy_score": 72.3, "co2_estimate_kg": 2.77, "cost_estimate_eur": 69.25}

↓

"Propose des optimisations"

↓

@mcp.tool suggest_optimizations(analysis_id)
   └── Le Chat/Mistral traite le contexte → suggestions intelligentes