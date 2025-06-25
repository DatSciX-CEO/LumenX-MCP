#!/usr/bin/env python3
"""
Advanced usage example for Legal Spend MCP Server

This example demonstrates advanced features including:
- Multi-source data aggregation
- Trend analysis
- Automated reporting
- Budget alerts
- Vendor benchmarking
"""

import asyncio
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any, List
import os
from decimal import Decimal
from dataclasses import dataclass
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# Simulated MCP client
class MCPClient:
    """Simulated MCP client for demonstration"""
    
    async def call_tool(self, tool_name: str, **params) -> Dict[str, Any]:
        """Call an MCP tool"""
        print(f"🔧 Calling: {tool_name}")
        # In production, this would make actual MCP calls
        return self._simulate_response(tool_name, params)
    
    async def get_resource(self, resource_name: str) -> str:
        """Get an MCP resource"""
        print(f"📋 Getting resource: {resource_name}")
        # In production, this would fetch actual MCP resources
        return self._simulate_resource(resource_name)
    
    def _simulate_response(self, tool_name: str, params: Dict) -> Dict[str, Any]:
        """Simulate tool responses for demo"""
        # Add simulated responses based on tool
        if tool_name == "get_legal_spend_summary":
            return self._simulate_spend_summary(params)
        elif tool_name == "get_vendor_performance":
            return self._simulate_vendor_performance(params)
        elif tool_name == "search_legal_transactions":
            return self._simulate_transaction_search(params)
        return {}
    
    def _simulate_spend_summary(self, params: Dict) -> Dict[str, Any]:
        """Simulate spend summary data"""
        return {
            "period": f"{params['start_date']} to {params['end_date']}",
            "total_amount": 1250000.0,
            "currency": "USD",
            "record_count": 245,
            "top_vendors": [
                {"name": "BigLaw Partners", "amount": 450000.0},
                {"name": "Smith & Associates", "amount": 285000.0},
                {"name": "Jones Legal", "amount": 215000.0},
                {"name": "Expert Consulting LLC", "amount": 180000.0},
                {"name": "Regional Law Group", "amount": 120000.0}
            ],
            "top_matters": [
                {"name": "M&A - Project Phoenix", "amount": 380000.0},
                {"name": "Patent Litigation - Case 2024-001", "amount": 295000.0},
                {"name": "Employment Class Action", "amount": 225000.0},
                {"name": "Regulatory Compliance Review", "amount": 180000.0},
                {"name": "Contract Disputes - Various", "amount": 170000.0}
            ],
            "by_department": {
                "Legal": 850000.0,
                "Compliance": 250000.0,
                "HR": 100000.0,
                "Finance": 50000.0
            },
            "by_practice_area": {
                "Corporate": 380000.0,
                "Litigation": 520000.0,
                "Employment": 225000.0,
                "Regulatory": 125000.0
            },
            "data_sources_used": ["legaltracker", "sap_erp", "postgres_legal"]
        }
    
    def _simulate_vendor_performance(self, params: Dict) -> Dict[str, Any]:
        """Simulate vendor performance data"""
        return {
            "vendor_name": params["vendor_name"],
            "analysis_period": f"{params['start_date']} to {params['end_date']}",
            "performance_metrics": {
                "total_spend": 285000.0,
                "invoice_count": 24,
                "average_invoice_amount": 11875.0,
                "currency": "USD"
            },
            "matter_breakdown": {
                "M&A - Project Phoenix": {"count": 8, "total": 120000.0},
                "Contract Review": {"count": 10, "total": 95000.0},
                "General Corporate": {"count": 6, "total": 70000.0}
            },
            "spend_trend": {
                "trend": "increasing",
                "change_percentage": 15.5,
                "monthly_totals": {
                    "2024-01": 35000.0,
                    "2024-02": 42000.0,
                    "2024-03": 48000.0,
                    "2024-04": 52000.0,
                    "2024-05": 55000.0,
                    "2024-06": 53000.0
                }
            },
            "industry_benchmarks": {
                "average_invoice_benchmark": 15000.0,
                "average_matter_cost_benchmark": 75000.0,
                "peer_comparison": "15% below industry average",
                "cost_efficiency_score": 0.88
            }
        }
    
    def _simulate_transaction_search(self, params: Dict) -> List[Dict]:
        """Simulate transaction search results"""
        return [
            {
                "transaction_id": f"INV-2024-{i:03d}",
                "date": (date(2024, 1, 1) + timedelta(days=i*10)).isoformat(),
                "vendor_name": "Various Vendors",
                "matter_name": f"Matter {i}",
                "amount": 10000.0 + i * 1000,
                "currency": "USD",
                "description": f"Legal services for matter {i}",
                "department": ["Legal", "Compliance", "HR"][i % 3],
                "practice_area": ["Corporate", "Litigation", "Employment"][i % 3]
            }
            for i in range(min(10, params.get('limit', 50)))
        ]
    
    def _simulate_resource(self, resource_name: str) -> str:
        """Simulate resource responses"""
        if resource_name == "legal_vendors":
            return json.dumps({
                "vendors": [
                    {"id": "1", "name": "BigLaw Partners", "type": "Law Firm"},
                    {"id": "2", "name": "Smith & Associates", "type": "Law Firm"},
                    {"id": "3", "name": "Expert Consulting LLC", "type": "Consultant"}
                ],
                "total_count": 3,
                "data_sources": ["legaltracker", "sap_erp"]
            })
        elif resource_name == "spend_categories":
            return json.dumps({
                "expense_categories": ["Legal Services", "Expert Witness", "Court Costs"],
                "practice_areas": ["Corporate", "Litigation", "Employment", "Regulatory"],
                "departments": ["Legal", "Compliance", "HR", "Finance"]
            })
        return "{}"


