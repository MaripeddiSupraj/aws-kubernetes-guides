# EKS Cluster Access - Complete Guide

## Table of Contents
1. [AWS Recommended Methods](#aws-recommended-methods)
2. [IAM-Based Access Control](#iam-based-access-control)
3. [RBAC Configuration](#rbac-configuration)
4. [Access Methods Overview](#access-methods-overview)
5. [Step-by-Step Implementation](#step-by-step-implementation)
6. [Advanced Access Patterns](#advanced-access-patterns)
7. [Security Best Practices](#security-best-practices)
8. [Troubleshooting Access Issues](#troubleshooting-access-issues)

---

## AWS Recommended Methods

### 1. EKS Access Entries (Recommended - Latest Method)

#### What are Access Entries?
- **New native AWS method** (introduced in 2023)
- **Replaces aws-auth ConfigMap** for most use cases
- **Integrated with AWS IAM** directly
- **No manual ConfigMap management** required

#### Enable Access Entries:
```bash
# Check if cluster supports access entries
aws eks describe-cluster --name my-cluster --query 'cluster.accessConfig'

# Enable access entries (for new clusters)
aws eks create-cluster \
  --name my-cluster \
  --version 1.28 \
  --role-arn arn:aws:iam::123456789012:role/EKSClusterRole \
  --resources-vpc-config subnetIds=subnet-12345,subnet-67890 \
  --access-config authenticationMode=API_AND_CONFIG_MAP

# For existing clusters, update authentication mode
aws eks update-cluster-config \
  --name my-cluster \
  --access-config authenticationMode=API_AND_CONFIG_MAP
```

#### Create Access Entry for IAM User:
```bash
# Add IAM user access
aws eks create-access-entry \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:user/john.doe \
  --type STANDARD \
  --username john.doe

# Associate with access policy
aws eks associate-access-policy \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:user/john.doe \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy \
  --access-scope type=cluster
```

#### Create Access Entry for IAM Role:
```bash
# Add IAM role access
aws eks create-access-entry \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/EKSAdminRole \
  --type STANDARD \
  --username eks-admin

# Associate with admin policy
aws eks associate-access-policy \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/EKSAdminRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster
```

### 2. Available AWS Managed Access Policies

#### Cluster-Level Policies:
```bash
# View all available policies
aws eks list-access-policies

# Common policies:
# - AmazonEKSClusterAdminPolicy: Full cluster admin access
# - AmazonEKSAdminPolicy: Admin access with some restrictions
# - AmazonEKSEditPolicy: Edit resources in cluster
# - AmazonEKSViewPolicy: Read-only access to cluster
```

#### Policy Details:
```yaml
# AmazonEKSClusterAdminPolicy - Full admin access
Policy: arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy
Permissions:
  - Full cluster administration
  - All Kubernetes API operations
  - Cluster configuration changes

# AmazonEKSAdminPolicy - Standard admin access
Policy: arn:aws:eks::aws:cluster-access-policy/AmazonEKSAdminPolicy
Permissions:
  - Most administrative operations
  - Cannot modify cluster-level resources
  - Cannot access kube-system namespace

# AmazonEKSEditPolicy - Edit access
Policy: arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy
Permissions:
  - Create, update, delete resources
  - Cannot view secrets
  - Cannot modify RBAC

# AmazonEKSViewPolicy - Read-only access
Policy: arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy
Permissions:
  - Read-only access to most resources
  - Cannot view secrets
  - Cannot modify anything
```

### 3. Namespace-Scoped Access

#### Create Namespace-Scoped Access:
```bash
# Create access entry with namespace scope
aws eks create-access-entry \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:user/developer \
  --type STANDARD \
  --username developer

# Associate with namespace-scoped policy
aws eks associate-access-policy \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:user/developer \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy \
  --access-scope type=namespace,namespaces=development,staging
```

---

## IAM-Based Access Control

### 1. IAM Roles for Different Access Levels

#### EKS Admin Role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::123456789012:user/admin1",
          "arn:aws:iam::123456789012:user/admin2"
        ]
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "Bool": {
          "aws:MultiFactorAuthPresent": "true"
        }
      }
    }
  ]
}
```

#### EKS Developer Role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/Department": "Engineering"
        }
      }
    }
  ]
}
```

#### EKS ReadOnly Role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:saml-provider/CompanySAML"
      },
      "Action": "sts:AssumeRoleWithSAML",
      "Condition": {
        "StringEquals": {
          "SAML:Role": "ReadOnlyUser"
        }
      }
    }
  ]
}
```

### 2. IAM Policies for EKS Access

#### EKS Cluster Access Policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
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
        "eks:AccessKubernetesApi"
      ],
      "Resource": "arn:aws:eks:*:123456789012:cluster/my-cluster"
    }
  ]
}
```

