# Quick Start Guide - Legal Spend MCP Server

Get up and running with the Legal Spend MCP Server in 5 minutes!

## 🚀 Quick Installation

### Option 1: Using Python pip

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

### Option 2: Using uv (faster)

```bash
# Install uv
pip install uv

# Clone and install
git clone https://github.com/DatSciX-CEO/LumenX-MCP.git
cd LumenX-MCP
uv pip install -e .
```

## ⚡ Quick Setup

### 1. Configure Environment

```bash
# Copy the sample environment file
cp .env.sample .env

# Or use the template
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

## 🔌 Connect to Claude Desktop

### Automatic Setup

```bash
# Run the installation script
python scripts/install.py
```

When prompted, choose "y" to set up Claude Desktop integration.

### Manual Setup

Add to your Claude Desktop config file:

**Windows**: `%APPDATA%\Claude\config\claude_config.json`  
**macOS**: `~/Library/Application Support/Claude/config/claude_config.json`  
**Linux**: `~/.config/claude/claude_config.json`

```json
{
  "mcpServers": {
    "legal-spend": {
      "command": "python",
      "args": ["-m", "legal_spend_mcp.server"],
      "cwd": "/path/to/LumenX-MCP",
      "env": {
        "PYTHONPATH": "/path/to/LumenX-MCP/src"
      }
    }
  }
}
```

## 🎯 Test It Out

Once connected to Claude Desktop, try these commands:

### Get Recent Spend Summary
Ask Claude: "What's our legal spend for the last quarter?"

### Search Transactions
Ask Claude: "Find all invoices from Smith & Associates over $20,000"

### Vendor Analysis
Ask Claude: "Analyze the performance of Jones Legal Partners"

### Budget Check
Ask Claude: "How is the Legal department tracking against budget?"

## 📊 Sample Queries

Here are some example queries to try with the sample data:

1. **Spend Overview**
   - "Show me total legal spend for Q1 2024"
   - "What are our top 5 vendors by spend?"

2. **Department Analysis**
   - "Break down legal spend by department"
   - "Which department has the highest legal costs?"

3. **Practice Area Insights**
   - "What's our spend on intellectual property matters?"
   - "Compare litigation vs corporate legal spend"

4. **Vendor Performance**
   - "How much have we spent with Smith & Associates?"
   - "Show me the trend for our top vendors"

5. **Transaction Search**
   - "Find all expert witness fees"
   - "Show me all invoices for the Patent Litigation Case"

## 🔧 Troubleshooting

### Server Won't Start
- Check Python version: `python --version` (need 3.10+)
- Verify .env file exists and has correct permissions
- Check logs: `LOG_LEVEL=DEBUG python -m legal_spend_mcp.server`

### Can't Connect to Claude
- Restart Claude Desktop after configuration
- Verify the path in claude_config.json is correct
- Check if the server is running: look for process listening on configured port

### No Data Showing
- Verify CSV_ENABLED=true in .env
- Check the CSV_FILE_PATH points to the sample data
- Ensure the dates in your queries match the sample data (2024)

## 📚 Next Steps

1. **Add Real Data Sources**
   - Configure LegalTracker API credentials
   - Set up database connections
   - Import your own CSV/Excel files

2. **Customize Categories**
   - Edit practice areas in models.py
   - Add custom vendor types
   - Define your expense categories

3. **Deploy to Production**
   - Run `bash scripts/deploy.sh`
   - Choose deployment option (Docker, Cloud, etc.)
   - Set up monitoring and alerts

## 🆘 Getting Help

- **Documentation**: See README.md for detailed docs
- **Issues**: https://github.com/DatSciX-CEO/LumenX-MCP/issues
- **Discussions**: https://github.com/DatSciX-CEO/LumenX-MCP/discussions

---

🎉 **Congratulations!** You're now running the Legal Spend MCP Server!