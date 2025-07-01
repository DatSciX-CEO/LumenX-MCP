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

    # SimpleLegal API configuration
    if os.getenv("SIMPLELEGAL_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="simplelegal",
            type="api",
            enabled=True,
            connection_params={
                "api_key": os.getenv("SIMPLELEGAL_API_KEY"),
                "base_url": os.getenv("SIMPLELEGAL_BASE_URL", "https://api.simplelegal.com"),
            }
        ))

    # Brightflag API configuration
    if os.getenv("BRIGHTFLAG_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="brightflag",
            type="api",
            enabled=True,
            connection_params={
                "api_key": os.getenv("BRIGHTFLAG_API_KEY"),
                "base_url": os.getenv("BRIGHTFLAG_BASE_URL", "https://api.brightflag.com"),
            }
        ))

    # TyMetrix 360 API configuration
    if os.getenv("TYMETRIX_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="tymetrix",
            type="api",
            enabled=True,
            connection_params={
                "client_id": os.getenv("TYMETRIX_CLIENT_ID"),
                "client_secret": os.getenv("TYMETRIX_CLIENT_SECRET"),
                "base_url": os.getenv("TYMETRIX_BASE_URL", "https://api.tymetrix.com"),
            }
        ))

    # Onit API configuration
    if os.getenv("ONIT_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="onit",
            type="api",
            enabled=True,
            connection_params={
                "api_key": os.getenv("ONIT_API_KEY"),
                "base_url": os.getenv("ONIT_BASE_URL"), # No default, must be provided
            }
        ))

    # Microsoft Dynamics 365 configuration
    if os.getenv("DYNAMICS365_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="dynamics365",
            type="api",
            enabled=True,
            connection_params={
                "client_id": os.getenv("DYNAMICS365_CLIENT_ID"),
                "client_secret": os.getenv("DYNAMICS365_CLIENT_SECRET"),
                "tenant_id": os.getenv("DYNAMICS365_TENANT_ID"),
                "resource": os.getenv("DYNAMICS365_RESOURCE"), # Customer-specific API endpoint
            }
        ))

    # NetSuite configuration
    if os.getenv("NETSUITE_ENABLED", "false").lower() == "true":
        config["data_sources"].append(DataSourceConfig(
            name="netsuite",
            type="api",
            enabled=True,
            connection_params={
                "account_id": os.getenv("NETSUITE_ACCOUNT_ID"),
                "consumer_key": os.getenv("NETSUITE_CONSUMER_KEY"),
                "consumer_secret": os.getenv("NETSUITE_CONSUMER_SECRET"),
                "token_id": os.getenv("NETSUITE_TOKEN_ID"),
                "token_secret": os.getenv("NETSUITE_TOKEN_SECRET"),
                "base_url": os.getenv("NETSUITE_BASE_URL"), # e.g., https://<account_id>.suitetalk.api.netsuite.com
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
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30

class OAuth2ClientCredentialsConfig(BaseModel):
    base_url: str
    client_id: str
    client_secret: str

class Dynamics365Config(OAuth2ClientCredentialsConfig):
    tenant_id: str
    resource: str

class NetSuiteConfig(BaseModel):
    account_id: str
    consumer_key: str
    consumer_secret: str
    token_id: str
    token_secret: str
    base_url: Optional[str] # Optional, can be derived from account_id

def load_validated_config() -> Dict[str, Any]:
    try:
        config = load_config()
        # Validate each data source config
        for source in config.get("data_sources", []):
            if source.type == "database":
                DatabaseConfig(**source.connection_params)
            elif source.type == "api":
                if source.name == "tymetrix":
                    OAuth2ClientCredentialsConfig(**source.connection_params)
                elif source.name == "dynamics365":
                    Dynamics365Config(**source.connection_params)
                elif source.name == "netsuite":
                    NetSuiteConfig(**source.connection_params)
                else:
                    APIConfig(**source.connection_params)
        return config
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed: {e}")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during configuration loading: {e}")
