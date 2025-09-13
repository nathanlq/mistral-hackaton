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

### Analyse de repo

Utilisateur dans Le Chat: "Analyse mon repo https://github.com/user/project pour l'optimisation énergétique"

↓

Le Chat → WebSocket /mcp → handle_mcp_request()
   method: "tools/call"
   tool: "analyze_repository" 
   args: {repo_url: "https://github.com/user/project"}

↓

EcoOptimizerHandler.analyze_repository(repo_url)
   ├── GitHubClient.get_repository_info(repo_url)
   ├── GitHubClient.get_source_files(repo_url, [".py", ".js"])
   ├── SonarQubeClient.trigger_analysis(project_key)
   ├── DependencyTrackClient.upload_bom(project_uuid, bom)
   └── CodeOptimizer.analyze_complexity(source_files)

↓

Génère analysis_id = "eco_analysis_12345"
   Stocke: {files, metrics, sonar_data, deps_data}

↓

Retour Le Chat: "Analyse terminée. ID: eco_analysis_12345
   - 45 fichiers Python analysés
   - Complexité moyenne: 8.3
   - 12 dépendances obsolètes détectées"


### Proposition d'optimisation

Utilisateur: "Propose des optimisations pour cette analyse"

↓

Le Chat → tools/call → "suggest_optimizations"
   args: {analysis_id: "eco_analysis_12345"}

↓

EcoOptimizerHandler.suggest_optimizations(analysis_id)
   ├── Récupère les données stockées (files, metrics)
   ├── EnergyMetrics.calculate_energy_score(complexity, deps)
   ├── SearchClient.search_energy_practices("python", "optimization")
   └── Appel API Mistral avec prompt enrichi:
       "Code: {...}, Métriques: {...}, Bonnes pratiques: {...}
        Propose 3 optimisations énergétiques concrètes"

↓

Retour Le Chat: 
   "Optimisations énergétiques suggérées:
   
   1. **Remplacer les boucles nested** (ligne 45-67)
      → List comprehension → -23% CPU
   
   2. **Éliminer pandas pour les petits datasets** 
      → Native Python → -40% mémoire
      
   3. **Upgrader requests → httpx**
      → HTTP/2 async → -15% réseau"