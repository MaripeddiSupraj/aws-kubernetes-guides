# Karpenter Complete Guide - From Scratch to Production

## Table of Contents
1. [What is Karpenter?](#what-is-karpenter)
2. [Why Use Karpenter?](#why-use-karpenter)
3. [Karpenter vs Traditional Auto Scaling](#karpenter-vs-traditional-auto-scaling)
4. [Prerequisites & Setup](#prerequisites--setup)
5. [Installation Guide](#installation-guide)
6. [Core Concepts](#core-concepts)
7. [Configuration Examples](#configuration-examples)
8. [Real-World Implementation](#real-world-implementation)
9. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
10. [Best Practices](#best-practices)

---

## What is Karpenter?

### Overview
Karpenter is an **open-source Kubernetes cluster autoscaler** built for AWS. It automatically provisions right-sized compute resources in response to changing application load.

### Key Characteristics
```
┌─────────────────────────────────────────────────────────────┐
│                    Karpenter Architecture                   │
├─────────────────────────────────────────────────────────────┤
│ Kubernetes Pods     │ Karpenter Controller │ AWS EC2        │
│ - Pending Pods      │ - Node Provisioning  │ - Instance     │
│ - Resource Requests │ - Scheduling Logic   │ - Launch       │
│ - Node Affinity     │ - Cost Optimization  │ - Termination  │
└─────────────────────────────────────────────────────────────┘
```

### How It Works
1. **Watches** for pods that can't be scheduled
2. **Evaluates** scheduling requirements and constraints
3. **Provisions** optimal EC2 instances directly (no Auto Scaling Groups)
4. **Terminates** underutilized nodes automatically
5. **Optimizes** for cost and performance continuously

---

## Why Use Karpenter?

### 1. Speed & Efficiency
- **Fast Scaling**: Provisions nodes in ~30 seconds vs 2-3 minutes with ASGs
- **Direct EC2 API**: No Auto Scaling Group overhead
- **Immediate Response**: Reacts to pod scheduling failures instantly

### 2. Cost Optimization
- **Right-Sizing**: Selects optimal instance types automatically
- **Spot Integration**: Seamless spot instance usage
- **Consolidation**: Automatically moves workloads to fewer, larger nodes
- **Waste Reduction**: Eliminates over-provisioning

### 3. Flexibility
- **Instance Diversity**: Uses 100+ instance types automatically
- **Mixed Workloads**: Handles different resource requirements efficiently
- **Custom Requirements**: Supports complex scheduling constraints

### 4. Operational Simplicity
- **No ASG Management**: Eliminates Auto Scaling Group complexity
- **Automatic Updates**: Handles node lifecycle automatically
- **Kubernetes Native**: Configuration through Kubernetes resources

---

## Karpenter vs Traditional Auto Scaling

### Comparison Matrix
| Feature | Karpenter | Cluster Autoscaler + ASG |
|---------|-----------|--------------------------|
| **Scaling Speed** | 30 seconds | 2-3 minutes |
| **Instance Selection** | 100+ types automatically | Pre-defined in ASG |
| **Cost Optimization** | Automatic right-sizing | Manual configuration |
| **Spot Integration** | Native, seamless | Complex setup |
| **Node Diversity** | High (multiple types) | Low (single type per ASG) |
| **Configuration** | Simple (1-2 resources) | Complex (multiple ASGs) |
| **Operational Overhead** | Low | High |
| **Bin Packing** | Excellent | Good |

### Traditional Auto Scaling Problems
```yaml
# Traditional approach - Multiple ASGs needed
ASG-1: m5.large   (General workloads)
ASG-2: c5.xlarge  (CPU intensive)
ASG-3: r5.2xlarge (Memory intensive)
ASG-4: t3.medium  (Burstable)

# Problems:
# - Pre-provisioning required
# - Poor bin packing
# - Slow scaling
# - Complex management
```

### Karpenter Solution
```yaml
# Karpenter approach - Single NodePool
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: default
spec:
  # Handles ALL workload types automatically
  template:
    spec:
      requirements:
      - key: kubernetes.io/arch
        operator: In
        values: ["amd64"]
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot", "on-demand"]
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: default
```

---

## Prerequisites & Setup

### 1. EKS Cluster Requirements
- **EKS Version**: 1.23 or later
- **VPC**: Properly configured with subnets
- **IAM**: Correct permissions for Karpenter
- **Security Groups**: Allow node communication

### 2. Required AWS Permissions

#### Karpenter Controller IAM Policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowScopedEC2InstanceAccessActions",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:CreateFleet"
      ],
      "Resource": [
        "arn:aws:ec2:*::image/*",
        "arn:aws:ec2:*::snapshot/*",
        "arn:aws:ec2:*:*:security-group/*",
        "arn:aws:ec2:*:*:subnet/*"
      ]
    },
    {
      "Sid": "AllowScopedEC2LaunchTemplateAccessActions",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateLaunchTemplate",
        "ec2:CreateTags"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2",
          "ec2:CreateAction": [
            "RunInstances",
            "CreateFleet",
            "CreateLaunchTemplate"
          ]
        }
      }
    },
    {
      "Sid": "AllowScopedResourceCreationTagging",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateTags"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:fleet/*",
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ec2:*:*:volume/*",
        "arn:aws:ec2:*:*:network-interface/*",
        "arn:aws:ec2:*:*:launch-template/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2",
          "ec2:CreateAction": [
            "RunInstances",
            "CreateFleet",
            "CreateLaunchTemplate"
          ]
        }
      }
    },
    {
      "Sid": "AllowScopedDeletion",
      "Effect": "Allow",
      "Action": [
        "ec2:TerminateInstances",
        "ec2:DeleteLaunchTemplate"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2"
        }
      }
    },
    {
      "Sid": "AllowRegionalReadActions",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeImages",
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceTypeOfferings",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSpotPriceHistory",
        "ec2:DescribeSubnets"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2"
        }
      }
    },
    {
      "Sid": "AllowSSMReadActions",
      "Effect": "Allow",
      "Action": "ssm:GetParameter",
      "Resource": "arn:aws:ssm:*:*:parameter/aws/service/*"
    },
    {
      "Sid": "AllowPricingReadActions",
      "Effect": "Allow",
      "Action": "pricing:GetProducts",
      "Resource": "*"
    },
    {
      "Sid": "AllowInterruptionQueueActions",
      "Effect": "Allow",
      "Action": [
        "sqs:DeleteMessage",
        "sqs:GetQueueUrl",
        "sqs:ReceiveMessage"
      ],
      "Resource": "arn:aws:sqs:*:*:Karpenter-*"
    },
    {
      "Sid": "AllowPassingInstanceRole",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::*:role/KarpenterNodeInstanceProfile-*"
    },
    {
      "Sid": "AllowScopedInstanceProfileCreationActions",
      "Effect": "Allow",
      "Action": [
        "iam:CreateInstanceProfile"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2"
        }
      }
    },
    {
      "Sid": "AllowScopedInstanceProfileTagActions",
      "Effect": "Allow",
      "Action": [
        "iam:TagInstanceProfile"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2"
        }
      }
    },
    {
      "Sid": "AllowScopedInstanceProfileActions",
      "Effect": "Allow",
      "Action": [
        "iam:AddRoleToInstanceProfile",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:DeleteInstanceProfile"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2"
        }
      }
    }
  ]
}
```

### 3. Node Instance Profile

#### Node IAM Role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Attach AWS Managed Policies:
- `AmazonEKSWorkerNodePolicy`
- `AmazonEKS_CNI_Policy`
- `AmazonEC2ContainerRegistryReadOnly`

---

## Installation Guide

### 1. Install Karpenter using Helm

#### Step 1: Add Helm Repository
```bash
helm repo add karpenter oci://public.ecr.aws/karpenter
helm repo update
```

#### Step 2: Create Namespace
```bash
kubectl create namespace karpenter
```

#### Step 3: Install Karpenter
```bash
helm install karpenter karpenter/karpenter \
  --version "0.37.0" \
  --namespace "karpenter" \
  --create-namespace \
  --set "settings.clusterName=my-cluster" \
  --set "settings.interruptionQueue=Karpenter-my-cluster" \
  --set "controller.resources.requests.cpu=1" \
  --set "controller.resources.requests.memory=1Gi" \
  --set "controller.resources.limits.cpu=1" \
  --set "controller.resources.limits.memory=1Gi" \
  --wait
```

### 2. Alternative: Install using kubectl

#### Download and Apply Manifests:
```bash
# Download Karpenter manifests
kubectl apply -f https://raw.githubusercontent.com/aws/karpenter-provider-aws/v0.37.0/pkg/apis/crds/karpenter.sh_nodeclaims.yaml
kubectl apply -f https://raw.githubusercontent.com/aws/karpenter-provider-aws/v0.37.0/pkg/apis/crds/karpenter.sh_nodepools.yaml
kubectl apply -f https://raw.githubusercontent.com/aws/karpenter-provider-aws/v0.37.0/pkg/apis/crds/karpenter.k8s.aws_ec2nodeclasses.yaml

# Apply Karpenter controller
kubectl apply -f https://raw.githubusercontent.com/aws/karpenter-provider-aws/v0.37.0/pkg/apis/v1beta1/karpenter.yaml
```

### 3. Verify Installation

#### Check Karpenter Pods:
```bash
kubectl get pods -n karpenter
kubectl logs -f -n karpenter -l app.kubernetes.io/name=karpenter
```

#### Verify CRDs:
```bash
kubectl get crd | grep karpenter
```

Expected output:
```
ec2nodeclasses.karpenter.k8s.aws
nodeclaims.karpenter.sh
nodepools.karpenter.sh
```

---

## Core Concepts

### 1. NodePool
**Purpose**: Defines the template and constraints for provisioning nodes

```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: default
spec:
  # Template for nodes
  template:
    metadata:
      labels:
        node-type: "karpenter-managed"
      annotations:
        example.com/owner: "platform-team"
    spec:
      # Node requirements and constraints
      requirements:
      - key: kubernetes.io/arch
        operator: In
        values: ["amd64"]
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot", "on-demand"]
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["m5.large", "m5.xlarge", "c5.large", "c5.xlarge"]
      
      # Node properties
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: default
      
      # Taints (optional)
      taints:
      - key: example.com/special-workload
        value: "true"
        effect: NoSchedule
  
  # Scaling limits
  limits:
    cpu: 1000
    memory: 1000Gi
  
  # Disruption settings
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 30s
    expireAfter: 30m
```

### 2. EC2NodeClass
**Purpose**: Defines AWS-specific configuration for EC2 instances

```yaml
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: default
spec:
  # AMI selection
  amiFamily: AL2 # Amazon Linux 2
  
  # Subnet selection
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  
  # Security group selection
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  
  # Instance profile
  role: "KarpenterNodeInstanceProfile-my-cluster"
  
  # User data (optional)
  userData: |
    #!/bin/bash
    /etc/eks/bootstrap.sh my-cluster
    echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
    sysctl -p
  
  # Block device mappings
  blockDeviceMappings:
  - deviceName: /dev/xvda
    ebs:
      volumeSize: 100Gi
      volumeType: gp3
      iops: 3000
      deleteOnTermination: true
      encrypted: true
  
  # Instance metadata options
  metadataOptions:
    httpEndpoint: enabled
    httpProtocolIPv6: disabled
    httpPutResponseHopLimit: 2
    httpTokens: required
  
  # Tags
  tags:
    Name: "Karpenter-my-cluster"
    Environment: "production"
    ManagedBy: "karpenter"
```

### 3. Key Concepts Explained

#### Requirements and Constraints:
```yaml
# Instance type flexibility
- key: node.kubernetes.io/instance-type
  operator: In
  values: ["m5.large", "m5.xlarge", "m5.2xlarge"]

# Capacity type (spot vs on-demand)
- key: karpenter.sh/capacity-type
  operator: In
  values: ["spot", "on-demand"]

# Architecture
- key: kubernetes.io/arch
  operator: In
  values: ["amd64"]

# Availability zones
- key: topology.kubernetes.io/zone
  operator: In
  values: ["us-west-2a", "us-west-2b", "us-west-2c"]
```

---

## Configuration Examples

### 1. Basic Configuration

#### Simple NodePool for General Workloads:
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: general-purpose
spec:
  template:
    spec:
      requirements:
      - key: kubernetes.io/arch
        operator: In
        values: ["amd64"]
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot", "on-demand"]
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: default
  limits:
    cpu: 1000
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 30s

---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: default
spec:
  amiFamily: AL2
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  role: "KarpenterNodeInstanceProfile-my-cluster"
```

### 2. Spot-Only Configuration

#### Cost-Optimized Spot Instances:
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: spot-only
spec:
  template:
    metadata:
      labels:
        node-type: "spot"
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot"]  # Only spot instances
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["m5.large", "m5.xlarge", "m4.large", "m4.xlarge", "c5.large", "c5.xlarge"]
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: spot-optimized
      taints:
      - key: spot-instance
        value: "true"
        effect: NoSchedule
  limits:
    cpu: 500
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 10s

---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: spot-optimized
spec:
  amiFamily: AL2
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  role: "KarpenterNodeInstanceProfile-my-cluster"
  userData: |
    #!/bin/bash
    /etc/eks/bootstrap.sh my-cluster
    # Spot instance optimizations
    echo "vm.swappiness=1" >> /etc/sysctl.conf
  tags:
    NodeType: "spot"
    CostOptimized: "true"
```

### 3. GPU Workloads Configuration

#### GPU-Enabled Nodes:
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: gpu-workloads
spec:
  template:
    metadata:
      labels:
        node-type: "gpu"
        workload-type: "ml"
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["on-demand"]  # GPU instances typically on-demand
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["p3.2xlarge", "p3.8xlarge", "g4dn.xlarge", "g4dn.2xlarge"]
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: gpu-optimized
      taints:
      - key: nvidia.com/gpu
        value: "true"
        effect: NoSchedule
  limits:
    cpu: 1000
    nvidia.com/gpu: 100
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 60s

---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: gpu-optimized
spec:
  amiFamily: AL2
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  role: "KarpenterNodeInstanceProfile-my-cluster"
  userData: |
    #!/bin/bash
    /etc/eks/bootstrap.sh my-cluster
    # Install NVIDIA drivers
    yum install -y nvidia-driver-latest-dkms
    # Install nvidia-docker2
    yum install -y nvidia-docker2
    systemctl restart docker
  blockDeviceMappings:
  - deviceName: /dev/xvda
    ebs:
      volumeSize: 200Gi  # Larger storage for ML workloads
      volumeType: gp3
      iops: 4000
      deleteOnTermination: true
  tags:
    NodeType: "gpu"
    Workload: "machine-learning"
```

### 4. Memory-Optimized Configuration

#### High-Memory Workloads:
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: memory-optimized
spec:
  template:
    metadata:
      labels:
        node-type: "memory-optimized"
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["on-demand", "spot"]
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["r5.large", "r5.xlarge", "r5.2xlarge", "r5.4xlarge", "r6i.large", "r6i.xlarge"]
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: memory-optimized
      taints:
      - key: workload-type
        value: "memory-intensive"
        effect: NoSchedule
  limits:
    memory: 2000Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 60s

---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: memory-optimized
spec:
  amiFamily: AL2
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  role: "KarpenterNodeInstanceProfile-my-cluster"
  userData: |
    #!/bin/bash
    /etc/eks/bootstrap.sh my-cluster
    # Memory optimizations
    echo "vm.swappiness=1" >> /etc/sysctl.conf
    echo "vm.overcommit_memory=1" >> /etc/sysctl.conf
    sysctl -p
  tags:
    NodeType: "memory-optimized"
```

---

## Real-World Implementation

### 1. E-commerce Platform Example

#### Architecture Overview:
```
┌─────────────────────────────────────────────────────────────┐
│                E-commerce Platform on Karpenter            │
├─────────────────────────────────────────────────────────────┤
│ Frontend (React)    │ API Gateway         │ Microservices   │
│ - Spot instances    │ - On-demand         │ - Mixed capacity │
│ - Burstable (t3)    │ - Compute (c5)      │ - Various sizes  │
├─────────────────────┼─────────────────────┼─────────────────┤
│ Background Jobs     │ Database            │ Cache Layer     │
│ - Spot only         │ - Memory optimized  │ - Memory opt.   │
│ - Interruptible     │ - On-demand only    │ - Spot capable  │
└─────────────────────────────────────────────────────────────┘
```

#### Frontend NodePool:
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: frontend
spec:
  template:
    metadata:
      labels:
        workload: "frontend"
        cost-optimization: "high"
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot"]  # Cost-optimized for frontend
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["t3.medium", "t3.large", "t3.xlarge"]  # Burstable for web traffic
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: frontend-nodes
      taints:
      - key: workload
        value: "frontend"
        effect: NoSchedule
  limits:
    cpu: 200
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 15s  # Quick consolidation for cost savings

---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: frontend-nodes
spec:
  amiFamily: AL2
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "ecommerce-cluster"
      tier: "public"  # Public subnets for frontend
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "ecommerce-cluster"
  role: "KarpenterNodeInstanceProfile-ecommerce"
  userData: |
    #!/bin/bash
    /etc/eks/bootstrap.sh ecommerce-cluster
    # Frontend optimizations
    echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
    sysctl -p
  tags:
    Workload: "frontend"
    Environment: "production"
```

#### Backend Services NodePool:
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: backend-services
spec:
  template:
    metadata:
      labels:
        workload: "backend"
        reliability: "high"
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["on-demand", "spot"]  # Mixed for reliability
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["m5.large", "m5.xlarge", "c5.large", "c5.xlarge"]
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: backend-nodes
      taints:
      - key: workload
        value: "backend"
        effect: NoSchedule
  limits:
    cpu: 500
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 30s

---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: backend-nodes
spec:
  amiFamily: AL2
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "ecommerce-cluster"
      tier: "private"  # Private subnets for backend
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "ecommerce-cluster"
  role: "KarpenterNodeInstanceProfile-ecommerce"
  blockDeviceMappings:
  - deviceName: /dev/xvda
    ebs:
      volumeSize: 50Gi
      volumeType: gp3
      iops: 3000
  tags:
    Workload: "backend"
    Environment: "production"
```

#### Database NodePool:
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: database
spec:
  template:
    metadata:
      labels:
        workload: "database"
        reliability: "critical"
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["on-demand"]  # On-demand only for databases
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["r5.xlarge", "r5.2xlarge", "r5.4xlarge"]  # Memory optimized
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: database-nodes
      taints:
      - key: workload
        value: "database"
        effect: NoSchedule
  limits:
    cpu: 100
    memory: 500Gi
  disruption:
    consolidationPolicy: WhenEmpty  # Conservative for databases
    consolidateAfter: 300s

---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: database-nodes
spec:
  amiFamily: AL2
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "ecommerce-cluster"
      tier: "private"
      database: "allowed"
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "ecommerce-cluster"
      database: "true"
  role: "KarpenterNodeInstanceProfile-ecommerce"
  userData: |
    #!/bin/bash
    /etc/eks/bootstrap.sh ecommerce-cluster
    # Database optimizations
    echo "vm.swappiness=1" >> /etc/sysctl.conf
    echo "vm.dirty_ratio=15" >> /etc/sysctl.conf
    echo "vm.dirty_background_ratio=5" >> /etc/sysctl.conf
    sysctl -p
  blockDeviceMappings:
  - deviceName: /dev/xvda
    ebs:
      volumeSize: 100Gi
      volumeType: gp3
      iops: 4000
      encrypted: true
  tags:
    Workload: "database"
    Environment: "production"
    Backup: "required"
```

### 2. Application Deployments

#### Frontend Application:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 5
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      nodeSelector:
        workload: "frontend"
      tolerations:
      - key: workload
        value: "frontend"
        effect: NoSchedule
      - key: spot-instance
        operator: Exists
        effect: NoSchedule
      containers:
      - name: frontend
        image: ecommerce/frontend:v2.1.0
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        ports:
        - containerPort: 80
```

#### Backend Service:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      nodeSelector:
        workload: "backend"
      tolerations:
      - key: workload
        value: "backend"
        effect: NoSchedule
      containers:
      - name: user-service
        image: ecommerce/user-service:v1.3.0
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
```

#### Database StatefulSet:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
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
      nodeSelector:
        workload: "database"
      tolerations:
      - key: workload
        value: "database"
        effect: NoSchedule
      containers:
      - name: postgresql
        image: postgres:14
        resources:
          requests:
            cpu: 1000m
            memory: 4Gi
          limits:
            cpu: 2000m
            memory: 8Gi
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3
      resources:
        requests:
          storage: 100Gi
```

---

## Monitoring & Troubleshooting

### 1. Monitoring Karpenter

#### Check Karpenter Status:
```bash
# Check Karpenter controller logs
kubectl logs -f -n karpenter -l app.kubernetes.io/name=karpenter

# Check NodePools
kubectl get nodepools

# Check NodeClaims (individual nodes)
kubectl get nodeclaims

# Check EC2NodeClasses
kubectl get ec2nodeclasses
```

#### Karpenter Metrics:
```bash
# Port forward to access metrics
kubectl port-forward -n karpenter svc/karpenter 8080:8080

# Access metrics
curl http://localhost:8080/metrics | grep karpenter
```

### 2. Common Issues and Solutions

#### Issue: Pods Stuck in Pending
```bash
# Check pod events
kubectl describe pod <pod-name>

# Check NodePool limits
kubectl describe nodepool <nodepool-name>

# Check if requirements can be satisfied
kubectl get nodeclaims -o wide
```

#### Issue: Nodes Not Scaling Down
```bash
# Check disruption settings
kubectl get nodepool <nodepool-name> -o yaml | grep -A 10 disruption

# Check node utilization
kubectl top nodes

# Force node consolidation (if needed)
kubectl annotate node <node-name> karpenter.sh/do-not-evict-
```

#### Issue: Wrong Instance Types Selected
```bash
# Check NodePool requirements
kubectl get nodepool <nodepool-name> -o yaml | grep -A 20 requirements

# Check available instance types
aws ec2 describe-instance-type-offerings --location-type availability-zone --filters Name=location,Values=us-west-2a
```

### 3. Debugging Commands

#### Comprehensive Debug Script:
```bash
#!/bin/bash
# karpenter-debug.sh

echo "=== Karpenter Debug Information ==="

echo "1. Karpenter Controller Status:"
kubectl get pods -n karpenter -o wide

echo -e "\n2. NodePools:"
kubectl get nodepools -o wide

echo -e "\n3. NodeClaims:"
kubectl get nodeclaims -o wide

echo -e "\n4. EC2NodeClasses:"
kubectl get ec2nodeclasses -o wide

echo -e "\n5. Pending Pods:"
kubectl get pods --all-namespaces --field-selector=status.phase=Pending

echo -e "\n6. Node Utilization:"
kubectl top nodes 2>/dev/null || echo "Metrics server not available"

echo -e "\n7. Recent Karpenter Events:"
kubectl get events -n karpenter --sort-by='.lastTimestamp' | tail -20

echo -e "\n8. Karpenter Controller Logs (last 50 lines):"
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter --tail=50

echo -e "\n9. AWS Instance Information:"
aws ec2 describe-instances --filters "Name=tag:karpenter.sh/cluster,Values=my-cluster" \
  --query 'Reservations[].Instances[].{InstanceId:InstanceId,InstanceType:InstanceType,State:State.Name,LaunchTime:LaunchTime}' \
  --output table
```

---

## Best Practices

### 1. NodePool Design

#### Multiple NodePools Strategy:
```yaml
# General purpose workloads
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: general
spec:
  template:
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot", "on-demand"]
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["m5.large", "m5.xlarge", "c5.large", "c5.xlarge"]
  limits:
    cpu: 1000

---
# Specialized workloads
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: compute-intensive
spec:
  template:
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["on-demand"]
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["c5.2xlarge", "c5.4xlarge", "c5.9xlarge"]
      taints:
      - key: workload-type
        value: "compute-intensive"
        effect: NoSchedule
  limits:
    cpu: 500
```

### 2. Cost Optimization

#### Spot Instance Best Practices:
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: cost-optimized
spec:
  template:
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot"]
      # Use diverse instance types for better spot availability
      - key: node.kubernetes.io/instance-type
        operator: In
        values: [
          "m5.large", "m5.xlarge", "m5.2xlarge",
          "m4.large", "m4.xlarge", "m4.2xlarge",
          "c5.large", "c5.xlarge", "c5.2xlarge",
          "c4.large", "c4.xlarge", "c4.2xlarge"
        ]
      # Spread across multiple AZs
      - key: topology.kubernetes.io/zone
        operator: In
        values: ["us-west-2a", "us-west-2b", "us-west-2c"]
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 15s  # Aggressive consolidation for cost savings
```

### 3. Security Best Practices

#### Secure NodeClass Configuration:
```yaml
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: secure
spec:
  amiFamily: AL2
  
  # Use specific subnets
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
      tier: "private"  # Private subnets only
  
  # Restrict security groups
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
      security-level: "high"
  
  # Secure instance metadata
  metadataOptions:
    httpEndpoint: enabled
    httpProtocolIPv6: disabled
    httpPutResponseHopLimit: 2
    httpTokens: required  # Require IMDSv2
  
  # Encrypted storage
  blockDeviceMappings:
  - deviceName: /dev/xvda
    ebs:
      volumeSize: 50Gi
      volumeType: gp3
      encrypted: true
      kmsKeyId: "alias/ebs-encryption-key"
  
  # Security-focused user data
  userData: |
    #!/bin/bash
    /etc/eks/bootstrap.sh my-cluster
    
    # Security hardening
    echo "net.ipv4.conf.all.send_redirects = 0" >> /etc/sysctl.conf
    echo "net.ipv4.conf.default.send_redirects = 0" >> /etc/sysctl.conf
    echo "net.ipv4.conf.all.accept_source_route = 0" >> /etc/sysctl.conf
    echo "net.ipv4.conf.default.accept_source_route = 0" >> /etc/sysctl.conf
    sysctl -p
    
    # Install security updates
    yum update -y --security
```

### 4. Performance Optimization

#### High-Performance Configuration:
```yaml
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: high-performance
spec:
  amiFamily: AL2
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "my-cluster"
  role: "KarpenterNodeInstanceProfile-my-cluster"
  
  # Performance-optimized storage
  blockDeviceMappings:
  - deviceName: /dev/xvda
    ebs:
      volumeSize: 100Gi
      volumeType: gp3
      iops: 4000
      throughput: 250
  
  # Performance tuning
  userData: |
    #!/bin/bash
    /etc/eks/bootstrap.sh my-cluster --container-runtime containerd
    
    # Performance optimizations
    echo "net.core.rmem_max = 134217728" >> /etc/sysctl.conf
    echo "net.core.wmem_max = 134217728" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_rmem = 4096 87380 134217728" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_wmem = 4096 65536 134217728" >> /etc/sysctl.conf
    echo "net.core.netdev_max_backlog = 5000" >> /etc/sysctl.conf
    sysctl -p
    
    # CPU performance
    echo "performance" > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### 5. Operational Best Practices

#### Monitoring and Alerting:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: karpenter-alerts
spec:
  groups:
  - name: karpenter.rules
    rules:
    - alert: KarpenterNodeClaimFailure
      expr: increase(karpenter_nodeclaims_created_total{reason="failed"}[5m]) > 0
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Karpenter node claim failures detected"
        description: "Karpenter has failed to create {{ $value }} node claims in the last 5 minutes"
    
    - alert: KarpenterHighPendingPods
      expr: karpenter_pods_state{state="pending"} > 10
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High number of pending pods"
        description: "{{ $value }} pods have been pending for more than 5 minutes"
    
    - alert: KarpenterNodeUtilizationLow
      expr: avg(karpenter_nodes_allocatable_cpu_cores - karpenter_nodes_allocated_cpu_cores) / avg(karpenter_nodes_allocatable_cpu_cores) > 0.5
      for: 10m
      labels:
        severity: info
      annotations:
        summary: "Low node utilization detected"
        description: "Average node CPU utilization is below 50% for 10 minutes"
```

This comprehensive guide covers everything you need to know about Karpenter, from basic concepts to production implementation. The examples are practical and can be adapted to your specific use cases.