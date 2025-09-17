# GitHub Actions with AWS - Complete CI/CD Implementation Guide

## Table of Contents
1. [GitHub Actions Overview](#github-actions-overview)
2. [AWS Integration Setup](#aws-integration-setup)
3. [Real-World Example: Node.js App to EKS](#real-world-example-nodejs-app-to-eks)
4. [Repository Structure & Setup](#repository-structure--setup)
5. [CI/CD Pipeline Implementation](#cicd-pipeline-implementation)
6. [Security Best Practices](#security-best-practices)
7. [Advanced Workflows](#advanced-workflows)
8. [Monitoring & Notifications](#monitoring--notifications)
9. [Troubleshooting](#troubleshooting)

---

## GitHub Actions Overview

### What is GitHub Actions?
- **Native CI/CD platform** integrated with GitHub repositories
- **Event-driven workflows** triggered by repository events
- **Scalable runners** (GitHub-hosted or self-hosted)
- **Marketplace ecosystem** with thousands of pre-built actions
- **Matrix builds** for testing across multiple environments

### Key Components:
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Repository    │    │    Workflow      │    │     Runner      │
│   (Code + YML)  │───►│   (CI/CD Logic)  │───►│  (Execution)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐            │
         └──────────────►│     Actions      │◄───────────┘
                         │   (Reusable)     │
                         └──────────────────┘
```

### Benefits for AWS Integration:
- **Seamless AWS service integration** via official actions
- **OIDC authentication** for secure, keyless access
- **Multi-environment deployments** with approval gates
- **Cost-effective** compared to other CI/CD platforms
- **Version control** for pipeline configurations

---

## AWS Integration Setup

### 1. AWS IAM Configuration for GitHub Actions

#### Create IAM Role for GitHub Actions (OIDC - Recommended):
```bash
# Create trust policy for GitHub OIDC
cat > github-actions-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*"
        }
      }
    }
  ]
}
EOF

# Create the IAM role
aws iam create-role \
  --role-name GitHubActionsRole \
  --assume-role-policy-document file://github-actions-trust-policy.json

# Create policy for required AWS permissions
cat > github-actions-permissions.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-deployment-bucket",
        "arn:aws:s3:::your-deployment-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/github-actions/*"
    }
  ]
}
EOF

# Create and attach the policy
aws iam create-policy \
  --policy-name GitHubActionsPolicy \
  --policy-document file://github-actions-permissions.json

aws iam attach-role-policy \
  --role-name GitHubActionsRole \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/GitHubActionsPolicy
```

#### Setup GitHub OIDC Provider:
```bash
# Create OIDC identity provider (one-time setup per AWS account)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. GitHub Repository Secrets Configuration

#### Required Repository Secrets:
```bash
# Navigate to GitHub Repository Settings > Secrets and Variables > Actions

# Add the following secrets:
AWS_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole
AWS_REGION=us-west-2
ECR_REPOSITORY=your-app-name
EKS_CLUSTER_NAME=production-cluster

# Optional: For non-OIDC setup (not recommended)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 3. EKS Cluster Setup

#### Create EKS Cluster for Deployment:
```bash
# Create EKS cluster
eksctl create cluster \
  --name production-cluster \
  --version 1.28 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10 \
  --managed \
  --enable-ssm

# Create ECR repository
aws ecr create-repository \
  --repository-name nodejs-sample-app \
  --region us-west-2
```

---

## Real-World Example: Node.js App to EKS

### 1. Sample Node.js Application

#### Application Structure:
```
nodejs-sample-app/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd-staging.yml
│       └── cd-production.yml
├── src/
│   ├── app.js
│   ├── routes/
│   │   ├── health.js
│   │   └── api.js
│   └── middleware/
│       └── auth.js
├── tests/
│   ├── unit/
│   └── integration/
├── k8s/
│   ├── base/
│   └── overlays/
├── Dockerfile
├── package.json
├── package-lock.json
└── README.md
```

#### Main Application Code:
```javascript
// src/app.js
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const healthRoutes = require('./routes/health');
const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/health', healthRoutes);
app.use('/api/v1', apiRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'Node.js Sample App - Deployed with GitHub Actions',
    version: process.env.APP_VERSION || '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    timestamp: new Date().toISOString(),
    hostname: require('os').hostname()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Something went wrong!',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Internal Server Error'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Route not found',
    path: req.originalUrl
  });
});

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV}`);
  console.log(`Version: ${process.env.APP_VERSION}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
  });
});

