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

from .models import LegalSpendRecord, SpendSummary, VendorType, PracticeArea, VendorPerformance
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
        end_date: date,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[LegalSpendRecord]:
        """Get spend data from LegalTracker API"""
        
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "status": "approved"
                }
                
                # Add filters if provided
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
        """Get vendors from LegalTracker"""
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
        """Test LegalTracker API connection"""
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
    """Database data source base class following MCP patterns"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.engine = self._create_engine()
    
    def _create_engine(self):
        """Create SQLAlchemy engine based on driver type"""
        params = self.config.connection_params
        driver = params["driver"]
        
        if driver == "postgresql":
            connection_string = (
                f"postgresql://{params['username']}:{params['password']}"
                f"@{params['host']}:{params['port']}/{params['database']}"
            )
        elif driver == "mssql":
            connection_string = (
                f"mssql+pymssql://{params['username']}:{params['password']}"
                f"@{params['host']}:{params['port']}/{params['database']}"
            )
        elif driver == "oracle":
            connection_string = (
                f"oracle+cx_oracle://{params['username']}:{params['password']}"
                f"@{params['host']}:{params['port']}/{params['service_name']}"
            )
        else:
            raise ValueError(f"Unsupported database driver: {driver}")
        
        return create_engine(connection_string)
    
    async def get_spend_data(
        self, 
        start_date: date, 
        end_date: date,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[LegalSpendRecord]:
        """Get spend data from database"""
        
        # Base query - customize based on your database schema
        query = """
        SELECT 
            invoice_id,
            vendor_name,
            vendor_type,
            matter_id,
            matter_name,
            department,
            practice_area,
            invoice_date,
            amount,
            currency,
            expense_category,
            description,
            billing_period_start,
            billing_period_end,
            status,
            budget_code
        FROM legal_spend_invoices
        WHERE invoice_date >= :start_date 
        AND invoice_date <= :end_date
        AND status = 'approved'
        """
        
        # Add filters to query
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        if filters:
            if "vendor" in filters:
                query += " AND LOWER(vendor_name) LIKE :vendor"
                params["vendor"] = f"%{filters['vendor'].lower()}%"
            if "department" in filters:
                query += " AND LOWER(department) = :department"
                params["department"] = filters["department"].lower()
            if "practice_area" in filters:
                query += " AND LOWER(practice_area) = :practice_area"
                params["practice_area"] = filters["practice_area"].lower()
        
        query += " ORDER BY invoice_date DESC"
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                
                records = []
                for row in result:
                    records.append(LegalSpendRecord(
                        invoice_id=str(row.invoice_id),
                        vendor_name=row.vendor_name,
                        vendor_type=VendorType(row.vendor_type or "Law Firm"),
                        matter_id=str(row.matter_id) if row.matter_id else None,
                        matter_name=row.matter_name,
                        department=row.department or "Legal",
                        practice_area=PracticeArea(row.practice_area or "General"),
                        invoice_date=row.invoice_date,
                        amount=Decimal(str(row.amount)),
                        currency=row.currency or "USD",
                        expense_category=row.expense_category or "Legal Services",
                        description=row.description or "",
                        billing_period_start=row.billing_period_start,
                        billing_period_end=row.billing_period_end,
                        status=row.status,
                        budget_code=row.budget_code,
                        source_system=self.config.name
                    ))
                
                return records
                
        except Exception as e:
            logger.error(f"Error fetching from database: {e}")
            return []
    
    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get vendors from database"""
        query = """
        SELECT DISTINCT 
            vendor_name,
            vendor_type
        FROM legal_spend_invoices
        WHERE vendor_name IS NOT NULL
        ORDER BY vendor_name
        """
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                vendors = []
                for idx, row in enumerate(result):
                    vendors.append({
                        "id": str(idx + 1),
                        "name": row.vendor_name,
                        "type": row.vendor_type or "Law Firm",
                        "source": self.config.name
                    })
                
                return vendors
                
        except Exception as e:
            logger.error(f"Error fetching vendors from database: {e}")
            return []
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
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
        start_date: date,
        end_date: date,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[LegalSpendRecord]:
        """Get spend data from file"""
        
        try:
            if self._data_cache is None:
                await self._load_data()
            
            # Filter by date range
            filtered_data = []
            for record in self._data_cache:
                if start_date <= record.invoice_date <= end_date:
                    # Apply additional filters
                    if self._matches_filters(record, filters):
                        filtered_data.append(record)
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error loading file data: {e}")
            return []
    
    async def _load_data(self):
        """Load data from file"""
        if self.file_type == "csv":
            df = pd.read_csv(self.file_path)
        elif self.file_type == "excel":
            sheet_name = self.config.connection_params.get("sheet_name", "Sheet1")
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        else:
            raise ValueError(f"Unsupported file type: {self.file_type}")
        
        # Convert to LegalSpendRecord objects
        self._data_cache = []
        for _, row in df.iterrows():
            try:
                self._data_cache.append(LegalSpendRecord(
                    invoice_id=str(row.get("invoice_id", row.get("id", "N/A"))),
                    vendor_name=str(row.get("vendor_name", row.get("vendor", "Unknown"))),
                    vendor_type=VendorType.LAW_FIRM,
                    matter_id=str(row.get("matter_id")) if pd.notna(row.get("matter_id")) else None,
                    matter_name=str(row.get("matter_name")) if pd.notna(row.get("matter_name")) else None,
                    department=str(row.get("department", "Legal")),
                    practice_area=PracticeArea(row.get("practice_area", "General")),
                    invoice_date=pd.to_datetime(row.get("invoice_date")).date(),
                    amount=Decimal(str(row.get("amount", 0))),
                    currency=str(row.get("currency", "USD")),
                    expense_category=str(row.get("expense_category", "Legal Services")),
                    description=str(row.get("description", "")),
                    source_system=f"File-{self.file_type}"
                ))
            except Exception as e:
                logger.warning(f"Error processing row: {e}")
                continue
    
    def _matches_filters(self, record: LegalSpendRecord, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if record matches filters"""
        if not filters:
            return True
        
        for key, value in filters.items():
            record_value = getattr(record, key, None)
            if record_value and value.lower() not in str(record_value).lower():
                return False
        
        return True
    
    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get vendors from file data"""
        if self._data_cache is None:
            await self._load_data()
        
        vendors = set()
        for record in self._data_cache:
            vendors.add(record.vendor_name)
        
        return [
            {"id": str(i), "name": vendor, "type": "Law Firm", "source": f"File-{self.file_type}"}
            for i, vendor in enumerate(vendors)
        ]
    
    async def test_connection(self) -> bool:
        """Test if file exists and is readable"""
        try:
            import os
            return os.path.exists(self.file_path) and os.access(self.file_path, os.R_OK)
        except Exception:
            return False

class DataSourceManager:
    """Manages multiple data sources following MCP patterns"""
    
    def __init__(self):
        self.sources: Dict[str, DataSourceInterface] = {}
    
    async def initialize_sources(self, config: Dict[str, Any]):
        """Initialize data sources from configuration"""
        for source_config in config.get("data_sources", []):
            if not source_config.enabled:
                continue
                
            try:
                source = create_data_source(source_config)
                # Test connection before adding
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
    ) -> List[LegalSpendRecord]:
        """Get spend data from specified source or all sources"""
        
        all_records = []
        
        if source_name:
            # Query specific source
            if source_name in self.sources:
                records = await self.sources[source_name].get_spend_data(start_date, end_date, filters)
                all_records.extend(records)
        else:
            # Query all sources
            for source in self.sources.values():
                try:
                    records = await source.get_spend_data(start_date, end_date, filters)
                    all_records.extend(records)
                except Exception as e:
                    logger.error(f"Error getting data from source: {e}")
        
        return all_records
    
    async def get_vendor_data(
        self,
        vendor_name: str,
        start_date: date,
        end_date: date
    ) -> List[LegalSpendRecord]:
        """Get all spend data for a specific vendor"""
        filters = {"vendor": vendor_name}
        return await self.get_spend_data(start_date, end_date, filters)
    
    async def calculate_spend_trend(self, records: List[LegalSpendRecord]) -> Dict[str, Any]:
        """Calculate spending trend from records"""
        if not records:
            return {"trend": "stable", "change_percentage": 0}
        
        # Group by month
        monthly_totals = defaultdict(Decimal)
        for record in records:
            month_key = f"{record.invoice_date.year}-{record.invoice_date.month:02d}"
            monthly_totals[month_key] += record.amount
        
        # Calculate trend (simple linear regression would be better)
        months = sorted(monthly_totals.keys())
        if len(months) < 2:
            return {"trend": "stable", "change_percentage": 0}
        
        first_month_total = monthly_totals[months[0]]
        last_month_total = monthly_totals[months[-1]]
        
        if first_month_total == 0:
            change_pct = 100 if last_month_total > 0 else 0
        else:
            change_pct = ((last_month_total - first_month_total) / first_month_total * 100)
        
        trend = "increasing" if change_pct > 5 else "decreasing" if change_pct < -5 else "stable"
        
        return {
            "trend": trend,
            "change_percentage": float(change_pct),
            "monthly_totals": {k: float(v) for k, v in monthly_totals.items()}
        }
    
    async def get_vendor_benchmarks(self, vendor_name: str) -> Dict[str, Any]:
        """Get benchmark data for a vendor (simplified version)"""
        # In a real implementation, this would compare against industry benchmarks
        return {
            "average_invoice_benchmark": 25000,
            "average_matter_cost_benchmark": 150000,
            "peer_comparison": "Within industry average",
            "cost_efficiency_score": 0.85
        }
    
    async def get_department_spend(
        self,
        department: str,
        start_date: date,
        end_date: date
    ) -> List[LegalSpendRecord]:
        """Get spend data for a specific department"""
        filters = {"department": department}
        return await self.get_spend_data(start_date, end_date, filters)
    
    async def get_monthly_breakdown(self, records: List[LegalSpendRecord]) -> Dict[str, float]:
        """Get monthly breakdown of spend from records"""
        monthly_totals = defaultdict(Decimal)
        
        for record in records:
            month_key = f"{record.invoice_date.year}-{record.invoice_date.month:02d}"
            monthly_totals[month_key] += record.amount
        
        return {k: float(v) for k, v in sorted(monthly_totals.items())}
    
    async def generate_budget_recommendations(
        self,
        variance_pct: float,
        records: List[LegalSpendRecord]
    ) -> List[str]:
        """Generate budget recommendations based on variance and spending patterns"""
        recommendations = []
        
        if variance_pct > 10:
            recommendations.append("Consider renegotiating rates with top vendors")
            recommendations.append("Implement stricter invoice approval processes")
            recommendations.append("Review matter budgets and implement caps where appropriate")
        elif variance_pct > 5:
            recommendations.append("Monitor spending closely for the remainder of the period")
            recommendations.append("Consider alternative fee arrangements for large matters")
        else:
            recommendations.append("Current spending is within acceptable variance")
            recommendations.append("Continue monitoring for any unusual patterns")
        
        # Analyze vendor concentration
        vendor_totals = defaultdict(Decimal)
        for record in records:
            vendor_totals[record.vendor_name] += record.amount
        
        total_spend = sum(vendor_totals.values())
        if total_spend > 0:
            top_vendor_pct = max(vendor_totals.values()) / total_spend * 100
            if top_vendor_pct > 40:
                recommendations.append(f"High vendor concentration ({top_vendor_pct:.1f}%) - consider diversifying")
        
        return recommendations
    
    async def search_transactions(
        self,
        search_term: str,
        start_date: date,
        end_date: date,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 50
    ) -> List[LegalSpendRecord]:
        """Search for transactions matching criteria"""
        all_records = await self.get_spend_data(start_date, end_date)
        
        matching_records = []
        search_lower = search_term.lower()
        
        for record in all_records:
            # Check if search term matches any field
            if (search_lower in record.vendor_name.lower() or
                (record.matter_name and search_lower in record.matter_name.lower()) or
                search_lower in record.description.lower() or
                search_lower in record.department.lower()):
                
                # Apply amount filters
                if min_amount and float(record.amount) < min_amount:
                    continue
                if max_amount and float(record.amount) > max_amount:
                    continue
                
                matching_records.append(record)
                
                if len(matching_records) >= limit:
                    break
        
        return matching_records
    
    async def get_all_vendors(self) -> List[Dict[str, str]]:
        """Get all vendors from all data sources"""
        all_vendors = []
        
        for source in self.sources.values():
            try:
                vendors = await source.get_vendors()
                all_vendors.extend(vendors)
            except Exception as e:
                logger.error(f"Error getting vendors from source: {e}")
        
        # Deduplicate by vendor name
        unique_vendors = {}
        for vendor in all_vendors:
            if vendor["name"] not in unique_vendors:
                unique_vendors[vendor["name"]] = vendor
        
        return list(unique_vendors.values())
    
    async def get_sources_status(self) -> List[Dict[str, Any]]:
        """Get status of all configured data sources"""
        status_list = []
        
        for name, source in self.sources.items():
            is_connected = await source.test_connection()
            status_list.append({
                "name": name,
                "type": source.config.type,
                "status": "active" if is_connected else "disconnected",
                "enabled": True
            })
        
        return status_list
    
    async def get_spend_categories(self) -> Dict[str, List[str]]:
        """Get available spend categories from data"""
        # In a real implementation, this would query the data sources
        # For now, return the enums and common values
        return {
            "expense_categories": [
                "Legal Services",
                "Expert Witness Fees",
                "Court Costs",
                "Discovery Costs",
                "Travel Expenses",
                "Other"
            ],
            "practice_areas": [area.value for area in PracticeArea],
            "departments": [
                "Legal",
                "Compliance",
                "HR",
                "Finance",
                "Operations",
                "Sales"
            ],
            "matter_types": [
                "Litigation",
                "Transaction",
                "Regulatory",
                "Employment",
                "Intellectual Property",
                "General Corporate"
            ],
            "completeness_score": 0.85
        }
    
    async def get_spend_overview(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get high-level spend overview for a period"""
        records = await self.get_spend_data(start_date, end_date)
        
        if not records:
            return {
                "total_spend": 0,
                "transaction_count": 0,
                "active_vendors": 0,
                "top_categories": [],
                "alerts": [],
                "trends": {}
            }
        
        # Calculate overview metrics
        total_spend = sum(float(r.amount) for r in records)
        vendors = set(r.vendor_name for r in records)
        
        # Category breakdown
        category_totals = defaultdict(float)
        for record in records:
            category_totals[record.expense_category] += float(record.amount)
        
        top_categories = sorted(
            [{"category": k, "amount": v} for k, v in category_totals.items()],
            key=lambda x: x["amount"],
            reverse=True
        )[:5]
        
        # Generate alerts
        alerts = []
        if total_spend > 1000000:
            alerts.append({"type": "high_spend", "message": "Total spend exceeds $1M for period"})
        
        # Check for unusual patterns
        daily_totals = defaultdict(float)
        for record in records:
            daily_totals[record.invoice_date] += float(record.amount)
        
        if daily_totals:
            avg_daily = sum(daily_totals.values()) / len(daily_totals)
            for date, amount in daily_totals.items():
                if amount > avg_daily * 3:
                    alerts.append({
                        "type": "spike",
                        "message": f"Unusual spend spike on {date}: ${amount:,.2f}"
                    })
        
        return {
            "total_spend": total_spend,
            "transaction_count": len(records),
            "active_vendors": len(vendors),
            "top_categories": top_categories,
            "alerts": alerts[:5],  # Limit to 5 alerts
            "trends": {
                "daily_average": avg_daily if daily_totals else 0,
                "peak_day": max(daily_totals.items(), key=lambda x: x[1]) if daily_totals else None
            }
        }
    
    async def generate_summary(
        self, 
        records: List[LegalSpendRecord], 
        start_date: date,
        end_date: date
    ) -> SpendSummary:
        """Generate spend summary from records"""
        
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
        
        total_amount = sum(r.amount for r in records)
        
        # Calculate top vendors
        vendor_totals = {}
        for record in records:
            vendor_totals[record.vendor_name] = vendor_totals.get(record.vendor_name, Decimal("0")) + record.amount
        
        top_vendors = [
            {"name": vendor, "amount": float(amount)}
            for vendor, amount in sorted(vendor_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Calculate top matters
        matter_totals = {}
        for record in records:
            matter = record.matter_name or "General"
            matter_totals[matter] = matter_totals.get(matter, Decimal("0")) + record.amount
        
        top_matters = [
            {"name": matter, "amount": float(amount)}
            for matter, amount in sorted(matter_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Group by department
        dept_totals = {}
        for record in records:
            dept_totals[record.department] = dept_totals.get(record.department, Decimal("0")) + record.amount
        
        # Group by practice area
        practice_totals = {}
        for record in records:
            practice_totals[record.practice_area.value] = practice_totals.get(record.practice_area.value, Decimal("0")) + record.amount
        
        return SpendSummary(
            total_amount=total_amount,
            currency=records[0].currency,
            period_start=start_date,
            period_end=end_date,
            record_count=len(records),
            top_vendors=top_vendors,
            top_matters=top_matters,
            by_department=dept_totals,
            by_practice_area=practice_totals
        )
    
    def get_active_sources(self) -> List[str]:
        """Get list of active data source names"""
        return list(self.sources.keys())
    
    async def cleanup(self):
        """Cleanup data sources"""
        for source in self.sources.values():
            # Close database connections, etc.
            if hasattr(source, 'engine'):
                source.engine.dispose()

def create_data_source(config: DataSourceConfig) -> DataSourceInterface:
    """Factory function to create data sources following MCP patterns"""
    
    if config.type == "api":
        if "legaltracker" in config.name.lower():
            return LegalTrackerDataSource(config)
        else:
            raise ValueError(f"Unknown API type: {config.name}")
    
    elif config.type == "database":
        return DatabaseDataSource(config)
    
    elif config.type == "file":
        return FileDataSource(config)
    
    else:
        raise ValueError(f"Unknown data source type: {config.type}")