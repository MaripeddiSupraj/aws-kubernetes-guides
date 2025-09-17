# Kubecost with EKS - Complete Implementation Guide

## Table of Contents
1. [Kubecost Overview](#kubecost-overview)
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Installation Methods](#installation-methods)
4. [Configuration & Integration](#configuration--integration)
5. [Cost Monitoring & Analytics](#cost-monitoring--analytics)
6. [Advanced Features](#advanced-features)
7. [Cost Optimization Strategies](#cost-optimization-strategies)
8. [Real-World Scenarios](#real-world-scenarios)
9. [Troubleshooting](#troubleshooting)

---

## Kubecost Overview

### What is Kubecost?
- **Real-time cost monitoring** for Kubernetes clusters
- **Resource allocation tracking** at pod, namespace, and cluster level
- **Cost optimization recommendations** based on actual usage
- **Multi-cloud support** (AWS, GCP, Azure)
- **Integration with AWS Cost Explorer** and billing APIs

### Key Benefits for EKS:
- **Granular cost visibility** down to individual pods
- **Right-sizing recommendations** for CPU/memory requests
- **Idle resource identification** and waste elimination
- **Showback/chargeback** capabilities for teams
- **Budget alerts** and cost governance

### Architecture Components:
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Kubecost UI   │    │  Prometheus      │    │  Cost Analyzer  │
│   (Frontend)    │◄──►│  (Metrics)       │◄──►│  (Backend)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌──────────────────────┐
                    │    EKS Cluster       │
                    │  (Nodes, Pods, etc.) │
                    └──────────────────────┘
```

---

## Prerequisites & Setup

### 1. EKS Cluster Requirements

#### Minimum Cluster Setup:
```bash
# Create EKS cluster with proper node groups
eksctl create cluster \
  --name kubecost-demo \
  --version 1.28 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed \
  --enable-ssm

# Verify cluster access
kubectl get nodes
```

#### Required IAM Permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetUsageReport",
        "ce:ListCostCategoryDefinitions",
        "ce:GetRightsizingRecommendation",
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots",
        "ec2:DescribeImages",
        "ec2:GetReservedInstancesExchangeQuote",
        "ec2:DescribeReservedInstances",
        "ec2:DescribeReservedInstancesModifications",
        "pricing:GetProducts"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. AWS Cost and Billing Setup

#### Enable Cost Explorer:
```bash
# Enable Cost Explorer (via AWS Console or CLI)
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

#### Create Service Account for AWS Integration:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kubecost-cost-analyzer
  namespace: kubecost
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/KubecostRole
---
apiVersion: v1
kind: Secret
metadata:
  name: kubecost-aws-credentials
  namespace: kubecost
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: "YOUR_ACCESS_KEY"
  AWS_SECRET_ACCESS_KEY: "YOUR_SECRET_KEY"
```

---

## Installation Methods

### 1. Helm Installation (Recommended)

#### Add Kubecost Helm Repository:
```bash
# Add repository
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm repo update

# Create namespace
kubectl create namespace kubecost
```

#### Basic Installation:
```bash
# Install with default values
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --create-namespace
```

#### Production Installation with Custom Values:
```yaml
# kubecost-values.yaml
global:
  prometheus:
    enabled: true
    fqdn: http://kubecost-prometheus-server.kubecost.svc.cluster.local:80

kubecostProductConfigs:
  # AWS Integration
  awsServiceKeyName: "kubecost-aws-credentials"
  awsServiceKeySecretName: "kubecost-aws-credentials"
  
  # Cluster configuration
  clusterName: "production-eks"
  currencyCode: "USD"
  
  # Data retention
  etlBucketConfigSecret: "kubecost-s3-config"
  
  # Alerts configuration
  alertConfigs:
    enabled: true
    frontendUrl: "http://kubecost.company.com"

# Prometheus configuration
prometheus:
  server:
    persistentVolume:
      enabled: true
      size: 100Gi
      storageClass: gp3
    retention: "30d"
    
  nodeExporter:
    enabled: true
    
  serviceAccounts:
    server:
      create: true
      annotations:
        eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/KubecostRole

# Grafana configuration
grafana:
  enabled: true
  sidecar:
    dashboards:
      enabled: true
  
# Network policy
networkPolicy:
  enabled: true

# Resource requests/limits
resources:
  requests:
    cpu: 200m
    memory: 512Mi
  limits:
    cpu: 800m
    memory: 2Gi

# Ingress configuration
ingress:
  enabled: true
  className: "alb"
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-west-2:ACCOUNT:certificate/CERT_ID
  hosts:
    - host: kubecost.company.com
      paths:
        - path: /
          pathType: Prefix
```

#### Install with Custom Values:
```bash
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --values kubecost-values.yaml \
  --wait
```

### 2. Manifest Installation

#### Complete Kubecost Deployment:
```yaml
# kubecost-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubecost-cost-analyzer
  namespace: kubecost
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cost-analyzer
  template:
    metadata:
      labels:
        app: cost-analyzer
    spec:
      serviceAccountName: kubecost-cost-analyzer
      containers:
      - name: cost-analyzer-frontend
        image: gcr.io/kubecost1/frontend:latest
        ports:
        - containerPort: 9090
        env:
        - name: GET_HOSTS_FROM
          value: "dns"
        resources:
          requests:
            cpu: 10m
            memory: 55Mi
          limits:
            cpu: 100m
            memory: 256Mi
            
      - name: cost-analyzer-server
        image: gcr.io/kubecost1/server:latest
        ports:
        - containerPort: 9003
        env:
        - name: PROMETHEUS_SERVER_ENDPOINT
          value: "http://kubecost-prometheus-server.kubecost.svc.cluster.local:80"
        - name: CLOUD_PROVIDER_API_KEY
          value: "AIzaSyDXQPG_MHUEy9neR7stolq6l0ujXmjJlvk"
        - name: CLUSTER_ID
          value: "production-eks"
        envFrom:
        - secretRef:
            name: kubecost-aws-credentials
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 800m
            memory: 2Gi
        volumeMounts:
        - name: persistent-configs
          mountPath: /var/configs
      volumes:
      - name: persistent-configs
        persistentVolumeClaim:
          claimName: kubecost-cost-analyzer
---
apiVersion: v1
kind: Service
metadata:
  name: kubecost-cost-analyzer
  namespace: kubecost
spec:
  selector:
    app: cost-analyzer
  ports:
  - name: http-ui
    port: 9090
    targetPort: 9090
  - name: http-api
    port: 9003
    targetPort: 9003
  type: ClusterIP
```

### 3. Verify Installation

#### Check Pod Status:
```bash
# Check all kubecost pods
kubectl get pods -n kubecost

# Check logs
kubectl logs -n kubecost deployment/kubecost-cost-analyzer -c cost-analyzer-server

# Port forward to access UI
kubectl port-forward -n kubecost service/kubecost-cost-analyzer 9090:9090
```

#### Access Kubecost UI:
```bash
# Local access
open http://localhost:9090

# Check service endpoints
kubectl get svc -n kubecost
kubectl get ingress -n kubecost
```

---

## Configuration & Integration

### 1. AWS Cost Integration

#### S3 Bucket for ETL Data:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kubecost-s3-config
  namespace: kubecost
type: Opaque
stringData:
  bucket-config.json: |
    {
      "bucket": "kubecost-etl-data-bucket",
      "region": "us-west-2",
      "access_key": "YOUR_ACCESS_KEY",
      "secret_key": "YOUR_SECRET_KEY"
    }
```

#### Cost and Usage Report Integration:
```bash
# Create CUR in AWS Console or via CLI
aws cur put-report-definition \
  --report-definition '{
    "ReportName": "kubecost-cur",
    "TimeUnit": "HOURLY",
    "Format": "Parquet",
    "Compression": "GZIP",
    "AdditionalSchemaElements": ["RESOURCES"],
    "S3Bucket": "kubecost-cur-bucket",
    "S3Prefix": "cur-data/",
    "S3Region": "us-west-2",
    "AdditionalArtifacts": ["ATHENA"],
    "RefreshClosedReports": true,
    "ReportVersioning": "OVERWRITE_REPORT"
  }'
```

#### Configure Kubecost for CUR:
```yaml
# Add to kubecost-values.yaml
kubecostProductConfigs:
  athenaProjectID: "ACCOUNT_ID"
  athenaBucketName: "kubecost-cur-bucket"
  athenaRegion: "us-west-2"
  athenaDatabase: "athenacurcfn_kubecost_cur"
  athenaTable: "kubecost_cur"
  masterPayerARN: "arn:aws:iam::MASTER_ACCOUNT:root"
```

### 2. Multi-Cluster Setup

#### Primary Cluster Configuration:
```yaml
# Primary cluster (aggregator)
kubecostProductConfigs:
  clusterName: "production-primary"
  federatedStorageConfigSecret: "federated-store-config"
  
# Federated storage secret
apiVersion: v1
kind: Secret
metadata:
  name: federated-store-config
  namespace: kubecost
type: Opaque
stringData:
  federated-store.yaml: |
    type: S3
    config:
      bucket: "kubecost-federated-storage"
      endpoint: "s3.us-west-2.amazonaws.com"
      region: "us-west-2"
      access_key: "YOUR_ACCESS_KEY"
      secret_key: "YOUR_SECRET_KEY"
```

#### Secondary Cluster Configuration:
```yaml
# Secondary clusters
kubecostProductConfigs:
  clusterName: "production-secondary-1"
  federatedStorageConfigSecret: "federated-store-config"
  
# Disable UI on secondary clusters
kubecostFrontend:
  enabled: false
```

### 3. Custom Pricing Configuration

#### Spot Instance Pricing:
```yaml
kubecostProductConfigs:
  spotLabel: "node.kubernetes.io/instance-type"
  spotLabelValue: "spot"
  
  # Custom spot pricing (optional)
  customPricesEnabled: true
  
# Custom pricing secret
apiVersion: v1
kind: Secret
metadata:
  name: custom-pricing
  namespace: kubecost
type: Opaque
stringData:
  custom-pricing.json: |
    {
      "CPU": "0.031611",
      "spotCPU": "0.006655",
      "RAM": "0.004237",
      "spotRAM": "0.000892",
      "GPU": "0.95",
      "storage": "0.00005",
      "zoneNetworkEgress": "0.01",
      "regionNetworkEgress": "0.02",
      "internetNetworkEgress": "0.12"
    }
```

---

## Cost Monitoring & Analytics

### 1. Cost Allocation Dashboard

#### Key Metrics to Monitor:
```bash
# Access cost allocation API
curl "http://localhost:9090/model/allocation" \
  -d '{"window":"7d","aggregate":"namespace"}' \
  -H "Content-Type: application/json"

# Get cluster costs
curl "http://localhost:9090/model/allocation" \
  -d '{"window":"30d","aggregate":"cluster"}' \
  -H "Content-Type: application/json"
```

#### Cost Breakdown Views:
- **By Namespace**: Team/application cost allocation
- **By Pod**: Granular resource usage
- **By Node**: Infrastructure cost distribution
- **By Label**: Custom cost categorization
- **By Controller**: Deployment/StatefulSet costs

### 2. Asset Monitoring

#### Infrastructure Asset Costs:
```bash
# Get asset costs (nodes, disks, etc.)
curl "http://localhost:9090/model/assets" \
  -d '{"window":"7d","aggregate":"type"}' \
  -H "Content-Type: application/json"

# Specific asset types
curl "http://localhost:9090/model/assets" \
  -d '{"window":"7d","filterTypes":["Node","Disk"]}' \
  -H "Content-Type: application/json"
```

### 3. Cost Alerts Configuration

#### Budget Alert Setup:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubecost-alerts
  namespace: kubecost
data:
  alerts.json: |
    [
      {
        "type": "budget",
        "threshold": 1000.0,
        "window": "7d",
        "aggregation": "namespace",
        "filter": {
          "namespace": "production"
        },
        "ownerContact": ["devops@company.com"]
      },
      {
        "type": "spendChange",
        "threshold": 0.20,
        "window": "1d",
        "baselineWindow": "7d",
        "aggregation": "cluster",
        "ownerContact": ["finance@company.com"]
      },
      {
        "type": "efficiency",
        "threshold": 0.50,
        "window": "7d",
        "aggregation": "namespace",
        "filter": {
          "namespace": "development"
        },
        "ownerContact": ["dev-team@company.com"]
      }
    ]
```

#### Slack Integration:
```yaml
# Slack webhook configuration
kubecostProductConfigs:
  slackWebhookUrl: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
  
# Alert manager configuration
alertmanager:
  enabled: true
  config:
    global:
      slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    route:
      group_by: ['alertname']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'slack-notifications'
    receivers:
    - name: 'slack-notifications'
      slack_configs:
      - channel: '#kubecost-alerts'
        title: 'Kubecost Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

---

## Advanced Features

### 1. Savings Recommendations

#### Right-Sizing Recommendations:
```bash
# Get right-sizing recommendations
curl "http://localhost:9090/model/savings/requestSizing" \
  -d '{"window":"7d","targetUtilization":0.80}' \
  -H "Content-Type: application/json"

# Cluster right-sizing
curl "http://localhost:9090/model/savings/clusterSizing" \
  -d '{"window":"30d","targetUtilization":0.70}' \
  -H "Content-Type: application/json"
```

#### Abandoned Resource Detection:
```bash
# Find abandoned resources
curl "http://localhost:9090/model/savings/abandoned" \
  -d '{"window":"7d"}' \
  -H "Content-Type: application/json"
```

### 2. Custom Cost Models

#### Department-Based Cost Allocation:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubecost-cost-model
  namespace: kubecost
data:
  cost-model.json: |
    {
      "description": "Department-based cost allocation",
      "CPU": 0.031611,
      "RAM": 0.004237,
      "GPU": 0.95,
      "storage": 0.00005,
      "loadBalancer": 0.025,
      "customCosts": {
        "engineering": {
          "hourlyCost": 50.0,
          "description": "Engineering overhead"
        },
        "operations": {
          "hourlyCost": 30.0,
          "description": "Operations overhead"
        }
      }
    }
```

### 3. Showback/Chargeback Reports

#### Monthly Chargeback Report:
```bash
# Generate monthly report
curl "http://localhost:9090/model/allocation" \
  -d '{
    "window": "month",
    "aggregate": "namespace",
    "accumulate": true,
    "shareIdle": true,
    "shareNamespaces": ["kube-system", "kubecost"]
  }' \
  -H "Content-Type: application/json" > monthly-chargeback.json

# Export to CSV
curl "http://localhost:9090/model/allocation/export" \
  -d '{
    "window": "month",
    "aggregate": "namespace",
    "format": "csv"
  }' \
  -H "Content-Type: application/json" > chargeback-report.csv
```

---

## Cost Optimization Strategies

### 1. Resource Right-Sizing

#### Implement VPA with Kubecost Data:
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: webapp-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: webapp
      maxAllowed:
        cpu: 2
        memory: 4Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
      controlledResources: ["cpu", "memory"]
```

#### Automated Right-Sizing Script:
```bash
#!/bin/bash
# get-rightsizing-recommendations.sh

KUBECOST_URL="http://localhost:9090"
NAMESPACE=${1:-"default"}
WINDOW=${2:-"7d"}

echo "Getting right-sizing recommendations for namespace: $NAMESPACE"

# Get recommendations
RECOMMENDATIONS=$(curl -s "$KUBECOST_URL/model/savings/requestSizing" \
  -d "{\"window\":\"$WINDOW\",\"filter\":{\"namespace\":\"$NAMESPACE\"}}" \
  -H "Content-Type: application/json")

# Parse and apply recommendations
echo "$RECOMMENDATIONS" | jq -r '.data[] | 
  "kubectl patch deployment \(.controllerName) -n \(.namespace) -p '"'"'
  {\"spec\":{\"template\":{\"spec\":{\"containers\":[{
    \"name\":\"\(.containerName)\",
    \"resources\":{
      \"requests\":{
        \"cpu\":\"\(.recommendedCPU)\",
        \"memory\":\"\(.recommendedMemory)\"
      }
    }
  }]}}}}'"'"'"'
```

### 2. Spot Instance Optimization

#### Spot Node Pool Configuration:
```yaml
# spot-nodepool.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: kubecost-demo
  region: us-west-2

nodeGroups:
- name: spot-workers
  instanceTypes: 
    - m5.large
    - m5.xlarge
    - m4.large
    - m4.xlarge
  spot: true
  minSize: 2
  maxSize: 10
  desiredCapacity: 4
  
  labels:
    node-type: spot
    cost-optimization: enabled
  
  taints:
    - key: spot-instance
      value: "true"
      effect: NoSchedule
      
  iam:
    withAddonPolicies:
      autoScaler: true
```

#### Spot-Tolerant Workload Configuration:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-processor
  namespace: production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: batch-processor
  template:
    metadata:
      labels:
        app: batch-processor
        cost-tier: spot-optimized
    spec:
      tolerations:
      - key: spot-instance
        operator: Equal
        value: "true"
        effect: NoSchedule
      
      nodeSelector:
        node-type: spot
        
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - batch-processor
              topologyKey: kubernetes.io/hostname
      
      containers:
      - name: processor
        image: batch-processor:v1.2.3
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
```

### 3. Storage Cost Optimization

#### EBS Volume Right-Sizing:
```bash
#!/bin/bash
# optimize-ebs-volumes.sh

# Get storage recommendations from Kubecost
STORAGE_RECS=$(curl -s "http://localhost:9090/model/savings/storage" \
  -d '{"window":"30d"}' \
  -H "Content-Type: application/json")

# Process recommendations
echo "$STORAGE_RECS" | jq -r '.data[] | 
  select(.recommendedSize < .currentSize) |
  "PVC: \(.pvcName) | Current: \(.currentSize)Gi | Recommended: \(.recommendedSize)Gi | Savings: $\(.monthlySavings)"'

# Generate resize commands
echo "$STORAGE_RECS" | jq -r '.data[] | 
  select(.recommendedSize < .currentSize) |
  "kubectl patch pvc \(.pvcName) -n \(.namespace) -p '"'"'{\"spec\":{\"resources\":{\"requests\":{\"storage\":\"\(.recommendedSize)Gi\"}}}}'"'"'"'
```

#### Storage Class Optimization:
```yaml
# Optimized storage classes
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-optimized
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-cost-optimized
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

---

## Real-World Scenarios

### 1. E-commerce Platform Cost Optimization

#### Scenario: Multi-tenant SaaS Platform
```yaml
# Production workload with cost tracking
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-api
  namespace: production
  labels:
    app: ecommerce-api
    cost-center: "engineering"
    team: "backend"
    environment: "production"
spec:
  replicas: 10
  selector:
    matchLabels:
      app: ecommerce-api
  template:
    metadata:
      labels:
        app: ecommerce-api
        cost-center: "engineering"
        team: "backend"
        tenant: "shared"
    spec:
      containers:
      - name: api
        image: ecommerce-api:v2.1.0
        resources:
          requests:
            cpu: 200m      # Right-sized based on Kubecost data
            memory: 512Mi  # Reduced from 1Gi (30% savings)
          limits:
            cpu: 500m
            memory: 1Gi
        env:
        - name: COST_ALLOCATION_LABEL
          value: "ecommerce-api"
```

#### Cost Allocation Query:
```bash
# Get cost breakdown by team
curl "http://localhost:9090/model/allocation" \
  -d '{
    "window": "30d",
    "aggregate": "label:team",
    "accumulate": true,
    "shareIdle": true
  }' \
  -H "Content-Type: application/json"

# Results show:
# - Backend team: $2,450/month (40% of total)
# - Frontend team: $1,225/month (20% of total)  
# - Data team: $1,837/month (30% of total)
# - DevOps team: $612/month (10% of total)
```

### 2. Development Environment Cost Control

#### Scenario: Auto-scaling Dev Environments
```yaml
# Development namespace with budget controls
apiVersion: v1
kind: Namespace
metadata:
  name: development
  labels:
    cost-center: "engineering"
    environment: "development"
    budget-limit: "500"  # $500/month limit
---
# Resource quota for cost control
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-resource-quota
  namespace: development
spec:
  hard:
    requests.cpu: "10"      # Max 10 CPU cores
    requests.memory: 20Gi   # Max 20GB memory
    persistentvolumeclaims: "10"
    count/pods: "50"
---
# Limit range for individual pods
apiVersion: v1
kind: LimitRange
metadata:
  name: dev-limit-range
  namespace: development
spec:
  limits:
  - default:
      cpu: 200m
      memory: 256Mi
    defaultRequest:
      cpu: 100m
      memory: 128Mi
    type: Container
```

#### Auto-shutdown for Dev Environments:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: dev-environment-shutdown
  namespace: development
spec:
  schedule: "0 18 * * 1-5"  # Shutdown at 6 PM weekdays
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: shutdown
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              # Scale down all deployments
              kubectl scale deployment --all --replicas=0 -n development
              
              # Delete non-essential pods
              kubectl delete pods -l environment=development,essential!=true -n development
              
              echo "Development environment shutdown completed"
          restartPolicy: OnFailure
---
# Auto-startup CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: dev-environment-startup
  namespace: development
spec:
  schedule: "0 8 * * 1-5"  # Startup at 8 AM weekdays
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: startup
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              # Scale up deployments to original size
              kubectl scale deployment --all --replicas=1 -n development
              
              echo "Development environment startup completed"
          restartPolicy: OnFailure
```

### 3. ML/AI Workload Cost Optimization

#### Scenario: GPU-Intensive ML Training
```yaml
# ML training job with cost optimization
apiVersion: batch/v1
kind: Job
metadata:
  name: ml-training-job
  namespace: ml-workloads
  labels:
    cost-center: "data-science"
    workload-type: "training"
    gpu-type: "nvidia-t4"
spec:
  template:
    metadata:
      labels:
        cost-center: "data-science"
        workload-type: "training"
    spec:
      nodeSelector:
        node-type: spot              # Use spot instances
        accelerator: nvidia-tesla-t4 # Specific GPU type
        
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      - key: spot-instance
        operator: Equal
        value: "true"
        effect: NoSchedule
        
      containers:
      - name: ml-trainer
        image: tensorflow/tensorflow:2.13.0-gpu
        resources:
          requests:
            cpu: 4
            memory: 16Gi
            nvidia.com/gpu: 1
          limits:
            cpu: 8
            memory: 32Gi
            nvidia.com/gpu: 1
        env:
        - name: COST_TRACKING_ENABLED
          value: "true"
        - name: JOB_COST_LABEL
          value: "ml-training-$(JOB_NAME)"
      restartPolicy: Never
  backoffLimit: 3
```

#### GPU Cost Monitoring:
```bash
# Monitor GPU costs specifically
curl "http://localhost:9090/model/allocation" \
  -d '{
    "window": "7d",
    "aggregate": "label:workload-type",
    "filter": {
      "label": {
        "gpu-type": "nvidia-t4"
      }
    }
  }' \
  -H "Content-Type: application/json"

# Results show GPU utilization and costs:
# - Training jobs: $1,200/week (80% GPU utilization)
# - Inference jobs: $300/week (60% GPU utilization)
# - Idle GPU time: $150/week (opportunity for optimization)
```

---

## Troubleshooting

### 1. Common Installation Issues

#### Prometheus Connection Issues:
```bash
# Check Prometheus connectivity
kubectl exec -n kubecost deployment/kubecost-cost-analyzer -c cost-analyzer-server -- \
  curl -s http://kubecost-prometheus-server.kubecost.svc.cluster.local:80/api/v1/query?query=up

# Verify Prometheus targets
kubectl port-forward -n kubecost svc/kubecost-prometheus-server 9090:80
# Visit http://localhost:9090/targets
```

#### AWS Integration Issues:
```bash
# Test AWS credentials
kubectl exec -n kubecost deployment/kubecost-cost-analyzer -c cost-analyzer-server -- \
  aws sts get-caller-identity

# Check Cost Explorer access
kubectl exec -n kubecost deployment/kubecost-cost-analyzer -c cost-analyzer-server -- \
  aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-02 \
    --granularity DAILY \
    --metrics BlendedCost
```

### 2. Data Quality Issues

#### Missing Cost Data:
```bash
# Check node labels and pricing
kubectl get nodes --show-labels | grep -E "(instance-type|zone)"

# Verify cost model configuration
kubectl get configmap -n kubecost kubecost-cost-analyzer -o yaml

# Check for missing metrics
curl "http://localhost:9090/model/allocation/summary" \
  -d '{"window":"1d"}' \
  -H "Content-Type: application/json"
```

#### Inaccurate Resource Allocation:
```bash
# Verify resource requests/limits
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[*].resources}{"\n"}{end}'

# Check for missing resource specifications
kubectl get pods --all-namespaces --field-selector=status.phase=Running -o json | \
  jq -r '.items[] | select(.spec.containers[].resources.requests == null) | "\(.metadata.namespace)/\(.metadata.name)"'
```

### 3. Performance Optimization

#### Reduce Memory Usage:
```yaml
# Optimize Kubecost configuration
kubecostProductConfigs:
  # Reduce data retention
  etlResolution: "1h"
  etlMaxPrometheusQueryDuration: "30m"
  
  # Limit concurrent queries
  maxQueryConcurrency: 5
  
  # Optimize aggregation
  aggregationInterval: "1h"

# Prometheus optimization
prometheus:
  server:
    retention: "15d"  # Reduce from default 30d
    resources:
      requests:
        memory: 2Gi
      limits:
        memory: 4Gi
```

#### Database Optimization:
```bash
# Clean up old data
kubectl exec -n kubecost deployment/kubecost-cost-analyzer -c cost-analyzer-server -- \
  /bin/sh -c "find /var/configs -name '*.db' -mtime +30 -delete"

# Compact database
kubectl exec -n kubecost deployment/kubecost-cost-analyzer -c cost-analyzer-server -- \
  sqlite3 /var/configs/cost-analyzer.db "VACUUM;"
```

### 4. Monitoring and Alerting

#### Health Check Endpoints:
```bash
# Kubecost health check
curl "http://localhost:9090/model/healthz"

# Prometheus health check  
curl "http://localhost:9090/prometheus/api/v1/query?query=up"

# Check data freshness
curl "http://localhost:9090/model/allocation/summary" \
  -d '{"window":"1h"}' \
  -H "Content-Type: application/json"
```

#### Custom Monitoring Dashboard:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubecost-monitoring-dashboard
  namespace: kubecost
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "Kubecost Health Monitoring",
        "panels": [
          {
            "title": "Cost Data Freshness",
            "type": "stat",
            "targets": [
              {
                "expr": "time() - kubecost_allocation_last_update_time",
                "legendFormat": "Data Age (seconds)"
              }
            ]
          },
          {
            "title": "Memory Usage",
            "type": "graph",
            "targets": [
              {
                "expr": "container_memory_usage_bytes{pod=~\"kubecost-cost-analyzer.*\"}",
                "legendFormat": "{{container}}"
              }
            ]
          },
          {
            "title": "API Response Time",
            "type": "graph", 
            "targets": [
              {
                "expr": "histogram_quantile(0.95, kubecost_api_request_duration_seconds_bucket)",
                "legendFormat": "95th percentile"
              }
            ]
          }
        ]
      }
    }
```

This comprehensive guide covers everything you need to successfully implement and optimize Kubecost with EKS, from basic installation to advanced cost optimization strategies and real-world scenarios.