#### EKS Admin Policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/EKS*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:DescribeSecurityGroups"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## RBAC Configuration

### 1. Traditional aws-auth ConfigMap Method

#### Complete aws-auth ConfigMap:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    # Node group role (required)
    - rolearn: arn:aws:iam::123456789012:role/EKSNodeGroupRole
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
    
    # Admin role
    - rolearn: arn:aws:iam::123456789012:role/EKSAdminRole
      username: eks-admin
      groups:
        - system:masters
    
    # Developer role
    - rolearn: arn:aws:iam::123456789012:role/EKSDeveloperRole
      username: developer
      groups:
        - developers
    
    # ReadOnly role
    - rolearn: arn:aws:iam::123456789012:role/EKSReadOnlyRole
      username: readonly-user
      groups:
        - readonly-users
    
    # Cross-account access
    - rolearn: arn:aws:iam::987654321098:role/CrossAccountEKSRole
      username: cross-account-user
      groups:
        - external-users

  mapUsers: |
    # Individual IAM users
    - userarn: arn:aws:iam::123456789012:user/john.doe
      username: john.doe
      groups:
        - developers
    
    - userarn: arn:aws:iam::123456789012:user/jane.admin
      username: jane.admin
      groups:
        - system:masters
    
    # Emergency break-glass user
    - userarn: arn:aws:iam::123456789012:user/emergency-admin
      username: emergency-admin
      groups:
        - system:masters

  mapAccounts: |
    # Trust entire AWS accounts (use carefully)
    - "123456789012"
    - "987654321098"
```

### 2. Kubernetes RBAC Roles

#### Developer Role (Namespace-Scoped):
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: developer-role
rules:
# Pods
- apiGroups: [""]
  resources: ["pods", "pods/log", "pods/exec"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
# Services
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
# ConfigMaps and Secrets
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
# Deployments
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
# Ingress
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: development
subjects:
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer-role
  apiGroup: rbac.authorization.k8s.io
```

#### ReadOnly ClusterRole:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: readonly-cluster-role
rules:
# Read-only access to most resources
- apiGroups: [""]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
# Exclude secrets from read access
- apiGroups: [""]
  resources: ["secrets"]
  verbs: []

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: readonly-binding
subjects:
- kind: Group
  name: readonly-users
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: readonly-cluster-role
  apiGroup: rbac.authorization.k8s.io
```

#### DevOps Role (Multi-Namespace):
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: devops-role
rules:
# Full access to application namespaces
- apiGroups: [""]
  resources: ["*"]
  verbs: ["*"]
  resourceNames: []
# Cluster-level read access
- apiGroups: [""]
  resources: ["nodes", "persistentvolumes"]
  verbs: ["get", "list", "watch"]
# Metrics and monitoring
- apiGroups: ["metrics.k8s.io"]
  resources: ["*"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: devops-binding
subjects:
- kind: Group
  name: devops
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: devops-role
  apiGroup: rbac.authorization.k8s.io

---
# Restrict devops from kube-system
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: kube-system
  name: kube-system-readonly
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: devops-kube-system-binding
  namespace: kube-system
subjects:
- kind: Group
  name: devops
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: kube-system-readonly
  apiGroup: rbac.authorization.k8s.io
```

---

## Access Methods Overview

### 1. kubectl Configuration Methods

#### Method 1: AWS CLI Integration (Recommended)
```bash
# Configure kubectl using AWS CLI
aws eks update-kubeconfig --region us-west-2 --name my-cluster

# Verify access
kubectl get nodes

# Use specific profile
aws eks update-kubeconfig --region us-west-2 --name my-cluster --profile production

# Use specific role
aws eks update-kubeconfig --region us-west-2 --name my-cluster --role-arn arn:aws:iam::123456789012:role/EKSAdminRole
```

