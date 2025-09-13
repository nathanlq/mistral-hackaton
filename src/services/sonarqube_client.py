import httpx
import os

class SonarQubeClient:
    def __init__(self):
        self.base_url = os.getenv("SONARQUBE_URL")
        self.token = os.getenv("SONARQUBE_TOKEN")
        
    async def trigger_analysis(self, repo_url: str):
        """Lance analyse SonarQube"""
        pass
    
    async def get_quality_metrics(self, analysis_id: str):
        """Récupère métriques qualité"""
        pass