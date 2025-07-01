from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
import json
import os
from decimal import Decimal
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
import logging
import time
from functools import wraps
import structlog

from .config import load_config
from .data_sources import create_data_source, DataSourceManager
from .models import LegalSpendRecord, SpendSummary

# Initialize FastMCP server following official documentation
mcp = FastMCP(
    name="Legal Spend Intelligence",
    dependencies=["httpx", "pandas", "sqlalchemy", "python-dateutil", "python-dotenv"]
)

@dataclass
class ServerContext:
    """Server context for managing data sources and state"""
    data_manager: DataSourceManager
    config: Dict[str, Any]

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
    """Manage server startup and shutdown lifecycle (Official MCP pattern)"""
    # Initialize on startup
    config = load_config()
    data_manager = DataSourceManager()
    
    # Initialize data sources based on configuration
    await data_manager.initialize_sources(config)
    
    try:
        yield ServerContext(data_manager=data_manager, config=config)
    finally:
        # Cleanup on shutdown
        await data_manager.cleanup()

# Pass lifespan to server (Official MCP pattern)
mcp = FastMCP(
    name="Legal Spend Intelligence", 
    lifespan=server_lifespan
)

# ===========================================
# MCP TOOLS (Following Official Patterns)
# ===========================================


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        tool_name = func.__name__
        
        try:
            logger.info("Tool execution started", tool=tool_name, args=len(args), kwargs=list(kwargs.keys()))
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                "Tool execution completed",
                tool=tool_name,
                execution_time=execution_time,
                success=True,
                result_size=len(str(result)) if result else 0
            )
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Tool execution failed",
                tool=tool_name,
                execution_time=execution_time,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    return wrapper
