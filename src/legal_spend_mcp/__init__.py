"""
Legal Spend MCP Server

A Model Context Protocol server for legal spend intelligence across multiple data sources[cite: 381].
"""

__version__ = "0.1.0"
__author__ = "DatSciX"

from .server import mcp
from .models import LegalSpendRecord, SpendSummary
from .data_sources import DataSourceManager
from .config import load_config

__all__ = [
    "mcp",
    "LegalSpendRecord", 
    "SpendSummary",
    "DataSourceManager",
    "load_config"
]