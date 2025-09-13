"""
Service de calcul d'impact carbone pour code Python
"""
import tempfile
import subprocess
import json
from pathlib import Path
from codecarbon import EmissionsTracker
import ast
import requests


async def analyze_carbon_impact(code: str, filename: str = "analysis.py") -> dict:
    """Analyse l'impact carbone d'un code Python"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        file_path = temp_path / filename
        file_path.write_text(code)
        
        runner_script = f"""
from codecarbon import EmissionsTracker
import sys
sys.path.append('{temp_path}')

tracker = EmissionsTracker(
    project_name="code_analysis",
    output_dir="{temp_path}",
    save_to_file=True,
    log_level="ERROR"
)

tracker.start()
try:
    exec(open('{file_path}').read())
except Exception as e:
    print(f"Execution error: {{e}}")
finally:
    emissions = tracker.stop()
    print(f"CARBON_RESULT:{{emissions}}")
"""
        
        runner_path = temp_path / "runner.py"
        runner_path.write_text(runner_script)
        
        result = subprocess.run([
            "python", str(runner_path)
        ], capture_output=True, text=True, timeout=600)
        
        emissions_file = temp_path / "emissions.csv"
        carbon_data = {"emissions_kg": 0, "energy_kwh": 0, "duration_s": 0}
        
        if emissions_file.exists():
            import pandas as pd
            df = pd.read_csv(emissions_file)
            if not df.empty:
                row = df.iloc[-1]
                carbon_data = {
                    "emissions_kg": float(row.get("emissions", 0)),
                    "energy_kwh": float(row.get("energy_consumed", 0)),
                    "duration_s": float(row.get("duration", 0)),
                    "cpu_energy": float(row.get("cpu_energy", 0)),
                    "ram_energy": float(row.get("ram_energy", 0))
                }
        
        complexity_score = analyze_code_complexity(code)
        
        return {
            "filename": filename,
            "carbon_impact": carbon_data,
            "complexity_analysis": complexity_score,
            "execution_output": result.stdout,
            "recommendations": generate_carbon_recommendations(complexity_score, carbon_data)
        }


def analyze_code_complexity(code: str) -> dict:
    """Analyse statique de la complexité du code"""
    try:
        tree = ast.parse(code)
        
        loops = 0
        nested_loops = 0
        recursions = 0
        
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.loop_depth = 0
                self.max_depth = 0
                
            def visit_For(self, node):
                nonlocal loops, nested_loops
                loops += 1
                self.loop_depth += 1
                self.max_depth = max(self.max_depth, self.loop_depth)
                if self.loop_depth > 1:
                    nested_loops += 1
                self.generic_visit(node)
                self.loop_depth -= 1
                
            def visit_While(self, node):
                nonlocal loops, nested_loops
                loops += 1
                self.loop_depth += 1
                self.max_depth = max(self.max_depth, self.loop_depth)
                if self.loop_depth > 1:
                    nested_loops += 1
                self.generic_visit(node)
                self.loop_depth -= 1
                
            def visit_FunctionDef(self, node):
                nonlocal recursions
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                        if child.func.id == node.name:
                            recursions += 1
                self.generic_visit(node)
        
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        return {
            "total_loops": loops,
            "nested_loops": nested_loops,
            "max_nesting_depth": visitor.max_depth,
            "recursive_functions": recursions,
            "complexity_score": loops + (nested_loops * 2) + (recursions * 1.5)
        }
        
    except Exception:
        return {"complexity_score": 0, "error": "Parse failed"}


def generate_carbon_recommendations(complexity: dict, carbon: dict) -> list:
    """Génère des recommandations d'optimisation"""
    recommendations = []
    
    if complexity.get("nested_loops", 0) > 0:
        recommendations.append({
            "type": "HIGH",
            "message": f"{complexity['nested_loops']} boucles imbriquées détectées - considérez vectorisation ou algorithmes plus efficaces",
            "impact": "Réduction potentielle de 20-80% de la consommation"
        })
    
    if complexity.get("complexity_score", 0) > 10:
        recommendations.append({
            "type": "MEDIUM", 
            "message": "Code complexe - profiling recommandé",
            "impact": "Optimisation ciblée possible"
        })
        
    if carbon.get("energy_kwh", 0) > 0.001:
        recommendations.append({
            "type": "MEDIUM",
            "message": "Consommation énergétique élevée détectée",
            "impact": f"Émissions: {carbon['emissions_kg']:.6f} kg CO2"
        })
    
    return recommendations


