# EKS Zero-Downtime Upgrade Guide - Complete Production Strategy

## Table of Contents
1. [Understanding EKS Upgrades](#understanding-eks-upgrades)
2. [Pre-Upgrade Prerequisites](#pre-upgrade-prerequisites)
3. [Sample Application Setup](#sample-application-setup)
4. [Upgrade Strategy & Planning](#upgrade-strategy--planning)
5. [Step-by-Step Upgrade Process](#step-by-step-upgrade-process)
6. [Real-World Example: E-commerce Platform Upgrade](#real-world-example-e-commerce-platform-upgrade)
7. [Rollback Procedures](#rollback-procedures)
8. [Post-Upgrade Validation](#post-upgrade-validation)
9. [Best Practices & Troubleshooting](#best-practices--troubleshooting)

---

## Understanding EKS Upgrades

### What Gets Upgraded?
```
┌─────────────────────────────────────────────────────────────┐
│                    EKS Upgrade Components                   │
├─────────────────────────────────────────────────────────────┤
│ Control Plane       │ Data Plane          │ Add-ons         │
│ - API Server        │ - Worker Nodes      │ - CoreDNS       │
│ - etcd              │ - kubelet           │ - kube-proxy    │
│ - Controller Mgr    │ - Container Runtime │ - VPC CNI       │
│ - Scheduler         │ - Node Groups       │ - EBS CSI       │
└─────────────────────────────────────────────────────────────┘
```

### Kubernetes Version Support Matrix
| EKS Version | Kubernetes | Support Status | End of Support |
|-------------|------------|----------------|----------------|
| 1.28 | 1.28.x | Current | Nov 2024 |
| 1.27 | 1.27.x | Supported | Jul 2024 |
| 1.26 | 1.26.x | Supported | May 2024 |
| 1.25 | 1.25.x | Deprecated | Feb 2024 |

### Upgrade Path Rules
- ✅ **Supported**: 1.25 → 1.26 → 1.27 → 1.28
- ❌ **Not Supported**: 1.25 → 1.27 (skipping versions)
- ⚠️ **Important**: Only one minor version increment at a time

---

## Pre-Upgrade Prerequisites

### 1. Cluster Health Assessment

#### Check Current Cluster Status:
```bash
# Get cluster information
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods --all-namespaces | grep -v Running

# Check cluster version
aws eks describe-cluster --name production-cluster --query 'cluster.version'

# Verify node group versions
aws eks describe-nodegroup --cluster-name production-cluster \
  --nodegroup-name primary-nodes --query 'nodegroup.version'
```

#### Health Check Script:
```bash
#!/bin/bash
# eks-health-check.sh

CLUSTER_NAME="production-cluster"
echo "=== EKS Cluster Health Check ==="

# 1. Cluster API Health
echo "Checking cluster API health..."
kubectl get --raw='/readyz?verbose' || echo "API server issues detected"

# 2. Node Status
echo "Checking node status..."
kubectl get nodes --no-headers | awk '{print $1 " " $2}' | while read node status; do
  if [ "$status" != "Ready" ]; then
    echo "WARNING: Node $node is $status"
  fi
done

# 3. System Pods Health
echo "Checking system pods..."
kubectl get pods -n kube-system --no-headers | grep -v Running | grep -v Completed

# 4. Persistent Volume Status
echo "Checking PV status..."
kubectl get pv --no-headers | awk '{print $1 " " $5}' | while read pv status; do
  if [ "$status" != "Bound" ]; then
    echo "WARNING: PV $pv is $status"
  fi
done

# 5. Resource Usage
echo "Checking resource usage..."
kubectl top nodes 2>/dev/null || echo "Metrics server not available"

echo "Health check completed!"
```

### 2. Backup Strategy

#### etcd Backup (Automatic with EKS):
```bash
# EKS automatically backs up etcd, but verify backup settings
aws eks describe-cluster --name production-cluster \
  --query 'cluster.logging.clusterLogging'

# Enable all logging if not already enabled
aws eks update-cluster-config --name production-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'
```

#### Application Data Backup:
```bash
# Backup persistent volumes using Velero
velero backup create pre-upgrade-backup-$(date +%Y%m%d) \
  --include-namespaces production,staging \
  --wait

# Verify backup
velero backup describe pre-upgrade-backup-$(date +%Y%m%d)

# Alternative: Manual PV snapshots
kubectl get pv -o jsonpath='{.items[*].spec.awsElasticBlockStore.volumeID}' | \
  xargs -I {} aws ec2 create-snapshot --volume-id {} \
  --description "Pre-upgrade backup $(date)"
```

### 3. Compatibility Verification

#### Check API Deprecations:
```bash
# Install kubectl-convert plugin
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl-convert"
chmod +x kubectl-convert && sudo mv kubectl-convert /usr/local/bin/

# Check for deprecated APIs
kubectl api-resources --verbs=list --namespaced -o name | \
  xargs -n 1 kubectl get --show-kind --ignore-not-found -o name

# Use Pluto to detect deprecated APIs
pluto detect-files --directory ./k8s-manifests/ --target-versions k8s=v1.28.0
```

#### Validate Workload Compatibility:
```bash
# Check Pod Security Standards compatibility
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}' | grep -v "null"

# Check for privileged containers
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[*].securityContext.privileged}{"\n"}{end}' | grep true
```

---

## Sample Application Setup

### E-commerce Platform Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                Production E-commerce Setup                  │
├─────────────────────────────────────────────────────────────┤
│ Frontend (React)    │ API Gateway         │ User Service    │
│ - 3 replicas        │ - 2 replicas        │ - 3 replicas    │
│ - Rolling updates   │ - Load balanced     │ - Stateless     │
├─────────────────────┼─────────────────────┼─────────────────┤
│ Product Service     │ Order Service       │ Payment Service │
│ - 4 replicas        │ - 3 replicas        │ - 2 replicas    │
│ - Cache layer       │ - Queue processing  │ - PCI compliant │
├─────────────────────┼─────────────────────┼─────────────────┤
│ Database            │ Cache               │ Message Queue   │
│ - PostgreSQL        │ - Redis Cluster     │ - RabbitMQ      │
│ - StatefulSet       │ - 3 nodes           │ - Persistent    │
└─────────────────────────────────────────────────────────────┘
```

### 1. Frontend Service (React App)

#### Deployment Configuration:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: production
  labels:
    app: frontend
    version: v2.1.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        version: v2.1.0
    spec:
      containers:
      - name: frontend
        image: ecommerce/frontend:v2.1.0
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: API_ENDPOINT
          value: "http://api-gateway.production.svc.cluster.local"
        - name: NODE_ENV
          value: "production"

---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: production
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - host: shop.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

### 2. API Gateway Service

#### Deployment with Circuit Breaker:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: production
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0  # Zero downtime
      maxSurge: 1
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: ecommerce/api-gateway:v1.5.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "400m"
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
          timeoutSeconds: 3
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "production"
        - name: USER_SERVICE_URL
          value: "http://user-service.production.svc.cluster.local:8080"
        - name: PRODUCT_SERVICE_URL
          value: "http://product-service.production.svc.cluster.local:8080"
        - name: ORDER_SERVICE_URL
          value: "http://order-service.production.svc.cluster.local:8080"

---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: production
spec:
  selector:
    app: api-gateway
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

### 3. Microservices (User, Product, Order)

#### User Service with Database:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: ecommerce/user-service:v1.3.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "400m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: DATABASE_USERNAME
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: username
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: password
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: production
spec:
  selector:
    app: user-service
  ports:
  - port: 8080
    targetPort: 8080
```

### 4. Stateful Services (Database, Cache)

#### PostgreSQL StatefulSet:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: production
spec:
  serviceName: postgresql
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:14
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: ecommerce
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: password
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3
      resources:
        requests:
          storage: 20Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  namespace: production
spec:
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None
```

#### Redis Cluster:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: production
spec:
  serviceName: redis
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - /etc/redis/redis.conf
        volumeMounts:
        - name: redis-config
          mountPath: /etc/redis
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
      volumes:
      - name: redis-config
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: redis-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3
      resources:
        requests:
          storage: 5Gi
```

---

## Upgrade Strategy & Planning

### 1. Upgrade Timeline Planning

#### Production Upgrade Schedule:
```
Week 1: Planning & Preparation
├── Day 1-2: Health assessment & compatibility check
├── Day 3-4: Backup strategy implementation
├── Day 5-6: Test environment upgrade
└── Day 7: Staging environment upgrade

Week 2: Production Upgrade
├── Day 1: Final preparations & team briefing
├── Day 2: Control plane upgrade (low traffic window)
├── Day 3-4: Node group upgrades (rolling)
├── Day 5: Add-on upgrades
├── Day 6-7: Validation & monitoring

Week 3: Post-Upgrade
├── Day 1-3: Performance monitoring
├── Day 4-5: Optimization & tuning
└── Day 6-7: Documentation & lessons learned
```

### 2. Risk Assessment Matrix

| Risk Level | Impact | Probability | Mitigation Strategy |
|------------|--------|-------------|-------------------|
| **High** | Service outage | Low | Blue-green deployment, immediate rollback |
| **Medium** | Performance degradation | Medium | Gradual traffic shifting, monitoring |
| **Low** | Minor compatibility issues | High | Thorough testing, feature flags |

### 3. Communication Plan

#### Stakeholder Notification Template:
```
Subject: EKS Cluster Upgrade - Production Environment

Dear Team,

We will be upgrading our production EKS cluster:
- Date: [DATE]
- Time: [TIME] (during low traffic window)
- Duration: Estimated 4-6 hours
- Expected Impact: Zero downtime for end users

Upgrade Details:
- Current Version: 1.26
- Target Version: 1.27
- Components: Control plane, worker nodes, add-ons

Rollback Plan: Available within 30 minutes if issues occur

Contact: [TEAM] for any questions or concerns
```

---

## Step-by-Step Upgrade Process

### Phase 1: Control Plane Upgrade

#### 1. Pre-Upgrade Validation:
```bash
#!/bin/bash
# pre-upgrade-validation.sh

CLUSTER_NAME="production-cluster"
TARGET_VERSION="1.27"

echo "=== Pre-Upgrade Validation ==="

# Check current version
CURRENT_VERSION=$(aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.version' --output text)
echo "Current version: $CURRENT_VERSION"
echo "Target version: $TARGET_VERSION"

# Validate upgrade path
if [[ "$CURRENT_VERSION" == "1.26" && "$TARGET_VERSION" == "1.27" ]]; then
    echo "✅ Valid upgrade path"
else
    echo "❌ Invalid upgrade path"
    exit 1
fi

# Check cluster health
kubectl get nodes --no-headers | grep -v Ready && echo "❌ Unhealthy nodes detected" || echo "✅ All nodes healthy"

# Check system pods
UNHEALTHY_PODS=$(kubectl get pods -n kube-system --no-headers | grep -v Running | grep -v Completed | wc -l)
if [ $UNHEALTHY_PODS -eq 0 ]; then
    echo "✅ All system pods healthy"
else
    echo "❌ $UNHEALTHY_PODS unhealthy system pods detected"
fi

# Check PVs
UNBOUND_PVS=$(kubectl get pv --no-headers | grep -v Bound | wc -l)
if [ $UNBOUND_PVS -eq 0 ]; then
    echo "✅ All PVs bound"
else
    echo "⚠️ $UNBOUND_PVS unbound PVs detected"
fi

echo "Validation completed!"
```

#### 2. Control Plane Upgrade:
```bash
# Start control plane upgrade
aws eks update-cluster-version \
  --name production-cluster \
  --kubernetes-version 1.27

# Monitor upgrade progress
UPGRADE_ID=$(aws eks describe-update --name production-cluster \
  --update-id $(aws eks list-updates --name production-cluster \
  --query 'updateIds[0]' --output text) \
  --query 'update.id' --output text)

echo "Upgrade ID: $UPGRADE_ID"

# Wait for completion (typically 20-30 minutes)
while true; do
  STATUS=$(aws eks describe-update --name production-cluster \
    --update-id $UPGRADE_ID --query 'update.status' --output text)
  
  echo "Upgrade status: $STATUS"
  
  if [ "$STATUS" = "Successful" ]; then
    echo "✅ Control plane upgrade completed successfully"
    break
  elif [ "$STATUS" = "Failed" ]; then
    echo "❌ Control plane upgrade failed"
    exit 1
  fi
  
  sleep 60
done

# Verify control plane version
aws eks describe-cluster --name production-cluster --query 'cluster.version'
```

#### 3. Validate Control Plane:
```bash
# Test API server connectivity
kubectl cluster-info

# Check control plane components
kubectl get componentstatuses

# Verify system pods are running
kubectl get pods -n kube-system

# Test basic operations
kubectl get nodes
kubectl get pods --all-namespaces
```

### Phase 2: Node Group Upgrades

#### 1. Managed Node Group Upgrade:
```bash
# List node groups
aws eks describe-nodegroup --cluster-name production-cluster \
  --nodegroup-name primary-nodes

# Start node group upgrade
aws eks update-nodegroup-version \
  --cluster-name production-cluster \
  --nodegroup-name primary-nodes \
  --kubernetes-version 1.27

# Monitor node group upgrade
NODEGROUP_UPDATE_ID=$(aws eks list-updates --name production-cluster \
  --nodegroup-name primary-nodes --query 'updateIds[0]' --output text)

while true; do
  STATUS=$(aws eks describe-update --name production-cluster \
    --nodegroup-name primary-nodes --update-id $NODEGROUP_UPDATE_ID \
    --query 'update.status' --output text)
  
  echo "Node group upgrade status: $STATUS"
  
  if [ "$STATUS" = "Successful" ]; then
    echo "✅ Node group upgrade completed"
    break
  elif [ "$STATUS" = "Failed" ]; then
    echo "❌ Node group upgrade failed"
    exit 1
  fi
  
  sleep 120
done
```

#### 2. Self-Managed Node Group Upgrade:
```bash
# For self-managed nodes, use rolling update strategy
# Create new launch template with updated AMI
aws ec2 create-launch-template-version \
  --launch-template-id lt-12345678 \
  --source-version 1 \
  --launch-template-data '{
    "ImageId": "ami-0abcdef1234567890",
    "UserData": "'$(base64 -w 0 userdata.sh)'"
  }'

# Update Auto Scaling Group
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name eks-nodes-asg \
  --launch-template '{
    "LaunchTemplateId": "lt-12345678",
    "Version": "$Latest"
  }'

# Perform rolling update
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name eks-nodes-asg \
  --preferences '{
    "InstanceWarmup": 300,
    "MinHealthyPercentage": 50
  }'
```

#### 3. Monitor Node Replacement:
```bash
# Monitor node replacement progress
watch -n 30 'kubectl get nodes -o wide'

# Check pod distribution during upgrade
kubectl get pods -o wide --all-namespaces | grep -E "(frontend|api-gateway|user-service)"

# Monitor application health
curl -s http://shop.example.com/health | jq .
```

### Phase 3: Add-on Upgrades

#### 1. CoreDNS Upgrade:
```bash
# Check current CoreDNS version
kubectl get deployment coredns -n kube-system -o jsonpath='{.spec.template.spec.containers[0].image}'

# Get recommended version for K8s 1.27
aws eks describe-addon-versions --addon-name coredns \
  --kubernetes-version 1.27 --query 'addons[0].addonVersions[0].addonVersion'

# Update CoreDNS
aws eks update-addon \
  --cluster-name production-cluster \
  --addon-name coredns \
  --addon-version v1.10.1-eksbuild.1 \
  --resolve-conflicts OVERWRITE

# Monitor CoreDNS upgrade
aws eks describe-addon --cluster-name production-cluster --addon-name coredns
```

#### 2. VPC CNI Upgrade:
```bash
# Update VPC CNI
aws eks update-addon \
  --cluster-name production-cluster \
  --addon-name vpc-cni \
  --addon-version v1.13.4-eksbuild.1 \
  --resolve-conflicts OVERWRITE

# Verify CNI pods
kubectl get pods -n kube-system -l k8s-app=aws-node
```

#### 3. EBS CSI Driver Upgrade:
```bash
# Update EBS CSI driver
aws eks update-addon \
  --cluster-name production-cluster \
  --addon-name aws-ebs-csi-driver \
  --addon-version v1.21.0-eksbuild.1 \
  --resolve-conflicts OVERWRITE

# Test storage functionality
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 1Gi
EOF

kubectl get pvc test-pvc
kubectl delete pvc test-pvc
```

---

## Real-World Example: E-commerce Platform Upgrade

### Scenario: Black Friday Preparation
**Situation**: Upgrade production cluster from 1.26 to 1.27 before Black Friday traffic surge

#### 1. Pre-Upgrade Application State:
```bash
# Check current application status
kubectl get deployments -n production
kubectl get pods -n production -o wide
kubectl top pods -n production

# Monitor application metrics
curl -s http://api-gateway.production.svc.cluster.local:8080/actuator/metrics | jq .
```

#### 2. Traffic Management During Upgrade:
```yaml
# Implement traffic splitting using Istio/ALB
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: frontend-traffic-split
  namespace: production
spec:
  hosts:
  - shop.example.com
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: frontend
        subset: v2-1-1  # New version
      weight: 100
  - route:
    - destination:
        host: frontend
        subset: v2-1-0  # Current version
      weight: 90
    - destination:
        host: frontend
        subset: v2-1-1  # New version
      weight: 10
```

#### 3. Database Connection Handling:
```yaml
# Ensure database connections are properly handled
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
  namespace: production
data:
  application.yml: |
    spring:
      datasource:
        hikari:
          maximum-pool-size: 20
          minimum-idle: 5
          connection-timeout: 30000
          idle-timeout: 600000
          max-lifetime: 1800000
          leak-detection-threshold: 60000
      jpa:
        properties:
          hibernate:
            connection:
              provider_disables_autocommit: true
```

#### 4. Monitoring During Upgrade:
```bash
# Real-time monitoring script
#!/bin/bash
# monitor-upgrade.sh

while true; do
  echo "=== $(date) ==="
  
  # Check node status
  echo "Nodes:"
  kubectl get nodes --no-headers | awk '{print $1 " " $2}' | head -5
  
  # Check application pods
  echo "Application Pods:"
  kubectl get pods -n production --no-headers | grep -E "(frontend|api-gateway|user-service)" | awk '{print $1 " " $3}'
  
  # Check service endpoints
  echo "Service Health:"
  curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://shop.example.com/health
  curl -s -o /dev/null -w "API Gateway: %{http_code}\n" http://api-gateway.production.svc.cluster.local:8080/actuator/health
  
  # Check error rates
  echo "Error Rate:"
  kubectl logs -n production deployment/api-gateway --tail=100 | grep ERROR | wc -l
  
  echo "---"
  sleep 30
done
```

#### 5. Upgrade Execution Timeline:

**T-0: Start Upgrade (2:00 AM EST - Low Traffic)**
```bash
# Enable maintenance mode banner
kubectl patch configmap frontend-config -n production \
  --patch '{"data":{"maintenance_mode":"true","maintenance_message":"System maintenance in progress. Service may be briefly interrupted."}}'

# Start control plane upgrade
aws eks update-cluster-version --name production-cluster --kubernetes-version 1.27
```

**T+30min: Control Plane Upgraded**
```bash
# Verify control plane
kubectl cluster-info
kubectl get nodes

# Start node group upgrade
aws eks update-nodegroup-version --cluster-name production-cluster --nodegroup-name primary-nodes --kubernetes-version 1.27
```

**T+90min: Node Group Upgrade in Progress**
```bash
# Monitor pod rescheduling
kubectl get pods -n production -o wide --watch

# Check application availability
for i in {1..10}; do
  curl -s http://shop.example.com/health
  sleep 10
done
```

**T+150min: Node Group Upgraded**
```bash
# Verify all nodes updated
kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo.kubeletVersion}'

# Start add-on upgrades
aws eks update-addon --cluster-name production-cluster --addon-name coredns --addon-version v1.10.1-eksbuild.1
aws eks update-addon --cluster-name production-cluster --addon-name vpc-cni --addon-version v1.13.4-eksbuild.1
```

**T+180min: Add-ons Upgraded**
```bash
# Disable maintenance mode
kubectl patch configmap frontend-config -n production \
  --patch '{"data":{"maintenance_mode":"false"}}'

# Full system validation
./validate-upgrade.sh
```

---

## Rollback Procedures

### 1. Control Plane Rollback
```bash
# Note: Control plane cannot be rolled back directly
# Must restore from backup or recreate cluster

# Emergency cluster recreation (last resort)
# 1. Export all resources
kubectl get all --all-namespaces -o yaml > cluster-backup.yaml

# 2. Create new cluster with previous version
eksctl create cluster --name production-cluster-rollback --version 1.26

# 3. Restore applications
kubectl apply -f cluster-backup.yaml
```

### 2. Node Group Rollback
```bash
# Rollback managed node group
aws eks update-nodegroup-version \
  --cluster-name production-cluster \
  --nodegroup-name primary-nodes \
  --kubernetes-version 1.26 \
  --force

# For self-managed nodes, revert launch template
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name eks-nodes-asg \
  --launch-template '{
    "LaunchTemplateId": "lt-12345678",
    "Version": "1"
  }'
```

### 3. Application Rollback
```bash
# Rollback application deployments
kubectl rollout undo deployment/frontend -n production
kubectl rollout undo deployment/api-gateway -n production
kubectl rollout undo deployment/user-service -n production

# Verify rollback
kubectl rollout status deployment/frontend -n production
```

### 4. Database Rollback
```bash
# Restore database from backup (if needed)
# Using Velero
velero restore create --from-backup pre-upgrade-backup-20231201

# Using manual snapshots
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier production-db-restored \
  --db-snapshot-identifier pre-upgrade-snapshot-20231201
```

---

## Post-Upgrade Validation

### 1. Comprehensive Health Check
```bash
#!/bin/bash
# post-upgrade-validation.sh

echo "=== Post-Upgrade Validation ==="

# 1. Cluster version verification
CLUSTER_VERSION=$(aws eks describe-cluster --name production-cluster --query 'cluster.version' --output text)
echo "Cluster version: $CLUSTER_VERSION"

# 2. Node version verification
echo "Node versions:"
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.nodeInfo.kubeletVersion}{"\n"}{end}'

# 3. Add-on versions
echo "Add-on versions:"
aws eks describe-addon --cluster-name production-cluster --addon-name coredns --query 'addon.addonVersion'
aws eks describe-addon --cluster-name production-cluster --addon-name vpc-cni --query 'addon.addonVersion'

# 4. System pods health
echo "System pods status:"
kubectl get pods -n kube-system --no-headers | grep -v Running | grep -v Completed

# 5. Application pods health
echo "Application pods status:"
kubectl get pods -n production --no-headers | grep -v Running

# 6. Service connectivity
echo "Service connectivity:"
kubectl get svc -n production

# 7. Ingress status
echo "Ingress status:"
kubectl get ingress -n production

# 8. Storage validation
echo "Storage validation:"
kubectl get pv | grep -v Bound

echo "Validation completed!"
```

### 2. Performance Testing
```bash
# Load testing script
#!/bin/bash
# performance-test.sh

echo "Starting performance tests..."

# Test frontend response time
for i in {1..100}; do
  curl -s -w "%{time_total}\n" -o /dev/null http://shop.example.com/
done | awk '{sum+=$1; count++} END {print "Average response time:", sum/count, "seconds"}'

# Test API endpoints
echo "Testing API endpoints..."
curl -s http://api-gateway.production.svc.cluster.local:8080/actuator/health | jq .

# Database connection test
kubectl exec -n production deployment/user-service -- \
  curl -s http://localhost:8080/actuator/health/db | jq .

# Memory and CPU usage
kubectl top pods -n production
kubectl top nodes

echo "Performance tests completed!"
```

### 3. Security Validation
```bash
# Security validation
kubectl auth can-i --list --as=system:serviceaccount:production:default

# Check Pod Security Standards
kubectl get pods -n production -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext.runAsNonRoot}{"\n"}{end}'

# Network policy validation
kubectl get networkpolicies -n production
```

---

## Best Practices & Troubleshooting

### 1. Best Practices Summary

#### Pre-Upgrade:
- ✅ **Test in non-production first** - Always upgrade dev/staging environments first
- ✅ **Backup everything** - etcd, persistent volumes, application data
- ✅ **Check compatibility** - API deprecations, add-on versions, workload compatibility
- ✅ **Plan maintenance window** - During low traffic periods
- ✅ **Prepare rollback plan** - Document rollback procedures and test them

#### During Upgrade:
- ✅ **Monitor continuously** - Application health, resource usage, error rates
- ✅ **Upgrade incrementally** - Control plane → nodes → add-ons
- ✅ **Validate each phase** - Don't proceed if issues are detected
- ✅ **Communicate status** - Keep stakeholders informed
- ✅ **Document issues** - Track any problems for future reference

#### Post-Upgrade:
- ✅ **Comprehensive validation** - Functional, performance, security testing
- ✅ **Monitor extended period** - Watch for delayed issues (24-48 hours)
- ✅ **Update documentation** - Reflect new versions and any changes
- ✅ **Review and improve** - Lessons learned for next upgrade
- ✅ **Clean up** - Remove old resources, update CI/CD pipelines

### 2. Common Issues & Solutions

#### Issue: Pods Stuck in Pending State
```bash
# Diagnosis
kubectl describe pod <pod-name> -n production
kubectl get events -n production --sort-by='.lastTimestamp'

# Common causes and solutions:
# 1. Resource constraints
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"

# 2. Node selector/affinity issues
kubectl get nodes --show-labels
kubectl describe pod <pod-name> -n production | grep -A 10 "Node-Selectors"

# 3. PVC mounting issues
kubectl get pvc -n production
kubectl describe pvc <pvc-name> -n production
```

#### Issue: Service Connectivity Problems
```bash
# Diagnosis
kubectl get endpoints -n production
kubectl get svc -n production -o wide

# Test connectivity
kubectl run debug-pod --image=busybox --rm -it -- /bin/sh
# Inside pod:
nslookup api-gateway.production.svc.cluster.local
wget -qO- http://api-gateway.production.svc.cluster.local:8080/health

# Check CoreDNS
kubectl logs -n kube-system deployment/coredns
```

#### Issue: High Resource Usage After Upgrade
```bash
# Monitor resource usage
kubectl top pods --all-namespaces --sort-by=memory
kubectl top nodes

# Check for resource leaks
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[0].resources.requests.memory}{"\n"}{end}' | sort -k3 -h

# Adjust resource limits if needed
kubectl patch deployment api-gateway -n production -p '{"spec":{"template":{"spec":{"containers":[{"name":"api-gateway","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
```

### 3. Monitoring and Alerting Setup

#### CloudWatch Alarms for Upgrade Monitoring:
```bash
# Create alarms for upgrade monitoring
aws cloudwatch put-metric-alarm \
  --alarm-name "EKS-Upgrade-Pod-Failures" \
  --alarm-description "Alert on pod failures during upgrade" \
  --metric-name "pod_number_of_container_restarts" \
  --namespace "ContainerInsights" \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ClusterName,Value=production-cluster

aws cloudwatch put-metric-alarm \
  --alarm-name "EKS-Upgrade-Node-NotReady" \
  --alarm-description "Alert on nodes not ready during upgrade" \
  --metric-name "cluster_node_count" \
  --namespace "ContainerInsights" \
  --statistic Average \
  --period 300 \
  --threshold 3 \
  --comparison-operator LessThanThreshold
```

### 4. Upgrade Checklist Template

```
□ Pre-Upgrade Phase
  □ Health assessment completed
  □ Compatibility check passed
  □ Backup strategy implemented
  □ Test environment upgraded successfully
  □ Staging environment upgraded successfully
  □ Rollback procedures documented and tested
  □ Team briefing completed
  □ Stakeholders notified

□ Upgrade Execution
  □ Maintenance window started
  □ Final health check passed
  □ Control plane upgrade initiated
  □ Control plane upgrade completed and validated
  □ Node group upgrade initiated
  □ Node group upgrade completed and validated
  □ Add-on upgrades completed
  □ Application validation passed
  □ Performance testing completed

□ Post-Upgrade Phase
  □ Comprehensive validation completed
  □ Monitoring enabled and alerts configured
  □ Documentation updated
  □ Stakeholders notified of completion
  □ Post-upgrade review scheduled
  □ Cleanup tasks completed
```

### 5. Emergency Contacts and Escalation

```
Upgrade Team Contacts:
- Lead Engineer: [NAME] - [PHONE] - [EMAIL]
- Platform Team: [NAME] - [PHONE] - [EMAIL]
- Database Admin: [NAME] - [PHONE] - [EMAIL]
- Network Team: [NAME] - [PHONE] - [EMAIL]

Escalation Path:
1. Technical Issues → Lead Engineer
2. Business Impact → Engineering Manager
3. Critical Outage → VP Engineering + CTO

Emergency Procedures:
- Rollback Decision: Within 30 minutes of issue detection
- Communication: Update status page within 15 minutes
- Customer Support: Notify within 10 minutes of user impact
```

This comprehensive guide provides everything needed to perform zero-downtime EKS upgrades in production environments, with real-world examples and detailed troubleshooting procedures that even fresh engineers can follow successfully.