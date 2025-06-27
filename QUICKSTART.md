# Quick Start Guide - Legal Spend MCP Server

Get up and running with the Legal Spend MCP Server in 5 minutes!

## 🚀 Quick Installation

### Using Python pip

```bash
# Clone the repository
git clone https://github.com/DatSciX-CEO/LumenX-MCP.git
cd LumenX-MCP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

## ⚡ Quick Setup

### 1. Configure Environment

```bash
# Copy the sample environment file
cp .env.template .env
```

### 2. Quick Test with Sample Data

The repository includes sample data to test immediately:

```bash
# Edit .env to use the sample CSV
CSV_ENABLED=true
CSV_FILE_PATH=./data/legal_spend_sample.csv
```

### 3. Run the Server

```bash
# Start the MCP server
python -m legal_spend_mcp.server
```

## 🔌 Integration

For details on integrating with clients like Claude Desktop, refer to [INTEGRATION.md](INTEGRATION.md).

## 🎯 Examples

For sample queries and usage examples, refer to [EXAMPLES.md](EXAMPLES.md).

## 🔧 Troubleshooting & Support

For troubleshooting tips and support options, refer to [SUPPORT.md](SUPPORT.md).

## 📚 Next Steps & Roadmap

For future plans and development roadmap, refer to [ROADMAP.md](ROADMAP.md).
