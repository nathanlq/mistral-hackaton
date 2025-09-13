#!/bin/bash

# EcoCode Optimizer - Setup script
echo "🌱 Setting up EcoCode Optimizer repository..."

# Create main directories
mkdir -p src/ecocode_optimizer
mkdir -p src/analyzers
mkdir -p src/metrics
mkdir -p tests
mkdir -p docs
mkdir -p examples

# Create main source files
touch src/ecocode_optimizer/__init__.py
touch src/ecocode_optimizer/server.py
touch src/ecocode_optimizer/github_client.py
touch src/ecocode_optimizer/optimizer.py

# Create analyzer modules
touch src/analyzers/__init__.py
touch src/analyzers/python_analyzer.py
touch src/analyzers/javascript_analyzer.py
touch src/analyzers/base_analyzer.py

# Create metrics modules
touch src/metrics/__init__.py
touch src/metrics/energy_calculator.py
touch src/metrics/co2_estimator.py
touch src/metrics/performance_metrics.py

# Create test files
touch tests/__init__.py
touch tests/test_analyzers.py
touch tests/test_metrics.py
touch tests/test_server.py

# Create config and setup files
touch requirements.txt
touch setup.py
touch .env.example
touch .gitignore
touch mcp_config.json

# Create example files
touch examples/sample_repo_analysis.py
touch examples/optimization_report.json

echo "✅ Repository structure created!"
echo "📁 Structure:"
tree . -I '__pycache__'