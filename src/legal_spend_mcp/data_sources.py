import asyncio
import pandas as pd
import httpx
from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
from .interfaces import DataSourceInterface
from collections import defaultdict
import hashlib
import os
from .models import LegalSpendRecord, SpendSummary, VendorType, PracticeArea, VendorPerformance
from .config import DataSourceConfig
from .registry import registry
from . import unimplemented_data_sources

logger = logging.getLogger(__name__)


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
        self.requests[key] = [
            req_time for req_time in self.requests[key] if req_time > cutoff
        ]

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
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

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
                        practice_area=PracticeArea(
                            invoice.get("practice_area", "General")
                        ),
                        invoice_date=datetime.strptime(
                            invoice["invoice_date"], "%Y-%m-%d"
                        ).date(),
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
                return [{
                    "id": vendor["id"],
                    "name": vendor["name"],
                    "type": vendor.get("type", "Law Firm"),
                    "source": "LegalTracker"
                } for vendor in data.get("vendors", [])]
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
    registration_key = "database"

    def __init__(self, config: 'DataSourceConfig'):
        super().__init__(config)
        self.engine = self._create_engine()

    def _create_engine(self):
        """Create SQLAlchemy engine based on driver type."""
        params = self.config.connection_params
        driver = params.get("driver")

        connection_strings = {
            "postgresql": (
                f"postgresql://{params.get('username')}:{params.get('password')}"
                f"@{params.get('host')}:{params.get('port')}/{params.get('database')}"
            ),
            "mssql": (
                f"mssql+pymssql://{params.get('username')}:{params.get('password')}"
                f"@{params.get('host')}:{params.get('port')}/{params.get('database')}"
            ),
            "oracle": (
                f"oracle+cx_oracle://{params.get('username')}:{params.get('password')}"
                f"@{params.get('host')}:{params.get('port')}/{params.get('service_name')}"
            )
        }

        if driver not in connection_strings:
            raise ValueError(f"Unsupported database driver: {driver}")

        return create_engine(connection_strings[driver])

    async def get_spend_data(
        self,
        start_date: date,
        end_date: date,
        filters: Optional[Dict[str, Any]] = None
    ) -> List['LegalSpendRecord']:
        """Get spend data from the database."""
        query = """
        SELECT
            invoice_id, vendor_name, vendor_type, matter_id, matter_name,
            department, practice_area, invoice_date, amount, currency,
            expense_category, description, billing_period_start,
            billing_period_end, status, budget_code
        FROM legal_spend_invoices
        WHERE invoice_date >= :start_date
        AND invoice_date <= :end_date
        AND status = 'approved'
        """
        params = {"start_date": start_date, "end_date": end_date}

        # Apply filters
        if filters:
            if "vendor" in filters:
                query += " AND LOWER(vendor_name) LIKE :vendor"
                params["vendor"] = f"%{filters['vendor'].lower()}%"
            if "department" in filters:
                query += " AND LOWER(department) = :department"
                params["department"] = filters['department'].lower()
            if "practice_area" in filters:
                query += " AND LOWER(practice_area) = :practice_area"
                params["practice_area"] = filters['practice_area'].lower()
            if "vendor_name" in filters:
                query += " AND LOWER(vendor_name) LIKE :vendor_name"
                params["vendor_name"] = f"%{filters['vendor_name'].lower()}%"
            if "min_amount" in filters:
                query += " AND amount >= :min_amount"
                params["min_amount"] = filters['min_amount']
            if "max_amount" in filters:
                query += " AND amount <= :max_amount"
                params["max_amount"] = filters['max_amount']

        query += " ORDER BY invoice_date DESC"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                records = []
                for row in result:
                    # Map vendor type
                    vendor_type = VendorType.LAW_FIRM  # Default
                    if row.vendor_type:
                        for vt in VendorType:
                            if vt.value.lower() == row.vendor_type.lower():
                                vendor_type = vt
                                break
                    # Map practice area
                    practice_area = PracticeArea.GENERAL  # Default
                    if row.practice_area:
                        for pa in PracticeArea:
                            if pa.value.lower() == row.practice_area.lower():
                                practice_area = pa
                                break

                    record = LegalSpendRecord(
                        invoice_id=row.invoice_id,
                        vendor_name=row.vendor_name,
                        vendor_type=vendor_type,
                        matter_id=row.matter_id,
                        matter_name=row.matter_name,
                        department=row.department or "Legal",
                        practice_area=practice_area,
                        invoice_date=row.invoice_date,
                        amount=Decimal(str(row.amount)),
                        currency=row.currency or "USD",
                        expense_category=row.expense_category or "Legal Services",
                        description=row.description or "",
                        billing_period_start=row.billing_period_start,
                        billing_period_end=row.billing_period_end,
                        status=row.status or "approved",
                        budget_code=row.budget_code,
                        source_system=self.config.name
                    )
                    records.append(record)
                return records
        except Exception as e:
            logger.error(f"Error fetching from database {self.config.name}: {e}")
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


