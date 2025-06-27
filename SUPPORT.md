# Troubleshooting & Support - Legal Spend MCP Server

This document provides common troubleshooting tips and information on how to get support for the Legal Spend MCP Server.

## 🔧 Troubleshooting

### Server Won't Start

-   **Check Python version**: Ensure you have Python 3.10 or higher installed. You can check your version with: `python --version`
-   **Verify `.env` file**: Make sure the `.env` file exists in the project root and has the correct permissions. It should be copied from `.env.template`.
-   **Check logs**: Increase the logging level to `DEBUG` in your `.env` file and restart the server to get more detailed output:
    ```bash
    LOG_LEVEL=DEBUG python -m legal_spend_mcp.server
    ```

### Can't Connect to MCP Client (e.g., Claude Desktop)

-   **Restart Client**: After configuring the MCP server, restart your client application (e.g., Claude Desktop) to ensure it reloads the configuration.
-   **Verify Configuration Path**: Double-check that the `claude_config.json` (or equivalent) file path is correct and that the `cwd` and `PYTHONPATH` settings are accurate for your environment.
-   **Server Running**: Confirm that the Legal Spend MCP Server is actually running. Look for its process listening on the configured port (default is usually `8080` if exposed).

### No Data Showing or Incorrect Results

-   **Enable Data Source**: Verify that the data source you expect to use is enabled in your `.env` file (e.g., `CSV_ENABLED=true`).
-   **File Paths**: If using file-based sources (CSV, Excel), ensure `CSV_FILE_PATH` or `EXCEL_FILE_PATH` in your `.env` points to the correct and accessible data file.
-   **Date Ranges**: Ensure the dates in your queries match the data available in your configured sources. For sample data, dates are typically in 2024.
-   **Data Format**: Confirm that your data files (CSV, Excel) adhere to the expected format and column names as described in `data/README.md`.

## 🆘 Getting Help

If you encounter issues that you cannot resolve using the troubleshooting steps above, please use the following resources:

-   **GitHub Issues**: For bug reports, feature requests, or detailed technical questions, please open an issue on our GitHub repository:
    [https://github.com/DatSciX-CEO/LumenX-MCP/issues](https://github.com/DatSciX-CEO/LumenX-MCP/issues)

-   **GitHub Discussions**: For general questions, ideas, or community discussions, visit our GitHub Discussions page:
    [https://github.com/DatSciX-CEO/LumenX-MCP/discussions](https://github.com/DatSciX-CEO/LumenX-MCP/discussions)

-   **Email Support**: For private inquiries or direct support, you can reach out to:
    patrick@datscix.com

When seeking help, please provide as much detail as possible, including:

-   The exact steps to reproduce the issue.
-   Any error messages or logs.
-   Your operating system and Python version.
-   Relevant parts of your `.env` configuration (excluding sensitive credentials).

We appreciate your patience and will do our best to assist you!
