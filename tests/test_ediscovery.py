import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
import json

from legal_spend_mcp.models import LegalSpendRecord, VendorType, PracticeArea
from legal_spend_mcp.data_sources import EDiscoveryDataSource, FileDataSource
from legal_spend_mcp.config import DataSourceConfig

class TestEDiscovery:
    """Test eDiscovery specific functionality"""

    def test_enums(self):
        """Test that new Enums are available"""
        assert VendorType.EDISCOVERY_VENDOR == "eDiscovery Vendor"
        assert VendorType.HOSTING_PROVIDER == "Hosting Provider"
        assert VendorType.FORENSICS == "Forensics"
        assert PracticeArea.EDISCOVERY == "eDiscovery"

    def test_legal_spend_record_metadata(self):
        """Test that LegalSpendRecord accepts metadata"""
        record = LegalSpendRecord(
            invoice_id="INV-001",
            vendor_name="Test Vendor",
            vendor_type=VendorType.EDISCOVERY_VENDOR,
            matter_id="MAT-001",
            matter_name="Test Matter",
            department="Legal",
            practice_area=PracticeArea.EDISCOVERY,
            invoice_date=date(2024, 1, 1),
            amount=Decimal("1000.00"),
            currency="USD",
            expense_category="Services",
            description="Test",
            metadata={"gb_hosted": 100, "users": 5}
        )
        assert record.metadata == {"gb_hosted": 100, "users": 5}
        assert record.vendor_type == VendorType.EDISCOVERY_VENDOR
        assert record.practice_area == PracticeArea.EDISCOVERY

    @pytest.mark.asyncio
    async def test_ediscovery_data_source(self):
        """Test EDiscoveryDataSource mock generation"""
        config = DataSourceConfig(
            name="ediscovery",
            type="api",
            enabled=True,
            connection_params={}
        )
        source = EDiscoveryDataSource(config)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        records = await source.get_spend_data(start_date, end_date)

        assert len(records) > 0
        for record in records:
            assert record.practice_area == PracticeArea.EDISCOVERY
            assert record.vendor_type in [
                VendorType.EDISCOVERY_VENDOR,
                VendorType.HOSTING_PROVIDER,
                VendorType.FORENSICS
            ]
            assert record.metadata is not None
            assert "gb_hosted" in record.metadata or "processing_gb" in record.metadata

        vendors = await source.get_vendors()
        assert len(vendors) == 4
        assert any(v["name"] == "Lighthouse" for v in vendors)
        assert any(v["name"] == "Relativity" for v in vendors)

    @pytest.mark.asyncio
    async def test_file_data_source_metadata_csv(self, tmp_path):
        """Test FileDataSource parses metadata from CSV"""
        csv_file = tmp_path / "test.csv"
        metadata_json = json.dumps({"key": "value"})

        # Using csv module to write correctly
        import csv
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["invoice_id", "vendor_name", "vendor_type", "practice_area", "invoice_date", "amount", "metadata", "billing_period_start", "billing_period_end"])
            writer.writerow(["INV-001", "Vendor1", "eDiscovery Vendor", "eDiscovery", "2024-01-01", "100", metadata_json, "2024-01-01", "2024-01-31"])

        config = DataSourceConfig(
            name="test_csv",
            type="file",
            enabled=True,
            connection_params={
                "file_type": "csv",
                "file_path": str(csv_file),
                "encoding": "utf-8",
                "delimiter": ",",
            },
        )
        source = FileDataSource(config)
        records = await source.get_spend_data(date(2024, 1, 1), date(2024, 1, 31))

        assert len(records) == 1
        assert records[0].vendor_type == VendorType.EDISCOVERY_VENDOR
        assert records[0].practice_area == PracticeArea.EDISCOVERY
        assert records[0].metadata == {"key": "value"}