async def analyze_github_carbon(repo_url: str) -> dict:
    """Analyse l'impact carbone d'un repo GitHub"""
    import git
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "repo"
        git.Repo.clone_from(repo_url, repo_path)
        
        py_files = list(repo_path.rglob("*.py"))
        
        results = []
        total_carbon = {"emissions_kg": 0, "energy_kwh": 0}
        
        for py_file in py_files[:5]:
            if py_file.stat().st_size > 1000000:
                continue
                
            code = py_file.read_text(encoding='utf-8', errors='ignore')
            result = await analyze_carbon_impact(code, py_file.name)
            results.append(result)
            
            carbon_data = result["carbon_impact"]
            total_carbon["emissions_kg"] += carbon_data.get("emissions_kg", 0)
            total_carbon["energy_kwh"] += carbon_data.get("energy_kwh", 0)
        
        return {
            "repo_url": repo_url,
            "total_carbon_impact": total_carbon,
            "file_analyses": results,
            "summary": f"Analysé {len(results)} fichiers Python"
        }
    
"""
Service de calcul d'impact carbone pour code Python
"""
import tempfile
import subprocess
import json
from pathlib import Path
from codecarbon import EmissionsTracker
import ast
import requests


async def analyze_carbon_impact(code: str, filename: str = "analysis.py") -> dict:
    """Analyse l'impact carbone d'un code Python"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        file_path = temp_path / filename
        file_path.write_text(code)
        
        runner_script = f"""
from codecarbon import EmissionsTracker
import sys
sys.path.append('{temp_path}')

tracker = EmissionsTracker(
    project_name="code_analysis",
    output_dir="{temp_path}",
    save_to_file=True,
    log_level="ERROR"
)

tracker.start()
try:
    exec(open('{file_path}').read())
except Exception as e:
    print(f"Execution error: {{e}}")
finally:
    emissions = tracker.stop()
    print(f"CARBON_RESULT:{{emissions}}")
"""
        
        runner_path = temp_path / "runner.py"
        runner_path.write_text(runner_script)
        
        result = subprocess.run([
            "python", str(runner_path)
        ], capture_output=True, text=True, timeout=600)
        
        emissions_file = temp_path / "emissions.csv"
        carbon_data = {"emissions_kg": 0, "energy_kwh": 0, "duration_s": 0}
        
        if emissions_file.exists():
            import pandas as pd
            df = pd.read_csv(emissions_file)
            if not df.empty:
                row = df.iloc[-1]
                carbon_data = {
                    "emissions_kg": float(row.get("emissions", 0)),
                    "energy_kwh": float(row.get("energy_consumed", 0)),
                    "duration_s": float(row.get("duration", 0)),
                    "cpu_energy": float(row.get("cpu_energy", 0)),
                    "ram_energy": float(row.get("ram_energy", 0))
                }
        
        complexity_score = analyze_code_complexity(code)
        
        return {
            "filename": filename,
            "carbon_impact": carbon_data,
            "complexity_analysis": complexity_score,
            "execution_output": result.stdout,
            "recommendations": generate_carbon_recommendations(complexity_score, carbon_data)
        }


def analyze_code_complexity(code: str) -> dict:
    """Analyse statique de la complexité du code"""
    try:
        tree = ast.parse(code)
        
        loops = 0
        nested_loops = 0
        recursions = 0
        
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.loop_depth = 0
                self.max_depth = 0
                
            def visit_For(self, node):
                nonlocal loops, nested_loops
                loops += 1
                self.loop_depth += 1
                self.max_depth = max(self.max_depth, self.loop_depth)
                if self.loop_depth > 1:
                    nested_loops += 1
                self.generic_visit(node)
                self.loop_depth -= 1
                
            def visit_While(self, node):
                nonlocal loops, nested_loops
                loops += 1
                self.loop_depth += 1
                self.max_depth = max(self.max_depth, self.loop_depth)
                if self.loop_depth > 1:
                    nested_loops += 1
                self.generic_visit(node)
                self.loop_depth -= 1
                
            def visit_FunctionDef(self, node):
                nonlocal recursions
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                        if child.func.id == node.name:
                            recursions += 1
                self.generic_visit(node)
        
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        return {
            "total_loops": loops,
            "nested_loops": nested_loops,
            "max_nesting_depth": visitor.max_depth,
            "recursive_functions": recursions,
            "complexity_score": loops + (nested_loops * 2) + (recursions * 1.5)
        }
        
    except Exception:
        return {"complexity_score": 0, "error": "Parse failed"}


def generate_carbon_recommendations(complexity: dict, carbon: dict) -> list:
    """Génère des recommandations d'optimisation"""
    recommendations = []
    
    if complexity.get("nested_loops", 0) > 0:
        recommendations.append({
            "type": "HIGH",
            "message": f"{complexity['nested_loops']} boucles imbriquées détectées - considérez vectorisation ou algorithmes plus efficaces",
            "impact": "Réduction potentielle de 20-80% de la consommation"
        })
    
    if complexity.get("complexity_score", 0) > 10:
        recommendations.append({
            "type": "MEDIUM", 
            "message": "Code complexe - profiling recommandé",
            "impact": "Optimisation ciblée possible"
        })
        
    if carbon.get("energy_kwh", 0) > 0.001:
        recommendations.append({
            "type": "MEDIUM",
            "message": "Consommation énergétique élevée détectée",
            "impact": f"Émissions: {carbon['emissions_kg']:.6f} kg CO2"
        })
    
    return recommendations


