from fastapi import FastAPI, WebSocket
from typing import Dict, Any
import json
from src.core.mcp_handler import EcoOptimizerHandler

app = FastAPI(title="EcoOptimizer MCP Server")