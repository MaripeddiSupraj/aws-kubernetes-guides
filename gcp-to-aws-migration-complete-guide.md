# GCP to AWS Migration - Complete Enterprise Guide

## Table of Contents
1. [Migration Overview & Strategy](#migration-overview--strategy)
2. [Pre-Migration Assessment](#pre-migration-assessment)
3. [Real-World Case Study: E-commerce Platform](#real-world-case-study-e-commerce-platform)
4. [Phase 1: Infrastructure Planning](#phase-1-infrastructure-planning)
5. [Phase 2: Data Migration](#phase-2-data-migration)
6. [Phase 3: Application Migration](#phase-3-application-migration)
7. [Phase 4: Network & Security](#phase-4-network--security)
8. [Phase 5: Testing & Validation](#phase-5-testing--validation)
9. [Phase 6: Cutover & Go-Live](#phase-6-cutover--go-live)
10. [Post-Migration Optimization](#post-migration-optimization)

---

## Migration Overview & Strategy

### Migration Approaches

#### 1. Lift and Shift (Rehost)
- **Timeline**: 3-6 months
- **Risk**: Low
- **Cost**: Medium
- **Benefits**: Quick migration, minimal code changes

#### 2. Replatform (Lift, Tinker, and Shift)
- **Timeline**: 6-12 months
- **Risk**: Medium
- **Cost**: Medium-High
- **Benefits**: Cloud-native features, better performance

#### 3. Refactor/Re-architect
- **Timeline**: 12-24 months
- **Risk**: High
- **Cost**: High
- **Benefits**: Full cloud-native, optimal performance

### Service Mapping: GCP to AWS

| GCP Service | AWS Equivalent | Migration Complexity |
|-------------|----------------|---------------------|
| GKE | EKS | Medium |
| Cloud SQL | RDS | Low |
| Cloud Storage | S3 | Low |
| Cloud Functions | Lambda | Medium |
| Cloud Run | Fargate | Medium |
| BigQuery | Redshift/Athena | High |
| Cloud Pub/Sub | SQS/SNS | Medium |
| Cloud Load Balancing | ALB/NLB | Low |
| Cloud CDN | CloudFront | Low |
| Cloud IAM | IAM | High |
| Cloud Monitoring | CloudWatch | Medium |
| Cloud Logging | CloudWatch Logs | Medium |

---

## Pre-Migration Assessment

### 1. Current State Analysis

#### Infrastructure Inventory Script:
```bash
#!/bin/bash
# gcp-inventory.sh - Comprehensive GCP resource inventory

echo "=== GCP Infrastructure Inventory ==="
echo "Generated on: $(date)"
echo ""

# Set project
PROJECT_ID=$(gcloud config get-value project)
echo "Project ID: $PROJECT_ID"
echo ""

# Compute instances
echo "=== Compute Instances ==="
gcloud compute instances list --format="table(name,zone,machineType,status,internalIP,externalIP)" > compute-instances.csv
cat compute-instances.csv
echo ""

# GKE clusters
echo "=== GKE Clusters ==="
gcloud container clusters list --format="table(name,location,currentMasterVersion,currentNodeVersion,status,nodeCount)" > gke-clusters.csv
cat gke-clusters.csv
echo ""

# Cloud SQL instances
echo "=== Cloud SQL Instances ==="
gcloud sql instances list --format="table(name,databaseVersion,region,tier,ipAddress.ipAddress,state)" > sql-instances.csv
cat sql-instances.csv
echo ""

# Storage buckets
echo "=== Cloud Storage Buckets ==="
gsutil ls -L -b gs://* > storage-buckets.txt 2>/dev/null
echo "Storage details saved to storage-buckets.txt"
echo ""

# Load balancers
echo "=== Load Balancers ==="
gcloud compute forwarding-rules list --format="table(name,region,IPAddress,target)" > load-balancers.csv
cat load-balancers.csv
echo ""

# Networks and subnets
echo "=== Networks ==="
gcloud compute networks list --format="table(name,subnet_mode,bgp_routing_mode)" > networks.csv
cat networks.csv
echo ""

echo "=== Subnets ==="
gcloud compute networks subnets list --format="table(name,region,network,range)" > subnets.csv
cat subnets.csv
echo ""

# Firewall rules
echo "=== Firewall Rules ==="
gcloud compute firewall-rules list --format="table(name,direction,priority,sourceRanges,allowed)" > firewall-rules.csv
cat firewall-rules.csv
echo ""

echo "Inventory complete. Files generated:"
echo "- compute-instances.csv"
echo "- gke-clusters.csv"
echo "- sql-instances.csv"
echo "- storage-buckets.txt"
echo "- load-balancers.csv"
echo "- networks.csv"
echo "- subnets.csv"
echo "- firewall-rules.csv"
```

### 2. Application Dependencies Analysis

#### Dependency Mapping Tool:
```python
#!/usr/bin/env python3
# dependency-analyzer.py

import json
import subprocess
import sys
from collections import defaultdict

class GCPDependencyAnalyzer:
    def __init__(self, project_id):
        self.project_id = project_id
        self.dependencies = defaultdict(list)
        
    def analyze_gke_workloads(self):
        """Analyze GKE workloads and their dependencies"""
        print("Analyzing GKE workloads...")
        
        # Get clusters
        clusters = self.run_gcloud_command([
            'container', 'clusters', 'list', 
            '--format=value(name,location)'
        ])
        
        for cluster_info in clusters:
            if not cluster_info.strip():
                continue
                
            name, location = cluster_info.strip().split('\t')
            
            # Get cluster credentials
            self.run_gcloud_command([
                'container', 'clusters', 'get-credentials',
                name, '--location', location
            ])
            
            # Analyze workloads
            self.analyze_k8s_resources(name)
    
    def analyze_k8s_resources(self, cluster_name):
        """Analyze Kubernetes resources"""
        resources = {
            'deployments': 'apps/v1',
            'services': 'v1',
            'configmaps': 'v1',
            'secrets': 'v1',
            'ingresses': 'networking.k8s.io/v1'
        }
        
        cluster_deps = {
            'cluster_name': cluster_name,
            'workloads': [],
            'external_dependencies': []
        }
        
        for resource_type, api_version in resources.items():
            try:
                output = subprocess.check_output([
                    'kubectl', 'get', resource_type, 
                    '--all-namespaces', '-o', 'json'
                ], text=True)
                
                data = json.loads(output)
                
                for item in data.get('items', []):
                    workload_info = {
                        'name': item['metadata']['name'],
                        'namespace': item['metadata']['namespace'],
                        'type': resource_type,
                        'dependencies': []
                    }
                    
                    # Analyze specific dependencies
                    if resource_type == 'deployments':
                        self.analyze_deployment_deps(item, workload_info)
                    elif resource_type == 'services':
                        self.analyze_service_deps(item, workload_info)
                    
                    cluster_deps['workloads'].append(workload_info)
                    
            except subprocess.CalledProcessError as e:
                print(f"Error analyzing {resource_type}: {e}")
        
        self.dependencies[cluster_name] = cluster_deps
    
    def analyze_deployment_deps(self, deployment, workload_info):
        """Analyze deployment dependencies"""
        spec = deployment.get('spec', {})
        template = spec.get('template', {})
        containers = template.get('spec', {}).get('containers', [])
        
        for container in containers:
            # Image dependencies
            image = container.get('image', '')
            if 'gcr.io' in image:
                workload_info['dependencies'].append({
                    'type': 'container_registry',
                    'source': 'GCR',
                    'target': 'ECR',
                    'resource': image
                })
            
            # Environment variables pointing to GCP services
            env_vars = container.get('env', [])
            for env_var in env_vars:
                value = env_var.get('value', '')
                if any(gcp_service in value for gcp_service in [
                    'googleapis.com', 'cloudsql', 'pubsub', 'storage.googleapis.com'
                ]):
                    workload_info['dependencies'].append({
                        'type': 'external_service',
                        'name': env_var.get('name'),
                        'value': value,
                        'migration_required': True
                    })
    
    def analyze_service_deps(self, service, workload_info):
        """Analyze service dependencies"""
        spec = service.get('spec', {})
        service_type = spec.get('type', 'ClusterIP')
        
        if service_type == 'LoadBalancer':
            workload_info['dependencies'].append({
                'type': 'load_balancer',
                'source': 'GCP Load Balancer',
                'target': 'AWS ALB/NLB',
                'migration_complexity': 'Medium'
            })
    
    def run_gcloud_command(self, args):
        """Run gcloud command and return output"""
        try:
            result = subprocess.check_output(['gcloud'] + args, text=True)
            return result.strip().split('\n')
        except subprocess.CalledProcessError as e:
            print(f"Error running gcloud command: {e}")
            return []
    
    def generate_migration_plan(self):
        """Generate migration plan based on dependencies"""
        migration_plan = {
            'phases': [],
            'estimated_timeline': '6-12 months',
            'complexity_score': 0
        }
        
        # Phase 1: Infrastructure
        phase1 = {
            'name': 'Infrastructure Setup',
            'duration': '2-4 weeks',
            'tasks': [
                'Setup AWS accounts and IAM',
                'Create VPC and networking',
                'Setup EKS clusters',
                'Configure ECR repositories'
            ]
        }
        migration_plan['phases'].append(phase1)
        
        # Phase 2: Data Migration
        phase2 = {
            'name': 'Data Migration',
            'duration': '4-8 weeks',
            'tasks': [
                'Migrate Cloud SQL to RDS',
                'Migrate Cloud Storage to S3',
                'Setup data replication',
                'Validate data integrity'
            ]
        }
        migration_plan['phases'].append(phase2)
        
        # Phase 3: Application Migration
        phase3 = {
            'name': 'Application Migration',
            'duration': '8-16 weeks',
            'tasks': []
        }
        
        for cluster_name, cluster_info in self.dependencies.items():
            phase3['tasks'].append(f'Migrate {cluster_name} workloads to EKS')
            
        migration_plan['phases'].append(phase3)
        
        return migration_plan
    
    def export_results(self):
        """Export analysis results"""
        results = {
            'project_id': self.project_id,
            'dependencies': dict(self.dependencies),
            'migration_plan': self.generate_migration_plan()
        }
        
        with open('gcp-migration-analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("Analysis complete. Results saved to gcp-migration-analysis.json")
        return results

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 dependency-analyzer.py <project-id>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    analyzer = GCPDependencyAnalyzer(project_id)
    analyzer.analyze_gke_workloads()
    analyzer.export_results()
```

---

## Real-World Case Study: E-commerce Platform

### Current GCP Architecture

#### Company: TechMart E-commerce
- **Industry**: Online Retail
- **Scale**: 10M+ users, 1000+ transactions/minute
- **Current GCP Setup**:
  - 3 GKE clusters (prod, staging, dev)
  - 50+ microservices
  - Cloud SQL (PostgreSQL)
  - Cloud Storage (product images, backups)
  - Cloud Pub/Sub (order processing)
  - Cloud Functions (image processing)
  - Cloud CDN
  - Cloud Load Balancing

#### Current Architecture Diagram:
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cloud CDN     │    │  Load Balancer   │    │   GKE Cluster   │
│   (Static)      │◄──►│   (HTTP/HTTPS)   │◄──►│   (50 services) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │   Cloud SQL      │    │  Cloud Storage  │
                    │  (PostgreSQL)    │    │  (Images/Files) │
                    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │   Cloud Pub/Sub  │    │ Cloud Functions │
                    │ (Order Queue)    │    │ (Image Process) │
                    └──────────────────┘    └─────────────────┘
```

### Target AWS Architecture:
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CloudFront    │    │      ALB         │    │   EKS Cluster   │
│   (CDN)         │◄──►│   (HTTP/HTTPS)   │◄──►│   (50 services) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │      RDS         │    │       S3        │
                    │  (PostgreSQL)    │    │  (Images/Files) │
                    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │      SQS         │    │     Lambda      │
                    │ (Order Queue)    │    │ (Image Process) │
                    └──────────────────┘    └─────────────────┘
```

---

## Phase 1: Infrastructure Planning

### 1. AWS Account Setup

#### Multi-Account Strategy:
```bash
#!/bin/bash
# aws-account-setup.sh

# Create AWS Organizations structure
aws organizations create-organization --feature-set ALL

# Create accounts for different environments
aws organizations create-account \
  --email techmart-prod@company.com \
  --account-name "TechMart Production"

aws organizations create-account \
  --email techmart-staging@company.com \
  --account-name "TechMart Staging"

aws organizations create-account \
  --email techmart-dev@company.com \
  --account-name "TechMart Development"

# Create OUs
PROD_OU=$(aws organizations create-organizational-unit \
  --parent-id r-xxxx \
  --name "Production" \
  --query 'OrganizationalUnit.Id' --output text)

NONPROD_OU=$(aws organizations create-organizational-unit \
  --parent-id r-xxxx \
  --name "Non-Production" \
  --query 'OrganizationalUnit.Id' --output text)

echo "Production OU: $PROD_OU"
echo "Non-Production OU: $NONPROD_OU"
```

### 2. Network Architecture

#### VPC Setup for Production:
```bash
#!/bin/bash
# vpc-setup.sh

# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=techmart-prod-vpc}]' \
  --query 'Vpc.VpcId' --output text)

echo "Created VPC: $VPC_ID"

# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=techmart-prod-igw}]' \
  --query 'InternetGateway.InternetGatewayId' --output text)

aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Create public subnets
PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-west-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=techmart-prod-public-1}]' \
  --query 'Subnet.SubnetId' --output text)

PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-west-2b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=techmart-prod-public-2}]' \
  --query 'Subnet.SubnetId' --output text)

# Create private subnets
PRIVATE_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.10.0/24 \
  --availability-zone us-west-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=techmart-prod-private-1}]' \
  --query 'Subnet.SubnetId' --output text)

PRIVATE_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-west-2b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=techmart-prod-private-2}]' \
  --query 'Subnet.SubnetId' --output text)

# Create database subnets
DB_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.20.0/24 \
  --availability-zone us-west-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=techmart-prod-db-1}]' \
  --query 'Subnet.SubnetId' --output text)

DB_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.21.0/24 \
  --availability-zone us-west-2b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=techmart-prod-db-2}]' \
  --query 'Subnet.SubnetId' --output text)

# Create NAT Gateways
EIP_1=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
EIP_2=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)

NAT_GW_1=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_1 \
  --allocation-id $EIP_1 \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=techmart-prod-nat-1}]' \
  --query 'NatGateway.NatGatewayId' --output text)

NAT_GW_2=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_2 \
  --allocation-id $EIP_2 \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=techmart-prod-nat-2}]' \
  --query 'NatGateway.NatGatewayId' --output text)

# Create route tables
PUBLIC_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=techmart-prod-public-rt}]' \
  --query 'RouteTable.RouteTableId' --output text)

PRIVATE_RT_1=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=techmart-prod-private-rt-1}]' \
  --query 'RouteTable.RouteTableId' --output text)

PRIVATE_RT_2=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=techmart-prod-private-rt-2}]' \
  --query 'RouteTable.RouteTableId' --output text)

# Add routes
aws ec2 create-route --route-table-id $PUBLIC_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 create-route --route-table-id $PRIVATE_RT_1 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_1
aws ec2 create-route --route-table-id $PRIVATE_RT_2 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_2

# Associate subnets with route tables
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_1 --route-table-id $PUBLIC_RT
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_2 --route-table-id $PUBLIC_RT
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_1 --route-table-id $PRIVATE_RT_1
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_2 --route-table-id $PRIVATE_RT_2

echo "Network setup complete!"
echo "VPC ID: $VPC_ID"
echo "Public Subnets: $PUBLIC_SUBNET_1, $PUBLIC_SUBNET_2"
echo "Private Subnets: $PRIVATE_SUBNET_1, $PRIVATE_SUBNET_2"
echo "Database Subnets: $DB_SUBNET_1, $DB_SUBNET_2"
```

### 3. EKS Cluster Setup

#### Production EKS Cluster:
```yaml
# eks-cluster-config.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: techmart-prod-eks
  region: us-west-2
  version: "1.28"

vpc:
  id: "vpc-xxxxxxxxx"  # Replace with actual VPC ID
  subnets:
    private:
      us-west-2a:
        id: "subnet-xxxxxxxxx"  # Private subnet 1
      us-west-2b:
        id: "subnet-xxxxxxxxx"  # Private subnet 2
    public:
      us-west-2a:
        id: "subnet-xxxxxxxxx"  # Public subnet 1
      us-west-2b:
        id: "subnet-xxxxxxxxx"  # Public subnet 2

iam:
  withOIDC: true
  serviceAccounts:
  - metadata:
      name: aws-load-balancer-controller
      namespace: kube-system
    wellKnownPolicies:
      awsLoadBalancerController: true
  - metadata:
      name: cluster-autoscaler
      namespace: kube-system
    wellKnownPolicies:
      autoScaler: true
  - metadata:
      name: ebs-csi-controller-sa
      namespace: kube-system
    wellKnownPolicies:
      ebsCSIController: true

managedNodeGroups:
- name: system-nodes
  instanceType: m5.large
  minSize: 2
  maxSize: 4
  desiredCapacity: 2
  privateNetworking: true
  labels:
    role: system
  taints:
  - key: CriticalAddonsOnly
    value: "true"
    effect: NoSchedule

- name: application-nodes
  instanceTypes: 
  - m5.large
  - m5.xlarge
  - m5.2xlarge
  minSize: 3
  maxSize: 20
  desiredCapacity: 6
  privateNetworking: true
  spot: true
  labels:
    role: application
  tags:
    k8s.io/cluster-autoscaler/enabled: "true"
    k8s.io/cluster-autoscaler/techmart-prod-eks: "owned"

addons:
- name: vpc-cni
  version: latest
- name: coredns
  version: latest
- name: kube-proxy
  version: latest
- name: aws-ebs-csi-driver
  version: latest

cloudWatch:
  clusterLogging:
    enableTypes: ["*"]
```

#### Create EKS Cluster:
```bash
# Create the cluster
eksctl create cluster -f eks-cluster-config.yaml

# Install essential add-ons
kubectl apply -f https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.7.2/v2_7_2_full.yaml

# Install cluster autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

## Phase 2: Data Migration

### 1. Cloud SQL to RDS Migration

#### Database Migration Strategy:
```bash
#!/bin/bash
# db-migration-setup.sh

# Create RDS subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name techmart-prod-db-subnet-group \
  --db-subnet-group-description "TechMart Production DB Subnet Group" \
  --subnet-ids subnet-xxxxxxxxx subnet-xxxxxxxxx \
  --tags Key=Name,Value=techmart-prod-db-subnet-group

# Create RDS parameter group
aws rds create-db-parameter-group \
  --db-parameter-group-name techmart-prod-postgres14 \
  --db-parameter-group-family postgres14 \
  --description "TechMart Production PostgreSQL 14 parameters"

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier techmart-prod-db \
  --db-instance-class db.r6g.xlarge \
  --engine postgres \
  --engine-version 14.9 \
  --master-username dbadmin \
  --master-user-password 'SecurePassword123!' \
  --allocated-storage 500 \
  --storage-type gp3 \
  --storage-encrypted \
  --vpc-security-group-ids sg-xxxxxxxxx \
  --db-subnet-group-name techmart-prod-db-subnet-group \
  --db-parameter-group-name techmart-prod-postgres14 \
  --backup-retention-period 7 \
  --multi-az \
  --auto-minor-version-upgrade \
  --deletion-protection \
  --tags Key=Name,Value=techmart-prod-db Key=Environment,Value=production

echo "RDS instance creation initiated..."
```

#### Database Migration Script:
```python
#!/usr/bin/env python3
# db-migration.py

import psycopg2
import boto3
import os
import subprocess
from datetime import datetime

class DatabaseMigrator:
    def __init__(self):
        self.gcp_config = {
            'host': os.getenv('GCP_DB_HOST'),
            'database': os.getenv('GCP_DB_NAME'),
            'user': os.getenv('GCP_DB_USER'),
            'password': os.getenv('GCP_DB_PASSWORD'),
            'port': 5432
        }
        
        self.aws_config = {
            'host': os.getenv('AWS_DB_HOST'),
            'database': os.getenv('AWS_DB_NAME'),
            'user': os.getenv('AWS_DB_USER'),
            'password': os.getenv('AWS_DB_PASSWORD'),
            'port': 5432
        }
    
    def create_schema_dump(self):
        """Create schema-only dump from GCP Cloud SQL"""
        print("Creating schema dump...")
        
        dump_file = f"schema_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        cmd = [
            'pg_dump',
            f"--host={self.gcp_config['host']}",
            f"--username={self.gcp_config['user']}",
            f"--dbname={self.gcp_config['database']}",
            '--schema-only',
            '--no-owner',
            '--no-privileges',
            f"--file={dump_file}"
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = self.gcp_config['password']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Schema dump created: {dump_file}")
            return dump_file
        else:
            print(f"Error creating schema dump: {result.stderr}")
            return None
    
    def restore_schema(self, dump_file):
        """Restore schema to AWS RDS"""
        print("Restoring schema to AWS RDS...")
        
        cmd = [
            'psql',
            f"--host={self.aws_config['host']}",
            f"--username={self.aws_config['user']}",
            f"--dbname={self.aws_config['database']}",
            f"--file={dump_file}"
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = self.aws_config['password']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Schema restored successfully")
            return True
        else:
            print(f"Error restoring schema: {result.stderr}")
            return False
    
    def setup_dms_replication(self):
        """Setup AWS DMS for data replication"""
        print("Setting up AWS DMS replication...")
        
        dms = boto3.client('dms', region_name='us-west-2')
        
        # Create replication subnet group
        try:
            dms.create_replication_subnet_group(
                ReplicationSubnetGroupIdentifier='techmart-dms-subnet-group',
                ReplicationSubnetGroupDescription='TechMart DMS Subnet Group',
                SubnetIds=[
                    'subnet-xxxxxxxxx',  # Private subnet 1
                    'subnet-xxxxxxxxx'   # Private subnet 2
                ],
                Tags=[
                    {'Key': 'Name', 'Value': 'techmart-dms-subnet-group'}
                ]
            )
        except dms.exceptions.ResourceAlreadyExistsFault:
            print("DMS subnet group already exists")
        
        # Create replication instance
        try:
            response = dms.create_replication_instance(
                ReplicationInstanceIdentifier='techmart-replication-instance',
                ReplicationInstanceClass='dms.r5.large',
                AllocatedStorage=100,
                VpcSecurityGroupIds=['sg-xxxxxxxxx'],
                ReplicationSubnetGroupIdentifier='techmart-dms-subnet-group',
                MultiAZ=True,
                PubliclyAccessible=False,
                Tags=[
                    {'Key': 'Name', 'Value': 'techmart-replication-instance'}
                ]
            )
            print("DMS replication instance created")
        except dms.exceptions.ResourceAlreadyExistsFault:
            print("DMS replication instance already exists")
        
        return True
    
    def create_dms_endpoints(self):
        """Create DMS source and target endpoints"""
        dms = boto3.client('dms', region_name='us-west-2')
        
        # Source endpoint (GCP Cloud SQL)
        try:
            dms.create_endpoint(
                EndpointIdentifier='techmart-source-endpoint',
                EndpointType='source',
                EngineName='postgres',
                Username=self.gcp_config['user'],
                Password=self.gcp_config['password'],
                ServerName=self.gcp_config['host'],
                Port=self.gcp_config['port'],
                DatabaseName=self.gcp_config['database'],
                Tags=[
                    {'Key': 'Name', 'Value': 'techmart-source-endpoint'}
                ]
            )
            print("Source endpoint created")
        except dms.exceptions.ResourceAlreadyExistsFault:
            print("Source endpoint already exists")
        
        # Target endpoint (AWS RDS)
        try:
            dms.create_endpoint(
                EndpointIdentifier='techmart-target-endpoint',
                EndpointType='target',
                EngineName='postgres',
                Username=self.aws_config['user'],
                Password=self.aws_config['password'],
                ServerName=self.aws_config['host'],
                Port=self.aws_config['port'],
                DatabaseName=self.aws_config['database'],
                Tags=[
                    {'Key': 'Name', 'Value': 'techmart-target-endpoint'}
                ]
            )
            print("Target endpoint created")
        except dms.exceptions.ResourceAlreadyExistsFault:
            print("Target endpoint already exists")
    
    def start_migration_task(self):
        """Start DMS migration task"""
        dms = boto3.client('dms', region_name='us-west-2')
        
        # Define table mappings
        table_mappings = {
            "rules": [
                {
                    "rule-type": "selection",
                    "rule-id": "1",
                    "rule-name": "1",
                    "object-locator": {
                        "schema-name": "public",
                        "table-name": "%"
                    },
                    "rule-action": "include"
                }
            ]
        }
        
        try:
            response = dms.create_replication_task(
                ReplicationTaskIdentifier='techmart-migration-task',
                SourceEndpointArn='arn:aws:dms:us-west-2:ACCOUNT:endpoint:techmart-source-endpoint',
                TargetEndpointArn='arn:aws:dms:us-west-2:ACCOUNT:endpoint:techmart-target-endpoint',
                ReplicationInstanceArn='arn:aws:dms:us-west-2:ACCOUNT:rep:techmart-replication-instance',
                MigrationType='full-load-and-cdc',
                TableMappings=str(table_mappings).replace("'", '"'),
                Tags=[
                    {'Key': 'Name', 'Value': 'techmart-migration-task'}
                ]
            )
            
            # Start the task
            dms.start_replication_task(
                ReplicationTaskArn=response['ReplicationTask']['ReplicationTaskArn'],
                StartReplicationTaskType='start-replication'
            )
            
            print("Migration task started")
            return True
            
        except Exception as e:
            print(f"Error starting migration task: {e}")
            return False
    
    def run_migration(self):
        """Run complete migration process"""
        print("Starting database migration process...")
        
        # Step 1: Create schema dump
        dump_file = self.create_schema_dump()
        if not dump_file:
            return False
        
        # Step 2: Restore schema
        if not self.restore_schema(dump_file):
            return False
        
        # Step 3: Setup DMS
        if not self.setup_dms_replication():
            return False
        
        # Step 4: Create endpoints
        self.create_dms_endpoints()
        
        # Step 5: Start migration task
        if not self.start_migration_task():
            return False
        
        print("Database migration initiated successfully!")
        print("Monitor the migration progress in AWS DMS console")
        return True

if __name__ == "__main__":
    migrator = DatabaseMigrator()
    migrator.run_migration()
```

### 2. Cloud Storage to S3 Migration

#### Storage Migration Script:
```bash
#!/bin/bash
# storage-migration.sh

# Install gsutil and aws cli if not present
which gsutil || echo "Please install Google Cloud SDK"
which aws || echo "Please install AWS CLI"

# Set variables
GCP_PROJECT="your-gcp-project"
AWS_REGION="us-west-2"
MIGRATION_LOG="storage-migration-$(date +%Y%m%d-%H%M%S).log"

echo "Starting Cloud Storage to S3 migration..." | tee -a $MIGRATION_LOG
echo "Timestamp: $(date)" | tee -a $MIGRATION_LOG

# Get list of GCS buckets
echo "Discovering GCS buckets..." | tee -a $MIGRATION_LOG
gsutil ls -p $GCP_PROJECT > gcs-buckets.txt

# Create corresponding S3 buckets
while IFS= read -r bucket_url; do
    if [[ $bucket_url == gs://* ]]; then
        bucket_name=$(echo $bucket_url | sed 's|gs://||' | sed 's|/||')
        
        echo "Processing bucket: $bucket_name" | tee -a $MIGRATION_LOG
        
        # Create S3 bucket with same name (if available)
        aws_bucket_name="techmart-${bucket_name}"
        
        echo "Creating S3 bucket: $aws_bucket_name" | tee -a $MIGRATION_LOG
        aws s3 mb s3://$aws_bucket_name --region $AWS_REGION 2>&1 | tee -a $MIGRATION_LOG
        
        # Configure bucket policies and settings
        aws s3api put-bucket-versioning \
            --bucket $aws_bucket_name \
            --versioning-configuration Status=Enabled 2>&1 | tee -a $MIGRATION_LOG
        
        aws s3api put-bucket-encryption \
            --bucket $aws_bucket_name \
            --server-side-encryption-configuration '{
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }' 2>&1 | tee -a $MIGRATION_LOG
        
        # Start data transfer using gsutil and aws cli
        echo "Starting data transfer for $bucket_name..." | tee -a $MIGRATION_LOG
        
        # Use gsutil to sync to local temp, then aws s3 sync to upload
        # For large datasets, consider using AWS DataSync or Storage Transfer Service
        
        temp_dir="/tmp/migration-${bucket_name}"
        mkdir -p $temp_dir
        
        # Download from GCS
        gsutil -m rsync -r -d gs://$bucket_name $temp_dir 2>&1 | tee -a $MIGRATION_LOG
        
        # Upload to S3
        aws s3 sync $temp_dir s3://$aws_bucket_name --storage-class STANDARD_IA 2>&1 | tee -a $MIGRATION_LOG
        
        # Cleanup temp directory
        rm -rf $temp_dir
        
        echo "Completed migration for bucket: $bucket_name" | tee -a $MIGRATION_LOG
    fi
done < gcs-buckets.txt

echo "Storage migration completed!" | tee -a $MIGRATION_LOG
echo "Check log file: $MIGRATION_LOG"
```

#### Advanced S3 Transfer using AWS DataSync:
```python
#!/usr/bin/env python3
# datasync-migration.py

import boto3
import json
from datetime import datetime

class DataSyncMigrator:
    def __init__(self, region='us-west-2'):
        self.datasync = boto3.client('datasync', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.region = region
    
    def create_gcs_location(self, bucket_name, access_key, secret_key):
        """Create DataSync location for Google Cloud Storage"""
        try:
            response = self.datasync.create_location_object_storage(
                ServerHostname='storage.googleapis.com',
                BucketName=bucket_name,
                AccessKey=access_key,
                SecretKey=secret_key,
                ServerProtocol='HTTPS',
                AgentArns=[
                    # You need to deploy DataSync agent first
                    'arn:aws:datasync:us-west-2:ACCOUNT:agent/agent-xxxxxxxxx'
                ],
                Tags=[
                    {'Key': 'Name', 'Value': f'gcs-{bucket_name}'},
                    {'Key': 'MigrationType', 'Value': 'GCS-to-S3'}
                ]
            )
            return response['LocationArn']
        except Exception as e:
            print(f"Error creating GCS location: {e}")
            return None
    
    def create_s3_location(self, bucket_name):
        """Create DataSync location for S3"""
        try:
            response = self.datasync.create_location_s3(
                S3BucketArn=f'arn:aws:s3:::{bucket_name}',
                S3Config={
                    'BucketAccessRoleArn': 'arn:aws:iam::ACCOUNT:role/DataSyncS3Role'
                },
                Tags=[
                    {'Key': 'Name', 'Value': f's3-{bucket_name}'},
                    {'Key': 'MigrationType', 'Value': 'GCS-to-S3'}
                ]
            )
            return response['LocationArn']
        except Exception as e:
            print(f"Error creating S3 location: {e}")
            return None
    
    def create_migration_task(self, source_arn, destination_arn, task_name):
        """Create DataSync migration task"""
        try:
            response = self.datasync.create_task(
                SourceLocationArn=source_arn,
                DestinationLocationArn=destination_arn,
                Name=task_name,
                Options={
                    'VerifyMode': 'POINT_IN_TIME_CONSISTENT',
                    'OverwriteMode': 'ALWAYS',
                    'Atime': 'BEST_EFFORT',
                    'Mtime': 'PRESERVE',
                    'Uid': 'NONE',
                    'Gid': 'NONE',
                    'PreserveDeletedFiles': 'PRESERVE',
                    'PreserveDevices': 'NONE',
                    'PosixPermissions': 'NONE',
                    'BytesPerSecond': -1,
                    'TaskQueueing': 'ENABLED'
                },
                Tags=[
                    {'Key': 'Name', 'Value': task_name},
                    {'Key': 'MigrationType', 'Value': 'GCS-to-S3'}
                ]
            )
            return response['TaskArn']
        except Exception as e:
            print(f"Error creating migration task: {e}")
            return None
    
    def start_migration_task(self, task_arn):
        """Start DataSync migration task"""
        try:
            response = self.datasync.start_task_execution(
                TaskArn=task_arn
            )
            return response['TaskExecutionArn']
        except Exception as e:
            print(f"Error starting migration task: {e}")
            return None
    
    def monitor_task_execution(self, execution_arn):
        """Monitor DataSync task execution"""
        try:
            response = self.datasync.describe_task_execution(
                TaskExecutionArn=execution_arn
            )
            return response
        except Exception as e:
            print(f"Error monitoring task execution: {e}")
            return None

# Usage example
if __name__ == "__main__":
    migrator = DataSyncMigrator()
    
    # Example migration
    gcs_bucket = "techmart-images"
    s3_bucket = "techmart-images-aws"
    
    # Create locations
    source_location = migrator.create_gcs_location(
        gcs_bucket, 
        "GCS_ACCESS_KEY", 
        "GCS_SECRET_KEY"
    )
    
    destination_location = migrator.create_s3_location(s3_bucket)
    
    if source_location and destination_location:
        # Create and start migration task
        task_arn = migrator.create_migration_task(
            source_location,
            destination_location,
            f"migrate-{gcs_bucket}-to-{s3_bucket}"
        )
        
        if task_arn:
            execution_arn = migrator.start_migration_task(task_arn)
            print(f"Migration started: {execution_arn}")
```

---

## Phase 3: Application Migration

### 1. Container Registry Migration

#### GCR to ECR Migration:
```bash
#!/bin/bash
# container-migration.sh

# Set variables
GCP_PROJECT="your-gcp-project"
AWS_ACCOUNT="123456789012"
AWS_REGION="us-west-2"
ECR_REGISTRY="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Starting container image migration from GCR to ECR..."

# Authenticate with both registries
gcloud auth configure-docker
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Get list of images from GCR
gcloud container images list --repository=gcr.io/$GCP_PROJECT --format="value(name)" > gcr-images.txt

while IFS= read -r image_name; do
    if [[ -n "$image_name" ]]; then
        # Extract image name without registry prefix
        clean_name=$(echo $image_name | sed "s|gcr.io/$GCP_PROJECT/||")
        
        echo "Processing image: $clean_name"
        
        # Create ECR repository
        aws ecr create-repository --repository-name $clean_name --region $AWS_REGION 2>/dev/null || echo "Repository $clean_name already exists"
        
        # Get all tags for this image
        gcloud container images list-tags $image_name --format="value(tags)" --filter="tags:*" > tags.tmp
        
        while IFS= read -r tags_line; do
            if [[ -n "$tags_line" ]]; then
                # Process each tag
                IFS=',' read -ra TAGS <<< "$tags_line"
                for tag in "${TAGS[@]}"; do
                    if [[ -n "$tag" ]]; then
                        echo "Migrating $clean_name:$tag"
                        
                        # Pull from GCR
                        docker pull $image_name:$tag
                        
                        # Tag for ECR
                        docker tag $image_name:$tag $ECR_REGISTRY/$clean_name:$tag
                        
                        # Push to ECR
                        docker push $ECR_REGISTRY/$clean_name:$tag
                        
                        # Clean up local images
                        docker rmi $image_name:$tag
                        docker rmi $ECR_REGISTRY/$clean_name:$tag
                    fi
                done
            fi
        done < tags.tmp
        
        rm -f tags.tmp
    fi
done < gcr-images.txt

rm -f gcr-images.txt
echo "Container migration completed!"
```

### 2. Kubernetes Workload Migration

#### Workload Analysis and Conversion:
```python
#!/usr/bin/env python3
# k8s-workload-migrator.py

import yaml
import json
import os
import re
from pathlib import Path

class KubernetesWorkloadMigrator:
    def __init__(self, gcp_project, aws_account, aws_region):
        self.gcp_project = gcp_project
        self.aws_account = aws_account
        self.aws_region = aws_region
        self.ecr_registry = f"{aws_account}.dkr.ecr.{aws_region}.amazonaws.com"
        
    def extract_gke_manifests(self, cluster_name, namespace=None):
        """Extract manifests from GKE cluster"""
        print(f"Extracting manifests from cluster: {cluster_name}")
        
        # Get cluster credentials
        os.system(f"gcloud container clusters get-credentials {cluster_name}")
        
        # Create output directory
        output_dir = Path(f"extracted-manifests/{cluster_name}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Resource types to extract
        resources = [
            'deployments', 'services', 'configmaps', 'secrets',
            'ingresses', 'persistentvolumeclaims', 'horizontalpodautoscalers'
        ]
        
        namespace_flag = f"-n {namespace}" if namespace else "--all-namespaces"
        
        for resource in resources:
            print(f"Extracting {resource}...")
            
            # Get resource YAML
            cmd = f"kubectl get {resource} {namespace_flag} -o yaml > {output_dir}/{resource}.yaml"
            os.system(cmd)
            
        print(f"Manifests extracted to {output_dir}")
        return output_dir
    
    def convert_manifest(self, manifest_file):
        """Convert GCP-specific configurations to AWS equivalents"""
        print(f"Converting manifest: {manifest_file}")
        
        with open(manifest_file, 'r') as f:
            docs = list(yaml.safe_load_all(f))
        
        converted_docs = []
        
        for doc in docs:
            if not doc or doc.get('kind') == 'List':
                continue
                
            converted_doc = self.convert_document(doc)
            if converted_doc:
                converted_docs.append(converted_doc)
        
        # Write converted manifests
        output_file = manifest_file.replace('.yaml', '-aws.yaml')
        with open(output_file, 'w') as f:
            yaml.dump_all(converted_docs, f, default_flow_style=False)
        
        print(f"Converted manifest saved: {output_file}")
        return output_file
    
    def convert_document(self, doc):
        """Convert individual Kubernetes document"""
        kind = doc.get('kind')
        
        if kind == 'Deployment':
            return self.convert_deployment(doc)
        elif kind == 'Service':
            return self.convert_service(doc)
        elif kind == 'Ingress':
            return self.convert_ingress(doc)
        elif kind == 'PersistentVolumeClaim':
            return self.convert_pvc(doc)
        else:
            return doc
    
    def convert_deployment(self, deployment):
        """Convert Deployment manifest"""
        # Update container images from GCR to ECR
        containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        
        for container in containers:
            image = container.get('image', '')
            if f'gcr.io/{self.gcp_project}' in image:
                # Convert GCR image to ECR
                image_name = image.split('/')[-1]
                container['image'] = f"{self.ecr_registry}/{image_name}"
        
        # Add AWS-specific annotations
        metadata = deployment.setdefault('metadata', {})
        annotations = metadata.setdefault('annotations', {})
        annotations['eks.amazonaws.com/compute-type'] = 'ec2'
        
        # Update resource requests/limits for AWS instance types
        self.update_resource_requirements(deployment)
        
        return deployment
    
    def convert_service(self, service):
        """Convert Service manifest"""
        spec = service.get('spec', {})
        
        # Convert GCP Load Balancer annotations to AWS ALB
        if spec.get('type') == 'LoadBalancer':
            metadata = service.setdefault('metadata', {})
            annotations = metadata.setdefault('annotations', {})
            
            # Remove GCP-specific annotations
            gcp_annotations = [k for k in annotations.keys() if 'cloud.google.com' in k]
            for ann in gcp_annotations:
                del annotations[ann]
            
            # Add AWS ALB annotations
            annotations.update({
                'service.beta.kubernetes.io/aws-load-balancer-type': 'nlb',
                'service.beta.kubernetes.io/aws-load-balancer-scheme': 'internet-facing',
                'service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled': 'true'
            })
        
        return service
    
    def convert_ingress(self, ingress):
        """Convert Ingress manifest to use AWS Load Balancer Controller"""
        metadata = ingress.setdefault('metadata', {})
        annotations = metadata.setdefault('annotations', {})
        
        # Remove GCP-specific annotations
        gcp_annotations = [k for k in annotations.keys() if 'cloud.google.com' in k or 'gce' in k]
        for ann in gcp_annotations:
            del annotations[ann]
        
        # Add AWS ALB annotations
        annotations.update({
            'kubernetes.io/ingress.class': 'alb',
            'alb.ingress.kubernetes.io/scheme': 'internet-facing',
            'alb.ingress.kubernetes.io/target-type': 'ip',
            'alb.ingress.kubernetes.io/healthcheck-path': '/health',
            'alb.ingress.kubernetes.io/listen-ports': '[{"HTTP": 80}, {"HTTPS": 443}]',
            'alb.ingress.kubernetes.io/ssl-redirect': '443'
        })
        
        return ingress
    
    def convert_pvc(self, pvc):
        """Convert PersistentVolumeClaim to use EBS"""
        spec = pvc.get('spec', {})
        
        # Update storage class from GCP to AWS
        storage_class = spec.get('storageClassName')
        if storage_class in ['standard', 'ssd']:
            spec['storageClassName'] = 'gp3'
        elif storage_class == 'standard-rwo':
            spec['storageClassName'] = 'gp3'
        
        # Add EBS-specific annotations
        metadata = pvc.setdefault('metadata', {})
        annotations = metadata.setdefault('annotations', {})
        annotations['volume.beta.kubernetes.io/storage-provisioner'] = 'ebs.csi.aws.com'
        
        return pvc
    
    def update_resource_requirements(self, deployment):
        """Update resource requirements for AWS instance types"""
        containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        
        for container in containers:
            resources = container.get('resources', {})
            requests = resources.get('requests', {})
            limits = resources.get('limits', {})
            
            # Adjust CPU requests (AWS uses different CPU allocation)
            if 'cpu' in requests:
                cpu_val = requests['cpu']
                if cpu_val.endswith('m'):
                    # Convert millicores, AWS typically needs slightly higher values
                    cpu_num = int(cpu_val[:-1])
                    requests['cpu'] = f"{max(100, int(cpu_num * 1.1))}m"
            
            # Adjust memory requests
            if 'memory' in requests:
                memory_val = requests['memory']
                # AWS instances have different memory configurations
                if memory_val.endswith('Mi'):
                    memory_num = int(memory_val[:-2])
                    requests['memory'] = f"{max(128, int(memory_num * 1.1))}Mi"
    
    def generate_kustomization(self, manifest_dir):
        """Generate Kustomization file for the converted manifests"""
        kustomization = {
            'apiVersion': 'kustomize.config.k8s.io/v1beta1',
            'kind': 'Kustomization',
            'resources': [],
            'commonLabels': {
                'migrated-from': 'gcp',
                'migration-tool': 'k8s-workload-migrator'
            },
            'images': []
        }
        
        # Find all converted YAML files
        for yaml_file in Path(manifest_dir).glob('*-aws.yaml'):
            kustomization['resources'].append(yaml_file.name)
        
        # Write kustomization.yaml
        kustomization_file = Path(manifest_dir) / 'kustomization.yaml'
        with open(kustomization_file, 'w') as f:
            yaml.dump(kustomization, f, default_flow_style=False)
        
        print(f"Kustomization file created: {kustomization_file}")
        return kustomization_file
    
    def migrate_cluster_workloads(self, cluster_name, namespace=None):
        """Complete migration process for a cluster"""
        print(f"Starting migration for cluster: {cluster_name}")
        
        # Step 1: Extract manifests
        manifest_dir = self.extract_gke_manifests(cluster_name, namespace)
        
        # Step 2: Convert manifests
        for yaml_file in manifest_dir.glob('*.yaml'):
            if yaml_file.name != 'kustomization.yaml':
                self.convert_manifest(yaml_file)
        
        # Step 3: Generate kustomization
        self.generate_kustomization(manifest_dir)
        
        # Step 4: Generate deployment script
        self.generate_deployment_script(manifest_dir, cluster_name)
        
        print(f"Migration completed for cluster: {cluster_name}")
        print(f"Converted manifests available in: {manifest_dir}")
    
    def generate_deployment_script(self, manifest_dir, cluster_name):
        """Generate deployment script for EKS"""
        script_content = f"""#!/bin/bash
# Deployment script for migrated workloads from {cluster_name}

set -e

echo "Deploying migrated workloads to EKS..."

# Ensure kubectl is configured for EKS
aws eks update-kubeconfig --region {self.aws_region} --name techmart-prod-eks

# Apply converted manifests
kubectl apply -k {manifest_dir}

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all

# Check pod status
echo "Pod status:"
kubectl get pods

echo "Deployment completed successfully!"
"""
        
        script_file = Path(manifest_dir) / 'deploy-to-eks.sh'
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_file, 0o755)
        
        print(f"Deployment script created: {script_file}")

# Usage example
if __name__ == "__main__":
    migrator = KubernetesWorkloadMigrator(
        gcp_project="your-gcp-project",
        aws_account="123456789012",
        aws_region="us-west-2"
    )
    
    # Migrate production cluster
    migrator.migrate_cluster_workloads("techmart-prod-gke", namespace="production")
    
    # Migrate staging cluster
    migrator.migrate_cluster_workloads("techmart-staging-gke", namespace="staging")
```

This comprehensive guide provides a detailed, step-by-step approach to migrating from GCP to AWS with real-world examples. The guide covers infrastructure planning, data migration, application migration, and includes practical scripts and tools for each phase.

Would you like me to continue with the remaining phases (Network & Security, Testing & Validation, Cutover & Go-Live, and Post-Migration Optimization)?