@dataclass
class SpendAlert:
    """Data class for spend alerts"""
    type: str
    severity: str  # "info", "warning", "critical"
    message: str
    amount: float
    threshold: float


class LegalSpendAnalyzer:
    """Advanced analyzer for legal spend data"""
    
    def __init__(self, client: MCPClient):
        self.client = client
    
    async def generate_executive_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate comprehensive executive report"""
        print("\n📊 Generating Executive Report...")
        print("=" * 60)
        
        # Gather data from multiple tools
        summary = await self.client.call_tool(
            "get_legal_spend_summary",
            start_date=start_date,
            end_date=end_date
        )
        
        # Analyze top vendors
        vendor_analyses = []
        for vendor in summary["top_vendors"][:3]:
            analysis = await self.client.call_tool(
                "get_vendor_performance",
                vendor_name=vendor["name"],
                start_date=start_date,
                end_date=end_date,
                include_benchmarks=True
            )
            vendor_analyses.append(analysis)
        
        # Generate insights
        insights = self._generate_insights(summary, vendor_analyses)
        
        # Create alerts
        alerts = self._check_spend_alerts(summary)
        
        return {
            "report_period": f"{start_date} to {end_date}",
            "executive_summary": self._create_executive_summary(summary),
            "key_metrics": self._extract_key_metrics(summary),
            "vendor_analysis": vendor_analyses,
            "insights": insights,
            "alerts": alerts,
            "recommendations": self._generate_recommendations(summary, vendor_analyses, alerts)
        }
    
    def _create_executive_summary(self, summary: Dict) -> str:
        """Create executive summary text"""
        return (
            f"Total legal spend for the period was ${summary['total_amount']:,.2f}, "
            f"across {summary['record_count']} transactions. "
            f"The Legal department accounted for {(summary['by_department'].get('Legal', 0) / summary['total_amount'] * 100):.1f}% "
            f"of total spend. Litigation matters represent the highest practice area spend at "
            f"{(summary['by_practice_area'].get('Litigation', 0) / summary['total_amount'] * 100):.1f}% of total."
        )
    
    def _extract_key_metrics(self, summary: Dict) -> Dict[str, Any]:
        """Extract key metrics for dashboard"""
        return {
            "total_spend": summary['total_amount'],
            "transaction_count": summary['record_count'],
            "average_transaction": summary['total_amount'] / summary['record_count'],
            "vendor_concentration": summary['top_vendors'][0]['amount'] / summary['total_amount'] * 100,
            "top_matter_percentage": (summary['top_matters'][0]['amount'] / summary['total_amount'] * 100) if summary.get('top_matters') else 0
        }
    
    def _generate_insights(self, summary: Dict, vendor_analyses: List[Dict]) -> List[str]:
        """Generate actionable insights"""
        insights = []
        
        # Vendor concentration insight
        top_vendor_pct = summary['top_vendors'][0]['amount'] / summary['total_amount'] * 100
        if top_vendor_pct > 30:
            insights.append(
                f"⚠️ High vendor concentration: {summary['top_vendors'][0]['name']} "
                f"represents {top_vendor_pct:.1f}% of total spend"
            )
        
        # Trend insights
        for analysis in vendor_analyses:
            if analysis['spend_trend']['change_percentage'] > 20:
                insights.append(
                    f"📈 Rapid spend increase: {analysis['vendor_name']} "
                    f"spending up {analysis['spend_trend']['change_percentage']:.1f}%"
                )
        
        # Department insights
        if summary['by_department'].get('Compliance', 0) > summary['by_department'].get('Legal', 0) * 0.3:
            insights.append(
                "📊 Significant compliance spend detected - consider dedicated compliance counsel"
            )
        
        return insights
    
    def _check_spend_alerts(self, summary: Dict) -> List[SpendAlert]:
        """Check for spending alerts"""
        alerts = []
        
        # Total spend alerts
        if summary['total_amount'] > 1000000:
            alerts.append(SpendAlert(
                type="total_spend",
                severity="warning",
                message="Total legal spend exceeds $1M threshold",
                amount=summary['total_amount'],
                threshold=1000000
            ))
        
        # Vendor concentration alerts
        top_vendor_pct = summary['top_vendors'][0]['amount'] / summary['total_amount'] * 100
        if top_vendor_pct > 40:
            alerts.append(SpendAlert(
                type="vendor_concentration",
                severity="critical",
                message=f"Critical vendor concentration: {summary['top_vendors'][0]['name']}",
                amount=top_vendor_pct,
                threshold=40
            ))
        
        return alerts
    
    def _generate_recommendations(self, summary: Dict, vendor_analyses: List[Dict], alerts: List[SpendAlert]) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Based on alerts
        for alert in alerts:
            if alert.type == "vendor_concentration":
                recommendations.append(
                    "Consider diversifying legal vendor portfolio to reduce concentration risk"
                )
            elif alert.type == "total_spend" and alert.severity == "warning":
                recommendations.append(
                    "Implement quarterly spend reviews with department heads"
                )
        
        # Based on trends
        increasing_vendors = [
            v for v in vendor_analyses 
            if v['spend_trend']['trend'] == 'increasing' and v['spend_trend']['change_percentage'] > 10
        ]
        if increasing_vendors:
            recommendations.append(
                "Negotiate volume discounts or alternative fee arrangements with rapidly growing vendors"
            )
        
        # Efficiency recommendations
        below_benchmark = [
            v for v in vendor_analyses
            if 'industry_benchmarks' in v and v['industry_benchmarks']['cost_efficiency_score'] < 0.8
        ]
        if below_benchmark:
            recommendations.append(
                "Review billing practices and consider rate negotiations for below-benchmark vendors"
            )
        
        return recommendations
    
    async def analyze_spend_patterns(self, months: int = 6) -> Dict[str, Any]:
        """Analyze spending patterns over time"""
        print(f"\n📈 Analyzing {months}-month spend patterns...")
        
        # Get monthly data
        monthly_data = []
        end_date = date.today()
        
        for i in range(months):
            month_end = date(end_date.year, end_date.month, 1) - timedelta(days=1)
            month_start = date(month_end.year, month_end.month, 1)
            
            if i > 0:
                end_date = month_start - timedelta(days=1)
            
            summary = await self.client.call_tool(
                "get_legal_spend_summary",
                start_date=month_start.isoformat(),
                end_date=month_end.isoformat()
            )
            
            monthly_data.append({
                "month": month_start.strftime("%Y-%m"),
                "total_spend": summary['total_amount'],
                "transaction_count": summary['record_count'],
                "top_vendor": summary['top_vendors'][0]['name'] if summary['top_vendors'] else "N/A"
            })
        
        # Analyze patterns
        df = pd.DataFrame(monthly_data)
        
        return {
            "monthly_trends": monthly_data,
            "average_monthly_spend": df['total_spend'].mean(),
            "spend_volatility": df['total_spend'].std() / df['total_spend'].mean(),
            "growth_rate": (df['total_spend'].iloc[-1] - df['total_spend'].iloc[0]) / df['total_spend'].iloc[0] * 100,
            "seasonality_detected": self._detect_seasonality(df)
        }
    
    def _detect_seasonality(self, df: pd.DataFrame) -> bool:
        """Simple seasonality detection"""
        # In a real implementation, use more sophisticated time series analysis
        return df['total_spend'].std() > df['total_spend'].mean() * 0.2
    
    async def benchmark_vendors(self, top_n: int = 5) -> Dict[str, Any]:
        """Benchmark top vendors against each other"""
        print(f"\n🏆 Benchmarking top {top_n} vendors...")
        
        # Get vendor list
        vendors_resource = await self.client.get_resource("legal_vendors")
        vendors_data = json.loads(vendors_resource)
        
        # Get current year data
        year_start = date(date.today().year, 1, 1).isoformat()
        year_end = date.today().isoformat()
        
        summary = await self.client.call_tool(
            "get_legal_spend_summary",
            start_date=year_start,
            end_date=year_end
        )
        
        # Analyze each top vendor
        vendor_metrics = []
        for vendor in summary['top_vendors'][:top_n]:
            performance = await self.client.call_tool(
                "get_vendor_performance",
                vendor_name=vendor['name'],
                start_date=year_start,
                end_date=year_end,
                include_benchmarks=True
            )
            
            vendor_metrics.append({
                "vendor": vendor['name'],
                "total_spend": performance['performance_metrics']['total_spend'],
                "avg_invoice": performance['performance_metrics']['average_invoice_amount'],
                "efficiency_score": performance['industry_benchmarks']['cost_efficiency_score'],
                "trend": performance['spend_trend']['trend'],
                "change_pct": performance['spend_trend']['change_percentage']
            })
        
        # Create comparison matrix
        df = pd.DataFrame(vendor_metrics)
        
        return {
            "vendor_comparison": vendor_metrics,
            "best_efficiency": df.loc[df['efficiency_score'].idxmax()]['vendor'],
            "lowest_avg_invoice": df.loc[df['avg_invoice'].idxmin()]['vendor'],
            "most_stable": df.loc[df['change_pct'].abs().idxmin()]['vendor'],
            "recommendations": self._generate_vendor_recommendations(df)
        }
    
    def _generate_vendor_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate vendor-specific recommendations"""
        recs = []
        
        # Efficiency recommendations
        low_efficiency = df[df['efficiency_score'] < 0.8]
        if not low_efficiency.empty:
            recs.append(
                f"Consider renegotiating with {', '.join(low_efficiency['vendor'].tolist())} "
                f"due to below-average efficiency scores"
            )
        
        # Cost recommendations
        high_cost = df[df['avg_invoice'] > df['avg_invoice'].mean() * 1.5]
        if not high_cost.empty:
            recs.append(
                f"Review billing guidelines with {', '.join(high_cost['vendor'].tolist())} "
                f"as their average invoices are significantly above peers"
            )
        
        return recs


