#!/bin/bash

# Legal Spend MCP Server Deployment Script
# This script handles deployment to various environments

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="legal-spend-mcp"
PYTHON_VERSION="3.10"

# Functions
print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [ "$(echo "$PYTHON_VER < $PYTHON_VERSION" | bc)" -eq 1 ]; then
        print_error "Python $PYTHON_VERSION or higher is required (found $PYTHON_VER)"
        exit 1
    fi
    print_success "Python $PYTHON_VER found"
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        exit 1
    fi
    print_success "Git found"
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please run install.py first"
        exit 1
    fi
    print_success ".env file found"
}

# Run tests
run_tests() {
    print_header "Running Tests"
    
    if python3 -m pytest tests/ -v --cov=legal_spend_mcp --cov-report=term-missing; then
        print_success "All tests passed"
    else
        print_error "Tests failed. Please fix issues before deploying"
        exit 1
    fi
}

# Build package
build_package() {
    print_header "Building Package"
    
    # Clean previous builds
    rm -rf dist/ build/ *.egg-info
    
    # Build the package
    if python3 -m pip install --upgrade build; then
        print_success "Build tools updated"
    else
        print_error "Failed to update build tools"
        exit 1
    fi
    
    if python3 -m pip install -e . && python3 -m build; then
        print_success "Package built successfully"
    else
        print_error "Package build failed"
        exit 1
    fi
}

# Deploy to development environment
deploy_dev() {
    print_header "Deploying to Development Environment"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install in development mode
    pip install -e ".[dev]"
    
    print_success "Development deployment complete"
    print_info "Activate environment with: source venv/bin/activate"
}

# Deploy to Docker
deploy_docker() {
    print_header "Deploying to Docker"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Create Dockerfile if it doesn't exist
    if [ ! -f "Dockerfile" ]; then
        print_info "Creating Dockerfile..."
        cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir .

# Copy environment file (will be overridden by volume mount)
COPY .env.template .env

# Expose MCP server port (if applicable)
EXPOSE 8080

# Run the server
CMD ["python", "-m", "legal_spend_mcp.server"]
EOF
        print_success "Dockerfile created"
    fi
    
    # Build Docker image
    print_info "Building Docker image..."
    if docker build -t $PROJECT_NAME:latest .; then
        print_success "Docker image built successfully"
    else
        print_error "Docker build failed"
        exit 1
    fi
    
    # Create docker-compose.yml if it doesn't exist
    if [ ! -f "docker-compose.yml" ]; then
        print_info "Creating docker-compose.yml..."
        cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  legal-spend-mcp:
    image: legal-spend-mcp:latest
    container_name: legal-spend-mcp
    environment:
      - LOG_LEVEL=INFO
    volumes:
      - ./.env:/app/.env
      - ./data:/app/data  # For file-based data sources
    ports:
      - "8080:8080"  # If the server exposes a port
    restart: unless-stopped
EOF
        print_success "docker-compose.yml created"
    fi
    
    print_success "Docker deployment ready"
    print_info "Run with: docker-compose up -d"
}

# Deploy to cloud (AWS Lambda example)
deploy_cloud() {
    print_header "Deploying to Cloud (AWS Lambda)"
    
    print_warning "Cloud deployment requires additional setup"
    
    # Check if serverless is installed
    if ! command -v serverless &> /dev/null; then
        print_warning "Serverless Framework not installed"
        print_info "Install with: npm install -g serverless"
        exit 1
    fi
    
    # Create serverless.yml if it doesn't exist
    if [ ! -f "serverless.yml" ]; then
        print_info "Creating serverless.yml..."
        cat > serverless.yml << 'EOF'
service: legal-spend-mcp

provider:
  name: aws
  runtime: python3.10
  region: us-east-1
  environment:
    MCP_SERVER_NAME: "Legal Spend Intelligence"
    LOG_LEVEL: INFO

functions:
  mcp-server:
    handler: src.legal_spend_mcp.server.handler
    timeout: 300
    memorySize: 512
    environment:
      LEGALTRACKER_API_KEY: ${env:LEGALTRACKER_API_KEY}
      # Add other environment variables as needed

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
EOF
        print_success "serverless.yml created"
    fi
    
    print_info "Please configure AWS credentials and environment variables"
    print_info "Deploy with: serverless deploy"
}

# Deploy to production server
deploy_production() {
    print_header "Deploying to Production Server"
    
    # Get deployment settings
    read -p "Enter production server hostname: " PROD_HOST
    read -p "Enter SSH user: " SSH_USER
    read -p "Enter deployment directory: " DEPLOY_DIR
    
    print_info "Preparing deployment package..."
    
    # Create deployment archive
    tar -czf deploy.tar.gz \
        src/ \
        pyproject.toml \
        README.md \
        LICENSE \
        .env.template \
        requirements.txt
    
    print_info "Copying files to production server..."
    
    # Copy to server
    scp deploy.tar.gz $SSH_USER@$PROD_HOST:/tmp/
    
    # Deploy on server
    ssh $SSH_USER@$PROD_HOST << EOF
        cd $DEPLOY_DIR
        tar -xzf /tmp/deploy.tar.gz
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -e .
        
        # Set up systemd service (optional)
        sudo tee /etc/systemd/system/legal-spend-mcp.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=Legal Spend MCP Server
After=network.target

[Service]
Type=simple
User=$SSH_USER
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/venv/bin"
ExecStart=$DEPLOY_DIR/venv/bin/python -m legal_spend_mcp.server
Restart=on-failure

[Install]
WantedBy=multi-user.target
SERVICEEOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable legal-spend-mcp
        sudo systemctl start legal-spend-mcp
EOF
    
    # Clean up
    rm deploy.tar.gz
    
    print_success "Production deployment complete"
}

# Create release
create_release() {
    print_header "Creating Release"
    
    # Get version from pyproject.toml
    VERSION=$(grep -oP '(?<=version = ")[^"]*' pyproject.toml)
    
    print_info "Current version: $VERSION"
    read -p "Enter new version (or press Enter to keep current): " NEW_VERSION
    
    if [ ! -z "$NEW_VERSION" ]; then
        # Update version in pyproject.toml
        sed -i "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
        VERSION=$NEW_VERSION
        
        # Commit version change
        git add pyproject.toml
        git commit -m "Bump version to $VERSION"
    fi
    
    # Create git tag
    git tag -a "v$VERSION" -m "Release version $VERSION"
    
    # Build release
    build_package
    
    print_success "Release v$VERSION created"
    print_info "Push with: git push origin main --tags"
    print_info "Upload to PyPI with: twine upload dist/*"
}

# Main menu
show_menu() {
    print_header "Legal Spend MCP Server Deployment"
    
    echo "Select deployment option:"
    echo "1) Development Environment"
    echo "2) Docker Container"
    echo "3) Cloud (AWS Lambda)"
    echo "4) Production Server"
    echo "5) Create Release"
    echo "6) Run Tests Only"
    echo "7) Exit"
    echo
    read -p "Enter your choice (1-7): " choice
    
    case $choice in
        1)
            check_prerequisites
            run_tests
            deploy_dev
            ;;
        2)
            check_prerequisites
            run_tests
            build_package
            deploy_docker
            ;;
        3)
            check_prerequisites
            run_tests
            build_package
            deploy_cloud
            ;;
        4)
            check_prerequisites
            run_tests
            build_package
            deploy_production
            ;;
        5)
            check_prerequisites
            run_tests
            create_release
            ;;
        6)
            check_prerequisites
            run_tests
            ;;
        7)
            print_info "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Run main menu
show_menu

print_success "Deployment script completed!"