#!/usr/bin/env python3
"""
Basic usage example for Legal Spend MCP Server

This example demonstrates how to interact with the Legal Spend MCP Server
using a Python client.
"""

import asyncio
import json
from datetime import date, timedelta
from typing import Dict, Any
import os
from dotenv import load_dotenv

# For this example, we'll simulate MCP client calls
# In production, you would use an actual MCP client library

async def call_mcp_tool(tool_name: str, **params) -> Dict[str, Any]:
    """Simulate calling an MCP tool"""
    print(f"\n📞 Calling tool: {tool_name}")
    print(f"   Parameters: {json.dumps(params, indent=2)}")
    
    # In a real implementation, this would call the MCP server
    # For demo purposes, we'll return sample data
    
    if tool_name == "get_legal_spend_summary":
        return {
            "period": f"{params['start_date']} to {params['end_date']}",
            "total_amount": 250000.0,
            "currency": "USD",
            "record_count": 45,
            "top_vendors": [
                {"name": "Smith & Associates", "amount": 85000.0},
                {"name": "Jones Legal", "amount": 65000.0},
                {"name": "Brown Law Firm", "amount": 45000.0}
            ],
            "by_department": {
                "Legal": 180000.0,
                "Compliance": 50000.0,
                "Finance": 20000.0
            }
        }
    
    elif tool_name == "search_legal_transactions":
        return [
            {
                "transaction_id": "INV-2024-001",
                "date": "2024-01-15",
                "vendor_name": "Smith & Associates",
                "matter_name": "ABC Corp Acquisition",
                "amount": 25000.0,
                "currency": "USD",
                "description": "Due diligence services"
            },
            {
                "transaction_id": "INV-2024-002",
                "date": "2024-01-20",
                "vendor_name": "Smith & Associates",
                "matter_name": "ABC Corp Acquisition",
                "amount": 15000.0,
                "currency": "USD",
                "description": "Contract negotiation"
            }
        ]
    
    return {"error": "Unknown tool"}


async def main():
    """Main example function"""
    
    print("=" * 60)
    print("Legal Spend MCP Server - Basic Usage Example")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Example 1: Get spend summary for the current quarter
    print("\n📊 Example 1: Quarterly Spend Summary")
    print("-" * 40)
    
    # Calculate current quarter dates
    today = date.today()
    quarter_start = date(today.year, ((today.month - 1) // 3) * 3 + 1, 1)
    quarter_end = date(today.year, ((today.month - 1) // 3 + 1) * 3 + 1, 1) - timedelta(days=1)
    
    summary = await call_mcp_tool(
        "get_legal_spend_summary",
        start_date=quarter_start.isoformat(),
        end_date=quarter_end.isoformat()
    )
    
    print(f"\n✅ Total Legal Spend: ${summary['total_amount']:,.2f} {summary['currency']}")
    print(f"   Transaction Count: {summary['record_count']}")
    print("\n   Top Vendors:")
    for vendor in summary['top_vendors'][:3]:
        print(f"   - {vendor['name']}: ${vendor['amount']:,.2f}")
    
    # Example 2: Search for specific vendor transactions
    print("\n🔍 Example 2: Search Vendor Transactions")
    print("-" * 40)
    
    transactions = await call_mcp_tool(
        "search_legal_transactions",
        search_term="Smith & Associates",
        start_date="2024-01-01",
        end_date="2024-12-31",
        min_amount=10000.0
    )
    
    print(f"\n✅ Found {len(transactions)} transactions")
    for txn in transactions[:3]:
        print(f"\n   Invoice: {txn['transaction_id']}")
        print(f"   Date: {txn['date']}")
        print(f"   Matter: {txn['matter_name']}")
        print(f"   Amount: ${txn['amount']:,.2f}")
        print(f"   Description: {txn['description']}")
    
    # Example 3: Department budget analysis
    print("\n💰 Example 3: Department Budget Analysis")
    print("-" * 40)
    
    budget_analysis = await call_mcp_tool(
        "get_budget_vs_actual",
        department="Legal",
        start_date="2024-01-01",
        end_date="2024-03-31",
        budget_amount=200000.0
    )
    
    # Simulated response
    budget_analysis = {
        "department": "Legal",
        "budget_analysis": {
            "budget_amount": 200000.0,
            "actual_spend": 180000.0,
            "variance": -20000.0,
            "variance_percentage": -10.0,
            "status": "under_budget"
        },
        "recommendations": [
            "Current spending is within acceptable variance",
            "Continue monitoring for any unusual patterns"
        ]
    }
    
    print(f"\n✅ Budget Status: {budget_analysis['budget_analysis']['status'].replace('_', ' ').title()}")
    print(f"   Budget: ${budget_analysis['budget_analysis']['budget_amount']:,.2f}")
    print(f"   Actual: ${budget_analysis['budget_analysis']['actual_spend']:,.2f}")
    print(f"   Variance: ${budget_analysis['budget_analysis']['variance']:,.2f} "
          f"({budget_analysis['budget_analysis']['variance_percentage']:.1f}%)")
    
    print("\n   Recommendations:")
    for rec in budget_analysis['recommendations']:
        print(f"   • {rec}")
    
    # Example 4: Vendor performance analysis
    print("\n📈 Example 4: Vendor Performance Analysis")
    print("-" * 40)
    
    vendor_performance = await call_mcp_tool(
        "get_vendor_performance",
        vendor_name="Smith & Associates",
        start_date="2024-01-01",
        end_date="2024-06-30",
        include_benchmarks=True
    )
    
    # Simulated response
    vendor_performance = {
        "vendor_name": "Smith & Associates",
        "performance_metrics": {
            "total_spend": 150000.0,
            "invoice_count": 12,
            "average_invoice_amount": 12500.0
        },
        "spend_trend": {
            "trend": "stable",
            "change_percentage": 2.5
        },
        "industry_benchmarks": {
            "average_invoice_benchmark": 15000.0,
            "cost_efficiency_score": 0.92
        }
    }
    
    print(f"\n✅ Vendor: {vendor_performance['vendor_name']}")
    print(f"   Total Spend: ${vendor_performance['performance_metrics']['total_spend']:,.2f}")
    print(f"   Invoice Count: {vendor_performance['performance_metrics']['invoice_count']}")
    print(f"   Average Invoice: ${vendor_performance['performance_metrics']['average_invoice_amount']:,.2f}")
    print(f"   Spend Trend: {vendor_performance['spend_trend']['trend'].title()} "
          f"({vendor_performance['spend_trend']['change_percentage']:+.1f}%)")
    
    if 'industry_benchmarks' in vendor_performance:
        print(f"\n   Benchmarks:")
        print(f"   - Industry Avg Invoice: ${vendor_performance['industry_benchmarks']['average_invoice_benchmark']:,.2f}")
        print(f"   - Cost Efficiency Score: {vendor_performance['industry_benchmarks']['cost_efficiency_score']:.2f}")
    
    print("\n" + "=" * 60)
    print("✨ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())