async def main():
    """Main function demonstrating advanced usage"""
    
    print("=" * 80)
    print("Legal Spend MCP Server - Advanced Usage Example")
    print("=" * 80)
    
    # Initialize client and analyzer
    client = MCPClient()
    analyzer = LegalSpendAnalyzer(client)
    
    # Example 1: Generate Executive Report
    print("\n🎯 Example 1: Executive Report Generation")
    print("-" * 60)
    
    report = await analyzer.generate_executive_report(
        start_date="2024-01-01",
        end_date="2024-06-30"
    )
    
    print(f"\n📄 Executive Summary:")
    print(f"   {report['executive_summary']}")
    
    print(f"\n📊 Key Metrics:")
    for metric, value in report['key_metrics'].items():
        if isinstance(value, float):
            if 'spend' in metric or 'transaction' in metric:
                print(f"   • {metric.replace('_', ' ').title()}: ${value:,.2f}")
            else:
                print(f"   • {metric.replace('_', ' ').title()}: {value:.1f}%")
        else:
            print(f"   • {metric.replace('_', ' ').title()}: {value}")
    
    print(f"\n💡 Key Insights:")
    for insight in report['insights']:
        print(f"   {insight}")
    
    print(f"\n⚠️  Alerts:")
    for alert in report['alerts']:
        icon = "🔴" if alert.severity == "critical" else "🟡" if alert.severity == "warning" else "🔵"
        print(f"   {icon} {alert.message}")
    
    print(f"\n✅ Recommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # Example 2: Spend Pattern Analysis
    print("\n\n🎯 Example 2: Spend Pattern Analysis")
    print("-" * 60)
    
    patterns = await analyzer.analyze_spend_patterns(months=6)
    
    print(f"\n📈 6-Month Spend Analysis:")
    print(f"   • Average Monthly Spend: ${patterns['average_monthly_spend']:,.2f}")
    print(f"   • Spend Volatility: {patterns['spend_volatility']:.2%}")
    print(f"   • Growth Rate: {patterns['growth_rate']:+.1f}%")
    print(f"   • Seasonality Detected: {'Yes' if patterns['seasonality_detected'] else 'No'}")
    
    print(f"\n   Monthly Breakdown:")
    for month_data in patterns['monthly_trends']:
        print(f"   {month_data['month']}: ${month_data['total_spend']:,.2f} "
              f"({month_data['transaction_count']} transactions)")
    
    # Example 3: Vendor Benchmarking
    print("\n\n🎯 Example 3: Vendor Benchmarking")
    print("-" * 60)
    
    benchmark = await analyzer.benchmark_vendors(top_n=5)
    
    print(f"\n🏆 Vendor Performance Rankings:")
    print(f"   • Best Efficiency: {benchmark['best_efficiency']}")
    print(f"   • Lowest Average Invoice: {benchmark['lowest_avg_invoice']}")
    print(f"   • Most Stable Spending: {benchmark['most_stable']}")
    
    print(f"\n   Detailed Comparison:")
    for vendor in benchmark['vendor_comparison']:
        print(f"\n   {vendor['vendor']}:")
        print(f"     - Total Spend: ${vendor['total_spend']:,.2f}")
        print(f"     - Avg Invoice: ${vendor['avg_invoice']:,.2f}")
        print(f"     - Efficiency: {vendor['efficiency_score']:.2f}")
        print(f"     - Trend: {vendor['trend']} ({vendor['change_pct']:+.1f}%)")
    
    if benchmark['recommendations']:
        print(f"\n   Vendor Recommendations:")
        for rec in benchmark['recommendations']:
            print(f"   • {rec}")
    
    # Example 4: Automated Budget Monitoring
    print("\n\n🎯 Example 4: Automated Budget Monitoring")
    print("-" * 60)
    
    # Simulate budget monitoring for multiple departments
    departments = ["Legal", "Compliance", "HR"]
    budgets = {"Legal": 900000, "Compliance": 300000, "HR": 150000}
    
    print(f"\n📊 Q1 Budget Status:")
    for dept in departments:
        budget_check = await client.call_tool(
            "get_budget_vs_actual",
            department=dept,
            start_date="2024-01-01",
            end_date="2024-03-31",
            budget_amount=budgets[dept] / 4  # Quarterly budget
        )
        
        # Simulated response
        actual = budgets[dept] / 4 * (0.8 + (hash(dept) % 40) / 100)  # 80-120% of budget
        variance_pct = ((actual - budgets[dept] / 4) / (budgets[dept] / 4)) * 100
        
        status_icon = "✅" if abs(variance_pct) < 10 else "⚠️" if variance_pct > 0 else "💰"
        print(f"\n   {status_icon} {dept}:")
        print(f"      Budget: ${budgets[dept] / 4:,.2f}")
        print(f"      Actual: ${actual:,.2f}")
        print(f"      Variance: {variance_pct:+.1f}%")
    
    print("\n" + "=" * 80)
    print("✨ Advanced examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    # Run the advanced examples
    asyncio.run(main())