class FileDataSource(DataSourceInterface):
    """File-based data source (CSV, Excel)."""
    registration_key = "file"

    def __init__(self, config: 'DataSourceConfig'):
        super().__init__(config)
        self.file_path = self.config.connection_params.get("file_path")
        self.file_type = self.config.connection_params.get("file_type")
        self._data_cache: Optional[List['LegalSpendRecord']] = None
        self._last_modified: Optional[datetime] = None

    async def _load_data(self) -> None:
        """Load data from file into cache if it has been modified."""
        if not self.file_path or not os.path.exists(self.file_path):
            logger.error(f"File not found: {self.file_path}")
            self._data_cache = []
            return

        current_modified = datetime.fromtimestamp(os.path.getmtime(self.file_path))
        if self._data_cache is not None and self._last_modified == current_modified:
            return  # Cache is still valid

        try:
            if self.file_type == "csv":
                await self._load_csv()
            elif self.file_type == "excel":
                await self._load_excel()
            else:
                logger.error(f"Unsupported file type: {self.file_type}")
                self._data_cache = []

            self._last_modified = current_modified
        except Exception as e:
            logger.error(f"Error loading file {self.file_path}: {e}")
            self._data_cache = []

    async def _load_csv(self) -> None:
        """Load data from a CSV file."""
        import csv
        encoding = self.config.connection_params.get("encoding", "utf-8")
        delimiter = self.config.connection_params.get("delimiter", ",")
        records = []
        with open(self.file_path, 'r', encoding=encoding) as file:
            reader = csv.DictReader(file, delimiter=delimiter)
            for row in reader:
                try:
                    vendor_type = next((vt for vt in VendorType if vt.value.lower() == row.get('vendor_type', '').lower()), VendorType.LAW_FIRM)
                    practice_area = next((pa for pa in PracticeArea if pa.value.lower() == row.get('practice_area', '').lower()), PracticeArea.GENERAL)

                    record = LegalSpendRecord(
                        invoice_id=row['invoice_id'],
                        vendor_name=row['vendor_name'],
                        vendor_type=vendor_type,
                        matter_id=row.get('matter_id'),
                        matter_name=row.get('matter_name'),
                        department=row.get('department', 'Legal'),
                        practice_area=practice_area,
                        invoice_date=datetime.strptime(row['invoice_date'], "%Y-%m-%d").date(),
                        amount=Decimal(row['amount']),
                        currency=row.get('currency', 'USD'),
                        expense_category=row.get('expense_category', 'Legal Services'),
                        description=row.get('description', ''),
                        billing_period_start=datetime.strptime(row['billing_period_start'], "%Y-%m-%d").date() if row.get('billing_period_start') else None,
                        billing_period_end=datetime.strptime(row['billing_period_end'], "%Y-%m-%d").date() if row.get('billing_period_end') else None,
                        status=row.get('status', 'approved'),
                        budget_code=row.get('budget_code'),
                        source_system=f"File-{self.file_type}"
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Error parsing CSV row: {e}")
                    continue
        self._data_cache = records

    async def _load_excel(self) -> None:
        """Load data from an Excel file."""
        sheet_name = self.config.connection_params.get("sheet_name", "Sheet1")
        df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        records = []
        for _, row in df.iterrows():
            try:
                invoice_date_val = row['invoice_date']
                invoice_date = pd.to_datetime(invoice_date_val).date()

                vendor_type = next((vt for vt in VendorType if vt.value.lower() == str(row.get('vendor_type', '')).lower()), VendorType.LAW_FIRM)
                practice_area = next((pa for pa in PracticeArea if pa.value.lower() == str(row.get('practice_area', '')).lower()), PracticeArea.GENERAL)

                record = LegalSpendRecord(
                    invoice_id=str(row['invoice_id']),
                    vendor_name=str(row['vendor_name']),
                    vendor_type=vendor_type,
                    matter_id=str(row.get('matter_id')) if pd.notna(row.get('matter_id')) else None,
                    matter_name=str(row.get('matter_name')) if pd.notna(row.get('matter_name')) else None,
                    department=str(row.get('department', 'Legal')),
                    practice_area=practice_area,
                    invoice_date=invoice_date,
                    amount=Decimal(str(row['amount'])),
                    currency=str(row.get('currency', 'USD')),
                    expense_category=str(row.get('expense_category', 'Legal Services')),
                    description=str(row.get('description', '')),
                    status=str(row.get('status', 'approved')),
                    budget_code=str(row.get('budget_code')) if pd.notna(row.get('budget_code')) else None,
                    source_system=f"File-{self.file_type}"
                )
                records.append(record)
            except Exception as e:
                logger.warning(f"Error parsing Excel row: {e}")
                continue
        self._data_cache = records

    async def get_spend_data(
        self,
        start_date: date,
        end_date: date,
        filters: Optional[Dict[str, Any]] = None
    ) -> List['LegalSpendRecord']:
        """Get spend data from the loaded file data."""
        await self._load_data()
        if self._data_cache is None:
            return []

        filtered_records = [
            r for r in self._data_cache if start_date <= r.invoice_date <= end_date
        ]

        if filters:
            if 'vendor_name' in filters:
                filt = filters['vendor_name'].lower()
                filtered_records = [r for r in filtered_records if filt in r.vendor_name.lower()]
            if 'department' in filters:
                filt = filters['department'].lower()
                filtered_records = [r for r in filtered_records if filt == r.department.lower()]
            if 'practice_area' in filters:
                filt = filters['practice_area'].lower()
                filtered_records = [r for r in filtered_records if filt == r.practice_area.value.lower()]

        return filtered_records

    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get unique vendors from the file data."""
        await self._load_data()
        if self._data_cache is None:
            return []
            
        vendor_dict = {
            record.vendor_name: {
                "id": hashlib.md5(record.vendor_name.encode()).hexdigest(),
                "name": record.vendor_name,
                "type": record.vendor_type.value,
                "source": f"File-{self.file_type}"
            } for record in self._data_cache
        }
        return sorted(vendor_dict.values(), key=lambda x: x["name"])

    async def test_connection(self) -> bool:
        """Test if the file is accessible and can be loaded."""
        if not self.file_path or not os.path.exists(self.file_path):
            return False
        try:
            await self._load_data()
            return self._data_cache is not None
        except Exception:
            return False


class CacheManager:
    """A simple in-memory cache manager."""

    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a deterministic cache key from function arguments."""
        key_data = f"{args}_{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get_or_set(
        self,
        key: str,
        func,
        *args,
        ttl: Optional[int] = None,
        **kwargs
    ):
        """Get from cache or execute the function and cache its result."""
        ttl = ttl if ttl is not None else self.default_ttl

        if key in self.cache:
            cached_data = self.cache[key]
            if datetime.utcnow() < cached_data['expires']:
                return cached_data['data']
            del self.cache[key]  # Expired

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
        for source_config in config.get("data_sources", []):
            try:
                if not source_config.enabled:
                    continue

                source = create_data_source(source_config)
                if await source.test_connection():
                    self.sources[source_config.name] = source
                    logger.info(
                        f"Initialized data source: {source_config.name}"
                    )
                else:
                    logger.warning(
                        f"Failed to connect to data source: {source_config.name}"
                    )
            except Exception as e:
                name = source_config.name if hasattr(source_config, 'name') else 'Unknown'
                logger.error(
                    f"Error initializing data source {name}: {e}"
                )

    def get_active_sources(self) -> List[str]:
        """Get a list of the names of the active data sources."""
        return list(self.sources.keys())

    async def get_spend_data(
        self,
        start_date: date,
        end_date: date,
        filters: Optional[Dict[str, Any]] = None,
        source_name: Optional[str] = None
    ) -> List['LegalSpendRecord']:
        """Get spend data with caching."""
        cache_key = self.cache._generate_key(
            "spend_data", start_date, end_date, filters, source_name
        )
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
        """Fetch spend data from sources, bypassing the cache."""
        all_records = []
        sources_to_query = (
            [self.sources[source_name]]
            if source_name and source_name in self.sources
            else self.sources.values()
        )

        tasks = [
            source.get_spend_data(start_date, end_date, filters)
            for source in sources_to_query
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_records.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error getting data from a source: {result}")

        return all_records

    async def get_all_vendors(self) -> List[Dict[str, str]]:
        """Get a list of all vendors from all data sources."""
        tasks = [source.get_vendors() for source in self.sources.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_vendors = {}
        for result in results:
            if isinstance(result, list):
                for vendor in result:
                    all_vendors[vendor['id']] = vendor
        
        return sorted(all_vendors.values(), key=lambda x: x['name'])

    async def get_sources_status(self) -> List[Dict[str, Any]]:
        """Get the status of all configured data sources."""
        statuses = []
        for name, source in self.sources.items():
            is_connected = await source.test_connection()
            statuses.append({
                "name": name,
                "type": source.config.type,
                "status": "active" if is_connected else "disconnected",
                "enabled": source.config.enabled
            })
        return statuses

    async def get_spend_categories(self) -> Dict[str, Any]:
        """Get all unique departments and practice areas."""
        all_records = await self.get_spend_data(
            start_date=date.today() - timedelta(days=365),
            end_date=date.today()
        )
        
        departments = sorted(list(set(r.department for r in all_records)))
        practice_areas = sorted(list(set(r.practice_area.value for r in all_records)))
        expense_categories = sorted(list(set(r.expense_category for r in all_records)))
        
        return {
            "departments": departments,
            "practice_areas": practice_areas,
            "expense_categories": expense_categories
        }

    async def get_spend_overview(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get a high-level overview of spend activity."""
        records = await self.get_spend_data(start_date, end_date)
        if not records:
            return {}

        summary = await self.generate_summary(records, start_date, end_date)
        
        return {
            "total_spend": summary.total_amount,
            "transaction_count": summary.record_count,
            "active_vendors": len(summary.top_vendors),
            "top_categories": summary.by_practice_area,
            "alerts": [],  # Placeholder for future alert logic
            "trends": {}  # Placeholder for future trend analysis
        }

    async def get_vendor_data(self, vendor_name: str, start_date: date, end_date: date) -> List[LegalSpendRecord]:
        """Get all spend data for a specific vendor."""
        filters = {"vendor_name": vendor_name}
        return await self.get_spend_data(start_date, end_date, filters)

    async def get_department_spend(self, department: str, start_date: date, end_date: date) -> List[LegalSpendRecord]:
        """Get all spend data for a specific department."""
        filters = {"department": department}
        return await self.get_spend_data(start_date, end_date, filters)

    async def calculate_spend_trend(self, records: List[LegalSpendRecord]) -> Dict[str, Any]:
        """Calculate the spend trend for a list of records."""
        if not records:
            return {"trend": "stable", "change_percentage": 0, "monthly_totals": {}}

        monthly_spend = defaultdict(Decimal)
        for record in records:
            month_key = record.invoice_date.strftime("%Y-%m")
            monthly_spend[month_key] += record.amount

        sorted_months = sorted(monthly_spend.keys())
        if len(sorted_months) < 2:
            return {"trend": "stable", "change_percentage": 0, "monthly_totals": {k: float(v) for k, v in monthly_spend.items()}}

        first_month_spend = monthly_spend[sorted_months[0]]
        last_month_spend = monthly_spend[sorted_months[-1]]
        
        change = last_month_spend - first_month_spend
        change_percentage = (change / first_month_spend * 100) if first_month_spend > 0 else 0

        trend = "stable"
        if change_percentage > 10:
            trend = "increasing"
        elif change_percentage < -10:
            trend = "decreasing"

        return {
            "trend": trend,
            "change_percentage": float(change_percentage),
            "monthly_totals": {k: float(v) for k, v in monthly_spend.items()}
        }

    async def get_vendor_benchmarks(self, vendor_name: str) -> Dict[str, Any]:
        """Get benchmark data for a vendor."""
        # This is a placeholder for a more complex implementation
        return {
            "average_invoice_benchmark": 15000.0,
            "cost_efficiency_score": 0.88,
            "peer_comparison": "15% below industry average"
        }

    async def get_monthly_breakdown(self, records: List[LegalSpendRecord]) -> Dict[str, float]:
        """Get a monthly breakdown of spend."""
        monthly_spend = defaultdict(Decimal)
        for record in records:
            month_key = record.invoice_date.strftime("%Y-%m")
            monthly_spend[month_key] += record.amount
        return {k: float(v) for k, v in sorted(monthly_spend.items())}

    async def generate_budget_recommendations(self, variance_pct: float, records: List[LegalSpendRecord]) -> List[str]:
        """Generate recommendations based on budget variance."""
        recommendations = []
        if variance_pct > 10:
            recommendations.append("Spending is significantly over budget. Review top expenses.")
        elif variance_pct < -10:
            recommendations.append("Spending is well under budget. Assess if resources are under-allocated.")
        else:
            recommendations.append("Spending is within the expected range.")
        return recommendations

    async def search_transactions(self, search_term: str, start_date: date, end_date: date, 
                                  min_amount: Optional[float] = None, max_amount: Optional[float] = None, 
                                  limit: int = 50) -> List[LegalSpendRecord]:
        """Search for transactions across all data sources."""
        all_records = await self.get_spend_data(start_date, end_date)
        
        search_term_lower = search_term.lower()
        
        filtered_records = [
            r for r in all_records
            if search_term_lower in r.vendor_name.lower() or
               (r.matter_name and search_term_lower in r.matter_name.lower()) or
               (r.description and search_term_lower in r.description.lower())
        ]
        
        if min_amount is not None:
            filtered_records = [r for r in filtered_records if r.amount >= Decimal(str(min_amount))]
        if max_amount is not None:
            filtered_records = [r for r in filtered_records if r.amount <= Decimal(str(max_amount))]
            
        return filtered_records[:limit]

    async def generate_summary(
        self,
        records: List[LegalSpendRecord],
        start_date: date,
        end_date: date
    ) -> SpendSummary:
        """Generate summary statistics from records."""
        if not records:
            return SpendSummary(
                total_amount=Decimal("0"),
                currency="USD",
                period_start=start_date,
                period_end=end_date,
                record_count=0,
                top_vendors=[],
                top_matters=[],
                by_department={},
                by_practice_area={}
            )

        total_amount = sum(record.amount for record in records)

        vendor_totals = defaultdict(Decimal)
        for record in records:
            vendor_totals[record.vendor_name] += record.amount

        top_vendors = sorted([{
            "name": name, "amount": float(amount)
        } for name, amount in vendor_totals.items()],
            key=lambda x: x["amount"],
            reverse=True
        )[:5]

        matter_totals = defaultdict(Decimal)
        for record in records:
            if record.matter_name:
                matter_totals[record.matter_name] += record.amount

        top_matters = sorted([{
            "name": name, "amount": float(amount)
        } for name, amount in matter_totals.items()],
            key=lambda x: x["amount"],
            reverse=True
        )[:5]

        by_department = defaultdict(Decimal)
        by_practice_area = defaultdict(Decimal)
        for record in records:
            by_department[record.department] += record.amount
            by_practice_area[record.practice_area.value] += record.amount

        return SpendSummary(
            total_amount=total_amount,
            currency=records[0].currency if records else "USD",
            period_start=start_date,
            period_end=end_date,
            record_count=len(records),
            top_vendors=top_vendors,
            top_matters=top_matters,
            by_department=dict(by_department),
            by_practice_area=dict(by_practice_area)
        )

    async def cleanup(self):
        """Clean up resources used by data sources."""
        for source in self.sources.values():
            if hasattr(source, 'engine') and source.engine:
                source.engine.dispose()
        logger.info("Data source resources cleaned up.")


def create_data_source(config: 'DataSourceConfig') -> DataSourceInterface:
    """Factory function to create data source instances using the registry."""
    source_name = config.name.lower()
    source_type = config.type.lower()

    # For APIs, the registration key is the specific name (e.g., 'legaltracker').
    # For other types, it's the generic type (e.g., 'database', 'file').
    registration_key = source_name if source_type == "api" else source_type

    try:
        source_class = registry.get_source_class(registration_key)
        return source_class(config)
    except ValueError:
        raise ValueError(
            f"No data source registered for key '{registration_key}' "
            f"(name: '{source_name}', type: '{source_type}')"
        )

