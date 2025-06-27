# Integration Guide - Legal Spend MCP Server

This guide provides instructions on how to integrate the Legal Spend MCP Server with various clients and tools.

## Claude Desktop Integration

### Automatic Setup

To automatically set up Claude Desktop integration, run the installation script:

```bash
python scripts/install.py
```

When prompted, choose "y" to set up Claude Desktop integration.

### Manual Setup

To manually configure Claude Desktop, add the following to your Claude Desktop config file:

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

## Other MCP Clients

If you are using another MCP-compatible client, you will need to configure it to connect to the Legal Spend MCP Server. Refer to your client's documentation for specific instructions.

**Server Endpoint**: The Legal Spend MCP Server typically runs on `http://localhost:8080` (or another port if configured in your `.env` file).

**MCP Tools and Resources**: The server exposes the following tools and resources:

- **Tools**:
  - `legal-spend-mcp://tools/get_legal_spend_summary`
  - `legal-spend-mcp://tools/get_vendor_performance`
  - `legal-spend-mcp://tools/get_budget_vs_actual`
  - `legal-spend-mcp://tools/search_legal_transactions`

- **Resources**:
  - `legal-spend-mcp://resources/legal_vendors`
  - `legal-spend-mcp://resources/data_sources`
  - `legal-spend-mcp://resources/spend_categories`
  - `legal-spend-mcp://resources/spend_overview/recent`
