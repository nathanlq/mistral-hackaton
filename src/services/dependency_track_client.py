class DependencyTrackClient:
    def __init__(self):
        self.base_url = None
        self.api_key = None
        
    async def upload_bom(self, project_uuid: str, bom_content: str):
        """Upload d'un SBOM pour analyse"""
        pass
    
    async def get_vulnerabilities(self, project_uuid: str):
        """Récupère les vulnérabilités"""
        pass
    
    async def get_outdated_dependencies(self, project_uuid: str):
        """Récupère les dépendances obsolètes"""
        pass