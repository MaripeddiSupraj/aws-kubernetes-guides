#!/bin/bash
set -e

echo "🎬 Running GKE Cost Optimizer Demo..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  Virtual environment not found. Run ./scripts/setup.sh first${NC}"
    exit 1
fi

echo -e "${BLUE}📊 Running cost optimization analysis...${NC}"
echo "Cluster: ${GKE_CLUSTER_NAME:-demo-cluster}"
echo "Project: ${GCP_PROJECT_ID:-demo-project}"
echo "Zone: ${GCP_ZONE:-us-central1-a}"
echo ""

# Run the optimizer
python src/main.py \
    --project-id "${GCP_PROJECT_ID:-demo-project}" \
    --cluster-name "${GKE_CLUSTER_NAME:-demo-cluster}" \
    --zone "${GCP_ZONE:-us-central1-a}" \
    --output "reports"

echo ""
echo -e "${GREEN}✅ Demo completed!${NC}"
echo "Check the 'reports' directory for detailed analysis."