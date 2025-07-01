import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, validator

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
    }
    
    # LegalTracker API configuration
    if os.getenv("LEGALTRACKER_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="legaltracker",
            type="api",
            enabled=True,
            connection_params={
                "api_key": os.getenv("LEGALTRACKER_API_KEY"),
                "base_url": os.getenv("LEGALTRACKER_BASE_URL", "https://api.legaltracker.com"),
                "timeout": int(os.getenv("LEGALTRACKER_TIMEOUT", "30")),
            }
        ))
    
    # SAP ERP configuration
    if os.getenv("SAP_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="sap_erp",
            type="database",
            enabled=True,
            connection_params={
                "driver": "mssql",
                "host": os.getenv("SAP_HOST"),
                "port": int(os.getenv("SAP_PORT", "1433")),
                "database": os.getenv("SAP_DATABASE"),
                "username": os.getenv("SAP_USER"),
                "password": os.getenv("SAP_PASSWORD"),
                "schema": os.getenv("SAP_SCHEMA", "dbo"),
            }
        ))
    
    # Oracle ERP configuration
    if os.getenv("ORACLE_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="oracle_erp",
            type="database",
            enabled=True,
            connection_params={
                "driver": "oracle",
                "host": os.getenv("ORACLE_HOST"),
                "port": int(os.getenv("ORACLE_PORT", "1521")),
                "service_name": os.getenv("ORACLE_SERVICE"),
                "username": os.getenv("ORACLE_USER"),
                "password": os.getenv("ORACLE_PASSWORD"),
            }
        ))
    
    # PostgreSQL configuration
    if os.getenv("POSTGRES_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="postgres_legal",
            type="database", 
            enabled=True,
            connection_params={
                "driver": "postgresql",
                "host": os.getenv("POSTGRES_HOST"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DB"),
                "username": os.getenv("POSTGRES_USER"),
                "password": os.getenv("POSTGRES_PASSWORD"),
            }
        ))
    
    # CSV file configuration
    if os.getenv("CSV_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="csv_import",
            type="file",
            enabled=True,
            connection_params={
                "file_type": "csv",
                "file_path": os.getenv("CSV_FILE_PATH"),
                "encoding": os.getenv("CSV_ENCODING", "utf-8"),
                "delimiter": os.getenv("CSV_DELIMITER", ","),
            }
        ))
    
    # Excel file configuration
    if os.getenv("EXCEL_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="excel_import",
            type="file", 
            enabled=True,
            connection_params={
                "file_type": "excel",
                "file_path": os.getenv("EXCEL_FILE_PATH"),
                "sheet_name": os.getenv("EXCEL_SHEET_NAME", "Sheet1"),
            }
        ))
    
    return config

class DatabaseConfig(BaseModel):
    driver: str
    host: str
    port: int
    database: str
    username: str
    password: str
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('driver')
    def validate_driver(cls, v):
        allowed_drivers = ['postgresql', 'mssql', 'oracle']
        if v not in allowed_drivers:
            raise ValueError(f'Driver must be one of {allowed_drivers}')
        return v

class APIConfig(BaseModel):
    api_key: str
    base_url: str
    timeout: int = 30
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if len(v) < 10:
            raise ValueError('API key too short')
        return v

def load_validated_config() -> Dict[str, Any]:
    try:
        config = load_config()
        # Validate each data source config
        for source in config.get("data_sources", []):
            if source.type == "database":
                DatabaseConfig(**source.connection_params)
            elif source.type == "api":
                APIConfig(**source.connection_params)
        return config
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed: {e}")
