from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from enum import Enum

class VendorType(str, Enum):
    """Vendor type enumeration"""
    LAW_FIRM = "Law Firm"
    CONSULTANT = "Consultant" 
    EXPERT_WITNESS = "Expert Witness"
    COURT_REPORTER = "Court Reporter"
    OTHER = "Other"

class PracticeArea(str, Enum):
    """Practice area enumeration"""
    LITIGATION = "Litigation"
    CORPORATE = "Corporate"
    EMPLOYMENT = "Employment"
    INTELLECTUAL_PROPERTY = "Intellectual Property" [cite: 312]
    REGULATORY = "Regulatory"
    REAL_ESTATE = "Real Estate"
    TAX = "Tax"
    GENERAL = "General"

@dataclass
class LegalSpendRecord:
    """Standardized legal spend record following MCP data model patterns"""
    invoice_id: str
    vendor_name: str
    vendor_type: VendorType
    matter_id: Optional[str]
    matter_name: Optional[str]
    department: str
    practice_area: PracticeArea
    invoice_date: date
    amount: Decimal
    currency: str
    expense_category: str
    description: str
    billing_period_start: Optional[date] = None [cite: 313]
    billing_period_end: Optional[date] = None [cite: 313]
    status: str = "approved" [cite: 313]
    budget_code: Optional[str] = None [cite: 313]
    source_system: Optional[str] = None [cite: 313]

@dataclass
class SpendSummary:
    """Spend summary statistics following MCP patterns"""
    total_amount: Decimal
    currency: str
    period_start: date
    period_end: date
    record_count: int
    top_vendors: List[Dict[str, Any]]
    top_matters: List[Dict[str, Any]]
    by_department: Dict[str, Decimal]
    by_practice_area: Dict[str, Decimal]

@dataclass
class VendorPerformance:
    """Vendor performance metrics"""
    vendor_name: str [cite: 314]
    total_spend: Decimal
    invoice_count: int
    average_invoice: Decimal
    matters_count: int
    performance_score: float
    trend: str  # "increasing", "decreasing", "stable"