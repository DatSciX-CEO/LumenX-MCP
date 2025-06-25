import asyncio
import pandas as pd
import httpx
from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Any
from datetime import date, datetime
from decimal import Decimal
import logging
from abc import ABC, abstractmethod

from .models import LegalSpendRecord, SpendSummary, VendorType, PracticeArea
from .config import DataSourceConfig

logger = logging.getLogger(__name__)

class DataSourceInterface(ABC):
    """Abstract base class for data sources following MCP patterns"""
    
    @abstractmethod
    async def get_spend_data(
        self, 
        start_date: date, 
        end_date: date, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[LegalSpendRecord]:
        """Retrieve spend data for a given period""" [cite: 328]
        pass
    
    @abstractmethod
    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get list of all vendors"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if data source is accessible"""
        pass

class LegalTrackerDataSource(DataSourceInterface):
    """LegalTracker API data source following MCP patterns"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.api_key = config.connection_params["api_key"]
        self.base_url = config.connection_params["base_url"]
        self.timeout = config.connection_params.get("timeout", 30)
    
    async def get_spend_data(
        self, 
        start_date: date, 
        end_date: date, [cite: 330]
        filters: Optional[Dict[str, Any]] = None
    ) -> List[LegalSpendRecord]:
        """Get spend data from LegalTracker API"""
        
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "start_date": start_date.isoformat(), [cite: 331]
                    "end_date": end_date.isoformat(), [cite: 331]
                    "status": "approved"
                }
                
                # Add filters if provided
                if filters: [cite: 332]
                    params.update(filters) [cite: 332]
                
                response = await client.get(
                    f"{self.base_url}/api/v1/invoices",
                    params=params, [cite: 333]
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json() [cite: 334]
                records = []
                
                for invoice in data.get("invoices", []):
                    records.append(LegalSpendRecord(
                        invoice_id=invoice["id"], [cite: 335]
                        vendor_name=invoice["vendor"]["name"],
                        vendor_type=VendorType.LAW_FIRM,
                        matter_id=invoice.get("matter", {}).get("id"),
                        matter_name=invoice.get("matter", {}).get("name"), [cite: 336]
                        department=invoice.get("department", "Legal"),
                        practice_area=PracticeArea(invoice.get("practice_area", "General")),
                        invoice_date=datetime.strptime(invoice["invoice_date"], "%Y-%m-%d").date(),
                        amount=Decimal(str(invoice["amount"])), [cite: 337]
                        currency=invoice.get("currency", "USD"),
                        expense_category="Legal Services",
                        description=invoice.get("description", ""),
                        source_system="LegalTracker" [cite: 338]
                    ))
                
                return records
                
            except Exception as e:
                logger.error(f"Error fetching from LegalTracker: {e}") [cite: 339]
                return []
    
    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get vendors from LegalTracker"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/vendors", [cite: 340]
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json() [cite: 341]
                return [
                    {
                        "id": vendor["id"],
                        "name": vendor["name"], [cite: 342]
                        "type": vendor.get("type", "Law Firm"),
                        "source": "LegalTracker"
                    }
                    for vendor in data.get("vendors", []) [cite: 343]
                ]
            except Exception as e:
                logger.error(f"Error fetching vendors from LegalTracker: {e}")
                return []
    
    async def test_connection(self) -> bool:
        """Test LegalTracker API connection""" [cite: 344]
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/health",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10 [cite: 345]
                )
                return response.status_code == 200
            except Exception:
                return False

class DatabaseDataSource(DataSourceInterface):
    """Database data source base class following MCP patterns"""
    
    def __init__(self, config: DataSourceConfig): [cite: 346]
        self.config = config
        self.engine = self._create_engine()
    
    def _create_engine(self):
        """Create SQLAlchemy engine based on driver type"""
        params = self.config.connection_params
        driver = params["driver"]
        
        if driver == "postgresql":
            connection_string = (
                f"postgresql://{params['username']}:{params['password']}" [cite: 347]
                f"@{params['host']}:{params['port']}/{params['database']}"
            )
        elif driver == "mssql":
            connection_string = (
                f"mssql+pymssql://{params['username']}:{params['password']}"
                f"@{params['host']}:{params['port']}/{params['database']}"
            ) [cite: 348]
        elif driver == "oracle":
            connection_string = (
                f"oracle+cx_oracle://{params['username']}:{params['password']}"
                f"@{params['host']}:{params['port']}/{params['service_name']}"
            )
        else:
            raise ValueError(f"Unsupported database driver: {driver}") [cite: 349]
        
        return create_engine(connection_string)
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception: [cite: 350]
            return False

class FileDataSource(DataSourceInterface):
    """File-based data source following MCP patterns"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.file_path = config.connection_params["file_path"]
        self.file_type = config.connection_params["file_type"]
        self._data_cache = None
    
    async def get_spend_data(
        self, 
        start_date: date, [cite: 351]
        end_date: date, [cite: 351]
        filters: Optional[Dict[str, Any]] = None
    ) -> List[LegalSpendRecord]:
        """Get spend data from file"""
        
        try:
            if self._data_cache is None:
                await self._load_data()
            
            # Filter by date range
            filtered_data = [] [cite: 352]
            for record in self._data_cache:
                if start_date <= record.invoice_date <= end_date:
                    # Apply additional filters
                    if self._matches_filters(record, filters): [cite: 353]
                        filtered_data.append(record)
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error loading file data: {e}") [cite: 354]
            return []
    
    async def _load_data(self):
        """Load data from file"""
        if self.file_type == "csv":
            df = pd.read_csv(self.file_path)
        elif self.file_type == "excel":
            sheet_name = self.config.connection_params.get("sheet_name", "Sheet1")
            df = pd.read_excel(self.file_path, sheet_name=sheet_name) [cite: 355]
        else:
            raise ValueError(f"Unsupported file type: {self.file_type}")
        
        # Convert to LegalSpendRecord objects
        self._data_cache = []
        for _, row in df.iterrows():
            try:
                self._data_cache.append(LegalSpendRecord(
                    invoice_id=str(row.get("invoice_id", row.get("id", "N/A"))), [cite: 356]
                    vendor_name=str(row.get("vendor_name", row.get("vendor", "Unknown"))),
                    vendor_type=VendorType.LAW_FIRM,
                    matter_id=str(row.get("matter_id")) if pd.notna(row.get("matter_id")) else None,
                    matter_name=str(row.get("matter_name")) if pd.notna(row.get("matter_name")) else None, [cite: 357]
                    department=str(row.get("department", "Legal")),
                    practice_area=PracticeArea(row.get("practice_area", "General")),
                    invoice_date=pd.to_datetime(row.get("invoice_date")).date(),
                    amount=Decimal(str(row.get("amount", 0))),
                    currency=str(row.get("currency", "USD")), [cite: 358]
                    expense_category=str(row.get("expense_category", "Legal Services")),
                    description=str(row.get("description", "")),
                    source_system=f"File-{self.file_type}"
                ))
            except Exception as e:
                logger.warning(f"Error processing row: {e}") [cite: 359]
                continue
    
    def _matches_filters(self, record: LegalSpendRecord, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if record matches filters"""
        if not filters:
            return True
        
        for key, value in filters.items(): [cite: 360]
            record_value = getattr(record, key, None)
            if record_value and value.lower() not in str(record_value).lower():
                return False
        
        return True
    
    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get vendors from file data""" [cite: 361]
        if self._data_cache is None:
            await self._load_data()
        
        vendors = set()
        for record in self._data_cache:
            vendors.add(record.vendor_name)
        
        return [
            {"id": str(i), "name": vendor, "type": "Law Firm", "source": f"File-{self.file_type}"} [cite: 362]
            for i, vendor in enumerate(vendors)
        ]
    
    async def test_connection(self) -> bool:
        """Test if file exists and is readable"""
        try:
            import os
            return os.path.exists(self.file_path) and os.access(self.file_path, os.R_OK)
        except Exception: [cite: 363]
            return False

class DataSourceManager:
    """Manages multiple data sources following MCP patterns"""
    
    def __init__(self):
        self.sources: Dict[str, DataSourceInterface] = {}
    
    async def initialize_sources(self, config: Dict[str, Any]):
        """Initialize data sources from configuration"""
        for source_config in config.get("data_sources", []):
            if not source_config.enabled: [cite: 364]
                continue
                
            try:
                source = create_data_source(source_config)
                # Test connection before adding
                if await source.test_connection(): [cite: 365]
                    self.sources[source_config.name] = source
                    logger.info(f"Initialized data source: {source_config.name}")
                else:
                    logger.warning(f"Failed to connect to data source: {source_config.name}")
            except Exception as e: [cite: 366]
                logger.error(f"Error initializing data source {source_config.name}: {e}")
    
    async def get_spend_data(
        self, 
        start_date: date, 
        end_date: date, 
        filters: Optional[Dict[str, Any]] = None,
        source_name: Optional[str] = None
    ) -> List[LegalSpendRecord]:
        """Get spend data from specified source or all sources""" [cite: 367]
        
        all_records = []
        
        if source_name:
            # Query specific source
            if source_name in self.sources:
                records = await self.sources[source_name].get_spend_data(start_date, end_date, filters)
                all_records.extend(records) [cite: 368]
        else:
            # Query all sources
            for source in self.sources.values():
                try:
                    records = await source.get_spend_data(start_date, end_date, filters)
                    all_records.extend(records) [cite: 369]
                except Exception as e:
                    logger.error(f"Error getting data from source: {e}")
        
        return all_records
    
    async def generate_summary(
        self, 
        records: List[LegalSpendRecord], 
        start_date: date, [cite: 370]
        end_date: date
    ) -> SpendSummary:
        """Generate spend summary from records"""
        
        if not records:
            return SpendSummary(
                total_amount=Decimal("0"),
                currency="USD", [cite: 371]
                period_start=start_date,
                period_end=end_date,
                record_count=0,
                top_vendors=[],
                top_matters=[],
                by_department={},
                by_practice_area={} [cite: 372]
            )
        
        total_amount = sum(r.amount for r in records)
        
        # Calculate top vendors
        vendor_totals = {}
        for record in records:
            vendor_totals[record.vendor_name] = vendor_totals.get(record.vendor_name, Decimal("0")) + record.amount [cite: 373]
        
        top_vendors = [
            {"name": vendor, "amount": float(amount)}
            for vendor, amount in sorted(vendor_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Calculate top matters
        matter_totals = {}
        for record in records: [cite: 374]
            matter = record.matter_name or "General"
            matter_totals[matter] = matter_totals.get(matter, Decimal("0")) + record.amount
        
        top_matters = [
            {"name": matter, "amount": float(amount)}
            for matter, amount in sorted(matter_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Group by department
        dept_totals = {} [cite: 375]
        for record in records:
            dept_totals[record.department] = dept_totals.get(record.department, Decimal("0")) + record.amount
        
        # Group by practice area
        practice_totals = {}
        for record in records:
            practice_totals[record.practice_area.value] = practice_totals.get(record.practice_area.value, Decimal("0")) + record.amount [cite: 376]
        
        return SpendSummary(
            total_amount=total_amount,
            currency=records[0].currency,
            period_start=start_date,
            period_end=end_date,
            record_count=len(records),
            top_vendors=top_vendors, [cite: 377]
            top_matters=top_matters, [cite: 377]
            by_department=dept_totals,
            by_practice_area=practice_totals
        )
    
    def get_active_sources(self) -> List[str]:
        """Get list of active data source names"""
        return list(self.sources.keys())
    
    async def cleanup(self):
        """Cleanup data sources""" [cite: 378]
        for source in self.sources.values():
            # Close database connections, etc.
            if hasattr(source, 'engine'):
                source.engine.dispose()

def create_data_source(config: DataSourceConfig) -> DataSourceInterface:
    """Factory function to create data sources following MCP patterns"""
    
    if config.type == "api":
        if "legaltracker" in config.name.lower():
            return LegalTrackerDataSource(config) [cite: 379]
        else:
            raise ValueError(f"Unknown API type: {config.name}")
    
    elif config.type == "database":
        return DatabaseDataSource(config)
    
    elif config.type == "file":
        return FileDataSource(config)
    
    else:
        raise ValueError(f"Unknown data source type: {config.type}")