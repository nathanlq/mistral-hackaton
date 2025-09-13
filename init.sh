#!/bin/bash

# Création de la structure du projet MCP EcoOptimizer
mkdir -p eco-optimizer-mcp
cd eco-optimizer-mcp

# Structure des dossiers
mkdir -p src/{core,services,models,utils}
mkdir -p tests/{unit,integration}
mkdir -p docs
mkdir -p config

# Fichiers de configuration
touch requirements.txt
touch pyproject.toml
touch .env.example
touch .gitignore

# Fichiers source principaux
touch src/__init__.py
touch src/main.py
touch src/server.py

# Core MCP
touch src/core/__init__.py
touch src/core/mcp_handler.py
touch src/core/optimizer.py
touch src/core/metrics.py

# Services externes
touch src/services/__init__.py
touch src/services/github_client.py
touch src/services/sonarqube_client.py
touch src/services/dependency_track_client.py
touch src/services/search_client.py

# Modèles de données
touch src/models/__init__.py
touch src/models/analysis.py
touch src/models/optimization.py

# Utilitaires
touch src/utils/__init__.py
touch src/utils/logger.py
touch src/utils/config.py

# Tests
touch tests/__init__.py
touch tests/unit/test_core.py
touch tests/integration/test_services.py

# Documentation
touch docs/API.md
touch docs/SETUP.md

echo "Structure du projet créée avec succès!"
echo "Projet: eco-optimizer-mcp"