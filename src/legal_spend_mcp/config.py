import os
from typing import Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class DataSourceConfig:
    """Configuration for a data source following MCP patterns"""
    name: str
    type: str  # 'api', 'database', 'file'
    enabled: bool
    connection_params: Dict[str, Any]
    
def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables (Official MCP pattern)"""
    
    # Load environment variables
    load_dotenv()
    
    config = {
        "server": {
            "name": os.getenv("MCP_SERVER_NAME", "Legal Spend Intelligence"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        },
        "data_sources": []
    } [cite: 316]
    
    # LegalTracker API configuration
    if os.getenv("LEGALTRACKER_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="legaltracker",
            type="api",
            enabled=True,
            connection_params={
                "api_key": os.getenv("LEGALTRACKER_API_KEY"),
                "base_url": os.getenv("LEGALTRACKER_BASE_URL", "https://api.legaltracker.com"), [cite: 317]
                "timeout": int(os.getenv("LEGALTRACKER_TIMEOUT", "30")),
            }
        ))
    
    # SAP ERP configuration
    if os.getenv("SAP_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="sap_erp",
            type="database", [cite: 318]
            enabled=True,
            connection_params={
                "driver": "mssql",
                "host": os.getenv("SAP_HOST"),
                "port": int(os.getenv("SAP_PORT", "1433")),
                "database": os.getenv("SAP_DATABASE"),
                "username": os.getenv("SAP_USER"), [cite: 319]
                "password": os.getenv("SAP_PASSWORD"), [cite: 319]
                "schema": os.getenv("SAP_SCHEMA", "dbo"),
            }
        ))
    
    # Oracle ERP configuration
    if os.getenv("ORACLE_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="oracle_erp", [cite: 320]
            type="database",
            enabled=True,
            connection_params={
                "driver": "oracle",
                "host": os.getenv("ORACLE_HOST"),
                "port": int(os.getenv("ORACLE_PORT", "1521")),
                "service_name": os.getenv("ORACLE_SERVICE"), [cite: 321]
                "username": os.getenv("ORACLE_USER"),
                "password": os.getenv("ORACLE_PASSWORD"),
            }
        ))
    
    # PostgreSQL configuration
    if os.getenv("POSTGRES_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="postgres_legal", [cite: 322]
            type="database", 
            enabled=True,
            connection_params={
                "driver": "postgresql",
                "host": os.getenv("POSTGRES_HOST"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DB"), [cite: 323]
                "username": os.getenv("POSTGRES_USER"),
                "password": os.getenv("POSTGRES_PASSWORD"),
            }
        ))
    
    # CSV file configuration
    if os.getenv("CSV_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="csv_import", [cite: 324]
            type="file",
            enabled=True,
            connection_params={
                "file_type": "csv",
                "file_path": os.getenv("CSV_FILE_PATH"),
                "encoding": os.getenv("CSV_ENCODING", "utf-8"),
                "delimiter": os.getenv("CSV_DELIMITER", ","), [cite: 325]
            }
        ))
    
    # Excel file configuration
    if os.getenv("EXCEL_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="excel_import",
            type="file", 
            enabled=True,
            connection_params={ [cite: 326]
                "file_type": "excel",
                "file_path": os.getenv("EXCEL_FILE_PATH"),
                "sheet_name": os.getenv("EXCEL_SHEET_NAME", "Sheet1"),
            }
        ))
    
    return config