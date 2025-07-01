# LumenX-MCP: The Legal Spend Intelligence Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://github.com/modelcontextprotocol)

**Unlock the full potential of your legal spend data.** LumenX-MCP is an open-source, enterprise-grade server that unifies your legal and financial data from any source, providing a single, intelligent point of access for AI agents and analytics platforms.

Built on the **Model Context Protocol (MCP)**, this server allows you to seamlessly connect to e-billing platforms, ERP systems, databases, and even local files, transforming fragmented data into a queryable, actionable resource.

---

## Key Features

- **Unified Data Access**: Connect to multiple data sources simultaneously, from LegalTracker and SAP to local CSV files.
- **Comprehensive Analytics**: Get instant insights with tools for spend summaries, vendor performance analysis, and budget variance.
- **Extensible by Design**: A modular architecture makes it easy to add new data source connectors and expand capabilities.
- **AI-Ready**: Built for the future of legal tech, enabling powerful integrations with AI agents and large language models.
- **High Performance**: A fully asynchronous architecture ensures that data retrieval is fast and efficient.
- **Enterprise-Grade**: Robust, validatable configuration and full Docker support for reliable, containerized deployments.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Docker (recommended for the easiest setup)
- Access to one or more of the supported data sources

### Installation

<<<<<<< HEAD
#### Using Docker (Recommended)

For a consistent and isolated environment, we recommend using Docker.

1.  **Build the Docker image:**
    ```bash
    docker build -t legal-spend-mcp .
    ```

2.  **Run the container:**
    ```bash
    docker run -d --name legal-spend-mcp -v ./.env:/app/.env -v ./data:/app/data legal-spend-mcp
    ```

#### From Source

If you prefer to install from source, you have two options:

1.  **Editable install (recommended for developers):** This uses the `pyproject.toml` file and is the best option if you plan to contribute.
    ```bash
    # Clone the repository
    git clone https://github.com/DatSciX-CEO/LumenX-MCP.git
    cd LumenX-MCP

    # Create virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install in editable mode with dev dependencies
    pip install -e .[dev]
    ```

2.  **Using `requirements.txt`:** This is a standard way to install dependencies for deployment or general use.
    ```bash
    # After cloning and activating your virtual environment
    pip install -r requirements.txt
    ```

### Configuration

1.  **Create your environment file:**
    ```bash
    cp .env.template .env
    ```

2.  **Enable your data sources:** Edit the `.env` file to enable the platforms you use and provide your credentials. The server will only initialize the sources you enable.
    ```dotenv
    # Enable the data sources you want to use
    LEGALTRACKER_ENABLED=true
    LEGALTRACKER_API_KEY=your_api_key_here
    LEGALTRACKER_BASE_URL=https://api.legaltracker.com

    # For instance-specific URLs, be sure to use your organization's endpoint
    ONIT_ENABLED=true
    ONIT_API_KEY=your_api_key
    ONIT_BASE_URL=https://<your-company>.onit.com
    ```

### Launch the Server

Once configured, you can start the server with:

```bash
python -m legal_spend_mcp.server
```
=======
### Using Docker (Recommended)

For a consistent and isolated environment, we recommend using Docker.

1.  **Build the Docker image:**
    ```bash
    docker build -t legal-spend-mcp .
    ```

2.  **Run the container:**
    ```bash
    docker run -d --name legal-spend-mcp -v ./.env:/app/.env -v ./data:/app/data legal-spend-mcp
    ```
>>>>>>> bdc9efc79a8022a84f6ec27e90604850f6513a1e

For more detailed instructions, see the [QUICKSTART.md](QUICKSTART.md) guide.

<<<<<<< HEAD
---

## Available Tools & Resources

The server exposes a rich set of tools and resources for any MCP-compatible client.

### Tools (Callable Functions)

-   `get_legal_spend_summary`: Get aggregated spend data with powerful filtering.
-   `get_vendor_performance`: Analyze performance metrics for a specific vendor.
-   `get_budget_vs_actual`: Compare actual spending against budgeted amounts.
-   `search_legal_transactions`: Perform a full-text search for specific transactions.

### Resources (Data Objects)
=======
<<<<<<< HEAD
If you prefer to install from source, you have two options:
=======
If you prefer to install from source:

```bash
# Clone the repository
git clone https://github.com/DatSciX-CEO/LumenX-MCP.git
cd LumenX-MCP
>>>>>>> 7d22fe718ed2de01113e744a44ac6d373ee3e75e

1.  **Editable install (recommended for developers):** This uses the `pyproject.toml` file and is the best option if you plan to contribute.
    ```bash
    # Clone the repository
    git clone https://github.com/DatSciX-CEO/LumenX-MCP.git
    cd LumenX-MCP

<<<<<<< HEAD
    # Create virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install in editable mode with dev dependencies
    pip install -e .[dev]
    ```

2.  **Using `requirements.txt`:** This is a standard way to install dependencies for deployment or general use.
    ```bash
    # After cloning and activating your virtual environment
    pip install -r requirements.txt
    ```
=======
# Install dependencies
pip install -e .[dev]
```
>>>>>>> 7d22fe718ed2de01113e744a44ac6d373ee3e75e
>>>>>>> bdc9efc79a8022a84f6ec27e90604850f6513a1e

-   `legal_vendors`: A comprehensive list of all vendors across all data sources.
-   `data_sources`: The status and configuration of all connected data sources.
-   `spend_categories`: All available spend categories, practice areas, and departments.
-   `spend_overview/recent`: A high-level overview of spend activity from the last 30 days.

---

## Supported Data Sources

LumenX-MCP is built to be a central hub for all your legal data.

### E-Billing & Matter Management
- **LegalTracker**: Real-time invoice and matter data.
- **SimpleLegal**: (Planned) Integration with SimpleLegal's API.
- **Brightflag**: (Planned) Integration with Brightflag's API.
- **TyMetrix 360**: (Planned) Integration with TyMetrix 360's API.
- **Onit**: (Planned) Integration with Onit's API.

<<<<<<< HEAD
=======
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

### E-Billing & Matter Management
- **LegalTracker**: Real-time invoice and matter data.
- **SimpleLegal**: (Planned) Integration with SimpleLegal's API.
- **Brightflag**: (Planned) Integration with Brightflag's API.
- **TyMetrix 360**: (Planned) Integration with TyMetrix 360's API.
- **Onit**: (Planned) Integration with Onit's API.

>>>>>>> bdc9efc79a8022a84f6ec27e90604850f6513a1e
### ERP Systems
- **SAP**: Via SQL Server database connection.
- **Oracle**: Via Oracle database connection.
- **Microsoft Dynamics 365**: (Planned) Integration with Dynamics 365's API.
- **NetSuite**: (Planned) Integration with NetSuite's API.

### Databases
- **PostgreSQL**: Full support for legal spend tables.
- **SQL Server**: Compatible with SAP and other ERP systems.
- **Oracle**: Enterprise financial system integration.

### File Imports
- **CSV**: Standard comma-separated values.
- **Excel**: .xlsx files with configurable sheet names.

---

## Contributing

We welcome contributions of all kinds, from bug fixes to new data source connectors! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
