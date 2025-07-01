import asyncio
import pandas as pd
import httpx
from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
import hashlib
from .models import LegalSpendRecord, SpendSummary, VendorType, PracticeArea, VendorPerformance
from .config import DataSourceConfig

logger = logging.getLogger(__name__)

class DataSourceInterface(ABC):
    """Abstract base class for data sources following MCP patterns"""
    
    def __init__(self, config: 'DataSourceConfig'):
        self.config = config

    @abstractmethod
    async def get_spend_data(
        self, 
        start_date: date, 
        end_date: date, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List['LegalSpendRecord']:
        """Retrieve spend data for a given period"""
        pass
    
    @abstractmethod
    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get list of all vendors"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if data source is accessible"""
        pass

class RateLimiter:
    """A simple rate limiter to manage API call frequency."""
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    async def acquire(self, key: str = "default"):
        """Acquire a rate limit token, waiting if necessary."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Clean up old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
        
        if len(self.requests[key]) >= self.max_requests:
            oldest_request = self.requests[key][0]
            wait_until = oldest_request + timedelta(seconds=self.window_seconds)
            sleep_time = (wait_until - now).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.requests[key].append(datetime.utcnow())

class LegalTrackerDataSource(DataSourceInterface):
    """Data source for the LegalTracker API."""
    def __init__(self, config: 'DataSourceConfig'):
        super().__init__(config)
        self.base_url = self.config.connection_params.get("base_url")
        self.api_key = self.config.connection_params.get("api_key")
        self.timeout = self.config.connection_params.get("timeout", 30)
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)  # 100 req/min
    
    async def get_spend_data(
        self, 
        start_date: date, 
        end_date: date,
        filters: Optional[Dict[str, Any]] = None
    ) -> List['LegalSpendRecord']:
        """Get spend data from LegalTracker API."""
        await self.rate_limiter.acquire(f"legaltracker_{self.api_key}")
        
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "status": "approved"
                }
                
                if filters:
                    params.update(filters)
                
                response = await client.get(
                    f"{self.base_url}/api/v1/invoices",
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                records = []
                
                for invoice in data.get("invoices", []):
                    records.append(LegalSpendRecord(
                        invoice_id=invoice["id"],
                        vendor_name=invoice["vendor"]["name"],
                        vendor_type=VendorType.LAW_FIRM,
                        matter_id=invoice.get("matter", {}).get("id"),
                        matter_name=invoice.get("matter", {}).get("name"),
                        department=invoice.get("department", "Legal"),
                        practice_area=PracticeArea(invoice.get("practice_area", "General")),
                        invoice_date=datetime.strptime(invoice["invoice_date"], "%Y-%m-%d").date(),
                        amount=Decimal(str(invoice["amount"])),
                        currency=invoice.get("currency", "USD"),
                        expense_category="Legal Services",
                        description=invoice.get("description", ""),
                        source_system="LegalTracker"
                    ))
                
                return records
            except Exception as e:
                logger.error(f"Error fetching from LegalTracker: {e}")
                return []
    
    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get vendors from LegalTracker."""
        await self.rate_limiter.acquire(f"legaltracker_{self.api_key}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/vendors",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                return [
                    {
                        "id": vendor["id"],
                        "name": vendor["name"],
                        "type": vendor.get("type", "Law Firm"),
                        "source": "LegalTracker"
                    }
                    for vendor in data.get("vendors", [])
                ]
            except Exception as e:
                logger.error(f"Error fetching vendors from LegalTracker: {e}")
                return []
    
    async def test_connection(self) -> bool:
        """Test LegalTracker API connection."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/health",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10
                )
                return response.status_code == 200
            except Exception:
                return False

class DatabaseDataSource(DataSourceInterface):
    """Database data source base class."""
    def __init__(self, config: 'DataSourceConfig'):
        super().__init__(config)
        self.engine = self._create_engine()
    
    def _create_engine(self):
        """Create SQLAlchemy engine based on driver type."""
        params = self.config.connection_params
        driver = params.get("driver")
        
        connection_strings = {
            "postgresql": f"postgresql://{params.get('username')}:{params.get('password')}@{params.get('host')}:{params.get('port')}/{params.get('database')}",
            "mssql": f"mssql+pymssql://{params.get('username')}:{params.get('password')}@{params.get('host')}:{params.get('port')}/{params.get('database')}",
            "oracle": f"oracle+cx_oracle://{params.get('username')}:{params.get('password')}@{params.get('host')}:{params.get('port')}/{params.get('service_name')}"
        }
        
        if driver not in connection_strings:
            raise ValueError(f"Unsupported database driver: {driver}")
            
        return create_engine(connection_strings[driver])
    
    async def get_spend_data(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> List['LegalSpendRecord']:
        """Get spend data from the database."""
        query = """
        SELECT ... FROM legal_spend_invoices
        WHERE invoice_date >= :start_date AND invoice_date <= :end_date AND status = 'approved'
        """
        params = {"start_date": start_date, "end_date": end_date}
        
        if filters:
            if "vendor" in filters:
                query += " AND LOWER(vendor_name) LIKE :vendor"
                params["vendor"] = f"%{filters['vendor'].lower()}%"
            # ... add other filters ...

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                # ... (rest of the data processing logic as in the original code) ...
                return [] # Placeholder for processed records
        except Exception as e:
            logger.error(f"Error fetching from database: {e}")
            return []
    
    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get a distinct list of vendors from the database."""
        query = "SELECT DISTINCT vendor_name, vendor_type FROM legal_spend_invoices WHERE vendor_name IS NOT NULL ORDER BY vendor_name"
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                vendors = []
                for row in result:
                    vendor_name = row.vendor_name
                    # Generate a stable ID based on the vendor name
                    vendor_id = hashlib.md5(vendor_name.encode()).hexdigest()
                    vendors.append({
                        "id": vendor_id,
                        "name": vendor_name,
                        "type": row.vendor_type or "Law Firm",
                        "source": self.config.name
                    })
                return vendors
        except Exception as e:
            logger.error(f"Error fetching vendors from database: {e}")
            return []

    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

# ... (FileDataSource class remains largely the same, but with deterministic vendor IDs)

class FileDataSource(DataSourceInterface):
    """File-based data source (CSV, Excel)."""
    def __init__(self, config: 'DataSourceConfig'):
        super().__init__(config)
        self.file_path = self.config.connection_params.get("file_path")
        self.file_type = self.config.connection_params.get("file_type")
        self._data_cache: Optional[List['LegalSpendRecord']] = None

    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get vendors from file data."""
        if self._data_cache is None:
            await self._load_data()
        
        vendor_names = sorted(list(set(record.vendor_name for record in self._data_cache)))
        
        return [
            {
                "id": hashlib.md5(vendor.encode()).hexdigest(),
                "name": vendor, 
                "type": "Law Firm", # Or derive from data if available
                "source": f"File-{self.file_type}"
            }
            for vendor in vendor_names
        ]

    # ... (Other methods for FileDataSource as in original, no major changes needed) ...


class CacheManager:
    """A simple in-memory cache manager."""
    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a deterministic cache key from function arguments."""
        key_data = f"{args}_{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_or_set(self, key: str, func, *args, ttl: Optional[int] = None, **kwargs):
        """Get from cache or execute the function and cache its result."""
        ttl = ttl if ttl is not None else self.default_ttl
        
        if key in self.cache:
            cached_data = self.cache[key]
            if datetime.utcnow() < cached_data['expires']:
                return cached_data['data']
            del self.cache[key] # Expired
            
        result = await func(*args, **kwargs)
        if result is not None:
             self.cache[key] = {
                'data': result,
                'expires': datetime.utcnow() + timedelta(seconds=ttl)
            }
        return result
    
    def invalidate(self, pattern: str = None):
        """Invalidate all cache entries or those matching a pattern."""
        if pattern:
            keys_to_remove = [k for k in self.cache if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()

class DataSourceManager:
    """Manages multiple data sources, with caching and analysis features."""
    def __init__(self):
        self.sources: Dict[str, DataSourceInterface] = {}
        self.cache = CacheManager()
    
    async def initialize_sources(self, config: Dict[str, Any]):
        """Initialize data sources from a configuration dictionary."""
        for source_config_dict in config.get("data_sources", []):
            # Assuming DataSourceConfig can be initialized from a dict
            source_config = DataSourceConfig(**source_config_dict)
            if not source_config.enabled:
                continue
            
            try:
                source = create_data_source(source_config)
                if await source.test_connection():
                    self.sources[source_config.name] = source
                    logger.info(f"Initialized data source: {source_config.name}")
                else:
                    logger.warning(f"Failed to connect to data source: {source_config.name}")
            except Exception as e:
                logger.error(f"Error initializing data source {source_config.name}: {e}")
    
    async def get_spend_data(
        self, 
        start_date: date, 
        end_date: date, 
        filters: Optional[Dict[str, Any]] = None,
        source_name: Optional[str] = None
    ) -> List['LegalSpendRecord']:
        """Get spend data with caching."""
        cache_key = self.cache._generate_key("spend_data", start_date, end_date, filters, source_name)
        return await self.cache.get_or_set(
            cache_key,
            self._get_spend_data_uncached,
            start_date,
            end_date,
            filters=filters,
            source_name=source_name,
            ttl=600  # 10-minute cache
        )

    async def _get_spend_data_uncached(
        self, 
        start_date: date, 
        end_date: date, 
        filters: Optional[Dict[str, Any]] = None,
        source_name: Optional[str] = None
    ) -> List['LegalSpendRecord']:
        """The actual implementation for fetching spend data from sources."""
        all_records = []
        sources_to_query = [self.sources[source_name]] if source_name and source_name in self.sources else self.sources.values()

        tasks = [source.get_spend_data(start_date, end_date, filters) for source in sources_to_query]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_records.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error getting data from a source: {result}")
        
        return all_records

    # ... (Include all other helper/analysis methods from the original DataSourceManager here) ...
    # e.g., get_vendor_data, calculate_spend_trend, get_all_vendors, etc.
    
    async def cleanup(self):
        """Clean up resources used by data sources."""
        for source in self.sources.values():
            if hasattr(source, 'engine') and source.engine:
                source.engine.dispose()
        logger.info("Data source resources cleaned up.")

def create_data_source(config: 'DataSourceConfig') -> DataSourceInterface:
    """Factory function to create data source instances."""
    source_type = config.type.lower()
    
    if source_type == "api":
        # Can be expanded for other APIs like SimpleLegal, Brightflag, etc.
        if "legaltracker" in config.name.lower():
            return LegalTrackerDataSource(config)
        raise ValueError(f"Unknown API source name: {config.name}")
    
    if source_type == "database":
        return DatabaseDataSource(config)
    
    if source_type == "file":
        return FileDataSource(config)
    
    raise ValueError(f"Unknown data source type: {config.type}")