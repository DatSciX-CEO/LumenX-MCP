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

@mcp.tool()
async def get_legal_spend_summary(
    start_date: str,
    end_date: str,
    department: Optional[str] = None,
    practice_area: Optional[str] = None,
    vendor: Optional[str] = None,
    data_source: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get legal spend summary for specified period with optional filters[cite: 384].
    Args:
        start_date: Start date in YYYY-MM-DD format [cite: 385]
        end_date: End date in YYYY-MM-DD format [cite: 385]
        department: Filter by department name (optional) [cite: 385]
        practice_area: Filter by practice area (optional) [cite: 385]
        vendor: Filter by vendor name (optional) [cite: 385]
        data_source: Query specific data source (optional) [cite: 385]
    
    Returns:
        Dictionary containing spend summary with totals, breakdowns, and insights [cite: 386]
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
            filters["department"] = department [cite: 387]
        if practice_area:
            filters["practice_area"] = practice_area [cite: 387]
        if vendor:
            filters["vendor"] = vendor [cite: 387]
        
        # Get data from specified source or all sources
        spend_data = await data_manager.get_spend_data(
           start_dt, end_dt, filters, data_source [cite: 388]
        )
        
        # Generate summary
        summary = await data_manager.generate_summary(spend_data, start_dt, end_dt)
        
        return {
            "period": f"{start_date} to {end_date}",
            "total_amount": float(summary.total_amount),
            "currency": summary.currency, [cite: 389]
            "record_count": summary.record_count,
            "top_vendors": summary.top_vendors,
            "top_matters": summary.top_matters,
            "by_department": {k: float(v) for k, v in summary.by_department.items()},
            "by_practice_area": {k: float(v) for k, v in summary.by_practice_area.items()},
            "data_sources_used": data_manager.get_active_sources(), [cite: 390]
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
    Analyze performance and spend patterns for a specific vendor[cite: 391].
    Args:
        vendor_name: Name of the vendor/law firm to analyze [cite: 392]
        start_date: Start date in YYYY-MM-DD format [cite: 392]
        end_date: End date in YYYY-MM-DD format [cite: 392]
        include_benchmarks: Include industry benchmark comparisons [cite: 392]
    
    Returns:
        Dictionary containing vendor performance metrics and analysis [cite: 392]
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() [cite: 393]
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() [cite: 393]
        
        # Get vendor-specific data
        vendor_data = await data_manager.get_vendor_data(vendor_name, start_dt, end_dt)
        
        if not vendor_data:
            return {"error": f"No data found for vendor: {vendor_name}"}
        
        # Calculate performance metrics
        total_spend = sum(float(record.amount) for record in vendor_data) [cite: 394]
        avg_invoice = total_spend / len(vendor_data) [cite: 394]
        
        # Group by matter
        matter_breakdown = {}
        for record in vendor_data:
            matter = record.matter_name or "General"
            if matter not in matter_breakdown:
                matter_breakdown[matter] = {"count": 0, "total": 0} [cite: 395]
            matter_breakdown[matter]["count"] += 1
            matter_breakdown[matter]["total"] += float(record.amount)
        
        result = {
            "vendor_name": vendor_name,
            "analysis_period": f"{start_date} to {end_date}", [cite: 396]
            "performance_metrics": {
                "total_spend": total_spend,
                "invoice_count": len(vendor_data),
                "average_invoice_amount": avg_invoice,
                "currency": vendor_data[0].currency if vendor_data else "USD"
            },
            "matter_breakdown": matter_breakdown, [cite: 397]
            "spend_trend": await data_manager.calculate_spend_trend(vendor_data) [cite: 397]
        }
        
        # Add benchmarks if requested
        if include_benchmarks:
            benchmarks = await data_manager.get_vendor_benchmarks(vendor_name)
            result["industry_benchmarks"] = benchmarks
        
        return result [cite: 398]
        
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
    Compare actual legal spend against budget for a department[cite: 399].
    
    Args:
        department: Department name to analyze [cite: 399]
        start_date: Start date in YYYY-MM-DD format [cite: 399]
        end_date: End date in YYYY-MM-DD format [cite: 399]
        budget_amount: Budget amount to compare against [cite: 399]
    
    Returns:
        Dictionary containing budget vs actual analysis with variance [cite: 399]
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() [cite: 400]
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() [cite: 400]
        
        # Get department spend data
        dept_data = await data_manager.get_department_spend(department, start_dt, end_dt)
        
        if not dept_data:
            return {"error": f"No spend data found for department: {department}"}
        
        actual_spend = sum(float(record.amount) for record in dept_data) [cite: 401]
        variance = actual_spend - budget_amount [cite: 401]
        variance_pct = (variance / budget_amount * 100) if budget_amount > 0 else 0 [cite: 401]
        
        # Monthly breakdown
        monthly_spend = await data_manager.get_monthly_breakdown(dept_data)
        
        return {
            "department": department, [cite: 402]
            "analysis_period": f"{start_date} to {end_date}", [cite: 402]
            "budget_analysis": {
                "budget_amount": budget_amount,
                "actual_spend": actual_spend,
                "variance": variance,
                "variance_percentage": variance_pct, [cite: 403]
                "status": "over_budget" if variance > 0 else "under_budget" [cite: 403]
            },
            "monthly_breakdown": monthly_spend,
            "transaction_count": len(dept_data),
            "recommendations": await data_manager.generate_budget_recommendations(
                variance_pct, dept_data
            ) [cite: 404]
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
    limit: int = 50 [cite: 405]
) -> List[Dict[str, Any]]:
    """
    Search for legal transactions based on description, vendor, or matter[cite: 405].
    Args:
        search_term: Search term to match against description, vendor, matter [cite: 406]
        start_date: Start date filter (YYYY-MM-DD, optional) [cite: 406]
        end_date: End date filter (YYYY-MM-DD, optional) [cite: 406]
        min_amount: Minimum transaction amount (optional) [cite: 406]
        max_amount: Maximum transaction amount (optional) [cite: 406]
        limit: Maximum number of results to return (default 50) [cite: 406]
    
    Returns:
        List of matching transactions with details [cite: 407]
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        # Default date range if not specified
        if not start_date or not end_date:
            end_dt = date.today()
            start_dt = date(end_dt.year, 1, 1)  # Start of current year
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() [cite: 408]
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() [cite: 408]
        
        # Search across all data sources
        matching_records = await data_manager.search_transactions(
            search_term=search_term,
            start_date=start_dt,
            end_date=end_dt,
            min_amount=min_amount, [cite: 409]
            max_amount=max_amount, [cite: 409]
            limit=limit [cite: 409]
        )
        
        # Format results
        results = []
        for record in matching_records:
            results.append({
                "transaction_id": record.invoice_id, [cite: 410]
                "date": record.invoice_date.isoformat(),
                "vendor_name": record.vendor_name,
                "matter_name": record.matter_name,
                "amount": float(record.amount),
                "currency": record.currency,
                "description": record.description, [cite: 411]
                "department": record.department, [cite: 411]
                "practice_area": record.practice_area, [cite: 411]
                "data_source": getattr(record, 'source_system', 'unknown') [cite: 411]
            })
        
        return results
        
    except ValueError as e:
        return [{"error": f"Invalid date format: {e}"}] [cite: 412]
    except Exception as e:
        return [{"error": f"Search failed: {e}"}] [cite: 412]

# ===========================================
# MCP RESOURCES (Following Official Patterns)
# ===========================================

@mcp.resource("legal_vendors")
async def get_legal_vendors() -> str:
    """
    Get list of all legal vendors across all data sources[cite: 412].
    Returns:
        JSON string containing vendor information [cite: 413]
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        vendors = await data_manager.get_all_vendors()
        return json.dumps({
            "vendors": vendors,
            "total_count": len(vendors),
            "data_sources": data_manager.get_active_sources(),
            "last_updated": datetime.utcnow().isoformat() [cite: 414]
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get vendors: {e}"})

@mcp.resource("data_sources") 
async def get_data_sources() -> str:
    """
    Get information about configured data sources and their status[cite: 415].
    Returns:
        JSON string containing data source status information [cite: 415]
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        sources_status = await data_manager.get_sources_status()
        return json.dumps({
            "data_sources": sources_status,
            "active_count": len([s for s in sources_status if s.get("status") == "active"]),
            "total_configured": len(sources_status), [cite: 416]
            "last_checked": datetime.utcnow().isoformat() [cite: 416]
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get data sources status: {e}"})

@mcp.resource("spend_categories")
async def get_spend_categories() -> str:
    """
    Get available legal spend categories and practice areas[cite: 417].
    Returns:
        JSON string containing category information [cite: 417]
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        categories = await data_manager.get_spend_categories()
        return json.dumps({
            "expense_categories": categories.get("expense_categories", []),
            "practice_areas": categories.get("practice_areas", []),
            "departments": categories.get("departments", []),
            "matter_types": categories.get("matter_types", []), [cite: 418]
            "data_completeness": categories.get("completeness_score", 0) [cite: 418]
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get spend categories: {e}"})

@mcp.resource("spend_overview://recent")
async def get_recent_spend_overview() -> str:
    """
    Get overview of recent legal spend activity (last 30 days)[cite: 419].
    Returns:
        JSON string containing recent spend overview [cite: 419]
    """
    ctx = mcp.request_context
    data_manager = ctx.lifespan_context.data_manager
    
    try:
        # Get last 30 days of data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        overview = await data_manager.get_spend_overview(start_date, end_date)
        
        return json.dumps({ [cite: 420]
            "period": f"Last 30 days ({start_date} to {end_date})",
            "total_spend": float(overview.get("total_spend", 0)),
            "transaction_count": overview.get("transaction_count", 0),
            "active_vendors": overview.get("active_vendors", 0),
            "top_categories": overview.get("top_categories", []),
            "alerts": overview.get("alerts", []),
            "trends": overview.get("trends", {}) [cite: 421]
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