@mcp.tool()
@monitor_performance
@validate_inputs
async def get_legal_spend_summary(
    start_date: str,
    end_date: str,
    department: Optional[str] = None,
    practice_area: Optional[str] = None,
    vendor: Optional[str] = None,
    data_source: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get legal spend summary for specified period with optional filters.
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        department: Filter by department name (optional)
        practice_area: Filter by practice area (optional)
        vendor: Filter by vendor name (optional)
        data_source: Query specific data source (optional)
    
    Returns:
        Dictionary containing spend summary with totals, breakdowns, and insights
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        # Convert string dates to date objects
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Build filters
        filters = {}
        if department:
            filters["department"] = department
        if practice_area:
            filters["practice_area"] = practice_area
        if vendor:
            filters["vendor"] = vendor
        
        # Get data from specified source or all sources
        spend_data = await data_manager.get_spend_data(
           start_dt, end_dt, filters, data_source
        )
        
        # Generate summary
        summary = await data_manager.generate_summary(spend_data, start_dt, end_dt)
        
        return {
            "period": f"{start_date} to {end_date}",
            "total_amount": float(summary.total_amount),
            "currency": summary.currency,
            "record_count": summary.record_count,
            "top_vendors": summary.top_vendors,
            "top_matters": summary.top_matters,
            "by_department": {k: float(v) for k, v in summary.by_department.items()},
            "by_practice_area": {k: float(v) for k, v in summary.by_practice_area.items()},
            "data_sources_used": data_manager.get_active_sources(),
            "filters_applied": filters
        }
        
    except ValueError as e:
        return {"error": f"Invalid date format: {e}"}
    except Exception as e:
        return {"error": f"Failed to get spend summary: {e}"}

@mcp.tool()
async def get_vendor_performance(
    vendor_name: str,
    start_date: str,
    end_date: str,
    include_benchmarks: bool = False
) -> Dict[str, Any]:
    """
    Analyze performance and spend patterns for a specific vendor.
    Args:
        vendor_name: Name of the vendor/law firm to analyze
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        include_benchmarks: Include industry benchmark comparisons
    
    Returns:
        Dictionary containing vendor performance metrics and analysis
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Get vendor-specific data
        vendor_data = await data_manager.get_vendor_data(vendor_name, start_dt, end_dt)
        
        if not vendor_data:
            return {"error": f"No data found for vendor: {vendor_name}"}
        
        # Calculate performance metrics
        total_spend = sum(float(record.amount) for record in vendor_data)
        avg_invoice = total_spend / len(vendor_data)
        
        # Group by matter
        matter_breakdown = {}
        for record in vendor_data:
            matter = record.matter_name or "General"
            if matter not in matter_breakdown:
                matter_breakdown[matter] = {"count": 0, "total": 0}
            matter_breakdown[matter]["count"] += 1
            matter_breakdown[matter]["total"] += float(record.amount)
        
        result = {
            "vendor_name": vendor_name,
            "analysis_period": f"{start_date} to {end_date}",
            "performance_metrics": {
                "total_spend": total_spend,
                "invoice_count": len(vendor_data),
                "average_invoice_amount": avg_invoice,
                "currency": vendor_data[0].currency if vendor_data else "USD"
            },
            "matter_breakdown": matter_breakdown,
            "spend_trend": await data_manager.calculate_spend_trend(vendor_data)
        }
        
        # Add benchmarks if requested
        if include_benchmarks:
            benchmarks = await data_manager.get_vendor_benchmarks(vendor_name)
            result["industry_benchmarks"] = benchmarks
        
        return result
        
    except ValueError as e:
        return {"error": f"Invalid date format: {e}"}
    except Exception as e:
        return {"error": f"Failed to analyze vendor performance: {e}"}

@mcp.tool()
async def get_budget_vs_actual(
    department: str,
    start_date: str,
    end_date: str,
    budget_amount: float
) -> Dict[str, Any]:
    """
    Compare actual legal spend against budget for a department.
    
    Args:
        department: Department name to analyze
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        budget_amount: Budget amount to compare against
    
    Returns:
        Dictionary containing budget vs actual analysis with variance
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Get department spend data
        dept_data = await data_manager.get_department_spend(department, start_dt, end_dt)
        
        if not dept_data:
            return {"error": f"No spend data found for department: {department}"}
        
        actual_spend = sum(float(record.amount) for record in dept_data)
        variance = actual_spend - budget_amount
        variance_pct = (variance / budget_amount * 100) if budget_amount > 0 else 0
        
        # Monthly breakdown
        monthly_spend = await data_manager.get_monthly_breakdown(dept_data)
        
        return {
            "department": department,
            "analysis_period": f"{start_date} to {end_date}",
            "budget_analysis": {
                "budget_amount": budget_amount,
                "actual_spend": actual_spend,
                "variance": variance,
                "variance_percentage": variance_pct,
                "status": "over_budget" if variance > 0 else "under_budget"
            },
            "monthly_breakdown": monthly_spend,
            "transaction_count": len(dept_data),
            "recommendations": await data_manager.generate_budget_recommendations(
                variance_pct, dept_data
            )
        }
        
    except ValueError as e:
        return {"error": f"Invalid date format: {e}"}
    except Exception as e:
        return {"error": f"Failed to perform budget analysis: {e}"}

@mcp.tool() 
async def search_legal_transactions(
    search_term: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search for legal transactions based on description, vendor, or matter.
    Args:
        search_term: Search term to match against description, vendor, matter
        start_date: Start date filter (YYYY-MM-DD, optional)
        end_date: End date filter (YYYY-MM-DD, optional)
        min_amount: Minimum transaction amount (optional)
        max_amount: Maximum transaction amount (optional)
        limit: Maximum number of results to return (default 50)
    
    Returns:
        List of matching transactions with details
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        # Default date range if not specified
        if not start_date or not end_date:
            end_dt = date.today()
            start_dt = date(end_dt.year, 1, 1)  # Start of current year
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Search across all data sources
        matching_records = await data_manager.search_transactions(
            search_term=search_term,
            start_date=start_dt,
            end_date=end_dt,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=limit
        )
        
        # Format results
        results = []
        for record in matching_records:
            results.append({
                "transaction_id": record.invoice_id,
                "date": record.invoice_date.isoformat(),
                "vendor_name": record.vendor_name,
                "matter_name": record.matter_name,
                "amount": float(record.amount),
                "currency": record.currency,
                "description": record.description,
                "department": record.department,
                "practice_area": record.practice_area,
                "data_source": getattr(record, 'source_system', 'unknown')
            })
        
        return results
        
    except ValueError as e:
        return [{"error": f"Invalid date format: {e}"}]
    except Exception as e:
        return [{"error": f"Search failed: {e}"}]

# ===========================================
# MCP RESOURCES (Following Official Patterns)
# ===========================================

@mcp.resource("legal-spend-mcp://resources/legal_vendors")
async def get_legal_vendors() -> str:
    """
    Get list of all legal vendors across all data sources.
    Returns:
        JSON string containing vendor information
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        vendors = await data_manager.get_all_vendors()
        return json.dumps({
            "vendors": vendors,
            "total_count": len(vendors),
            "data_sources": data_manager.get_active_sources(),
            "last_updated": datetime.utcnow().isoformat()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get vendors: {e}"})

@mcp.resource("legal-spend-mcp://resources/data_sources") 
async def get_data_sources() -> str:
    """
    Get information about configured data sources and their status.
    Returns:
        JSON string containing data source status information
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        sources_status = await data_manager.get_sources_status()
        return json.dumps({
            "data_sources": sources_status,
            "active_count": len([s for s in sources_status if s.get("status") == "active"]),
            "total_configured": len(sources_status),
            "last_checked": datetime.utcnow().isoformat()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get data sources status: {e}"})

@mcp.resource("legal-spend-mcp://resources/spend_categories")
async def get_spend_categories() -> str:
    """
    Get available legal spend categories and practice areas.
    Returns:
        JSON string containing category information
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        categories = await data_manager.get_spend_categories()
        return json.dumps({
            "expense_categories": categories.get("expense_categories", []),
            "practice_areas": categories.get("practice_areas", []),
            "departments": categories.get("departments", []),
            "matter_types": categories.get("matter_types", []),
            "data_completeness": categories.get("completeness_score", 0)
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get spend categories: {e}"})

@mcp.resource("legal-spend-mcp://resources/spend_overview/recent")
async def get_recent_spend_overview() -> str:
    """
    Get overview of recent legal spend activity (last 30 days).
    Returns:
        JSON string containing recent spend overview
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        # Get last 30 days of data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        overview = await data_manager.get_spend_overview(start_date, end_date)
        
        return json.dumps({
            "period": f"Last 30 days ({start_date} to {end_date})",
            "total_spend": float(overview.get("total_spend", 0)),
            "transaction_count": overview.get("transaction_count", 0),
            "active_vendors": overview.get("active_vendors", 0),
            "top_categories": overview.get("top_categories", []),
            "alerts": overview.get("alerts", []),
            "trends": overview.get("trends", {})
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get recent overview: {e}"})

# ===========================================
# SERVER STARTUP (Official MCP Pattern)
# ===========================================

def main():
    """Main function to run the MCP server (Official pattern)"""
    import asyncio
    
    # Run the server using official MCP pattern
    mcp.run()

if __name__ == "__main__":
    main()