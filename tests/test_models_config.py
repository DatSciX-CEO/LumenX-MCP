import pytest
import asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, List
import os
from unittest.mock import Mock, AsyncMock

from legal_spend_mcp.models import LegalSpendRecord, VendorType, PracticeArea
from legal_spend_mcp.config import DataSourceConfig
from legal_spend_mcp.data_sources import DataSourceManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_spend_record():
    """Create a sample legal spend record for testing"""
    return LegalSpendRecord(
        invoice_id="INV-001",
        vendor_name="Smith & Associates",
        vendor_type=VendorType.LAW_FIRM,
        matter_id="MATT-001",
        matter_name="ABC Corp Acquisition",
        department="Legal",
        practice_area=PracticeArea.CORPORATE,
        invoice_date=date(2024, 1, 15),
        amount=Decimal("15000.00"),
        currency="USD",
        expense_category="Legal Services",
        description="Corporate transaction legal services",
        source_system="test"
    )


@pytest.fixture
def sample_spend_records():
    """Create multiple sample records for testing"""
    records = []
    
    # Create diverse test data
    vendors = ["Smith & Associates", "Jones Legal", "Brown Law Firm"]
    departments = ["Legal", "Compliance", "Finance"]
    practice_areas = [PracticeArea.CORPORATE, PracticeArea.LITIGATION, PracticeArea.EMPLOYMENT]
    
    for i in range(10):
        records.append(LegalSpendRecord(
            invoice_id=f"INV-{i:03d}",
            vendor_name=vendors[i % len(vendors)],
            vendor_type=VendorType.LAW_FIRM,
            matter_id=f"MATT-{i:03d}",
            matter_name=f"Matter {i}",
            department=departments[i % len(departments)],
            practice_area=practice_areas[i % len(practice_areas)],
            invoice_date=date(2024, 1 + (i % 3), 1 + (i % 28)),
            amount=Decimal(str(10000 + i * 1000)),
            currency="USD",
            expense_category="Legal Services",
            description=f"Legal services for matter {i}",
            source_system="test"
        ))
    
    return records


@pytest.fixture
def mock_data_source_config():
    """Create a mock data source configuration"""
    return DataSourceConfig(
        name="test_source",
        type="api",
        enabled=True,
        connection_params={
            "api_key": "test_key",
            "base_url": "https://test.api.com",
            "timeout": 30
        }
    )


@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary"""
    return {
        "server": {
            "name": "Test Legal Spend Server",
            "log_level": "DEBUG"
        },
        "data_sources": [
            DataSourceConfig(
                name="test_api",
                type="api",
                enabled=True,
                connection_params={
                    "api_key": "test_key",
                    "base_url": "https://test.api.com"
                }
            )
        ]
    }


@pytest.fixture
async def mock_data_manager():
    """Create a mock data source manager"""
    manager = DataSourceManager()
    
    # Mock the internal methods
    manager.get_spend_data = AsyncMock()
    manager.get_vendor_data = AsyncMock()
    manager.calculate_spend_trend = AsyncMock()
    manager.get_vendor_benchmarks = AsyncMock()
    manager.get_department_spend = AsyncMock()
    manager.get_monthly_breakdown = AsyncMock()
    manager.generate_budget_recommendations = AsyncMock()
    manager.search_transactions = AsyncMock()
    manager.get_all_vendors = AsyncMock()
    manager.get_sources_status = AsyncMock()
    manager.get_spend_categories = AsyncMock()
    manager.get_spend_overview = AsyncMock()
    manager.generate_summary = AsyncMock()
    manager.get_active_sources = Mock(return_value=["test_source"])
    
    return manager


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client for API testing"""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={
        "invoices": [{
            "id": "INV-001",
            "vendor": {"name": "Test Vendor"},
            "matter": {"id": "MATT-001", "name": "Test Matter"},
            "department": "Legal",
            "practice_area": "Corporate",
            "invoice_date": "2024-01-15",
            "amount": "15000.00",
            "currency": "USD",
            "description": "Test invoice"
        }]
    })
    mock_response.raise_for_status = Mock()
    mock_client.get = AsyncMock(return_value=mock_response)
    
    return mock_client


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file for testing"""
    csv_content = """invoice_id,vendor_name,matter_name,department,practice_area,invoice_date,amount,currency,description
INV-001,Test Vendor,Test Matter,Legal,Corporate,2024-01-15,15000.00,USD,Test invoice
INV-002,Another Vendor,Another Matter,Compliance,Litigation,2024-02-15,25000.00,USD,Another invoice
"""
    
    csv_file = tmp_path / "test_legal_spend.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def temp_excel_file(tmp_path):
    """Create a temporary Excel file for testing"""
    import pandas as pd
    
    data = {
        "invoice_id": ["INV-001", "INV-002"],
        "vendor_name": ["Test Vendor", "Another Vendor"],
        "matter_name": ["Test Matter", "Another Matter"],
        "department": ["Legal", "Compliance"],
        "practice_area": ["Corporate", "Litigation"],
        "invoice_date": ["2024-01-15", "2024-02-15"],
        "amount": [15000.00, 25000.00],
        "currency": ["USD", "USD"],
        "description": ["Test invoice", "Another invoice"]
    }
    
    df = pd.DataFrame(data)
    excel_file = tmp_path / "test_legal_spend.xlsx"
    df.to_excel(excel_file, index=False, sheet_name="Sheet1")
    return str(excel_file)


@pytest.fixture
def mock_database_engine():
    """Create a mock database engine"""
    engine = Mock()
    connection = Mock()
    result = Mock()
    
    # Mock query results
    result.__iter__ = Mock(return_value=iter([
        Mock(
            invoice_id="INV-001",
            vendor_name="Test Vendor",
            vendor_type="Law Firm",
            matter_id="MATT-001",
            matter_name="Test Matter",
            department="Legal",
            practice_area="Corporate",
            invoice_date=date(2024, 1, 15),
            amount=Decimal("15000.00"),
            currency="USD",
            expense_category="Legal Services",
            description="Test invoice",
            billing_period_start=None,
            billing_period_end=None,
            status="approved",
            budget_code=None
        )
    ]))
    
    connection.execute = Mock(return_value=result)
    connection.__enter__ = Mock(return_value=connection)
    connection.__exit__ = Mock(return_value=None)
    engine.connect = Mock(return_value=connection)
    
    return engine


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables"""
    test_env = {
        "MCP_SERVER_NAME": "Test Legal Spend Server",
        "LOG_LEVEL": "DEBUG",
        "LEGALTRACKER_ENABLED": "false",
        "SAP_ENABLED": "false",
        "ORACLE_ENABLED": "false",
        "POSTGRES_ENABLED": "false",
        "CSV_ENABLED": "false",
        "EXCEL_ENABLED": "false"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)