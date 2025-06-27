import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
import json

from legal_spend_mcp.server import (
    mcp,
    get_legal_spend_summary,
    get_vendor_performance,
    get_budget_vs_actual,
    search_legal_transactions,
    get_legal_vendors,
    get_data_sources,
    get_spend_categories,
    get_recent_spend_overview,
    ServerContext
)
from legal_spend_mcp.models import SpendSummary


class TestMCPTools:
    """Test MCP tool implementations"""
    
    @pytest.mark.asyncio
    async def test_get_legal_spend_summary_success(self, mock_data_manager, sample_spend_records, mocker):
        """Test successful legal spend summary retrieval"""
        # Setup mock
        mock_data_manager.get_spend_data.return_value = sample_spend_records
        mock_data_manager.generate_summary.return_value = SpendSummary(
            total_amount=Decimal("145000.00"),
            currency="USD",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
            record_count=10,
            top_vendors=[{"name": "Smith & Associates", "amount": 60000.0}],
            top_matters=[{"name": "Matter 1", "amount": 30000.0}],
            by_department={"Legal": Decimal("100000.00")},
            by_practice_area={"Corporate": Decimal("80000.00")}
        )
        
        # Create mock context
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        # Create a mock mcp object and set its request_context
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_legal_spend_summary(
            start_date="2024-01-01",
            end_date="2024-03-31",
            department="Legal"
        )
        
        # Assertions
        assert result["total_amount"] == 145000.0
        assert result["currency"] == "USD"
        assert result["record_count"] == 10
        assert len(result["top_vendors"]) == 1
        assert result["filters_applied"]["department"] == "Legal"
        
        # Verify mock calls
        mock_data_manager.get_spend_data.assert_called_once()
        mock_data_manager.generate_summary.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_legal_spend_summary_invalid_date(self, mock_data_manager, mocker):
        """Test legal spend summary with invalid date format"""
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_legal_spend_summary(
            start_date="invalid-date",
            end_date="2024-03-31"
        )
        
        assert "error" in result
        assert "Invalid date format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_vendor_performance_success(self, mock_data_manager, sample_spend_records, mocker):
        """Test successful vendor performance analysis"""
        # Setup mock
        vendor_records = [r for r in sample_spend_records if r.vendor_name == "Smith & Associates"]
        mock_data_manager.get_vendor_data.return_value = vendor_records
        mock_data_manager.calculate_spend_trend.return_value = {
            "trend": "increasing",
            "change_percentage": 15.5,
            "monthly_totals": {"2024-01": 10000.0, "2024-02": 11550.0}
        }
        mock_data_manager.get_vendor_benchmarks.return_value = {
            "average_invoice_benchmark": 25000,
            "cost_efficiency_score": 0.85
        }
        
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_vendor_performance(
            vendor_name="Smith & Associates",
            start_date="2024-01-01",
            end_date="2024-03-31",
            include_benchmarks=True
        )
        
        # Assertions
        assert result["vendor_name"] == "Smith & Associates"
        assert "performance_metrics" in result
        assert "spend_trend" in result
        assert "industry_benchmarks" in result
        assert result["spend_trend"]["trend"] == "increasing"
    
    @pytest.mark.asyncio
    async def test_get_budget_vs_actual_success(self, mock_data_manager, sample_spend_records, mocker):
        """Test budget vs actual comparison"""
        # Setup mock
        dept_records = [r for r in sample_spend_records if r.department == "Legal"]
        mock_data_manager.get_department_spend.return_value = dept_records
        mock_data_manager.get_monthly_breakdown.return_value = {
            "2024-01": 30000.0,
            "2024-02": 35000.0,
            "2024-03": 35000.0
        }
        mock_data_manager.generate_budget_recommendations.return_value = [
            "Consider renegotiating rates with top vendors",
            "Monitor spending closely for the remainder of the period"
        ]
        
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_budget_vs_actual(
            department="Legal",
            start_date="2024-01-01",
            end_date="2024-03-31",
            budget_amount=90000.0
        )
        
        # Assertions
        assert result["department"] == "Legal"
        assert "budget_analysis" in result
        assert result["budget_analysis"]["budget_amount"] == 90000.0
        assert "monthly_breakdown" in result
        assert "recommendations" in result
        assert len(result["recommendations"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_legal_transactions_success(self, mock_data_manager, sample_spend_records, mocker):
        """Test transaction search functionality"""
        # Setup mock
        mock_data_manager.search_transactions.return_value = sample_spend_records[:3]
        
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await search_legal_transactions(
            search_term="Smith",
            start_date="2024-01-01",
            end_date="2024-03-31",
            min_amount=10000.0,
            limit=10
        )
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 3
        assert all("transaction_id" in item for item in result)
        assert all("vendor_name" in item for item in result)
        assert all("amount" in item for item in result)


class TestMCPResources:
    """Test MCP resource implementations"""
    
    @pytest.mark.asyncio
    async def test_get_legal_vendors(self, mock_data_manager, mocker):
        """Test legal vendors resource"""
        # Setup mock
        mock_data_manager.get_all_vendors.return_value = [
            {"id": "1", "name": "Smith & Associates", "type": "Law Firm", "source": "test"},
            {"id": "2", "name": "Jones Legal", "type": "Law Firm", "source": "test"}
        ]
        
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_legal_vendors()
        
        # Parse JSON result
        data = json.loads(result)
        
        # Assertions
        assert "vendors" in data
        assert len(data["vendors"]) == 2
        assert data["total_count"] == 2
        assert "data_sources" in data
        assert "last_updated" in data
    
    @pytest.mark.asyncio
    async def test_get_data_sources(self, mock_data_manager, mocker):
        """Test data sources status resource"""
        # Setup mock
        mock_data_manager.get_sources_status.return_value = [
            {"name": "test_api", "type": "api", "status": "active", "enabled": True},
            {"name": "test_db", "type": "database", "status": "disconnected", "enabled": True}
        ]
        
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_data_sources()
        
        # Parse JSON result
        data = json.loads(result)
        
        # Assertions
        assert "data_sources" in data
        assert len(data["data_sources"]) == 2
        assert data["active_count"] == 1
        assert data["total_configured"] == 2
    
    @pytest.mark.asyncio
    async def test_get_spend_categories(self, mock_data_manager, mocker):
        """Test spend categories resource"""
        # Setup mock
        mock_data_manager.get_spend_categories.return_value = {
            "expense_categories": ["Legal Services", "Expert Witness Fees"],
            "practice_areas": ["Corporate", "Litigation"],
            "departments": ["Legal", "Compliance"],
            "matter_types": ["Transaction", "Dispute"],
            "completeness_score": 0.85
        }
        
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_spend_categories()
        
        # Parse JSON result
        data = json.loads(result)
        
        # Assertions
        assert "expense_categories" in data
        assert "practice_areas" in data
        assert len(data["expense_categories"]) == 2
        assert data["data_completeness"] == 0.85
    
    @pytest.mark.asyncio
    async def test_get_recent_spend_overview(self, mock_data_manager, mocker):
        """Test recent spend overview resource"""
        # Setup mock
        mock_data_manager.get_spend_overview.return_value = {
            "total_spend": 500000.0,
            "transaction_count": 50,
            "active_vendors": 15,
            "top_categories": [{"category": "Legal Services", "amount": 400000.0}],
            "alerts": [{"type": "high_spend", "message": "Total spend exceeds $1M"}],
            "trends": {"daily_average": 16666.67}
        }
        
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_recent_spend_overview()
        
        # Parse JSON result
        data = json.loads(result)
        
        # Assertions
        assert "period" in data
        assert "Last 30 days" in data["period"]
        assert data["total_spend"] == 500000.0
        assert data["transaction_count"] == 50
        assert len(data["alerts"]) == 1


class TestErrorHandling:
    """Test error handling in various scenarios"""
    
    @pytest.mark.asyncio
    async def test_data_source_connection_failure(self, mock_data_manager, mocker):
        """Test handling of data source connection failures"""
        # Setup mock to raise exception
        mock_data_manager.get_spend_data.side_effect = Exception("Connection failed")
        
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_legal_spend_summary(
            start_date="2024-01-01",
            end_date="2024-03-31"
        )
        
        assert "error" in result
        assert "Failed to get spend summary" in result["error"]
    
    @pytest.mark.asyncio
    async def test_vendor_not_found(self, mock_data_manager, mocker):
        """Test handling when vendor is not found"""
        # Setup mock to return empty list
        mock_data_manager.get_vendor_data.return_value = []
        
        mock_ctx = mocker.Mock()
        mock_ctx.lifespan_context = ServerContext(
            data_manager=mock_data_manager,
            config={"test": True}
        )
        
        mock_mcp_instance = mocker.Mock()
        mock_mcp_instance.request_context = mock_ctx
        mocker.patch("legal_spend_mcp.server.mcp", mock_mcp_instance)

        result = await get_vendor_performance(
            vendor_name="Non-existent Vendor",
            start_date="2024-01-01",
            end_date="2024-03-31"
        )
        
        assert "error" in result
        assert "No data found for vendor" in result["error"]