class SonarQubeClient:
    def __init__(self):
        self.base_url = None
        self.token = None
        
    async def trigger_analysis(self, project_key: str):
        """Lance une analyse SonarQube"""
        pass
    
    async def get_quality_metrics(self, project_key: str):
        """Récupère les métriques de qualité"""
        pass
    
    async def get_code_smells(self, project_key: str):
        """Récupère les code smells"""
        pass