from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from enum import Enum
import datetime

class ErrorCode(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    DATA_SOURCE_ERROR = "DATA_SOURCE_ERROR"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"

class VendorType(str, Enum):
    """Vendor type enumeration"""
    LAW_FIRM = "Law Firm"
    CONSULTANT = "Consultant"
    EXPERT_WITNESS = "Expert Witness"
    COURT_REPORTER = "Court Reporter"
    EDISCOVERY_VENDOR = "eDiscovery Vendor"
    HOSTING_PROVIDER = "Hosting Provider"
    FORENSICS = "Forensics"
    OTHER = "Other"

class PracticeArea(str, Enum):
    """Practice area enumeration"""
    LITIGATION = "Litigation"
    CORPORATE = "Corporate"
    EMPLOYMENT = "Employment"
    INTELLECTUAL_PROPERTY = "Intellectual Property"
    REGULATORY = "Regulatory"
    REAL_ESTATE = "Real Estate"
    TAX = "Tax"
    EDISCOVERY = "eDiscovery"
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
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    status: str = "approved"
    budget_code: Optional[str] = None
    source_system: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

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
    vendor_name: str
    total_spend: Decimal
    invoice_count: int
    average_invoice: Decimal
    matters_count: int
    performance_score: float
    trend: str  # "increasing", "decreasing", "stable"

@dataclass
class MCPError:
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    
def create_error_response(code: ErrorCode, message: str, details: Optional[Dict] = None):
    return {
        "error": {
            "code": code.value,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    }