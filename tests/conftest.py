import pytest
from datetime import date
from decimal import Decimal
import os
from unittest.mock import patch

from legal_spend_mcp.models import (
    VendorType,
    PracticeArea,
    LegalSpendRecord,
    SpendSummary,
    VendorPerformance
)
from legal_spend_mcp.config import DataSourceConfig, load_config


class TestEnums:
    """Test enumeration classes"""
    
    def test_vendor_type_enum(self):
        """Test VendorType enum values"""
        assert VendorType.LAW_FIRM == "Law Firm"
        assert VendorType.CONSULTANT == "Consultant"
        assert VendorType.EXPERT_WITNESS == "Expert Witness"
        assert VendorType.COURT_REPORTER == "Court Reporter"
        assert VendorType.OTHER == "Other"
    
    def test_practice_area_enum(self):
        """Test PracticeArea enum values"""
        assert PracticeArea.LITIGATION == "Litigation"
        assert PracticeArea.CORPORATE == "Corporate"
        assert PracticeArea.EMPLOYMENT == "Employment"
        assert PracticeArea.INTELLECTUAL_PROPERTY == "Intellectual Property"
        assert PracticeArea.REGULATORY == "Regulatory"
        assert PracticeArea.REAL_ESTATE == "Real Estate"
        assert PracticeArea.TAX == "Tax"
        assert PracticeArea.GENERAL == "General"


class TestLegalSpendRecord:
    """Test LegalSpendRecord model"""
    
    def test_create_legal_spend_record(self):
        """Test creating a legal spend record"""
        record = LegalSpendRecord(
            invoice_id="INV-001",
            vendor_name="Test Law Firm",
            vendor_type=VendorType.LAW_FIRM,
            matter_id="MATT-001",
            matter_name="Test Matter",
            department="Legal",
            practice_area=PracticeArea.CORPORATE,
            invoice_date=date(2024, 1, 15),
            amount=Decimal("10000.00"),
            currency="USD",
            expense_category="Legal Services",
            description="Corporate legal services"
        )
        
        assert record.invoice_id == "INV-001"
        assert record.vendor_name == "Test Law Firm"
        assert record.vendor_type == VendorType.LAW_FIRM
        assert record.amount == Decimal("10000.00")
        assert record.status == "approved"  # Default value
    
    def test_optional_fields(self):
        """Test optional fields with None values"""
        record = LegalSpendRecord(
            invoice_id="INV-002",
            vendor_name="Test Vendor",
            vendor_type=VendorType.LAW_FIRM,
            matter_id=None,
            matter_name=None,
            department="Legal",
            practice_area=PracticeArea.GENERAL,
            invoice_date=date(2024, 1, 15),
            amount=Decimal("5000.00"),
            currency="USD",
            expense_category="Legal Services",
            description="General legal services"
        )
        
        assert record.matter_id is None
        assert record.matter_name is None
        assert record.billing_period_start is None
        assert record.billing_period_end is None
        assert record.budget_code is None
        assert record.source_system is None


class TestSpendSummary:
    """Test SpendSummary model"""
    
    def test_create_spend_summary(self):
        """Test creating a spend summary"""
        summary = SpendSummary(
            total_amount=Decimal("100000.00"),
            currency="USD",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
            record_count=50,
            top_vendors=[
                {"name": "Vendor 1", "amount": 40000.0},
                {"name": "Vendor 2", "amount": 30000.0}
            ],
            top_matters=[
                {"name": "Matter 1", "amount": 50000.0},
                {"name": "Matter 2", "amount": 25000.0}
            ],
            by_department={
                "Legal": Decimal("80000.00"),
                "Compliance": Decimal("20000.00")
            },
            by_practice_area={
                "Corporate": Decimal("60000.00"),
                "Litigation": Decimal("40000.00")
            }
        )
        
        assert summary.total_amount == Decimal("100000.00")
        assert summary.record_count == 50
        assert len(summary.top_vendors) == 2
        assert summary.by_department["Legal"] == Decimal("80000.00")
    
    def test_empty_spend_summary(self):
        """Test creating an empty spend summary"""
        summary = SpendSummary(
            total_amount=Decimal("0"),
            currency="USD",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
            record_count=0,
            top_vendors=[],
            top_matters=[],
            by_department={},
            by_practice_area={}
        )
        
        assert summary.total_amount == Decimal("0")
        assert summary.record_count == 0
        assert len(summary.top_vendors) == 0
        assert len(summary.by_department) == 0


class TestVendorPerformance:
    """Test VendorPerformance model"""
    
    def test_create_vendor_performance(self):
        """Test creating vendor performance metrics"""
        performance = VendorPerformance(
            vendor_name="Test Law Firm",
            total_spend=Decimal("500000.00"),
            invoice_count=25,
            average_invoice=Decimal("20000.00"),
            matters_count=10,
            performance_score=0.85,
            trend="increasing"
        )
        
        assert performance.vendor_name == "Test Law Firm"
        assert performance.total_spend == Decimal("500000.00")
        assert performance.invoice_count == 25
        assert performance.average_invoice == Decimal("20000.00")
        assert performance.performance_score == 0.85
        assert performance.trend == "increasing"