#### Method 2: Manual kubeconfig
```yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTi... # Base64 encoded CA cert
    server: https://ABCDEF1234567890.gr7.us-west-2.eks.amazonaws.com
  name: arn:aws:eks:us-west-2:123456789012:cluster/my-cluster
contexts:
- context:
    cluster: arn:aws:eks:us-west-2:123456789012:cluster/my-cluster
    user: arn:aws:eks:us-west-2:123456789012:cluster/my-cluster
  name: arn:aws:eks:us-west-2:123456789012:cluster/my-cluster
current-context: arn:aws:eks:us-west-2:123456789012:cluster/my-cluster
users:
- name: arn:aws:eks:us-west-2:123456789012:cluster/my-cluster
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: aws
      args:
      - eks
      - get-token
      - --cluster-name
      - my-cluster
      - --region
      - us-west-2
      env:
      - name: AWS_PROFILE
        value: production
```

### 2. Cross-Account Access

#### Setup Cross-Account Role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::TRUSTED-ACCOUNT:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }
  ]
}
```

#### Cross-Account Access Configuration:
```bash
# Assume cross-account role
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/CrossAccountEKSRole \
  --role-session-name cross-account-session \
  --external-id unique-external-id

# Configure kubectl with assumed role
export AWS_ACCESS_KEY_ID=ASIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...

aws eks update-kubeconfig --region us-west-2 --name my-cluster
```

### 3. Federated Access (SAML/OIDC)

#### OIDC Identity Provider Setup:
```bash
# Create OIDC identity provider
aws iam create-open-id-connect-provider \
  --url https://your-oidc-provider.com \
  --thumbprint-list 9e99a48a9960b14926bb7f3b02e22da2b0ab7280 \
  --client-id-list your-client-id
```

#### OIDC Role Trust Policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/your-oidc-provider.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "your-oidc-provider.com:aud": "your-client-id",
          "your-oidc-provider.com:sub": "user@company.com"
        }
      }
    }
  ]
}
```

---

## Step-by-Step Implementation

### 1. Complete Setup for New Cluster

#### Step 1: Create EKS Cluster with Access Entries
```bash
# Create cluster with access entries enabled
aws eks create-cluster \
  --name production-cluster \
  --version 1.28 \
  --role-arn arn:aws:iam::123456789012:role/EKSClusterRole \
  --resources-vpc-config subnetIds=subnet-12345,subnet-67890,securityGroupIds=sg-12345 \
  --access-config authenticationMode=API_AND_CONFIG_MAP \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'

# Wait for cluster to be active
aws eks wait cluster-active --name production-cluster
```

#### Step 2: Create IAM Roles
```bash
# Create admin role
aws iam create-role \
  --role-name EKSAdminRole \
  --assume-role-policy-document file://eks-admin-trust-policy.json

aws iam attach-role-policy \
  --role-name EKSAdminRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

# Create developer role
aws iam create-role \
  --role-name EKSDeveloperRole \
  --assume-role-policy-document file://eks-developer-trust-policy.json

# Create readonly role
aws iam create-role \
  --role-name EKSReadOnlyRole \
  --assume-role-policy-document file://eks-readonly-trust-policy.json
```

#### Step 3: Configure Access Entries
```bash
# Add admin access
aws eks create-access-entry \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:role/EKSAdminRole \
  --type STANDARD \
  --username eks-admin

aws eks associate-access-policy \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:role/EKSAdminRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster

# Add developer access (namespace-scoped)
aws eks create-access-entry \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:role/EKSDeveloperRole \
  --type STANDARD \
  --username developer

aws eks associate-access-policy \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:role/EKSDeveloperRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy \
  --access-scope type=namespace,namespaces=development,staging

# Add readonly access
aws eks create-access-entry \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:role/EKSReadOnlyRole \
  --type STANDARD \
  --username readonly-user

aws eks associate-access-policy \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:role/EKSReadOnlyRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy \
  --access-scope type=cluster
```

#### Step 4: Create Kubernetes RBAC
```bash
# Update kubeconfig as admin
aws sts assume-role --role-arn arn:aws:iam::123456789012:role/EKSAdminRole --role-session-name admin-session
aws eks update-kubeconfig --region us-west-2 --name production-cluster

# Create namespaces
kubectl create namespace development
kubectl create namespace staging
kubectl create namespace production

# Apply RBAC configurations
kubectl apply -f developer-rbac.yaml
kubectl apply -f readonly-rbac.yaml
```

### 2. Migration from aws-auth to Access Entries

#### Step 1: Enable Access Entries on Existing Cluster
```bash
# Update existing cluster to support both methods
aws eks update-cluster-config \
  --name existing-cluster \
  --access-config authenticationMode=API_AND_CONFIG_MAP
```

