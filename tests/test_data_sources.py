import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pandas as pd
from pathlib import Path

from legal_spend_mcp.interfaces import DataSourceInterface
from legal_spend_mcp.data_sources import (
    LegalTrackerDataSource,
    DatabaseDataSource,
    FileDataSource,
    DataSourceManager,
    create_data_source,
)
from legal_spend_mcp import unimplemented_data_sources
from legal_spend_mcp.models import LegalSpendRecord, VendorType, PracticeArea
from legal_spend_mcp.config import DataSourceConfig


class TestLegalTrackerDataSource:
    """Test LegalTracker API data source"""

    @pytest.mark.asyncio
    async def test_get_spend_data_success(self, mock_data_source_config, mocker):
        """Test successful spend data retrieval from API"""
        mocker.patch("legal_spend_mcp.data_sources.RateLimiter.acquire")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "invoices": [
                {
                    "id": "INV-001",
                    "vendor": {"name": "Test Vendor"},
                    "matter": {"id": "MATT-001", "name": "Test Matter"},
                    "department": "Legal",
                    "practice_area": "Corporate",
                    "invoice_date": "2024-01-15",
                    "amount": "15000.00",
                    "currency": "USD",
                    "description": "Test invoice",
                }
            ]
        }
        mock_response.raise_for_status = mocker.Mock()
        mock_client_class = mocker.patch("legal_spend_mcp.data_sources.httpx.AsyncClient")
        mock_instance = mock_client_class.return_value
        mock_client = mock_instance.__aenter__.return_value
        mock_client.get.return_value = mock_response

        source = LegalTrackerDataSource(mock_data_source_config)
        records = await source.get_spend_data(
            start_date=date(2024, 1, 1), end_date=date(2024, 3, 31)
        )

        assert len(records) == 1
        assert records[0].invoice_id == "INV-001"
        assert records[0].vendor_name == "Test Vendor"
        assert records[0].amount == Decimal("15000.00")
        assert records[0].source_system == "LegalTracker"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_spend_data_with_filters(
        self, mock_data_source_config, mocker
    ):
        """Test spend data retrieval with filters"""
        mocker.patch("legal_spend_mcp.data_sources.RateLimiter.acquire")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invoices": [{}]}
        mock_response.raise_for_status = mocker.Mock()
        mock_client_class = mocker.patch("legal_spend_mcp.data_sources.httpx.AsyncClient")
        mock_instance = mock_client_class.return_value
        mock_client = mock_instance.__aenter__.return_value
        mock_client.get.return_value = mock_response

        source = LegalTrackerDataSource(mock_data_source_config)
        filters = {"department": "Legal", "vendor": "Test Vendor"}
        await source.get_spend_data(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            filters=filters,
        )

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["department"] == "Legal"
        assert call_args[1]["params"]["vendor"] == "Test Vendor"

    @pytest.mark.asyncio
    async def test_get_spend_data_api_error(self, mock_data_source_config, mocker):
        """Test handling of API errors"""
        mocker.patch("legal_spend_mcp.data_sources.RateLimiter.acquire")
        mock_client_class = mocker.patch("legal_spend_mcp.data_sources.httpx.AsyncClient")
        mock_instance = mock_client_class.return_value
        mock_client = mock_instance.__aenter__.return_value
        mock_client.get.side_effect = Exception("API Error")

        source = LegalTrackerDataSource(mock_data_source_config)
        records = await source.get_spend_data(
            start_date=date(2024, 1, 1), end_date=date(2024, 3, 31)
        )

        assert records == []

    @pytest.mark.asyncio
    async def test_get_vendors_success(self, mock_data_source_config, mocker):
        """Test successful vendor retrieval"""
        mocker.patch("legal_spend_mcp.data_sources.RateLimiter.acquire")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "vendors": [
                {"id": "V1", "name": "Vendor 1", "type": "Law Firm"},
                {"id": "V2", "name": "Vendor 2", "type": "Consultant"},
            ]
        }
        mock_response.raise_for_status = mocker.Mock()
        mock_client_class = mocker.patch("legal_spend_mcp.data_sources.httpx.AsyncClient")
        mock_instance = mock_client_class.return_value
        mock_client = mock_instance.__aenter__.return_value
        mock_client.get.return_value = mock_response
        
        source = LegalTrackerDataSource(mock_data_source_config)
        vendors = await source.get_vendors()

        assert len(vendors) == 2
        assert vendors[0]["name"] == "Vendor 1"
        assert vendors[1]["type"] == "Consultant"
        mock_client.get.assert_called_once()


    @pytest.mark.asyncio
    async def test_connection(self, mock_data_source_config, mocker):
        """Test API connection check"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_client_class = mocker.patch("legal_spend_mcp.data_sources.httpx.AsyncClient")
        mock_instance = mock_client_class.return_value
        mock_client = mock_instance.__aenter__.return_value
        mock_client.get.return_value = mock_response

        source = LegalTrackerDataSource(mock_data_source_config)
        result = await source.test_connection()

        assert result is True
        mock_client.get.assert_called_with(
            "https://test.api.com/api/v1/health",
            headers={"Authorization": "Bearer test_key"},
            timeout=10,
        )


class TestDatabaseDataSource:
    """Test database data source"""

    def test_create_engine_postgresql(self, mocker):
        """Test PostgreSQL engine creation"""
        config = DataSourceConfig(
            name="test_pg",
            type="database",
            enabled=True,
            connection_params={
                "driver": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "username": "user",
                "password": "pass",
            },
        )
        mock_create_engine = mocker.patch(
            "legal_spend_mcp.data_sources.create_engine"
        )
        source = DatabaseDataSource(config)
        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@localhost:5432/testdb"
        )

    def test_create_engine_mssql(self, mocker):
        """Test SQL Server engine creation"""
        config = DataSourceConfig(
            name="test_mssql",
            type="database",
            enabled=True,
            connection_params={
                "driver": "mssql",
                "host": "localhost",
                "port": 1433,
                "database": "testdb",
                "username": "user",
                "password": "pass",
            },
        )
        mock_create_engine = mocker.patch(
            "legal_spend_mcp.data_sources.create_engine"
        )
        source = DatabaseDataSource(config)
        mock_create_engine.assert_called_once_with(
            "mssql+pymssql://user:pass@localhost:1433/testdb"
        )

    def test_create_engine_unsupported(self):
        """Test unsupported database driver"""
        config = DataSourceConfig(
            name="test_unsupported",
            type="database",
            enabled=True,
            connection_params={"driver": "unsupported", "host": "localhost"},
        )
        with pytest.raises(ValueError, match="Unsupported database driver"):
            DatabaseDataSource(config)

    @pytest.mark.asyncio
    async def test_get_spend_data(self, mock_database_engine, mocker):
        """Test getting spend data from database"""
        config = DataSourceConfig(
            name="test_db",
            type="database",
            enabled=True,
            connection_params={
                "driver": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "username": "user",
                "password": "pass",
            },
        )
        mocker.patch(
            "legal_spend_mcp.data_sources.create_engine",
            return_value=mock_database_engine,
        )
        source = DatabaseDataSource(config)
        records = await source.get_spend_data(
            start_date=date(2024, 1, 1), end_date=date(2024, 3, 31)
        )
        assert len(records) == 1
        assert records[0].invoice_id == "INV-001"
        assert records[0].vendor_name == "Test Vendor"
        assert records[0].source_system == "test_db"

    @pytest.mark.asyncio
    async def test_get_spend_data_with_filters(self, mock_database_engine, mocker):
        """Test database query with filters"""
        config = DataSourceConfig(
            name="test_db",
            type="database",
            enabled=True,
            connection_params={
                "driver": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "username": "user",
                "password": "pass",
            },
        )
        mocker.patch(
            "legal_spend_mcp.data_sources.create_engine",
            return_value=mock_database_engine,
        )
        source = DatabaseDataSource(config)
        filters = {
            "vendor": "Test",
            "department": "Legal",
            "practice_area": "Corporate",
        }
        await source.get_spend_data(
            start_date=date(2024, 1, 1), end_date=date(2024, 3, 31), filters=filters
        )
        conn = mock_database_engine.connect().__enter__()
        conn.execute.assert_called_once()
        query_call = conn.execute.call_args[0][0]
        assert "vendor_name" in str(query_call)
        assert "department" in str(query_call)
        assert "practice_area" in str(query_call)


class TestFileDataSource:
    """Test file-based data source"""

    @pytest.mark.asyncio
    async def test_csv_data_source(self, temp_csv_file):
        """Test CSV file data source"""
        config = DataSourceConfig(
            name="test_csv",
            type="file",
            enabled=True,
            connection_params={
                "file_type": "csv",
                "file_path": temp_csv_file,
                "encoding": "utf-8",
                "delimiter": ",",
            },
        )
        source = FileDataSource(config)
        records = await source.get_spend_data(
            start_date=date(2024, 1, 1), end_date=date(2024, 3, 31)
        )
        assert len(records) == 2
        assert records[0].vendor_name == "Test Vendor"
        assert records[1].vendor_name == "Another Vendor"
        assert records[0].amount == Decimal("15000.00")
        assert records[1].amount == Decimal("25000.00")

    @pytest.mark.asyncio
    async def test_excel_data_source(self, temp_excel_file):
        """Test Excel file data source"""
        config = DataSourceConfig(
            name="test_excel",
            type="file",
            enabled=True,
            connection_params={
                "file_type": "excel",
                "file_path": temp_excel_file,
                "sheet_name": "Sheet1",
            },
        )
        source = FileDataSource(config)
        records = await source.get_spend_data(
            start_date=date(2024, 1, 1), end_date=date(2024, 3, 31)
        )
        assert len(records) == 2
        assert all(r.source_system == "File-excel" for r in records)

    @pytest.mark.asyncio
    async def test_file_data_source_with_filters(self, temp_csv_file):
        """Test file data source with filters"""
        config = DataSourceConfig(
            name="test_csv",
            type="file",
            enabled=True,
            connection_params={"file_type": "csv", "file_path": temp_csv_file},
        )
        source = FileDataSource(config)
        filters = {"vendor_name": "Test"}
        records = await source.get_spend_data(
            start_date=date(2024, 1, 1), end_date=date(2024, 3, 31), filters=filters
        )
        assert len(records) == 1
        assert records[0].vendor_name == "Test Vendor"

    @pytest.mark.asyncio
    async def test_file_not_found(self):
        """Test handling of missing file"""
        config = DataSourceConfig(
            name="test_missing",
            type="file",
            enabled=True,
            connection_params={
                "file_type": "csv",
                "file_path": "/nonexistent/file.csv",
            },
        )
        source = FileDataSource(config)
        result = await source.test_connection()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_vendors_from_file(self, temp_csv_file):
        """Test getting vendors from file"""
        config = DataSourceConfig(
            name="test_csv",
            type="file",
            enabled=True,
            connection_params={"file_type": "csv", "file_path": temp_csv_file},
        )
        source = FileDataSource(config)
        vendors = await source.get_vendors()
        assert len(vendors) == 2
        vendor_names = [v["name"] for v in vendors]
        assert "Test Vendor" in vendor_names
        assert "Another Vendor" in vendor_names


class TestDataSourceManager:
    """Test data source manager"""

    @pytest.mark.asyncio
    async def test_initialize_sources(self, mock_config, mocker):
        """Test initialization of data sources"""
        manager = DataSourceManager()
        mock_source = mocker.AsyncMock()
        mock_source.test_connection.return_value = True
        mocker.patch(
            "legal_spend_mcp.data_sources.create_data_source",
            return_value=mock_source,
        )
        await manager.initialize_sources(mock_config)
        assert len(manager.sources) == 1
        assert "test_api" in manager.sources

    @pytest.mark.asyncio
    async def test_get_spend_data_all_sources(self, sample_spend_records, mocker):
        """Test getting data from all sources"""
        manager = DataSourceManager()
        source1 = mocker.AsyncMock()
        source1.get_spend_data.return_value = sample_spend_records[:5]
        source2 = mocker.AsyncMock()
        source2.get_spend_data.return_value = sample_spend_records[5:]
        manager.sources = {"source1": source1, "source2": source2}
        records = await manager.get_spend_data(
            start_date=date(2024, 1, 1), end_date=date(2024, 3, 31)
        )
        assert len(records) == 10
        source1.get_spend_data.assert_called_once()
        source2.get_spend_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_spend_data_specific_source(
        self, sample_spend_records, mocker
    ):
        """Test getting data from specific source"""
        manager = DataSourceManager()
        source1 = mocker.AsyncMock()
        source1.get_spend_data.return_value = sample_spend_records[:5]
        source2 = mocker.AsyncMock()
        source2.get_spend_data.return_value = []
        manager.sources = {"source1": source1, "source2": source2}
        records = await manager.get_spend_data(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            source_name="source1",
        )
        assert len(records) == 5
        source1.get_spend_data.assert_called_once()
        source2.get_spend_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_summary(self, sample_spend_records):
        """Test summary generation"""
        manager = DataSourceManager()
        summary = await manager.generate_summary(
            records=sample_spend_records,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        assert summary.total_amount == sum(
            r.amount for r in sample_spend_records
        )
        assert summary.record_count == len(sample_spend_records)
        assert len(summary.top_vendors) <= 5
        assert len(summary.top_matters) <= 5
        assert "Legal" in summary.by_department
        assert PracticeArea.CORPORATE.value in summary.by_practice_area.keys()

    @pytest.mark.asyncio
    async def test_calculate_spend_trend(self, sample_spend_records):
        """Test spend trend calculation"""
        manager = DataSourceManager()
        trend = await manager.calculate_spend_trend(sample_spend_records)
        assert "trend" in trend
        assert trend["trend"] in ["increasing", "decreasing", "stable"]
        assert "change_percentage" in trend
        assert "monthly_totals" in trend

    @pytest.mark.asyncio
    async def test_search_transactions(self, sample_spend_records, mocker):
        """Test transaction search"""
        manager = DataSourceManager()
        source = mocker.AsyncMock()
        source.get_spend_data.return_value = sample_spend_records
        manager.sources = {"test": source}
        results = await manager.search_transactions(
            search_term="Smith",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            min_amount=10000.0,
            limit=5,
        )
        assert len(results) <= 5
        assert all("Smith" in r.vendor_name for r in results)
        assert all(float(r.amount) >= 10000.0 for r in results)


class TestDataSourceFactory:
    """Test data source factory function"""

    def test_create_api_data_source(self):
        """Test creating API data source"""
        config = DataSourceConfig(
            name="legaltracker",
            type="api",
            enabled=True,
            connection_params={
                "api_key": "test",
                "base_url": "https://test.api.com",
            },
        )
        source = create_data_source(config)
        assert isinstance(source, LegalTrackerDataSource)

    def test_create_database_data_source(self, mocker):
        """Test creating database data source"""
        config = DataSourceConfig(
            name="test_db",
            type="database",
            enabled=True,
            connection_params={
                "driver": "postgresql",
                "username": "user",
                "password": "pass",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
            },
        )
        mocker.patch("legal_spend_mcp.data_sources.create_engine")
        source = create_data_source(config)
        assert isinstance(source, DatabaseDataSource)

    def test_create_file_data_source(self):
        """Test creating file data source"""
        config = DataSourceConfig(
            name="test_file",
            type="file",
            enabled=True,
            connection_params={"file_type": "csv", "file_path": "test.csv"},
        )
        source = create_data_source(config)
        assert isinstance(source, FileDataSource)

    def test_create_unknown_data_source(self):
        """Test creating unknown data source type"""
        config = DataSourceConfig(
            name="test_unknown",
            type="unknown",
            enabled=True,
            connection_params={},
        )
        with pytest.raises(
            ValueError, match="No data source registered for key 'unknown'"
        ):
            create_data_source(config)

    @pytest.mark.parametrize(
        "source_name, expected_class",
        [
            ("simplelegal", "SimpleLegalDataSource"),
            ("brightflag", "BrightflagDataSource"),
            ("tymetrix", "TyMetrixDataSource"),
            ("onit", "OnitDataSource"),
            ("dynamics365", "Dynamics365DataSource"),
            ("netsuite", "NetSuiteDataSource"),
        ],
    )
    def test_create_new_api_data_sources(
        self, source_name, expected_class, mocker
    ):
        """Test creating new placeholder API data sources"""
        config = DataSourceConfig(
            name=source_name,
            type="api",
            enabled=True,
            connection_params={
                "api_key": "test",
                "base_url": "https://test.api.com",
            },
        )
        source = create_data_source(config)
        assert source.__class__.__name__ == expected_class