class TestDataSourceConfig:
    """Test DataSourceConfig model"""
    
    def test_create_data_source_config(self):
        """Test creating data source configuration"""
        config = DataSourceConfig(
            name="test_source",
            type="api",
            enabled=True,
            connection_params={
                "api_key": "test_key",
                "base_url": "https://api.test.com"
            }
        )
        
        assert config.name == "test_source"
        assert config.type == "api"
        assert config.enabled is True
        assert config.connection_params["api_key"] == "test_key"
    
    def test_disabled_data_source(self):
        """Test disabled data source configuration"""
        config = DataSourceConfig(
            name="disabled_source",
            type="database",
            enabled=False,
            connection_params={}
        )
        
        assert config.enabled is False


class TestConfigLoading:
    """Test configuration loading"""
    
    def test_load_config_defaults(self):
        """Test loading configuration with defaults"""
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()
            
            assert config["server"]["name"] == "Legal Spend Intelligence"
            assert config["server"]["log_level"] == "INFO"
            assert len(config["data_sources"]) == 0
    
    def test_load_config_with_legaltracker(self):
        """Test loading configuration with LegalTracker enabled"""
        env_vars = {
            "LEGALTRACKER_ENABLED": "true",
            "LEGALTRACKER_API_KEY": "test_api_key",
            "LEGALTRACKER_BASE_URL": "https://test.legaltracker.com",
            "LEGALTRACKER_TIMEOUT": "60"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert len(config["data_sources"]) == 1
            source = config["data_sources"][0]
            assert source.name == "legaltracker"
            assert source.type == "api"
            assert source.enabled is True
            assert source.connection_params["api_key"] == "test_api_key"
            assert source.connection_params["base_url"] == "https://test.legaltracker.com"
            assert source.connection_params["timeout"] == 60
    
    def test_load_config_with_database(self):
        """Test loading configuration with database sources"""
        env_vars = {
            "SAP_ENABLED": "true",
            "SAP_HOST": "sap.example.com",
            "SAP_PORT": "1433",
            "SAP_DATABASE": "LEGAL_DB",
            "SAP_USER": "sap_user",
            "SAP_PASSWORD": "sap_pass",
            "SAP_SCHEMA": "legal"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert len(config["data_sources"]) == 1
            source = config["data_sources"][0]
            assert source.name == "sap_erp"
            assert source.type == "database"
            assert source.connection_params["driver"] == "mssql"
            assert source.connection_params["host"] == "sap.example.com"
            assert source.connection_params["port"] == 1433
            assert source.connection_params["database"] == "LEGAL_DB"
    
    def test_load_config_with_files(self):
        """Test loading configuration with file sources"""
        env_vars = {
            "CSV_ENABLED": "true",
            "CSV_FILE_PATH": "/data/legal_spend.csv",
            "CSV_ENCODING": "utf-8",
            "CSV_DELIMITER": ";",
            "EXCEL_ENABLED": "true",
            "EXCEL_FILE_PATH": "/data/legal_spend.xlsx",
            "EXCEL_SHEET_NAME": "Spend Data"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert len(config["data_sources"]) == 2
            
            # Check CSV configuration
            csv_source = next(s for s in config["data_sources"] if s.name == "csv_import")
            assert csv_source.type == "file"
            assert csv_source.connection_params["file_type"] == "csv"
            assert csv_source.connection_params["file_path"] == "/data/legal_spend.csv"
            assert csv_source.connection_params["delimiter"] == ";"
            
            # Check Excel configuration
            excel_source = next(s for s in config["data_sources"] if s.name == "excel_import")
            assert excel_source.type == "file"
            assert excel_source.connection_params["file_type"] == "excel"
            assert excel_source.connection_params["sheet_name"] == "Spend Data"
    
    def test_load_config_multiple_sources(self):
        """Test loading configuration with multiple data sources"""
        env_vars = {
            "LEGALTRACKER_ENABLED": "true",
            "LEGALTRACKER_API_KEY": "api_key",
            "POSTGRES_ENABLED": "true",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "legal",
            "POSTGRES_USER": "user",
            "POSTGRES_PASSWORD": "pass",
            "CSV_ENABLED": "true",
            "CSV_FILE_PATH": "/data/spend.csv"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert len(config["data_sources"]) == 3
            source_names = [s.name for s in config["data_sources"]]
            assert "legaltracker" in source_names
            assert "postgres_legal" in source_names
            assert "csv_import" in source_names
    
    def test_load_config_with_custom_server_name(self):
        """Test loading configuration with custom server name"""
        env_vars = {
            "MCP_SERVER_NAME": "Custom Legal Server",
            "LOG_LEVEL": "DEBUG"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert config["server"]["name"] == "Custom Legal Server"
            assert config["server"]["log_level"] == "DEBUG"