async def analyze_github_carbon(repo_url: str) -> dict:
    """Analyse l'impact carbone d'un repo GitHub"""
    import git
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "repo"
        git.Repo.clone_from(repo_url, repo_path)
        
        py_files = list(repo_path.rglob("*.py"))
        
        results = []
        total_carbon = {"emissions_kg": 0, "energy_kwh": 0}
        
        for py_file in py_files[:5]:
            if py_file.stat().st_size > 1000000:
                continue
                
            code = py_file.read_text(encoding='utf-8', errors='ignore')
            result = await analyze_carbon_impact(code, py_file.name)
            results.append(result)
            
            carbon_data = result["carbon_impact"]
            total_carbon["emissions_kg"] += carbon_data.get("emissions_kg", 0)
            total_carbon["energy_kwh"] += carbon_data.get("energy_kwh", 0)
        
        return {
            "repo_url": repo_url,
            "total_carbon_impact": total_carbon,
            "file_analyses": results,
            "summary": f"Analysé {len(results)} fichiers Python"
        }


# === MAIN DE TEST ===
async def main():
    """Test du service carbon analyzer"""
    
    # Code de test inefficace
    test_code = """
def inefficient_sorting():
    # Bubble sort - O(n²)
    data = list(range(1000, 0, -1))
    n = len(data)
    for i in range(n):
        for j in range(0, n-i-1):
            if data[j] > data[j+1]:
                data[j], data[j+1] = data[j+1], data[j]
    return data

def nested_loops_example():
    # Boucles imbriquées inutiles
    result = []
    for i in range(100):
        temp = []
        for j in range(100):
            for k in range(10):
                temp.append(i * j * k)
        result.extend(temp)
    return result

def recursive_fibonacci(n):
    # Fibonacci récursif - très inefficace
    if n <= 1:
        return n
    return recursive_fibonacci(n-1) + recursive_fibonacci(n-2)

# Exécution des fonctions
if __name__ == "__main__":
    data = inefficient_sorting()
    nested_result = nested_loops_example()
    fib = recursive_fibonacci(20)
    print(f"Completed - sorted: {len(data)}, nested: {len(nested_result)}, fib: {fib}")
"""
    
    print("🔬 Test analyse carbone - Code inefficace")
    print("=" * 50)
    
    try:
        # Test analyse carbone
        result = await analyze_carbon_impact(test_code, "test_inefficient.py")
        
        print(f"📁 Fichier: {result['filename']}")
        print(f"⚡ Émissions CO2: {result['carbon_impact']['emissions_kg']:.6f} kg")
        print(f"🔋 Énergie: {result['carbon_impact']['energy_kwh']:.6f} kWh")
        print(f"⏱️  Durée: {result['carbon_impact']['duration_s']:.2f}s")
        
        complexity = result['complexity_analysis']
        print(f"\n📊 Analyse complexité:")
        print(f"   - Boucles: {complexity.get('total_loops', 0)}")
        print(f"   - Boucles imbriquées: {complexity.get('nested_loops', 0)}")
        print(f"   - Profondeur max: {complexity.get('max_nesting_depth', 0)}")
        print(f"   - Récursions: {complexity.get('recursive_functions', 0)}")
        print(f"   - Score complexité: {complexity.get('complexity_score', 0):.1f}")
        
        print(f"\n💡 Recommandations ({len(result['recommendations'])}):")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"   {i}. [{rec['type']}] {rec['message']}")
            print(f"      Impact: {rec['impact']}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Test terminé")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())