#### Step 2: Migrate Existing aws-auth Entries
```bash
# Get current aws-auth ConfigMap
kubectl get configmap aws-auth -n kube-system -o yaml > current-aws-auth.yaml

# Extract roles and users from aws-auth
# For each role in mapRoles, create access entry:
aws eks create-access-entry \
  --cluster-name existing-cluster \
  --principal-arn arn:aws:iam::123456789012:role/ExistingRole \
  --type STANDARD \
  --username existing-user

# Associate appropriate policy
aws eks associate-access-policy \
  --cluster-name existing-cluster \
  --principal-arn arn:aws:iam::123456789012:role/ExistingRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy \
  --access-scope type=cluster
```

#### Step 3: Validate and Switch
```bash
# Test access with new method
aws sts assume-role --role-arn arn:aws:iam::123456789012:role/ExistingRole --role-session-name test
aws eks update-kubeconfig --region us-west-2 --name existing-cluster
kubectl get nodes

# Once validated, switch to API-only mode
aws eks update-cluster-config \
  --name existing-cluster \
  --access-config authenticationMode=API

# Remove aws-auth ConfigMap (optional, after full validation)
kubectl delete configmap aws-auth -n kube-system
```

---

## Advanced Access Patterns

### 1. Temporary Access Patterns

#### Time-Limited Access Role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/contractor"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "DateLessThan": {
          "aws:CurrentTime": "2024-12-31T23:59:59Z"
        },
        "IpAddress": {
          "aws:SourceIp": "203.0.113.0/24"
        }
      }
    }
  ]
}
```

#### Emergency Break-Glass Access:
```bash
# Create emergency access entry (use sparingly)
aws eks create-access-entry \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:user/emergency-admin \
  --type STANDARD \
  --username emergency-admin

aws eks associate-access-policy \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:user/emergency-admin \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster

# Monitor emergency access usage
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=emergency-admin \
  --start-time 2024-01-01 \
  --end-time 2024-01-31
```

### 2. Service Account Access

#### Create Service Account with IAM Role:
```bash
# Create IAM role for service account
eksctl create iamserviceaccount \
  --name cluster-admin-sa \
  --namespace kube-system \
  --cluster production-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy \
  --approve

# Use service account for automation
kubectl create job admin-task --image=bitnami/kubectl -- kubectl get nodes
kubectl patch job admin-task -p '{"spec":{"template":{"spec":{"serviceAccountName":"cluster-admin-sa"}}}}'
```

### 3. Multi-Cluster Access Management

#### Centralized Access Management:
```bash
# Create cross-cluster admin role
aws iam create-role \
  --role-name MultiClusterAdminRole \
  --assume-role-policy-document file://multi-cluster-trust-policy.json

# Add access to multiple clusters
for cluster in prod-us-west-2 prod-us-east-1 staging-us-west-2; do
  aws eks create-access-entry \
    --cluster-name $cluster \
    --principal-arn arn:aws:iam::123456789012:role/MultiClusterAdminRole \
    --type STANDARD \
    --username multi-cluster-admin
  
  aws eks associate-access-policy \
    --cluster-name $cluster \
    --principal-arn arn:aws:iam::123456789012:role/MultiClusterAdminRole \
    --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
    --access-scope type=cluster
done
```

---

## Security Best Practices

### 1. Principle of Least Privilege

#### Granular Namespace Access:
```bash
# Create role with access to specific namespaces only
aws eks create-access-entry \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:role/TeamARole \
  --type STANDARD \
  --username team-a-user

aws eks associate-access-policy \
  --cluster-name production-cluster \
  --principal-arn arn:aws:iam::123456789012:role/TeamARole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy \
  --access-scope type=namespace,namespaces=team-a-dev,team-a-staging
```

### 2. MFA Enforcement

#### MFA-Required Role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/admin"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "Bool": {
          "aws:MultiFactorAuthPresent": "true"
        },
        "NumericLessThan": {
          "aws:MultiFactorAuthAge": "3600"
        }
      }
    }
  ]
}
```

### 3. IP Restriction