module.exports = app;
```

#### Health Check Routes:
```javascript
// src/routes/health.js
const express = require('express');
const router = express.Router();

// Liveness probe
router.get('/live', (req, res) => {
  res.status(200).json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Readiness probe
router.get('/ready', (req, res) => {
  // Add actual readiness checks here (database, external services, etc.)
  const isReady = true; // Replace with actual health checks
  
  if (isReady) {
    res.status(200).json({
      status: 'ready',
      timestamp: new Date().toISOString(),
      checks: {
        database: 'healthy',
        cache: 'healthy'
      }
    });
  } else {
    res.status(503).json({
      status: 'not ready',
      timestamp: new Date().toISOString()
    });
  }
});

// Startup probe
router.get('/startup', (req, res) => {
  res.status(200).json({
    status: 'started',
    timestamp: new Date().toISOString(),
    version: process.env.APP_VERSION || '1.0.0'
  });
});

module.exports = router;
```

#### API Routes:
```javascript
// src/routes/api.js
const express = require('express');
const router = express.Router();

// Sample API endpoints
router.get('/users', (req, res) => {
  res.json({
    users: [
      { id: 1, name: 'John Doe', email: 'john@example.com' },
      { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
    ],
    total: 2,
    timestamp: new Date().toISOString()
  });
});

router.get('/metrics', (req, res) => {
  res.json({
    metrics: {
      requests_total: Math.floor(Math.random() * 1000),
      response_time_avg: Math.floor(Math.random() * 100),
      memory_usage: process.memoryUsage(),
      cpu_usage: process.cpuUsage()
    },
    timestamp: new Date().toISOString()
  });
});

router.post('/data', (req, res) => {
  const { data } = req.body;
  
  if (!data) {
    return res.status(400).json({
      error: 'Data is required',
      timestamp: new Date().toISOString()
    });
  }
  
  res.status(201).json({
    message: 'Data received successfully',
    received: data,
    timestamp: new Date().toISOString()
  });
});

module.exports = router;
```

#### Package.json:
```json
{
  "name": "nodejs-sample-app",
  "version": "1.0.0",
  "description": "Sample Node.js application for GitHub Actions CI/CD demo",
  "main": "src/app.js",
  "scripts": {
    "start": "node src/app.js",
    "dev": "nodemon src/app.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/ tests/",
    "lint:fix": "eslint src/ tests/ --fix",
    "security:audit": "npm audit",
    "security:check": "npm audit --audit-level moderate"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "morgan": "^1.10.0"
  },
  "devDependencies": {
    "jest": "^29.6.2",
    "supertest": "^6.3.3",
    "nodemon": "^3.0.1",
    "eslint": "^8.45.0",
    "eslint-config-standard": "^17.1.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=8.0.0"
  },
  "keywords": ["nodejs", "express", "github-actions", "kubernetes", "aws"],
  "author": "Your Name",
  "license": "MIT"
}
```

### 2. Dockerfile (Multi-stage Build)

#### Production-Ready Dockerfile:
```dockerfile
# Dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Production stage
FROM node:18-alpine AS production

# Create app directory
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy package files
COPY package*.json ./

# Copy dependencies from builder stage
COPY --from=builder /app/node_modules ./node_modules

# Copy application code
COPY src/ ./src/

# Change ownership to nodejs user
RUN chown -R nodejs:nodejs /app

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health/live', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) }).on('error', () => process.exit(1))"

# Start the application
CMD ["npm", "start"]
```

### 3. Kubernetes Manifests

#### Base Deployment:
```yaml
# k8s/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodejs-sample-app
  labels:
    app: nodejs-sample-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nodejs-sample-app
  template:
    metadata:
      labels:
        app: nodejs-sample-app
    spec:
      containers:
      - name: nodejs-sample-app
        image: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/nodejs-sample-app:latest
        ports:
        - containerPort: 3000
          name: http
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "3000"
        - name: APP_VERSION
          value: "1.0.0"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health/live
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health/startup
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1001
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
```

#### Service and Ingress:
```yaml
# k8s/base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nodejs-sample-app
  labels:
    app: nodejs-sample-app
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
    name: http
  selector:
    app: nodejs-sample-app
---
# k8s/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nodejs-sample-app
  labels:
    app: nodejs-sample-app
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health/ready
spec:
  rules:
  - host: nodejs-app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nodejs-sample-app
            port:
              number: 80
```

#### Kustomization:
```yaml
# k8s/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
- ingress.yaml

commonLabels:
  app: nodejs-sample-app
  managed-by: github-actions

images:
- name: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/nodejs-sample-app
  newTag: latest
```

---

## CI/CD Pipeline Implementation

### 1. Continuous Integration Workflow

#### CI Pipeline (.github/workflows/ci.yml):
```yaml
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  NODE_VERSION: '18'
  
jobs:
  test:
    name: Test and Quality Checks
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [16, 18, 20]
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Run linting
      run: npm run lint
      
    - name: Run security audit
      run: npm audit --audit-level moderate
      
    - name: Run tests
      run: npm run test:coverage
      
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info
        flags: unittests
        name: codecov-umbrella
        
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push'
    
    permissions:
      id-token: write
      contents: read
      
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: ${{ secrets.AWS_REGION }}
        
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2
      
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ steps.login-ecr.outputs.registry }}/${{ secrets.ECR_REPOSITORY }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
          
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ steps.login-ecr.outputs.registry }}/${{ secrets.ECR_REPOSITORY }}:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-results.sarif'
        
    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'

  security-scan:
    name: Security Scanning
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Run Snyk to check for vulnerabilities
      uses: snyk/actions/node@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      with:
        args: --severity-threshold=high
        
    - name: Upload result to GitHub Code Scanning
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: snyk.sarif
```

### 2. Staging Deployment Workflow

#### Staging CD Pipeline (.github/workflows/cd-staging.yml):
```yaml
name: Deploy to Staging

