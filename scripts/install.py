#!/usr/bin/env python3
"""
Installation script for Legal Spend MCP Server

This script handles the installation and setup of the Legal Spend MCP Server,
including environment configuration and dependency verification.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import json
from typing import Dict, Any, Optional


class Colors:
    """Terminal colors for output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message: str):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.OKBLUE}ℹ️  {message}{Colors.ENDC}")


def check_python_version():
    """Check if Python version meets requirements"""
    print_info("Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error(f"Python 3.10+ is required. You have {version.major}.{version.minor}.{version.micro}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH"""
    return shutil.which(command) is not None


def install_dependencies():
    """Install Python dependencies"""
    print_info("Installing dependencies...")
    
    # Check if we should use uv or pip
    use_uv = check_command_exists("uv")
    
    if use_uv:
        print_info("Using uv for installation (faster)...")
        cmd = ["uv", "pip", "install", "-e", ".[dev]"]
    else:
        print_info("Using pip for installation...")
        cmd = [sys.executable, "-m", "pip", "install", "-e", ".[dev]"]
    
    try:
        subprocess.run(cmd, check=True)
        print_success("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def setup_environment():
    """Set up environment configuration"""
    print_info("Setting up environment configuration...")
    
    env_template = Path(".env.template")
    env_file = Path(".env")
    
    if not env_template.exists():
        print_error(".env.template not found")
        return False
    
    if env_file.exists():
        response = input(f"\n{Colors.WARNING}.env file already exists. Overwrite? (y/N): {Colors.ENDC}")
        if response.lower() != 'y':
            print_info("Keeping existing .env file")
            return True
    
    # Copy template to .env
    shutil.copy(env_template, env_file)
    print_success(".env file created from template")
    
    # Offer to configure data sources
    print_info("\nWould you like to configure data sources now?")
    configure = input(f"{Colors.OKCYAN}Configure data sources? (y/N): {Colors.ENDC}")
    
    if configure.lower() == 'y':
        configure_data_sources(env_file)
    else:
        print_info("You can configure data sources later by editing .env")
    
    return True


def configure_data_sources(env_file: Path):
    """Interactive configuration of data sources"""
    print_header("Data Source Configuration")
    
    config_lines = env_file.read_text().splitlines()
    updated_lines = []
    
    # LegalTracker configuration
    print_info("\n1. LegalTracker API Configuration")
    use_legaltracker = input("Enable LegalTracker API? (y/N): ").lower() == 'y'
    
    for line in config_lines:
        if line.startswith("LEGALTRACKER_ENABLED="):
            updated_lines.append(f"LEGALTRACKER_ENABLED={'true' if use_legaltracker else 'false'}")
        elif line.startswith("LEGALTRACKER_API_KEY=") and use_legaltracker:
            api_key = input("Enter LegalTracker API key: ").strip()
            if api_key:
                updated_lines.append(f"LEGALTRACKER_API_KEY={api_key}")
            else:
                updated_lines.append(line)
        elif line.startswith("LEGALTRACKER_BASE_URL=") and use_legaltracker:
            base_url = input("Enter LegalTracker base URL (press Enter for default): ").strip()
            if base_url:
                updated_lines.append(f"LEGALTRACKER_BASE_URL={base_url}")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Database configuration
    print_info("\n2. Database Configuration")
    databases = {
        "PostgreSQL": ("POSTGRES", "5432"),
        "SQL Server (SAP)": ("SAP", "1433"),
        "Oracle": ("ORACLE", "1521")
    }
    
    for db_name, (prefix, default_port) in databases.items():
        use_db = input(f"\nEnable {db_name}? (y/N): ").lower() == 'y'
        
        if use_db:
            print_info(f"Configuring {db_name}...")
            host = input("Host: ").strip()
            port = input(f"Port (default {default_port}): ").strip() or default_port
            database = input("Database name: ").strip()
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            
            # Update configuration
            for i, line in enumerate(updated_lines):
                if line.startswith(f"{prefix}_ENABLED="):
                    updated_lines[i] = f"{prefix}_ENABLED=true"
                elif line.startswith(f"{prefix}_HOST="):
                    updated_lines[i] = f"{prefix}_HOST={host}"
                elif line.startswith(f"{prefix}_PORT="):
                    updated_lines[i] = f"{prefix}_PORT={port}"
                elif line.startswith(f"{prefix}_DATABASE=") or line.startswith(f"{prefix}_DB="):
                    updated_lines[i] = f"{line.split('=')[0]}={database}"
                elif line.startswith(f"{prefix}_USER="):
                    updated_lines[i] = f"{prefix}_USER={username}"
                elif line.startswith(f"{prefix}_PASSWORD="):
                    updated_lines[i] = f"{prefix}_PASSWORD={password}"
    
    # File sources configuration
    print_info("\n3. File Sources Configuration")
    
    # CSV configuration
    use_csv = input("\nEnable CSV file import? (y/N): ").lower() == 'y'
    if use_csv:
        csv_path = input("Enter CSV file path: ").strip()
        for i, line in enumerate(updated_lines):
            if line.startswith("CSV_ENABLED="):
                updated_lines[i] = "CSV_ENABLED=true"
            elif line.startswith("CSV_FILE_PATH="):
                updated_lines[i] = f"CSV_FILE_PATH={csv_path}"
    
    # Excel configuration
    use_excel = input("\nEnable Excel file import? (y/N): ").lower() == 'y'
    if use_excel:
        excel_path = input("Enter Excel file path: ").strip()
        sheet_name = input("Enter sheet name (default 'Sheet1'): ").strip() or "Sheet1"
        for i, line in enumerate(updated_lines):
            if line.startswith("EXCEL_ENABLED="):
                updated_lines[i] = "EXCEL_ENABLED=true"
            elif line.startswith("EXCEL_FILE_PATH="):
                updated_lines[i] = f"EXCEL_FILE_PATH={excel_path}"
            elif line.startswith("EXCEL_SHEET_NAME="):
                updated_lines[i] = f"EXCEL_SHEET_NAME={sheet_name}"
    
    # Write updated configuration
    env_file.write_text('\n'.join(updated_lines))
    print_success("Configuration saved to .env")


def setup_mcp_client():
    """Set up MCP client configuration"""
    print_info("\nSetting up MCP client configuration...")
    
    # Detect Claude Desktop configuration
    system = platform.system()
    
    if system == "Windows":
        config_dir = Path.home() / "AppData" / "Roaming" / "Claude" / "config"
    elif system == "Darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support" / "Claude" / "config"
    else:  # Linux
        config_dir = Path.home() / ".config" / "claude"
    
    config_file = config_dir / "claude_config.json"
    
    if not config_dir.exists():
        print_warning(f"Claude configuration directory not found at {config_dir}")
        print_info("Please ensure Claude Desktop is installed")
        return False
    
    # Load existing config or create new
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Add our server configuration
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Get the current script directory
    server_path = Path.cwd()
    
    config["mcpServers"]["legal-spend"] = {
        "command": "python",
        "args": ["-m", "legal_spend_mcp.server"],
        "cwd": str(server_path),
        "env": {
            "PYTHONPATH": str(server_path / "src")
        }
    }
    
    # Write updated config
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print_success(f"MCP client configuration updated at {config_file}")
        return True
    except Exception as e:
        print_error(f"Failed to update MCP client configuration: {e}")
        return False


def run_tests():
    """Run test suite to verify installation"""
    print_info("\nRunning tests to verify installation...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("All tests passed!")
            return True
        else:
            print_warning("Some tests failed. Check the output above.")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to run tests: {e}")
        return False


def main():
    """Main installation function"""
    print_header("Legal Spend MCP Server Installation")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Set up environment
    if not setup_environment():
        sys.exit(1)
    
    # Offer to set up MCP client
    setup_client = input(f"\n{Colors.OKCYAN}Set up Claude Desktop integration? (y/N): {Colors.ENDC}")
    if setup_client.lower() == 'y':
        setup_mcp_client()
    
    # Offer to run tests
    run_tests_prompt = input(f"\n{Colors.OKCYAN}Run tests to verify installation? (y/N): {Colors.ENDC}")
    if run_tests_prompt.lower() == 'y':
        run_tests()
    
    # Final instructions
    print_header("Installation Complete!")
    
    print(f"{Colors.OKGREEN}✨ Legal Spend MCP Server has been installed successfully!{Colors.ENDC}\n")
    
    print("Next steps:")
    print("1. Review and update the configuration in .env")
    print("2. Start the server with: python -m legal_spend_mcp.server")
    print("3. Restart Claude Desktop to load the MCP server")
    
    print(f"\n{Colors.OKCYAN}For more information, see the README.md file.{Colors.ENDC}")


if __name__ == "__main__":
    main()