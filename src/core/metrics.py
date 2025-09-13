from datetime import datetime

class EnergyMetrics:
    async def calculate_energy_score(self, complexity: int, code_smells: int, outdated_deps: int) -> float:
        """Calcul score énergétique (0-100)"""
        # Algorithme de scoring énergétique
        base_score = 100
        complexity_penalty = min(complexity * 2, 40)
        smells_penalty = min(code_smells * 1.5, 30)
        deps_penalty = min(outdated_deps * 3, 30)
        
        return max(0, base_score - complexity_penalty - smells_penalty - deps_penalty)
    
    async def estimate_co2_impact(self, energy_score: float) -> float:
        """Estimation CO2 en kg/an"""
        # Modèle simplifié: plus le score est bas, plus l'impact CO2 est élevé
        return (100 - energy_score) * 0.1
    
    async def calculate_cost_impact(self, energy_score: float) -> float:
        """Estimation coût énergétique en €/an"""
        return (100 - energy_score) * 2.5