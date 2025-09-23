#!/bin/bash
set -e

echo "🚀 Setting up GKE Cost Optimizer Agent..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required but not installed${NC}"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is required but not installed${NC}"
        exit 1
    fi
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI is required but not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites are installed${NC}"
}

# Setup Python virtual environment
setup_python_env() {
    echo "🐍 Setting up Python environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ Python environment ready${NC}"
}

# Setup GCP authentication
setup_gcp_auth() {
    echo "🔐 Setting up GCP authentication..."
    
    # Check if already authenticated
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        echo -e "${GREEN}✅ Already authenticated with GCP${NC}"
    else
        echo "Please authenticate with GCP:"
        gcloud auth login
        gcloud auth application-default login
    fi
}

# Create necessary directories
create_directories() {
    echo "📁 Creating directories..."
    
    mkdir -p reports logs
    chmod 755 reports logs
    
    echo -e "${GREEN}✅ Directories created${NC}"
}

# Setup environment file
setup_env_file() {
    echo "📝 Setting up environment file..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env file with your configuration${NC}"
    else
        echo -e "${GREEN}✅ .env file already exists${NC}"
    fi
}

# Main setup function
main() {
    echo "🎯 GKE Cost Optimizer Agent Setup"
    echo "=================================="
    
    check_prerequisites
    setup_python_env
    create_directories
    setup_env_file
    setup_gcp_auth
    
    echo ""
    echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your GCP configuration"
    echo "2. Run: source venv/bin/activate"
    echo "3. Run: python src/main.py --help"
}

# Run main function
main "$@"