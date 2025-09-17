# ArgoCD with EKS - Complete GitOps Implementation Guide

## Table of Contents
1. [ArgoCD Overview & Architecture](#argocd-overview--architecture)
2. [Prerequisites & EKS Setup](#prerequisites--eks-setup)
3. [ArgoCD Installation (Recommended Approach)](#argocd-installation-recommended-approach)
4. [Security & RBAC Configuration](#security--rbac-configuration)
5. [Go Sample Application Setup](#go-sample-application-setup)
6. [GitOps Repository Structure](#gitops-repository-structure)
7. [Application Deployment with ArgoCD](#application-deployment-with-argocd)
8. [Advanced ArgoCD Features](#advanced-argocd-features)
9. [Production Best Practices](#production-best-practices)
10. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## ArgoCD Overview & Architecture

### What is ArgoCD?
- **Declarative GitOps** continuous delivery tool for Kubernetes
- **Git as single source of truth** for application and infrastructure state
- **Automated synchronization** between Git repositories and Kubernetes clusters
- **Multi-cluster management** with centralized control plane
- **Web UI and CLI** for application management

### GitOps Benefits:
- **Version Control**: All changes tracked in Git
- **Rollback Capability**: Easy revert to previous states
- **Audit Trail**: Complete history of deployments
- **Security**: No direct cluster access needed
- **Consistency**: Declarative desired state management

### ArgoCD Architecture:
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Git Repository │    │   ArgoCD Server  │    │  EKS Cluster    │
│   (Source of     │◄──►│   (Controller)   │◄──►│  (Target)       │
│    Truth)        │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐            │
         └──────────────►│   ArgoCD UI      │◄───────────┘
                         │   (Dashboard)    │
                         └──────────────────┘
```

---

## Prerequisites & EKS Setup

### 1. EKS Cluster Requirements

#### Create EKS Cluster:
```bash
# Create cluster with eksctl
eksctl create cluster \
  --name argocd-demo \
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
kubectl get namespaces
```

#### Install Required Tools:
```bash
# Install ArgoCD CLI
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64

# Verify installation
argocd version --client

# Install Helm (if not already installed)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install kubectl (if not already installed)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### 2. AWS Load Balancer Controller (Required for Ingress)

#### Install AWS Load Balancer Controller:
```bash
# Create IAM policy
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

# Create service account
eksctl create iamserviceaccount \
  --cluster=argocd-demo \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install controller via Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=argocd-demo \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

---

## ArgoCD Installation (Recommended Approach)

### 1. Namespace and Core Installation

#### Create ArgoCD Namespace:
```bash
kubectl create namespace argocd
```

#### Install ArgoCD (Stable Release - Recommended):
```bash
# Install stable release (recommended for production)
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Verify installation
kubectl get pods -n argocd
kubectl get svc -n argocd
```

### 2. High Availability Installation (Production)

#### HA ArgoCD Installation:
```bash
# For production environments, use HA installation
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/ha/install.yaml

# Verify HA components
kubectl get pods -n argocd
# Should see multiple replicas of argocd-server, argocd-repo-server, etc.
```

### 3. Custom Configuration (Recommended)

#### ArgoCD Configuration ConfigMap:
```yaml
# argocd-cmd-params-cm.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cmd-params-cm
  namespace: argocd
  labels:
    app.kubernetes.io/name: argocd-cmd-params-cm
    app.kubernetes.io/part-of: argocd
data:
  # Server configuration
  server.insecure: "false"
  server.grpc.web: "true"
  
  # Repository server configuration
  reposerver.parallelism.limit: "10"
  
  # Application controller configuration
  controller.status.processors: "20"
  controller.operation.processors: "10"
  controller.self.heal.timeout.seconds: "5"
  controller.repo.server.timeout.seconds: "60"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-server-config
  namespace: argocd
  labels:
    app.kubernetes.io/name: argocd-server-config
    app.kubernetes.io/part-of: argocd
data:
  # OIDC configuration (optional)
  url: https://argocd.company.com
  
  # Git repository credentials template
  repositories: |
    - type: git
      url: https://github.com/company/gitops-configs
    - type: helm
      url: https://charts.bitnami.com/bitnami
      name: bitnami
  
  # Resource customizations
  resource.customizations: |
    argoproj.io/Application:
      health.lua: |
        hs = {}
        hs.status = "Healthy"
        return hs
  
  # Application instance label key
  application.instanceLabelKey: argocd.argoproj.io/instance
```

#### Apply Configuration:
```bash
kubectl apply -f argocd-cmd-params-cm.yaml
kubectl rollout restart deployment argocd-server -n argocd
kubectl rollout restart deployment argocd-repo-server -n argocd
```

### 4. Ingress Configuration (ALB)

#### ArgoCD Ingress with ALB:
```yaml
# argocd-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/backend-protocol: HTTPS
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-west-2:ACCOUNT:certificate/CERT_ID
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/healthcheck-path: /healthz
    alb.ingress.kubernetes.io/healthcheck-protocol: HTTPS
spec:
  rules:
  - host: argocd.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 443
```

#### Apply Ingress:
```bash
kubectl apply -f argocd-ingress.yaml

# Check ingress status
kubectl get ingress -n argocd
kubectl describe ingress argocd-server-ingress -n argocd
```

### 5. Initial Admin Setup

#### Get Initial Admin Password:
```bash
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo

# Login via CLI
argocd login argocd.company.com --username admin --password <password>

# Change admin password
argocd account update-password --current-password <current> --new-password <new>

# Delete initial secret (security best practice)
kubectl -n argocd delete secret argocd-initial-admin-secret
```

---

## Security & RBAC Configuration

### 1. RBAC Configuration

#### ArgoCD RBAC Policy:
```yaml
# argocd-rbac-cm.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
  labels:
    app.kubernetes.io/name: argocd-rbac-cm
    app.kubernetes.io/part-of: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    # Admin role - full access
    p, role:admin, applications, *, */*, allow
    p, role:admin, clusters, *, *, allow
    p, role:admin, repositories, *, *, allow
    p, role:admin, certificates, *, *, allow
    p, role:admin, projects, *, *, allow
    p, role:admin, accounts, *, *, allow
    p, role:admin, gpgkeys, *, *, allow
    
    # Developer role - application management
    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, create, */*, allow
    p, role:developer, applications, update, */*, allow
    p, role:developer, applications, sync, */*, allow
    p, role:developer, applications, delete, */*, allow
    p, role:developer, repositories, get, *, allow
    p, role:developer, clusters, get, *, allow
    p, role:developer, projects, get, *, allow
    
    # DevOps role - infrastructure management
    p, role:devops, applications, *, */*, allow
    p, role:devops, clusters, *, *, allow
    p, role:devops, repositories, *, *, allow
    p, role:devops, projects, *, *, allow
    
    # ReadOnly role - view only
    p, role:readonly, applications, get, */*, allow
    p, role:readonly, repositories, get, *, allow
    p, role:readonly, clusters, get, *, allow
    p, role:readonly, projects, get, *, allow
    
    # Group mappings (if using OIDC/SAML)
    g, argocd-admins, role:admin
    g, developers, role:developer
    g, devops-team, role:devops
    g, viewers, role:readonly
```

#### Apply RBAC Configuration:
```bash
kubectl apply -f argocd-rbac-cm.yaml
kubectl rollout restart deployment argocd-server -n argocd
```

### 2. Service Account and Cluster Access

#### ArgoCD Service Account with Cluster Admin:
```yaml
# argocd-cluster-admin.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: argocd-application-controller
  namespace: argocd
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: argocd-application-controller
rules:
- apiGroups:
  - '*'
  resources:
  - '*'
  verbs:
  - '*'
- nonResourceURLs:
  - '*'
  verbs:
  - '*'
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: argocd-application-controller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: argocd-application-controller
subjects:
- kind: ServiceAccount
  name: argocd-application-controller
  namespace: argocd
```

### 3. Network Policies (Security)

#### ArgoCD Network Policy:
```yaml
# argocd-network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: argocd-server-network-policy
  namespace: argocd
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: argocd-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: aws-load-balancer-controller
    ports:
    - protocol: TCP
      port: 8080
    - protocol: TCP
      port: 8083
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 22
```

---

## Go Sample Application Setup

### 1. Sample Go Application

#### Create Go Application Structure:
```bash
# Create application directory
mkdir -p go-sample-app
cd go-sample-app

# Initialize Go module
go mod init github.com/company/go-sample-app
```

#### Main Application Code:
```go
// main.go
package main

import (
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "time"
)

type HealthResponse struct {
    Status    string    `json:"status"`
    Timestamp time.Time `json:"timestamp"`
    Version   string    `json:"version"`
    Hostname  string    `json:"hostname"`
}

type AppResponse struct {
    Message   string    `json:"message"`
    Timestamp time.Time `json:"timestamp"`
    Version   string    `json:"version"`
    Hostname  string    `json:"hostname"`
}

func main() {
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }

    version := os.Getenv("APP_VERSION")
    if version == "" {
        version = "1.0.0"
    }

    hostname, _ := os.Hostname()

    http.HandleFunc("/", homeHandler(version, hostname))
    http.HandleFunc("/health", healthHandler(version, hostname))
    http.HandleFunc("/ready", readyHandler(version, hostname))

    log.Printf("Starting server on port %s, version %s", port, version)
    log.Fatal(http.ListenAndServe(":"+port, nil))
}

func homeHandler(version, hostname string) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        response := AppResponse{
            Message:   "Hello from Go Sample App deployed with ArgoCD!",
            Timestamp: time.Now(),
            Version:   version,
            Hostname:  hostname,
        }

        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(response)
    }
}

func healthHandler(version, hostname string) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        response := HealthResponse{
            Status:    "healthy",
            Timestamp: time.Now(),
            Version:   version,
            Hostname:  hostname,
        }

        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(response)
    }
}

func readyHandler(version, hostname string) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        response := HealthResponse{
            Status:    "ready",
            Timestamp: time.Now(),
            Version:   version,
            Hostname:  hostname,
        }

        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(response)
    }
}
```

#### Go Module Dependencies:
```go
// go.mod
module github.com/company/go-sample-app

go 1.21

// No external dependencies for this simple example
```

### 2. Dockerfile (Multi-stage Build)

#### Optimized Dockerfile:
```dockerfile
# Dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Final stage
FROM alpine:3.18

# Install ca-certificates for HTTPS requests
RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy the binary from builder stage
COPY --from=builder /app/main .

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -D -s /bin/sh -u 1001 -G appgroup appuser

# Change ownership of the binary
RUN chown appuser:appgroup main

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the binary
CMD ["./main"]
```

### 3. Build and Push Container Image

#### Build Script:
```bash
#!/bin/bash
# build-and-push.sh

set -e

# Configuration
IMAGE_NAME="go-sample-app"
REGISTRY="your-account.dkr.ecr.us-west-2.amazonaws.com"
VERSION=${1:-"v1.0.0"}

echo "Building and pushing $IMAGE_NAME:$VERSION"

# Build image
docker build -t $IMAGE_NAME:$VERSION .
docker tag $IMAGE_NAME:$VERSION $REGISTRY/$IMAGE_NAME:$VERSION
docker tag $IMAGE_NAME:$VERSION $REGISTRY/$IMAGE_NAME:latest

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $REGISTRY

# Create repository if it doesn't exist
aws ecr describe-repositories --repository-names $IMAGE_NAME --region us-west-2 || \
aws ecr create-repository --repository-name $IMAGE_NAME --region us-west-2

# Push images
docker push $REGISTRY/$IMAGE_NAME:$VERSION
docker push $REGISTRY/$IMAGE_NAME:latest

echo "Successfully pushed $REGISTRY/$IMAGE_NAME:$VERSION"
```

#### Execute Build:
```bash
chmod +x build-and-push.sh
./build-and-push.sh v1.0.0
```

---

## GitOps Repository Structure

### 1. Repository Structure (Best Practices)

#### Recommended Directory Structure:
```
gitops-configs/
├── applications/
│   ├── go-sample-app/
│   │   ├── base/
│   │   │   ├── kustomization.yaml
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── configmap.yaml
│   │   │   └── ingress.yaml
│   │   └── overlays/
│   │       ├── development/
│   │       │   ├── kustomization.yaml
│   │       │   └── patches/
│   │       ├── staging/
│   │       │   ├── kustomization.yaml
│   │       │   └── patches/
│   │       └── production/
│   │           ├── kustomization.yaml
│   │           └── patches/
├── argocd-apps/
│   ├── go-sample-app-dev.yaml
│   ├── go-sample-app-staging.yaml
│   └── go-sample-app-prod.yaml
└── projects/
    └── default-project.yaml
```

### 2. Base Kubernetes Manifests

#### Deployment (Base):
```yaml
# applications/go-sample-app/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-sample-app
  labels:
    app: go-sample-app
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: go-sample-app
  template:
    metadata:
      labels:
        app: go-sample-app
        version: v1.0.0
    spec:
      containers:
      - name: go-sample-app
        image: your-account.dkr.ecr.us-west-2.amazonaws.com/go-sample-app:v1.0.0
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: PORT
          value: "8080"
        - name: APP_VERSION
          value: "v1.0.0"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1001
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
```

#### Service (Base):
```yaml
# applications/go-sample-app/base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: go-sample-app
  labels:
    app: go-sample-app
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: go-sample-app
```

#### ConfigMap (Base):
```yaml
# applications/go-sample-app/base/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: go-sample-app-config
  labels:
    app: go-sample-app
data:
  app.properties: |
    # Application configuration
    log.level=info
    metrics.enabled=true
    
  nginx.conf: |
    # Nginx configuration for reverse proxy (if needed)
    upstream backend {
        server localhost:8080;
    }
```

#### Ingress (Base):
```yaml
# applications/go-sample-app/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: go-sample-app
  labels:
    app: go-sample-app
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  rules:
  - host: go-app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: go-sample-app
            port:
              number: 80
```

#### Base Kustomization:
```yaml
# applications/go-sample-app/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

metadata:
  name: go-sample-app-base

resources:
- deployment.yaml
- service.yaml
- configmap.yaml
- ingress.yaml

commonLabels:
  app: go-sample-app
  managed-by: argocd

images:
- name: your-account.dkr.ecr.us-west-2.amazonaws.com/go-sample-app
  newTag: v1.0.0
```

### 3. Environment Overlays

#### Development Overlay:
```yaml
# applications/go-sample-app/overlays/development/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

metadata:
  name: go-sample-app-development

namespace: development

resources:
- ../../base

patchesStrategicMerge:
- patches/deployment-patch.yaml
- patches/ingress-patch.yaml

replicas:
- name: go-sample-app
  count: 1

images:
- name: your-account.dkr.ecr.us-west-2.amazonaws.com/go-sample-app
  newTag: latest

commonLabels:
  environment: development
```

#### Development Patches:
```yaml
# applications/go-sample-app/overlays/development/patches/deployment-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-sample-app
spec:
  template:
    spec:
      containers:
      - name: go-sample-app
        env:
        - name: APP_VERSION
          value: "development"
        - name: LOG_LEVEL
          value: "debug"
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 256Mi
---
# applications/go-sample-app/overlays/development/patches/ingress-patch.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: go-sample-app
spec:
  rules:
  - host: go-app-dev.company.com
```

#### Production Overlay:
```yaml
# applications/go-sample-app/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

metadata:
  name: go-sample-app-production

namespace: production

resources:
- ../../base

patchesStrategicMerge:
- patches/deployment-patch.yaml
- patches/ingress-patch.yaml
- patches/hpa-patch.yaml

replicas:
- name: go-sample-app
  count: 5

images:
- name: your-account.dkr.ecr.us-west-2.amazonaws.com/go-sample-app
  newTag: v1.0.0

commonLabels:
  environment: production
```

#### Production Patches:
```yaml
# applications/go-sample-app/overlays/production/patches/deployment-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-sample-app
spec:
  template:
    spec:
      containers:
      - name: go-sample-app
        env:
        - name: APP_VERSION
          value: "v1.0.0"
        - name: LOG_LEVEL
          value: "info"
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
---
# applications/go-sample-app/overlays/production/patches/hpa-patch.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: go-sample-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: go-sample-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Application Deployment with ArgoCD

### 1. ArgoCD Application Definitions

#### Development Application:
```yaml
# argocd-apps/go-sample-app-dev.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: go-sample-app-dev
  namespace: argocd
  labels:
    environment: development
    team: backend
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  
  source:
    repoURL: https://github.com/company/gitops-configs
    targetRevision: HEAD
    path: applications/go-sample-app/overlays/development
  
  destination:
    server: https://kubernetes.default.svc
    namespace: development
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  
  revisionHistoryLimit: 10
  
  ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
    - /spec/replicas
```

#### Production Application:
```yaml
# argocd-apps/go-sample-app-prod.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: go-sample-app-prod
  namespace: argocd
  labels:
    environment: production
    team: backend
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  
  source:
    repoURL: https://github.com/company/gitops-configs
    targetRevision: v1.0.0  # Use specific tag for production
    path: applications/go-sample-app/overlays/production
  
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  
  syncPolicy:
    # Manual sync for production (recommended)
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true
    retry:
      limit: 3
      backoff:
        duration: 10s
        factor: 2
        maxDuration: 5m
  
  revisionHistoryLimit: 20
```

### 2. Deploy Applications

#### Apply ArgoCD Applications:
```bash
# Create namespaces first
kubectl create namespace development --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f -

# Deploy development application
kubectl apply -f argocd-apps/go-sample-app-dev.yaml

# Deploy production application (manual sync)
kubectl apply -f argocd-apps/go-sample-app-prod.yaml
```

#### Sync Applications via CLI:
```bash
# Sync development application
argocd app sync go-sample-app-dev

# Sync production application (manual)
argocd app sync go-sample-app-prod

# Check application status
argocd app list
argocd app get go-sample-app-dev
```

### 3. Application Management

#### View Application Status:
```bash
# List all applications
argocd app list

# Get detailed application info
argocd app get go-sample-app-dev

# View application logs
argocd app logs go-sample-app-dev

# View sync history
argocd app history go-sample-app-dev
```

#### Manual Operations:
```bash
# Manual sync
argocd app sync go-sample-app-prod

# Rollback to previous version
argocd app rollback go-sample-app-prod 5

# Refresh application (detect changes)
argocd app refresh go-sample-app-dev

# Delete application
argocd app delete go-sample-app-dev
```

---

## Advanced ArgoCD Features

### 1. App of Apps Pattern

#### Root Application:
```yaml
# argocd-apps/root-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-applications
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/company/gitops-configs
    targetRevision: HEAD
    path: argocd-apps
  
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### 2. Multi-Source Applications

#### Multi-Source Application:
```yaml
# Multi-source application example
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: go-sample-app-multi-source
  namespace: argocd
spec:
  project: default
  
  sources:
  - repoURL: https://github.com/company/gitops-configs
    targetRevision: HEAD
    path: applications/go-sample-app/overlays/production
  - repoURL: https://github.com/company/helm-charts
    targetRevision: HEAD
    path: go-sample-app
    helm:
      valueFiles:
      - $values/applications/go-sample-app/values-prod.yaml
  - repoURL: https://github.com/company/gitops-configs
    targetRevision: HEAD
    path: applications/go-sample-app
    ref: values
  
  destination:
    server: https://kubernetes.default.svc
    namespace: production
```

### 3. Sync Waves and Hooks

#### Sync Waves Example:
```yaml
# Deployment with sync wave
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-sample-app
  annotations:
    argocd.argoproj.io/sync-wave: "2"  # Deploy after wave 1
spec:
  # ... deployment spec
---
# Service with earlier sync wave
apiVersion: v1
kind: Service
metadata:
  name: go-sample-app
  annotations:
    argocd.argoproj.io/sync-wave: "1"  # Deploy first
spec:
  # ... service spec
```

#### Pre/Post Sync Hooks:
```yaml
# Database migration job (pre-sync hook)
apiVersion: batch/v1
kind: Job
metadata:
  name: go-sample-app-migration
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: migrate/migrate:latest
        command: ["migrate", "-path", "/migrations", "-database", "postgres://...", "up"]
      restartPolicy: Never
```

### 4. Resource Health Checks

#### Custom Health Check:
```yaml
# Custom resource health check
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  resource.customizations.health.argoproj.io_Rollout: |
    hs = {}
    if obj.status ~= nil then
      if obj.status.phase == "Degraded" then
        hs.status = "Degraded"
        hs.message = obj.status.message
        return hs
      end
      if obj.status.phase == "Progressing" then
        hs.status = "Progressing"
        hs.message = obj.status.message
        return hs
      end
    end
    hs.status = "Healthy"
    return hs
```

---

## Production Best Practices

### 1. Security Best Practices

#### Repository Access with SSH Keys:
```yaml
# SSH key secret for private repositories
apiVersion: v1
kind: Secret
metadata:
  name: private-repo-ssh
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
type: Opaque
stringData:
  type: git
  url: git@github.com:company/private-gitops-configs.git
  sshPrivateKey: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    ... (your private key)
    -----END OPENSSH PRIVATE KEY-----
```

#### Sealed Secrets Integration:
```bash
# Install Sealed Secrets Controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret
echo -n mypassword | kubectl create secret generic mysecret --dry-run=client --from-file=password=/dev/stdin -o yaml | kubeseal -o yaml > mysealedsecret.yaml
```

### 2. Monitoring and Observability

#### ArgoCD Metrics Configuration:
```yaml
# Enable metrics in argocd-server-config
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-server-config
  namespace: argocd
data:
  application.instanceLabelKey: argocd.argoproj.io/instance
  server.metrics: "true"
  controller.metrics: "true"
  reposerver.metrics: "true"
```

#### Prometheus ServiceMonitor:
```yaml
# ArgoCD ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-metrics
  namespace: argocd
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-metrics
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-server-metrics
  namespace: argocd
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-server-metrics
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### 3. Backup and Disaster Recovery

#### ArgoCD Backup Script:
```bash
#!/bin/bash
# argocd-backup.sh

BACKUP_DIR="/backup/argocd/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Creating ArgoCD backup..."

# Backup ArgoCD applications
kubectl get applications -n argocd -o yaml > $BACKUP_DIR/applications.yaml

# Backup ArgoCD projects
kubectl get appprojects -n argocd -o yaml > $BACKUP_DIR/projects.yaml

# Backup ArgoCD configuration
kubectl get configmaps -n argocd -o yaml > $BACKUP_DIR/configmaps.yaml
kubectl get secrets -n argocd -o yaml > $BACKUP_DIR/secrets.yaml

# Backup RBAC configuration
kubectl get clusterroles,clusterrolebindings -l app.kubernetes.io/part-of=argocd -o yaml > $BACKUP_DIR/rbac.yaml

echo "Backup completed: $BACKUP_DIR"

# Upload to S3 (optional)
aws s3 sync $BACKUP_DIR s3://company-argocd-backups/$(basename $BACKUP_DIR)/
```

### 4. High Availability Configuration

#### HA ArgoCD with Redis:
```yaml
# Redis for HA ArgoCD
apiVersion: apps/v1
kind: Deployment
metadata:
  name: argocd-redis-ha-haproxy
  namespace: argocd
spec:
  replicas: 3
  selector:
    matchLabels:
      app: argocd-redis-ha-haproxy
  template:
    metadata:
      labels:
        app: argocd-redis-ha-haproxy
    spec:
      containers:
      - name: haproxy
        image: haproxy:2.6.2-alpine
        ports:
        - containerPort: 6379
        - containerPort: 26379
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

---

## Monitoring & Troubleshooting

### 1. ArgoCD Health Monitoring

#### Health Check Script:
```bash
#!/bin/bash
# argocd-health-check.sh

echo "=== ArgoCD Health Check ==="

# Check ArgoCD pods
echo "1. Checking ArgoCD pods..."
kubectl get pods -n argocd

# Check ArgoCD services
echo "2. Checking ArgoCD services..."
kubectl get svc -n argocd

# Check application status
echo "3. Checking application status..."
argocd app list

# Check sync status
echo "4. Checking sync status..."
for app in $(argocd app list -o name); do
    echo "App: $app"
    argocd app get $app | grep -E "(Health Status|Sync Status)"
done

# Check ArgoCD server logs
echo "5. Recent ArgoCD server logs..."
kubectl logs -n argocd deployment/argocd-server --tail=10

echo "=== Health Check Complete ==="
```

### 2. Common Issues and Solutions

#### Sync Issues Troubleshooting:
```bash
# Check application events
kubectl describe application go-sample-app-dev -n argocd

# Check resource differences
argocd app diff go-sample-app-dev

# Force refresh
argocd app refresh go-sample-app-dev --hard

# Check repository access
argocd repo list
argocd repo get https://github.com/company/gitops-configs
```

#### Performance Optimization:
```yaml
# Optimize ArgoCD performance
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cmd-params-cm
  namespace: argocd
data:
  # Increase parallelism
  controller.status.processors: "20"
  controller.operation.processors: "10"
  
  # Optimize repository server
  reposerver.parallelism.limit: "10"
  
  # Reduce resource usage
  controller.self.heal.timeout.seconds: "5"
  controller.repo.server.timeout.seconds: "60"
```

### 3. Monitoring Dashboard

#### Grafana Dashboard for ArgoCD:
```json
{
  "dashboard": {
    "title": "ArgoCD Monitoring",
    "panels": [
      {
        "title": "Application Sync Status",
        "type": "stat",
        "targets": [
          {
            "expr": "argocd_app_info",
            "legendFormat": "{{name}} - {{sync_status}}"
          }
        ]
      },
      {
        "title": "Sync Operations",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(argocd_app_sync_total[5m])",
            "legendFormat": "Sync Rate"
          }
        ]
      },
      {
        "title": "Repository Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "argocd_git_request_duration_seconds",
            "legendFormat": "Git Request Duration"
          }
        ]
      }
    ]
  }
}
```

This comprehensive guide provides everything needed to implement ArgoCD with EKS following best practices, from basic setup to advanced production configurations with a complete Go application example.