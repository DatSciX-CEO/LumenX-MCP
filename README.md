# LumenX-MCP Legal Spend Intelligence Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://github.com/modelcontextprotocol)

A Model Context Protocol (MCP) server for intelligent legal spend analysis across multiple data sources. Part of the LumenX suite powered by DatSciX.

## 🚀 Features

- **Multi-Source Integration**: Connect to multiple data sources simultaneously
  - LegalTracker API integration
  - Database support (PostgreSQL, SQL Server, Oracle)
  - File imports (CSV, Excel)
- **Comprehensive Analytics**:
  - Spend summaries by period, department, practice area
  - Vendor performance analysis
  - Budget vs. actual comparisons
  - Transaction search capabilities
- **MCP Compliant**: Full implementation of Model Context Protocol standards
- **Async Architecture**: High-performance asynchronous data processing
- **Extensible Design**: Easy to add new data sources and analytics

## 📋 Prerequisites

- Python 3.10 or higher
- Access to one or more supported data sources
- MCP-compatible client (e.g., Claude Desktop)

## 🛠️ Installation

### Using pip

```bash
pip install legal-spend-mcp
```

### From Source

```bash
# Clone the repository
git clone https://github.com/DatSciX-CEO/LumenX-MCP.git
cd LumenX-MCP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Using uv (recommended)

```bash
# Install uv if not already installed
pip install uv

# Clone and install
git clone https://github.com/DatSciX-CEO/LumenX-MCP.git
cd LumenX-MCP
uv pip install -e .
```

## ⚙️ Configuration

1. Copy the environment template:
```bash
cp .env.template .env
```

2. Edit `.env` with your data source credentials:

```bash
# Enable the data sources you want to use
LEGALTRACKER_ENABLED=true
LEGALTRACKER_API_KEY=your_api_key_here
LEGALTRACKER_BASE_URL=https://api.legaltracker.com

# Database connections (optional)
SAP_ENABLED=false
SAP_HOST=your_sap_host
SAP_PORT=1433
SAP_DATABASE=your_database
SAP_USER=your_username
SAP_PASSWORD=your_password

# File sources (optional)
CSV_ENABLED=true
CSV_FILE_PATH=/path/to/legal_spend.csv
```

## 🚀 Quick Start

Refer to the [QUICKSTART.md](QUICKSTART.md) for detailed instructions on how to get the server up and running.

## 📚 Available Tools

### `legal-spend-mcp://tools/get_legal_spend_summary`
Get aggregated spend data with filtering options.

**Parameters:**
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format
- `department` (optional): Filter by department
- `practice_area` (optional): Filter by practice area
- `vendor` (optional): Filter by vendor name
- `data_source` (optional): Query specific data source

**Example:**
```python
result = await get_legal_spend_summary(
    start_date="2024-01-01",
    end_date="2024-12-31",
    department="Legal"
)
```

### `legal-spend-mcp://tools/get_vendor_performance`
Analyze performance metrics for a specific vendor.

**Parameters:**
- `vendor_name` (required): Name of the vendor
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format
- `include_benchmarks` (optional): Include industry comparisons

### `legal-spend-mcp://tools/get_budget_vs_actual`
Compare actual spending against budgeted amounts.

**Parameters:**
- `department` (required): Department name
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format
- `budget_amount` (required): Budget amount to compare

### `legal-spend-mcp://tools/search_legal_transactions`
Search for specific transactions across all data sources.

**Parameters:**
- `search_term` (required): Search query
- `start_date` (optional): Start date filter
- `end_date` (optional): End date filter
- `min_amount` (optional): Minimum amount filter
- `max_amount` (optional): Maximum amount filter
- `limit` (optional): Maximum results (default: 50)

## 📊 Resources

The server provides several MCP resources for reference data:

- [`legal-spend-mcp://resources/legal_vendors`](legal-spend-mcp://resources/legal_vendors): List of all vendors across data sources
- [`legal-spend-mcp://resources/data_sources`](legal-spend-mcp://resources/data_sources): Status and configuration of data sources
- [`legal-spend-mcp://resources/spend_categories`](legal-spend-mcp://resources/spend_categories): Available categories and practice areas
- [`legal-spend-mcp://resources/spend_overview/recent`](legal-spend-mcp://resources/spend_overview/recent): Recent spend activity overview

## 🔌 Supported Data Sources

### LegalTracker API
- Real-time invoice and matter data
- Vendor management information
- Practice area classifications

### Databases
- **PostgreSQL**: Full support for legal spend tables
- **SQL Server**: Compatible with SAP and other ERP systems
- **Oracle**: Enterprise financial system integration

### File Imports
- **CSV**: Standard comma-separated values
- **Excel**: .xlsx files with configurable sheet names

## 📝 Data Model

The server uses a standardized data model for legal spend records:

```python
@dataclass
class LegalSpendRecord:
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
    # ... additional fields
```

## 🧪 Testing

Refer to the [CONTRIBUTING.md](CONTRIBUTING.md) for instructions on how to run tests.

## 🤝 Contributing

Refer to the [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io)
- Powered by [DatSciX](https://datscix.com)
- Part of the LumenX suite of enterprise tools

## 📞 Support

Refer to the [SUPPORT.md](SUPPORT.md) for information on how to get help.

## 🗺️ Roadmap

Refer to the [ROADMAP.md](ROADMAP.md) for future plans and features.