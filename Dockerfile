FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for building certain Python packages
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy only necessary files for installation
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package and its dependencies
RUN pip install --no-cache-dir .

# Copy the environment template which can be used as a base
COPY .env.template .env

# Expose the default MCP server port (if it runs a web server)
# This is often not needed for CLI-based MCP servers but is good practice
EXPOSE 8080

# Command to run the server
CMD ["python", "-m", "legal_spend_mcp.server"]
