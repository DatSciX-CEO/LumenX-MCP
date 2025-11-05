#!/bin/bash
# Setup script for GNN Application

set -e

echo "==================================="
echo "GNN Application Setup"
echo "==================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Warning: Node.js is not installed. Frontend will not be built."
else
    echo "Node version: $(node --version)"
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements-gnn.txt

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p data models .cache

# Copy environment file
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Install frontend dependencies (if Node.js is available)
if command -v node &> /dev/null; then
    echo ""
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Download Ollama model (optional)
read -p "Do you want to download Ollama model for local LLM? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v ollama &> /dev/null; then
        echo "Downloading llama3.2 model..."
        ollama pull llama3.2
    else
        echo "Ollama is not installed. Please install from https://ollama.ai"
    fi
fi

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "To start the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start backend: python -m uvicorn gnn_app.api.main:app --reload"
echo "3. Start frontend (in another terminal): cd frontend && npm run dev"
echo ""
echo "Or use Docker:"
echo "docker-compose -f docker-compose.gnn.yml up"
echo ""
