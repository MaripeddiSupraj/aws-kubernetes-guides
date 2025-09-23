# GKE Cost Optimizer Agent

An intelligent AI agent that continuously monitors GKE clusters for cost optimization opportunities and resource waste.

## 🎯 Features

- **Resource Waste Detection**: Identifies underutilized pods and nodes
- **Cost Analysis**: Calculates potential savings with specific recommendations
- **Zombie Resource Cleanup**: Finds unused PVCs, services, and load balancers
- **Right-sizing Recommendations**: Suggests optimal CPU/memory requests
- **Node Pool Optimization**: Recommends machine types and autoscaling settings
- **Automated Reports**: Generates actionable cost optimization reports

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GKE Cluster   │───▶│  Cost Optimizer  │───▶│   Dashboard     │
│   (Metrics)     │    │     Agent        │    │   (Reports)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  GCP Cost APIs   │
                       │  (Billing Data)  │
                       └──────────────────┘
```

## 🚀 Quick Start

1. **Setup GCP credentials**:
   ```bash
   gcloud auth application-default login
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure cluster**:
   ```bash
   export GKE_CLUSTER_NAME="your-cluster"
   export GCP_PROJECT_ID="your-project"
   export GCP_ZONE="your-zone"
   ```

4. **Run the agent**:
   ```bash
   python src/main.py
   ```

## 📊 Expected Results

- **20-40% cost reduction** through right-sizing
- **Automated waste detection** saving 5-10 hours/week
- **Proactive optimization** preventing cost spikes
- **Detailed reports** for stakeholder communication

## 🛠️ Components

- `src/cluster_scanner.py` - Kubernetes resource analysis
- `src/cost_analyzer.py` - GCP billing integration
- `src/optimizer.py` - Recommendation engine
- `src/reporter.py` - Report generation
- `src/main.py` - Main orchestration

## 📋 Prerequisites

- GKE cluster with monitoring enabled
- GCP billing API access
- Python 3.9+
- kubectl configured for your cluster