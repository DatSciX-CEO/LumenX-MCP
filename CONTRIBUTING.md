# Contributing to LumenX-MCP

First off, thank you for considering contributing to the Legal Spend Intelligence Server! We welcome any and all contributions, from bug reports to new features.

## Getting Started

To get started, you'll need to set up a local development environment.

### 1. Fork & Clone

1.  **Fork** the repository on GitHub.
2.  **Clone** your fork locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/LumenX-MCP.git
    cd LumenX-MCP
    ```

### 2. Set Up Environment

We recommend using a virtual environment to manage dependencies.

**Using `venv` (standard):**
```bash
# Create a virtual environment
python -m venv venv

# Activate it
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

For development, you can install all dependencies using one of the following methods:

**Using `pyproject.toml` (recommended):**
This is the preferred method as it uses the primary dependency definition.
```bash
pip install -e ".[dev]"
```

**Using `requirements-dev.txt`:**
This file contains all core and development dependencies.
```bash
pip install -r requirements-dev.txt
```

## Running Tests

We use `pytest` for testing. To ensure your changes are working correctly, please run the full test suite.

```bash
pytest
```

To run tests with coverage reporting:
```bash
pytest --cov=legal_spend_mcp
```

## Code Style & Linting

We enforce a consistent code style using `black`, `ruff`, and `mypy`. Before submitting your changes, please run these tools to format your code and check for issues.

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type-check with MyPy
mypy src/
```

Our CI pipeline will also run these checks, so it's best to run them locally first.

## Submitting Changes

1.  Create a new branch for your feature or bug fix:
    ```bash
    git checkout -b feature/my-amazing-feature
    ```

2.  Make your changes.

3.  Run the tests and linters as described above.

4.  Commit your changes with a descriptive commit message. We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.
    ```bash
    git commit -m "feat: Add new analytics endpoint for vendor comparison"
    ```

5.  Push your branch to your fork:
    ```bash
    git push origin feature/my-amazing-feature
    ```

6.  Open a **Pull Request** from your fork to the `main` branch of the original repository. Provide a clear description of your changes.

## Code of Conduct

This project and everyone participating in it is governed by a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior.