on:
  push:
    branches: [ develop ]
  workflow_dispatch:
    inputs:
      image_tag:
        description: 'Image tag to deploy'
        required: false
        default: 'latest'

env:
  AWS_REGION: us-west-2
  EKS_CLUSTER_NAME: staging-cluster
  NAMESPACE: staging

jobs:
  deploy-staging:
    name: Deploy to Staging Environment
    runs-on: ubuntu-latest
    environment: staging
    
    permissions:
      id-token: write
      contents: read
      
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: ${{ env.AWS_REGION }}
        
    - name: Setup kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.28.0'
        
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --region ${{ env.AWS_REGION }} --name ${{ env.EKS_CLUSTER_NAME }}
        
    - name: Setup Kustomize
      uses: imranismail/setup-kustomize@v2
      
    - name: Deploy to staging
      run: |
        cd k8s/overlays/staging
        
        # Update image tag
        IMAGE_TAG=${{ github.event.inputs.image_tag || 'latest' }}
        kustomize edit set image ${{ secrets.ECR_REGISTRY }}/${{ secrets.ECR_REPOSITORY }}:${IMAGE_TAG}
        
        # Apply manifests
        kustomize build . | kubectl apply -f -
        
        # Wait for rollout
        kubectl rollout status deployment/nodejs-sample-app -n ${{ env.NAMESPACE }} --timeout=300s
        
    - name: Run smoke tests
      run: |
        # Get service endpoint
        ENDPOINT=$(kubectl get ingress nodejs-sample-app -n ${{ env.NAMESPACE }} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        
        # Wait for endpoint to be ready
        for i in {1..30}; do
          if curl -f http://${ENDPOINT}/health/ready; then
            echo "Staging deployment successful!"
            break
          fi
          echo "Waiting for endpoint to be ready... ($i/30)"
          sleep 10
        done
        
    - name: Notify Slack
      uses: 8398a7/action-slack@v3
      if: always()
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        fields: repo,message,commit,author,action,eventName,ref,workflow
```

### 3. Production Deployment Workflow

#### Production CD Pipeline (.github/workflows/cd-production.yml):
```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      image_tag:
        description: 'Image tag to deploy'
        required: true
      environment:
        description: 'Target environment'
        required: true
        default: 'production'
        type: choice
        options:
        - production
        - production-blue
        - production-green

env:
  AWS_REGION: us-west-2
  EKS_CLUSTER_NAME: production-cluster
  NAMESPACE: production

jobs:
  pre-deployment-checks:
    name: Pre-deployment Checks
    runs-on: ubuntu-latest
    
    outputs:
      image_tag: ${{ steps.extract_tag.outputs.tag }}
      
    steps:
    - name: Extract tag
      id: extract_tag
      run: |
        if [[ "${{ github.event_name }}" == "push" ]]; then
          TAG=${GITHUB_REF#refs/tags/}
        else
          TAG=${{ github.event.inputs.image_tag }}
        fi
        echo "tag=${TAG}" >> $GITHUB_OUTPUT
        
    - name: Validate image exists
      run: |
        # Configure AWS credentials and check if image exists in ECR
        echo "Validating image: ${{ steps.extract_tag.outputs.tag }}"
        
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: pre-deployment-checks
    environment: 
      name: production
      url: https://nodejs-app.company.com
      
    permissions:
      id-token: write
      contents: read
      
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: ${{ env.AWS_REGION }}
        
    - name: Setup kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.28.0'
        
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --region ${{ env.AWS_REGION }} --name ${{ env.EKS_CLUSTER_NAME }}
        
    - name: Setup Kustomize
      uses: imranismail/setup-kustomize@v2
      
    - name: Create deployment backup
      run: |
        kubectl get deployment nodejs-sample-app -n ${{ env.NAMESPACE }} -o yaml > deployment-backup.yaml
        
    - name: Deploy to production
      run: |
        cd k8s/overlays/production
        
        # Update image tag
        IMAGE_TAG=${{ needs.pre-deployment-checks.outputs.image_tag }}
        kustomize edit set image ${{ secrets.ECR_REGISTRY }}/${{ secrets.ECR_REPOSITORY }}:${IMAGE_TAG}
        
        # Apply manifests with rolling update
        kustomize build . | kubectl apply -f -
        
        # Wait for rollout with timeout
        kubectl rollout status deployment/nodejs-sample-app -n ${{ env.NAMESPACE }} --timeout=600s
        
    - name: Run health checks
      run: |
        # Get service endpoint
        ENDPOINT=$(kubectl get ingress nodejs-sample-app -n ${{ env.NAMESPACE }} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        
        # Comprehensive health checks
        echo "Running health checks against: ${ENDPOINT}"
        
        # Check health endpoint
        curl -f http://${ENDPOINT}/health/ready || exit 1
        
        # Check API endpoints
        curl -f http://${ENDPOINT}/api/v1/users || exit 1
        
        # Performance test
        for i in {1..10}; do
          RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://${ENDPOINT}/)
          echo "Response time: ${RESPONSE_TIME}s"
          if (( $(echo "${RESPONSE_TIME} > 2.0" | bc -l) )); then
            echo "Response time too high: ${RESPONSE_TIME}s"
            exit 1
          fi
        done
        
        echo "All health checks passed!"
        
    - name: Update deployment status
      run: |
        # Tag the successful deployment
        git tag -a "deployed-$(date +%Y%m%d-%H%M%S)" -m "Production deployment: ${{ needs.pre-deployment-checks.outputs.image_tag }}"
        
    - name: Rollback on failure
      if: failure()
      run: |
        echo "Deployment failed, initiating rollback..."
        kubectl rollout undo deployment/nodejs-sample-app -n ${{ env.NAMESPACE }}
        kubectl rollout status deployment/nodejs-sample-app -n ${{ env.NAMESPACE }} --timeout=300s
        
    - name: Notify teams
      uses: 8398a7/action-slack@v3
      if: always()
      with:
        status: ${{ job.status }}
        channel: '#production-deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        fields: repo,message,commit,author,action,eventName,ref,workflow
        custom_payload: |
          {
            "text": "Production Deployment ${{ job.status }}",
            "attachments": [{
              "color": "${{ job.status }}" === "success" ? "good" : "danger",
              "fields": [{
                "title": "Image Tag",
                "value": "${{ needs.pre-deployment-checks.outputs.image_tag }}",
                "short": true
              }, {
                "title": "Environment",
                "value": "${{ env.NAMESPACE }}",
                "short": true
              }]
            }]
          }
```

### 4. Environment-Specific Overlays

#### Staging Overlay:
```yaml
# k8s/overlays/staging/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: staging

resources:
- ../../base

patchesStrategicMerge:
- deployment-patch.yaml
- ingress-patch.yaml

replicas:
- name: nodejs-sample-app
  count: 2

commonLabels:
  environment: staging

images:
- name: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/nodejs-sample-app
  newTag: latest
```

#### Staging Patches:
```yaml
# k8s/overlays/staging/deployment-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodejs-sample-app
spec:
  template:
    spec:
      containers:
      - name: nodejs-sample-app
        env:
        - name: NODE_ENV
          value: "staging"
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
# k8s/overlays/staging/ingress-patch.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nodejs-sample-app
spec:
  rules:
  - host: nodejs-app-staging.company.com
```

#### Production Overlay:
```yaml
# k8s/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: production

resources:
- ../../base
- hpa.yaml
- pdb.yaml

patchesStrategicMerge:
- deployment-patch.yaml
- ingress-patch.yaml

replicas:
- name: nodejs-sample-app
  count: 5

commonLabels:
  environment: production

images:
- name: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/nodejs-sample-app
  newTag: v1.0.0
```

#### Production Resources:
```yaml
# k8s/overlays/production/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nodejs-sample-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nodejs-sample-app
  minReplicas: 3
  maxReplicas: 20
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
---
# k8s/overlays/production/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: nodejs-sample-app-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: nodejs-sample-app
```

---

## Security Best Practices

### 1. OIDC Configuration (Keyless Authentication)

#### Enhanced OIDC Trust Policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:YOUR_ORG/nodejs-sample-app:ref:refs/heads/main",
            "repo:YOUR_ORG/nodejs-sample-app:ref:refs/heads/develop",
            "repo:YOUR_ORG/nodejs-sample-app:ref:refs/tags/*"
          ]
        },
        "StringEquals": {
          "token.actions.githubusercontent.com:repository": "YOUR_ORG/nodejs-sample-app"
        }
      }
    }
  ]
}
```

### 2. Secrets Management

#### Using AWS Systems Manager Parameter Store:
```yaml
# In workflow file
- name: Get secrets from Parameter Store
  run: |
    DB_PASSWORD=$(aws ssm get-parameter --name "/github-actions/db-password" --with-decryption --query 'Parameter.Value' --output text)
    echo "::add-mask::$DB_PASSWORD"
    echo "DB_PASSWORD=$DB_PASSWORD" >> $GITHUB_ENV
```

#### GitHub Environment Secrets:
```yaml
# Environment-specific secrets configuration
environments:
  staging:
    secrets:
      - DATABASE_URL
      - API_KEY
      - SLACK_WEBHOOK
  production:
    secrets:
      - DATABASE_URL
      - API_KEY
      - SLACK_WEBHOOK
      - MONITORING_TOKEN
    protection_rules:
      - type: required_reviewers
        required_reviewers: ["devops-team"]
      - type: wait_timer
        wait_timer: 5
```

### 3. Container Security

#### Security Scanning in CI:
```yaml
- name: Run comprehensive security scan
  run: |
    # Scan for vulnerabilities
    trivy image --exit-code 1 --severity HIGH,CRITICAL ${{ env.IMAGE_URI }}
    
    # Scan for secrets
    trufflehog git file://. --only-verified
    
    # Scan for misconfigurations
    checkov -f Dockerfile --framework dockerfile
```

### 4. Network Security

#### Network Policies for Kubernetes:
```yaml
# k8s/base/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: nodejs-sample-app-netpol
spec:
  podSelector:
    matchLabels:
      app: nodejs-sample-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 3000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

---

## Advanced Workflows

### 1. Matrix Builds for Multi-Environment

#### Multi-Environment Deployment:
```yaml
name: Multi-Environment Deployment

on:
  workflow_dispatch:
    inputs:
      environments:
        description: 'Environments to deploy (comma-separated)'
        required: true
        default: 'staging,production'
      image_tag:
        description: 'Image tag to deploy'
        required: true

jobs:
  deploy:
    name: Deploy to ${{ matrix.environment }}
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        environment: ${{ fromJson(github.event.inputs.environments) }}
      fail-fast: false
      
    environment: ${{ matrix.environment }}
    
    steps:
    - name: Deploy to ${{ matrix.environment }}
      run: |
        echo "Deploying ${{ github.event.inputs.image_tag }} to ${{ matrix.environment }}"
        # Deployment logic here
```

### 2. Blue-Green Deployment

#### Blue-Green Deployment Workflow:
```yaml
name: Blue-Green Deployment

on:
  workflow_dispatch:
    inputs:
      target_slot:
        description: 'Target deployment slot'
        required: true
        type: choice
        options:
        - blue
        - green

jobs:
  deploy-blue-green:
    name: Blue-Green Deployment
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to ${{ github.event.inputs.target_slot }} slot
      run: |
        CURRENT_SLOT=$(kubectl get service nodejs-sample-app-active -o jsonpath='{.spec.selector.slot}')
        TARGET_SLOT=${{ github.event.inputs.target_slot }}
        
        echo "Current active slot: $CURRENT_SLOT"
        echo "Deploying to slot: $TARGET_SLOT"
        
        # Deploy to target slot
        kubectl set image deployment/nodejs-sample-app-${TARGET_SLOT} \
          nodejs-sample-app=${{ env.IMAGE_URI }} \
          -n production
          
        # Wait for rollout
        kubectl rollout status deployment/nodejs-sample-app-${TARGET_SLOT} -n production
        
        # Run health checks
        kubectl run health-check --rm -i --restart=Never \
          --image=curlimages/curl -- \
          curl -f http://nodejs-sample-app-${TARGET_SLOT}/health/ready
        
    - name: Switch traffic
      if: success()
      run: |
        TARGET_SLOT=${{ github.event.inputs.target_slot }}
        
        # Update active service to point to new slot
        kubectl patch service nodejs-sample-app-active \
          -p '{"spec":{"selector":{"slot":"'${TARGET_SLOT}'"}}}' \
          -n production
          
        echo "Traffic switched to $TARGET_SLOT slot"
```

### 3. Canary Deployment with Flagger

#### Canary Deployment Configuration:
```yaml
# k8s/overlays/production/canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: nodejs-sample-app
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nodejs-sample-app
  progressDeadlineSeconds: 60
  service:
    port: 80
    targetPort: 3000
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 30s
    webhooks:
    - name: load-test
      url: http://flagger-loadtester.test/
      metadata:
        cmd: "hey -z 1m -q 10 -c 2 http://nodejs-sample-app-canary.production/"
```

### 4. Automated Rollback

#### Rollback Workflow:
```yaml
name: Automated Rollback

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to rollback'
        required: true
        type: choice
        options:
        - staging
        - production
      revision:
        description: 'Revision to rollback to (optional)'
        required: false

jobs:
  rollback:
    name: Rollback Deployment
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    
    steps:
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: ${{ secrets.AWS_REGION }}
        
    - name: Setup kubectl
      uses: azure/setup-kubectl@v3
      
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --region ${{ secrets.AWS_REGION }} --name ${{ secrets.EKS_CLUSTER_NAME }}
        
    - name: Perform rollback
      run: |
        NAMESPACE=${{ github.event.inputs.environment }}
        
        if [ -n "${{ github.event.inputs.revision }}" ]; then
          # Rollback to specific revision
          kubectl rollout undo deployment/nodejs-sample-app \
            --to-revision=${{ github.event.inputs.revision }} \
            -n $NAMESPACE
        else
          # Rollback to previous revision
          kubectl rollout undo deployment/nodejs-sample-app -n $NAMESPACE
        fi
        
        # Wait for rollback to complete
        kubectl rollout status deployment/nodejs-sample-app -n $NAMESPACE --timeout=300s
        
    - name: Verify rollback
      run: |
        NAMESPACE=${{ github.event.inputs.environment }}
        
        # Get current revision
        CURRENT_REVISION=$(kubectl get deployment nodejs-sample-app -n $NAMESPACE -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
        echo "Current revision after rollback: $CURRENT_REVISION"
        
        # Run health checks
        kubectl run rollback-health-check --rm -i --restart=Never \
          --image=curlimages/curl -- \
          curl -f http://nodejs-sample-app.$NAMESPACE/health/ready
          
        echo "Rollback completed successfully"
```

---

## Monitoring & Notifications

### 1. Deployment Monitoring

#### Deployment Status Monitoring:
```yaml
name: Monitor Deployment Status

on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
  workflow_dispatch:

jobs:
  monitor:
    name: Monitor Application Health
    runs-on: ubuntu-latest
    
    steps:
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: ${{ secrets.AWS_REGION }}
        
    - name: Check application health
      run: |
        # Check staging
        STAGING_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://nodejs-app-staging.company.com/health/ready || echo "000")
        
        # Check production
        PROD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://nodejs-app.company.com/health/ready || echo "000")
        
        echo "Staging status: $STAGING_STATUS"
        echo "Production status: $PROD_STATUS"
        
        # Alert if any environment is down
        if [ "$STAGING_STATUS" != "200" ] || [ "$PROD_STATUS" != "200" ]; then
          echo "::error::Application health check failed"
          echo "HEALTH_CHECK_FAILED=true" >> $GITHUB_ENV
        fi
        
    - name: Send alert
      if: env.HEALTH_CHECK_FAILED == 'true'
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        channel: '#alerts'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        fields: repo,message,commit,author,action,eventName,ref,workflow
        custom_payload: |
          {
            "text": "🚨 Application Health Check Failed",
            "attachments": [{
              "color": "danger",
              "fields": [{
                "title": "Alert Type",
                "value": "Health Check Failure",
                "short": true
              }, {
                "title": "Time",
                "value": "${{ github.run_started_at }}",
                "short": true
              }]
            }]
          }
```

### 2. Performance Monitoring

#### Performance Testing Workflow:
```yaml
name: Performance Testing

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:
    inputs:
      target_url:
        description: 'Target URL for performance testing'
        required: true
        default: 'https://nodejs-app.company.com'
      duration:
        description: 'Test duration'
        required: true
        default: '5m'

jobs:
  performance-test:
    name: Run Performance Tests
    runs-on: ubuntu-latest
    
    steps:
    - name: Install k6
      run: |
        sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
        echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
        sudo apt-get update
        sudo apt-get install k6
        
    - name: Create performance test script
      run: |
        cat > performance-test.js << 'EOF'
        import http from 'k6/http';
        import { check, sleep } from 'k6';
        
        export let options = {
          stages: [
            { duration: '1m', target: 10 },
            { duration: '3m', target: 50 },
            { duration: '1m', target: 0 },
          ],
          thresholds: {
            http_req_duration: ['p(95)<500'],
            http_req_failed: ['rate<0.1'],
          },
        };
        
        export default function() {
          let response = http.get('${{ github.event.inputs.target_url || 'https://nodejs-app.company.com' }}');
          check(response, {
            'status is 200': (r) => r.status === 200,
            'response time < 500ms': (r) => r.timings.duration < 500,
          });
          sleep(1);
        }
        EOF
        
    - name: Run performance test
      run: |
        k6 run --duration ${{ github.event.inputs.duration || '5m' }} performance-test.js
        
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: |
          *.json
          *.html
```

### 3. Slack Integration

#### Advanced Slack Notifications:
```yaml
- name: Deployment notification
  uses: 8398a7/action-slack@v3
  if: always()
  with:
    status: ${{ job.status }}
    channel: '#deployments'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
    fields: repo,message,commit,author,action,eventName,ref,workflow,job,took
    custom_payload: |
      {
        "username": "GitHub Actions",
        "icon_emoji": ":github:",
        "text": "${{ job.status == 'success' && '✅' || '❌' }} Deployment ${{ job.status }}",
        "attachments": [{
          "color": "${{ job.status == 'success' && 'good' || 'danger' }}",
          "fields": [
            {
              "title": "Repository",
              "value": "${{ github.repository }}",
              "short": true
            },
            {
              "title": "Environment",
              "value": "${{ github.event.inputs.environment || 'staging' }}",
              "short": true
            },
            {
              "title": "Image Tag",
              "value": "${{ github.sha }}",
              "short": true
            },
            {
              "title": "Triggered By",
              "value": "${{ github.actor }}",
              "short": true
            },
            {
              "title": "Workflow",
              "value": "${{ github.workflow }}",
              "short": false
            }
          ],
          "actions": [
            {
              "type": "button",
              "text": "View Logs",
              "url": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
            },
            {
              "type": "button",
              "text": "View App",
              "url": "https://nodejs-app.company.com"
            }
          ]
        }]
      }
```

---

## Troubleshooting

### 1. Common Issues and Solutions

#### Debug Workflow Issues:
```yaml
- name: Debug information
  if: failure()
  run: |
    echo "=== Debug Information ==="
    echo "GitHub Context:"
    echo "  Event: ${{ github.event_name }}"
    echo "  Ref: ${{ github.ref }}"
    echo "  SHA: ${{ github.sha }}"
    echo "  Actor: ${{ github.actor }}"
    
    echo "Environment Variables:"
    env | sort
    
    echo "AWS CLI Version:"
    aws --version
    
    echo "kubectl Version:"
    kubectl version --client
    
    echo "Current AWS Identity:"
    aws sts get-caller-identity
    
    echo "EKS Cluster Info:"
    aws eks describe-cluster --name ${{ secrets.EKS_CLUSTER_NAME }} --region ${{ secrets.AWS_REGION }}
```

#### ECR Authentication Issues:
```yaml
- name: Troubleshoot ECR login
  if: failure()
  run: |
    echo "=== ECR Troubleshooting ==="
    
    # Check ECR repository exists
    aws ecr describe-repositories --repository-names ${{ secrets.ECR_REPOSITORY }} --region ${{ secrets.AWS_REGION }} || echo "Repository not found"
    
    # Check ECR permissions
    aws ecr get-authorization-token --region ${{ secrets.AWS_REGION }} || echo "Authorization failed"
    
    # Test docker login
    aws ecr get-login-password --region ${{ secrets.AWS_REGION }} | docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }} || echo "Docker login failed"
```

### 2. Workflow Debugging

#### Enhanced Logging:
```yaml
- name: Enable debug logging
  run: |
    echo "::debug::Starting deployment process"
    echo "::notice::Deploying image ${{ env.IMAGE_TAG }}"
    echo "::warning::This is a production deployment"
    
    # Set debug mode
    echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
    echo "ACTIONS_RUNNER_DEBUG=true" >> $GITHUB_ENV
```

#### Conditional Debugging:
```yaml
- name: Debug on failure
  if: failure()
  run: |
    # Capture logs
    kubectl logs -l app=nodejs-sample-app -n ${{ env.NAMESPACE }} --tail=100
    
    # Describe resources
    kubectl describe deployment nodejs-sample-app -n ${{ env.NAMESPACE }}
    kubectl describe pods -l app=nodejs-sample-app -n ${{ env.NAMESPACE }}
    
    # Check events
    kubectl get events -n ${{ env.NAMESPACE }} --sort-by='.lastTimestamp'
```

### 3. Performance Optimization

#### Workflow Optimization:
```yaml
- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
      
- name: Cache Docker layers
  uses: actions/cache@v3
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-buildx-
```

#### Parallel Job Execution:
```yaml
jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-type: [unit, integration, e2e]
    steps:
    - name: Run ${{ matrix.test-type }} tests
      run: npm run test:${{ matrix.test-type }}
      
  build:
    name: Build Image
    runs-on: ubuntu-latest
    needs: test
    # Build only runs after all tests pass
```

This comprehensive guide provides everything needed to implement a complete CI/CD pipeline with GitHub Actions and AWS, using a real-world Node.js application as an example. The guide covers security best practices, advanced deployment strategies, monitoring, and troubleshooting procedures.