#### IP-Restricted Access:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/remote-user"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": [
            "203.0.113.0/24",
            "198.51.100.0/24"
          ]
        }
      }
    }
  ]
}
```

### 4. Audit and Monitoring

#### CloudTrail for EKS Access:
```json
{
  "eventVersion": "1.05",
  "userIdentity": {
    "type": "AssumedRole",
    "principalId": "AIDACKCEVSQ6C2EXAMPLE",
    "arn": "arn:aws:sts::123456789012:assumed-role/EKSAdminRole/admin-session",
    "accountId": "123456789012"
  },
  "eventTime": "2024-01-15T10:30:00Z",
  "eventSource": "eks.amazonaws.com",
  "eventName": "CreateAccessEntry",
  "sourceIPAddress": "203.0.113.12",
  "resources": [
    {
      "accountId": "123456789012",
      "type": "AWS::EKS::Cluster",
      "ARN": "arn:aws:eks:us-west-2:123456789012:cluster/production-cluster"
    }
  ]
}
```

#### Monitor kubectl Access:
```bash
# Enable audit logging on EKS cluster
aws eks update-cluster-config \
  --name production-cluster \
  --logging '{"clusterLogging":[{"types":["audit"],"enabled":true}]}'

# Query audit logs
aws logs filter-log-events \
  --log-group-name /aws/eks/production-cluster/cluster \
  --filter-pattern '{ $.verb = "create" || $.verb = "delete" || $.verb = "update" }' \
  --start-time 1642204800000
```

---

## Troubleshooting Access Issues

### 1. Common Access Problems

#### Problem: "You must be logged in to the server (Unauthorized)"
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check if user/role has EKS access
aws eks describe-cluster --name my-cluster

# Verify kubeconfig
kubectl config current-context
kubectl config view --minify

# Check access entries
aws eks list-access-entries --cluster-name my-cluster
```

#### Problem: "error: exec plugin: invalid apiVersion"
```bash
# Update AWS CLI
pip install --upgrade awscli

# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name my-cluster --force

# Check kubectl version compatibility
kubectl version --client
```

#### Problem: Access denied for specific operations
```bash
# Check current user permissions
kubectl auth can-i --list

# Check specific permission
kubectl auth can-i create pods --namespace development

# Verify RBAC configuration
kubectl get rolebindings,clusterrolebindings --all-namespaces -o wide | grep username
```

### 2. Debugging Commands

#### Complete Access Diagnostic:
```bash
#!/bin/bash
# eks-access-debug.sh

CLUSTER_NAME=$1
if [ -z "$CLUSTER_NAME" ]; then
  echo "Usage: $0 <cluster-name>"
  exit 1
fi

echo "=== EKS Access Diagnostic for $CLUSTER_NAME ==="

echo "1. AWS Identity:"
aws sts get-caller-identity

echo -e "\n2. Cluster Information:"
aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.{Status:status,Version:version,Endpoint:endpoint,AuthMode:accessConfig.authenticationMode}'

echo -e "\n3. Access Entries:"
aws eks list-access-entries --cluster-name $CLUSTER_NAME

echo -e "\n4. Current kubeconfig context:"
kubectl config current-context

echo -e "\n5. Test basic access:"
kubectl get nodes 2>&1 | head -5

echo -e "\n6. Check permissions:"
kubectl auth can-i --list 2>&1 | head -10

echo -e "\n7. aws-auth ConfigMap (if exists):"
kubectl get configmap aws-auth -n kube-system -o yaml 2>/dev/null | head -20

echo -e "\n8. Recent authentication events:"
aws logs filter-log-events \
  --log-group-name /aws/eks/$CLUSTER_NAME/cluster \
  --filter-pattern "authentication" \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --max-items 5 2>/dev/null
```

### 3. Access Recovery Procedures

#### Recover Lost Admin Access:
```bash
# Method 1: Use cluster creator credentials
# The IAM user/role that created the cluster has automatic admin access

# Method 2: Use root account (emergency only)
aws sts get-caller-identity  # Verify you're using root

# Method 3: Update aws-auth as cluster creator
kubectl patch configmap aws-auth -n kube-system --patch '
data:
  mapUsers: |
    - userarn: arn:aws:iam::123456789012:user/emergency-admin
      username: emergency-admin
      groups:
        - system:masters
'

# Method 4: Create new access entry (if access entries enabled)
aws eks create-access-entry \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:user/recovery-admin \
  --type STANDARD \
  --username recovery-admin

aws eks associate-access-policy \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:user/recovery-admin \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster
```

This comprehensive guide covers all possible ways to access EKS clusters, from the latest AWS recommended methods to traditional approaches, with complete implementation examples and troubleshooting procedures.