class GitHubClient:
    def __init__(self):
        self.token = None  # À charger depuis config
        
    async def get_repository_info(self, repo_url: str):
        """Récupère les infos du repository"""
        pass
    
    async def get_source_files(self, repo_url: str, extensions: list):
        """Récupère les fichiers source"""
        pass
    
    async def analyze_commits(self, repo_url: str, limit: int = 100):
        """Analyse l'historique des commits"""
        pass