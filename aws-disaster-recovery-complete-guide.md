# AWS Disaster Recovery - Complete Implementation Guide

## Table of Contents
1. [DR Strategy Overview](#dr-strategy-overview)
2. [3-Tier Application DR (EC2 + ALB + RDS)](#3-tier-application-dr)
3. [EKS Workloads DR](#eks-workloads-dr)
4. [Cross-Region Implementation](#cross-region-implementation)
5. [Automation & Orchestration](#automation--orchestration)
6. [Testing & Validation](#testing--validation)
7. [Interview Scenarios](#interview-scenarios)

---

## DR Strategy Overview

### AWS DR Patterns (RTO/RPO Matrix)
```
┌─────────────────┬──────────────┬──────────────┬─────────────────┐
│   DR Pattern    │     RTO      │     RPO      │   Cost Impact   │
├─────────────────┼──────────────┼──────────────┼─────────────────┤
│ Backup/Restore  │ Hours-Days   │ Hours        │ Low ($)         │
│ Pilot Light     │ 10-30 mins   │ Minutes      │ Medium ($$)     │
│ Warm Standby    │ 5-10 mins    │ Seconds      │ High ($$$)      │
│ Multi-Site      │ < 1 min      │ Near Zero    │ Very High ($$$$)│
└─────────────────┴──────────────┴──────────────┴─────────────────┘
```

### Business Requirements Assessment
```yaml
# DR Requirements Template
business_requirements:
  rto_target: "15 minutes"        # Recovery Time Objective
  rpo_target: "5 minutes"         # Recovery Point Objective
  availability_target: "99.99%"   # 4.32 minutes downtime/month
  
critical_services:
  - user_authentication
  - payment_processing
  - order_management
  
non_critical_services:
  - analytics
  - reporting
  - batch_processing

compliance_requirements:
  - pci_dss
  - sox_compliance
  - gdpr_data_residency
```

---

## 3-Tier Application DR

### Architecture Overview
```
Primary Region (us-east-1)          DR Region (us-west-2)
┌─────────────────────────────┐    ┌─────────────────────────────┐
│  Route 53 (Health Checks)   │    │                             │
│           │                 │    │                             │
│  ┌─────────▼──────────┐     │    │  ┌─────────────────────┐    │
│  │   Application      │     │    │  │   Application       │    │
│  │   Load Balancer    │     │    │  │   Load Balancer     │    │
│  │                    │     │    │  │   (Standby)         │    │
│  └─────────┬──────────┘     │    │  └─────────┬─────────┘    │
│            │                │    │            │              │
│  ┌─────────▼──────────┐     │    │  ┌─────────▼─────────┐    │
│  │     Web Tier       │     │    │  │     Web Tier      │    │
│  │   (Auto Scaling)   │     │    │  │   (Min Capacity)  │    │
│  └─────────┬──────────┘     │    │  └─────────┬─────────┘    │
│            │                │    │            │              │
│  ┌─────────▼──────────┐     │    │  ┌─────────▼─────────┐    │
│  │    App Tier        │     │    │  │    App Tier       │    │
│  │   (Auto Scaling)   │     │    │  │   (Min Capacity)  │    │
│  └─────────┬──────────┘     │    │  └─────────┬─────────┘    │
│            │                │    │            │              │
│  ┌─────────▼──────────┐     │    │  ┌─────────▼─────────┐    │
│  │   RDS Primary      │────────────▶│   RDS Read         │    │
│  │   (Multi-AZ)       │     │    │  │   Replica          │    │
│  └────────────────────┘     │    │  └───────────────────┘    │
└─────────────────────────────┘    └─────────────────────────────┘
```

### 1. Database Layer DR (RDS)

#### Cross-Region Read Replica Setup:
```bash
# Create cross-region read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier "prod-db-replica-west" \
  --source-db-instance-identifier "arn:aws:rds:us-east-1:123456789012:db:prod-db-primary" \
  --db-instance-class "db.r6g.xlarge" \
  --publicly-accessible false \
  --auto-minor-version-upgrade false \
  --region us-west-2

# Enable automated backups on replica
aws rds modify-db-instance \
  --db-instance-identifier "prod-db-replica-west" \
  --backup-retention-period 7 \
  --apply-immediately \
  --region us-west-2
```

#### RDS Terraform Configuration:
```hcl
# Primary RDS in us-east-1
resource "aws_db_instance" "primary" {
  identifier = "prod-db-primary"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.xlarge"
  
  allocated_storage     = 500
  max_allocated_storage = 2000
  storage_encrypted     = true
  
  db_name  = "production"
  username = "dbadmin"
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
  
  vpc_security_group_ids = [aws_security_group.rds_primary.id]
  db_subnet_group_name   = aws_db_subnet_group.primary.name
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  multi_az               = true
  publicly_accessible    = false
  
  # Enable automated backups for cross-region replica
  copy_tags_to_snapshot = true
  
  tags = {
    Name        = "Production Primary DB"
    Environment = "production"
    DR_Role     = "primary"
  }
}

# Cross-region read replica in us-west-2
resource "aws_db_instance" "replica" {
  provider = aws.west
  
  identifier = "prod-db-replica-west"
  
  # Source from primary region
  replicate_source_db = aws_db_instance.primary.arn
  
  instance_class = "db.r6g.xlarge"
  
  vpc_security_group_ids = [aws_security_group.rds_replica.id]
  
  backup_retention_period = 7
  
  # Can be promoted to standalone
  auto_minor_version_upgrade = false
  
  tags = {
    Name        = "Production DR Replica"
    Environment = "production"
    DR_Role     = "replica"
  }
}
```

### 2. Application Layer DR (EC2 Auto Scaling)

#### Launch Template for DR Region:
```hcl
# Launch template for DR region
resource "aws_launch_template" "app_dr" {
  provider = aws.west
  
  name_prefix   = "prod-app-dr-"
  image_id      = data.aws_ami.app_ami_west.id
  instance_type = "m5.large"
  
  vpc_security_group_ids = [aws_security_group.app_dr.id]
  
  iam_instance_profile {
    name = aws_iam_instance_profile.app_dr.name
  }
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    region           = "us-west-2"
    environment      = "production-dr"
    db_endpoint      = aws_db_instance.replica.endpoint
    s3_bucket        = aws_s3_bucket.app_assets_dr.bucket
    parameter_prefix = "/production-dr"
  }))
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "Production DR App Server"
      Environment = "production-dr"
      DR_Role     = "standby"
    }
  }
}

# Auto Scaling Group (minimal capacity)
resource "aws_autoscaling_group" "app_dr" {
  provider = aws.west
  
  name                = "prod-app-dr-asg"
  vpc_zone_identifier = aws_subnet.private_dr[*].id
  
  target_group_arns = [aws_lb_target_group.app_dr.arn]
  health_check_type = "ELB"
  
  min_size         = 0  # Pilot light - no running instances
  max_size         = 10
  desired_capacity = 0
  
  launch_template {
    id      = aws_launch_template.app_dr.id
    version = "$Latest"
  }
  
  tag {
    key                 = "Name"
    value               = "Production DR ASG"
    propagate_at_launch = false
  }
}
```

### 3. Load Balancer DR Configuration:

```hcl
# Application Load Balancer in DR region
resource "aws_lb" "app_dr" {
  provider = aws.west
  
  name               = "prod-app-dr-alb"
  internal           = false
  load_balancer_type = "application"
  
  security_groups = [aws_security_group.alb_dr.id]
  subnets         = aws_subnet.public_dr[*].id
  
  enable_deletion_protection = false
  
  tags = {
    Name        = "Production DR ALB"
    Environment = "production-dr"
    DR_Role     = "standby"
  }
}

# Target group for DR
resource "aws_lb_target_group" "app_dr" {
  provider = aws.west
  
  name     = "prod-app-dr-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.dr.id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  tags = {
    Name        = "Production DR Target Group"
    Environment = "production-dr"
  }
}

# Listener for DR ALB
resource "aws_lb_listener" "app_dr" {
  provider = aws.west
  
  load_balancer_arn = aws_lb.app_dr.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.app_dr.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_dr.arn
  }
}
```

### 4. Route 53 Health Checks & Failover:

```hcl
# Health check for primary region
resource "aws_route53_health_check" "primary" {
  fqdn                            = aws_lb.app_primary.dns_name
  port                            = 443
  type                            = "HTTPS"
  resource_path                   = "/health"
  failure_threshold               = "3"
  request_interval                = "30"
  cloudwatch_alarm_region         = "us-east-1"
  cloudwatch_alarm_name           = "ALB-HealthCheck-Failed"
  insufficient_data_health_status = "Failure"
  
  tags = {
    Name = "Primary Region Health Check"
  }
}

# DNS records with failover routing
resource "aws_route53_record" "primary" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "app.company.com"
  type    = "A"
  
  set_identifier = "primary"
  
  failover_routing_policy {
    type = "PRIMARY"
  }
  
  health_check_id = aws_route53_health_check.primary.id
  
  alias {
    name                   = aws_lb.app_primary.dns_name
    zone_id                = aws_lb.app_primary.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "secondary" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "app.company.com"
  type    = "A"
  
  set_identifier = "secondary"
  
  failover_routing_policy {
    type = "SECONDARY"
  }
  
  alias {
    name                   = aws_lb.app_dr.dns_name
    zone_id                = aws_lb.app_dr.zone_id
    evaluate_target_health = true
  }
}
```

---

## EKS Workloads DR

### Architecture Overview
```
Primary Region (us-east-1)          DR Region (us-west-2)
┌─────────────────────────────┐    ┌─────────────────────────────┐
│     EKS Cluster             │    │     EKS Cluster             │
│  ┌─────────────────────┐    │    │  ┌─────────────────────┐    │
│  │   Control Plane     │    │    │  │   Control Plane     │    │
│  │   (Managed by AWS)  │    │    │  │   (Managed by AWS)  │    │
│  └─────────────────────┘    │    │  └─────────────────────┘    │
│                             │    │                             │
│  ┌─────────────────────┐    │    │  ┌─────────────────────┐    │
│  │   Worker Nodes      │    │    │  │   Worker Nodes      │    │
│  │   ┌─────────────┐   │    │    │  │   ┌─────────────┐   │    │
│  │   │ Application │   │    │    │  │   │ Application │   │    │
│  │   │   Pods      │   │    │    │  │   │   Pods      │   │    │
│  │   └─────────────┘   │    │    │  │   └─────────────┘   │    │
│  │   ┌─────────────┐   │    │    │  │   ┌─────────────┐   │    │
│  │   │   Storage   │   │    │    │  │   │   Storage   │   │    │
│  │   │    (EBS)    │   │    │    │  │   │    (EBS)    │   │    │
│  │   └─────────────┘   │    │    │  │   └─────────────┘   │    │
│  └─────────────────────┘    │    │  └─────────────────────┘    │
│                             │    │                             │
│  ┌─────────────────────┐    │    │  ┌─────────────────────┐    │
│  │   RDS Primary       │────────────▶│   RDS Replica       │    │
│  └─────────────────────┘    │    │  └─────────────────────┘    │
│                             │    │                             │
│  ┌─────────────────────┐    │    │  ┌─────────────────────┐    │
│  │   S3 Bucket         │────────────▶│   S3 Bucket         │    │
│  │ (Cross-Region Repl) │    │    │  │   (Replica)         │    │
│  └─────────────────────┘    │    │  └─────────────────────┘    │
└─────────────────────────────┘    └─────────────────────────────┘
```

### 1. EKS Cluster DR Setup:

#### Primary EKS Cluster:
```hcl
# Primary EKS cluster
module "eks_primary" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "production-primary"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc_primary.vpc_id
  subnet_ids = module.vpc_primary.private_subnets
  
  # Enable cluster logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  
  # Node groups
  eks_managed_node_groups = {
    general = {
      desired_size = 6
      max_size     = 20
      min_size     = 3
      
      instance_types = ["m5.xlarge"]
      capacity_type  = "ON_DEMAND"
      
      k8s_labels = {
        Environment = "production"
        NodeGroup   = "general"
      }
    }
  }
  
  # Enable IRSA
  enable_irsa = true
  
  # Cluster security group additional rules
  cluster_security_group_additional_rules = {
    egress_nodes_ephemeral_ports_tcp = {
      description                = "To node 1025-65535"
      protocol                   = "tcp"
      from_port                  = 1025
      to_port                    = 65535
      type                       = "egress"
      source_node_security_group = true
    }
  }
  
  tags = {
    Environment = "production"
    DR_Role     = "primary"
  }
}

# DR EKS cluster
module "eks_dr" {
  source = "terraform-aws-modules/eks/aws"
  
  providers = {
    aws = aws.west
  }
  
  cluster_name    = "production-dr"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc_dr.vpc_id
  subnet_ids = module.vpc_dr.private_subnets
  
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  
  eks_managed_node_groups = {
    general = {
      desired_size = 0  # Pilot light - no running nodes initially
      max_size     = 20
      min_size     = 0
      
      instance_types = ["m5.xlarge"]
      capacity_type  = "ON_DEMAND"
      
      k8s_labels = {
        Environment = "production-dr"
        NodeGroup   = "general"
      }
    }
  }
  
  enable_irsa = true
  
  tags = {
    Environment = "production-dr"
    DR_Role     = "standby"
  }
}
```

### 2. Container Registry Replication:

#### ECR Cross-Region Replication:
```hcl
# ECR repository with cross-region replication
resource "aws_ecr_repository" "app" {
  name                 = "production-app"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Environment = "production"
  }
}

# Cross-region replication configuration
resource "aws_ecr_replication_configuration" "main" {
  replication_configuration {
    rule {
      destination {
        region      = "us-west-2"
        registry_id = data.aws_caller_identity.current.account_id
      }
      
      repository_filter {
        filter      = "production-*"
        filter_type = "PREFIX_MATCH"
      }
    }
  }
}

# ECR repository in DR region
resource "aws_ecr_repository" "app_dr" {
  provider = aws.west
  
  name                 = "production-app"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Environment = "production-dr"
  }
}
```

### 3. Kubernetes Manifests for DR:

#### Application Deployment with Multi-Region Support:
```yaml
# k8s/production/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: production
  labels:
    app: web-app
    version: v1.0.0
spec:
  replicas: 6
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
        version: v1.0.0
    spec:
      serviceAccountName: web-app-sa
      containers:
      - name: web-app
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/production-app:v1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: AWS_REGION
          valueFrom:
            fieldRef:
              fieldPath: metadata.annotations['eks.amazonaws.com/region']
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: app-data
          mountPath: /data
      volumes:
      - name: app-data
        persistentVolumeClaim:
          claimName: app-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-service
  namespace: production
spec:
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - app.company.com
    secretName: app-tls
  rules:
  - host: app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app-service
            port:
              number: 80
```

#### Persistent Volume Backup Strategy:
```yaml
# k8s/production/storage.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data-pvc
  namespace: production
  annotations:
    volume.beta.kubernetes.io/storage-class: gp3
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: gp3
---
# Velero backup schedule
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: production-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  template:
    includedNamespaces:
    - production
    storageLocation: aws-s3
    volumeSnapshotLocations:
    - aws-ebs
    ttl: 720h0m0s  # 30 days retention
```

### 4. EKS Add-ons for DR:

#### Velero for Backup and Restore:
```bash
# Install Velero in both regions
# Primary region
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts/
helm install velero vmware-tanzu/velero \
  --namespace velero \
  --create-namespace \
  --set-file credentials.secretContents.cloud=./velero-credentials \
  --set configuration.provider=aws \
  --set configuration.backupStorageLocation.bucket=production-velero-backups \
  --set configuration.backupStorageLocation.config.region=us-east-1 \
  --set configuration.volumeSnapshotLocation.config.region=us-east-1 \
  --set initContainers[0].name=velero-plugin-for-aws \
  --set initContainers[0].image=velero/velero-plugin-for-aws:v1.8.0 \
  --set initContainers[0].volumeMounts[0].mountPath=/target \
  --set initContainers[0].volumeMounts[0].name=plugins

# DR region
helm install velero vmware-tanzu/velero \
  --namespace velero \
  --create-namespace \
  --set-file credentials.secretContents.cloud=./velero-credentials \
  --set configuration.provider=aws \
  --set configuration.backupStorageLocation.bucket=production-velero-backups \
  --set configuration.backupStorageLocation.config.region=us-west-2 \
  --set configuration.volumeSnapshotLocation.config.region=us-west-2 \
  --set configuration.restoreOnlyMode=true
```

#### External DNS for Multi-Region:
```yaml
# k8s/external-dns/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: external-dns
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: external-dns
  template:
    metadata:
      labels:
        app: external-dns
    spec:
      serviceAccountName: external-dns
      containers:
      - name: external-dns
        image: k8s.gcr.io/external-dns/external-dns:v0.13.6
        args:
        - --source=service
        - --source=ingress
        - --domain-filter=company.com
        - --provider=aws
        - --policy=sync
        - --aws-zone-type=public
        - --registry=txt
        - --txt-owner-id=production-cluster
        - --txt-prefix=external-dns-
        env:
        - name: AWS_DEFAULT_REGION
          value: us-east-1
```

---

## Cross-Region Implementation

### 1. Data Synchronization Strategy:

#### S3 Cross-Region Replication:
```hcl
# S3 bucket replication configuration
resource "aws_s3_bucket" "primary" {
  bucket = "production-app-data-primary"
  
  tags = {
    Environment = "production"
    DR_Role     = "primary"
  }
}

resource "aws_s3_bucket_versioning" "primary" {
  bucket = aws_s3_bucket.primary.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_replication_configuration" "primary" {
  role   = aws_iam_role.s3_replication.arn
  bucket = aws_s3_bucket.primary.id
  
  rule {
    id     = "replicate-to-dr"
    status = "Enabled"
    
    destination {
      bucket        = aws_s3_bucket.dr.arn
      storage_class = "STANDARD_IA"
      
      # Encryption in destination
      encryption_configuration {
        replica_kms_key_id = aws_kms_key.s3_dr.arn
      }
    }
  }
  
  depends_on = [aws_s3_bucket_versioning.primary]
}

# DR region bucket
resource "aws_s3_bucket" "dr" {
  provider = aws.west
  
  bucket = "production-app-data-dr"
  
  tags = {
    Environment = "production-dr"
    DR_Role     = "replica"
  }
}
```

### 2. Network Connectivity:

#### VPC Peering for Cross-Region:
```hcl
# VPC Peering connection
resource "aws_vpc_peering_connection" "primary_to_dr" {
  vpc_id        = module.vpc_primary.vpc_id
  peer_vpc_id   = module.vpc_dr.vpc_id
  peer_region   = "us-west-2"
  auto_accept   = false
  
  tags = {
    Name = "Primary to DR VPC Peering"
  }
}

# Accept peering connection in DR region
resource "aws_vpc_peering_connection_accepter" "dr" {
  provider = aws.west
  
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_dr.id
  auto_accept               = true
  
  tags = {
    Name = "DR VPC Peering Accepter"
  }
}

# Route table entries for peering
resource "aws_route" "primary_to_dr" {
  count = length(module.vpc_primary.private_route_table_ids)
  
  route_table_id            = module.vpc_primary.private_route_table_ids[count.index]
  destination_cidr_block    = module.vpc_dr.vpc_cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_dr.id
}

resource "aws_route" "dr_to_primary" {
  provider = aws.west
  count    = length(module.vpc_dr.private_route_table_ids)
  
  route_table_id            = module.vpc_dr.private_route_table_ids[count.index]
  destination_cidr_block    = module.vpc_primary.vpc_cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_dr.id
}
```

---

## Automation & Orchestration

### 1. DR Failover Automation:

#### Lambda Function for Automated Failover:
```python
# lambda/dr_failover.py
import boto3
import json
import os
from datetime import datetime

def lambda_handler(event, context):
    """
    Automated DR failover orchestration
    """
    
    # Initialize AWS clients
    route53 = boto3.client('route53')
    rds = boto3.client('rds', region_name='us-west-2')
    autoscaling = boto3.client('autoscaling', region_name='us-west-2')
    eks = boto3.client('eks', region_name='us-west-2')
    
    try:
        # Step 1: Promote RDS read replica
        print("Promoting RDS read replica to primary...")
        rds.promote_read_replica(
            DBInstanceIdentifier='prod-db-replica-west'
        )
        
        # Wait for promotion to complete
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(
            DBInstanceIdentifier='prod-db-replica-west',
            WaiterConfig={'Delay': 30, 'MaxAttempts': 20}
        )
        
        # Step 2: Scale up Auto Scaling Groups
        print("Scaling up Auto Scaling Groups...")
        autoscaling.update_auto_scaling_group(
            AutoScalingGroupName='prod-app-dr-asg',
            DesiredCapacity=6,
            MinSize=3
        )
        
        # Step 3: Scale EKS node groups
        print("Scaling EKS node groups...")
        eks.update_nodegroup_config(
            clusterName='production-dr',
            nodegroupName='general',
            scalingConfig={
                'minSize': 3,
                'maxSize': 20,
                'desiredSize': 6
            }
        )
        
        # Step 4: Update Route 53 DNS records
        print("Updating Route 53 DNS records...")
        
        # Get hosted zone ID
        hosted_zones = route53.list_hosted_zones_by_name(
            DNSName='company.com'
        )
        zone_id = hosted_zones['HostedZones'][0]['Id'].split('/')[-1]
        
        # Update DNS to point to DR region
        route53.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Comment': f'DR Failover - {datetime.now().isoformat()}',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': 'app.company.com',
                            'Type': 'A',
                            'SetIdentifier': 'primary',
                            'Failover': {'Type': 'PRIMARY'},
                            'AliasTarget': {
                                'DNSName': os.environ['DR_ALB_DNS_NAME'],
                                'EvaluateTargetHealth': True,
                                'HostedZoneId': os.environ['DR_ALB_ZONE_ID']
                            }
                        }
                    }
                ]
            }
        )
        
        # Step 5: Send notifications
        sns = boto3.client('sns')
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Subject='DR Failover Completed',
            Message=f'''
            DR Failover has been completed successfully.
            
            Actions taken:
            1. RDS read replica promoted to primary
            2. Auto Scaling Groups scaled up
            3. EKS node groups scaled up
            4. DNS records updated to DR region
            
            Timestamp: {datetime.now().isoformat()}
            '''
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'DR failover completed successfully',
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error during DR failover: {str(e)}")
        
        # Send error notification
        sns = boto3.client('sns')
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Subject='DR Failover Failed',
            Message=f'DR Failover failed with error: {str(e)}'
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }
```

#### CloudWatch Alarms for Automatic Triggering:
```hcl
# CloudWatch alarm for primary region health
resource "aws_cloudwatch_metric_alarm" "primary_region_health" {
  alarm_name          = "primary-region-health-check"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "This metric monitors primary region health"
  alarm_actions       = [aws_sns_topic.dr_alerts.arn]
  
  dimensions = {
    HealthCheckId = aws_route53_health_check.primary.id
  }
  
  tags = {
    Environment = "production"
    Purpose     = "dr-monitoring"
  }
}

# Lambda function for DR orchestration
resource "aws_lambda_function" "dr_failover" {
  filename         = "dr_failover.zip"
  function_name    = "production-dr-failover"
  role            = aws_iam_role.lambda_dr.arn
  handler         = "dr_failover.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900  # 15 minutes
  
  environment {
    variables = {
      DR_ALB_DNS_NAME = aws_lb.app_dr.dns_name
      DR_ALB_ZONE_ID  = aws_lb.app_dr.zone_id
      SNS_TOPIC_ARN   = aws_sns_topic.dr_alerts.arn
    }
  }
  
  tags = {
    Environment = "production"
    Purpose     = "dr-automation"
  }
}

# SNS topic for DR alerts
resource "aws_sns_topic" "dr_alerts" {
  name = "production-dr-alerts"
  
  tags = {
    Environment = "production"
    Purpose     = "dr-notifications"
  }
}
```

### 2. EKS DR Automation Script:

```bash
#!/bin/bash
# scripts/eks-dr-failover.sh

set -e

DR_REGION="us-west-2"
DR_CLUSTER="production-dr"
PRIMARY_REGION="us-east-1"
PRIMARY_CLUSTER="production-primary"

echo "Starting EKS DR failover process..."

# Step 1: Scale up DR cluster node groups
echo "Scaling up DR cluster node groups..."
aws eks update-nodegroup-config \
  --cluster-name "$DR_CLUSTER" \
  --nodegroup-name "general" \
  --scaling-config minSize=3,maxSize=20,desiredSize=6 \
  --region "$DR_REGION"

# Wait for nodes to be ready
echo "Waiting for nodes to be ready..."
kubectl config use-context "arn:aws:eks:${DR_REGION}:$(aws sts get-caller-identity --query Account --output text):cluster/${DR_CLUSTER}"

# Wait for nodes
kubectl wait --for=condition=Ready nodes --all --timeout=600s

# Step 2: Restore from Velero backup
echo "Restoring applications from Velero backup..."

# Get latest backup
LATEST_BACKUP=$(velero backup get --output json | jq -r '.items | sort_by(.metadata.creationTimestamp) | last | .metadata.name')

echo "Restoring from backup: $LATEST_BACKUP"
velero restore create "dr-restore-$(date +%Y%m%d-%H%M%S)" \
  --from-backup "$LATEST_BACKUP" \
  --wait

# Step 3: Update database connections
echo "Updating database connections..."
kubectl patch secret db-credentials \
  -p '{"data":{"host":"'$(echo -n "prod-db-replica-west.region.rds.amazonaws.com" | base64)'"}}' \
  -n production

# Step 4: Restart deployments to pick up new DB connection
echo "Restarting deployments..."
kubectl rollout restart deployment/web-app -n production
kubectl rollout status deployment/web-app -n production --timeout=300s

# Step 5: Verify application health
echo "Verifying application health..."
sleep 30

# Get ingress URL
INGRESS_URL=$(kubectl get ingress web-app-ingress -n production -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Health check
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$INGRESS_URL/health")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ DR failover completed successfully!"
    echo "Application is healthy at: https://$INGRESS_URL"
else
    echo "❌ Health check failed (HTTP $HTTP_STATUS)"
    exit 1
fi

# Step 6: Send notification
aws sns publish \
  --topic-arn "arn:aws:sns:${DR_REGION}:$(aws sts get-caller-identity --query Account --output text):production-dr-alerts" \
  --subject "EKS DR Failover Completed" \
  --message "EKS DR failover completed successfully. Application is running in $DR_REGION region." \
  --region "$DR_REGION"

echo "DR failover process completed!"
```

---

## Testing & Validation

### 1. DR Testing Framework:

#### Automated DR Testing Script:
```bash
#!/bin/bash
# scripts/dr-test.sh

set -e

TEST_TYPE=${1:-"pilot-light"}  # pilot-light, warm-standby, full-failover
ENVIRONMENT=${2:-"staging"}

echo "Starting DR test: $TEST_TYPE for $ENVIRONMENT environment"

# Test configuration
case $TEST_TYPE in
  "pilot-light")
    RTO_TARGET=1800  # 30 minutes
    RPO_TARGET=300   # 5 minutes
    ;;
  "warm-standby")
    RTO_TARGET=600   # 10 minutes
    RPO_TARGET=60    # 1 minute
    ;;
  "full-failover")
    RTO_TARGET=60    # 1 minute
    RPO_TARGET=5     # 5 seconds
    ;;
esac

# Start timing
START_TIME=$(date +%s)

echo "Test started at: $(date)"
echo "RTO Target: $RTO_TARGET seconds"
echo "RPO Target: $RPO_TARGET seconds"

# Step 1: Simulate primary region failure
echo "Simulating primary region failure..."
if [ "$ENVIRONMENT" = "staging" ]; then
    # For staging, actually stop services
    aws autoscaling update-auto-scaling-group \
      --auto-scaling-group-name "staging-app-asg" \
      --desired-capacity 0 \
      --region us-east-1
else
    echo "Production test - using Route 53 health check manipulation"
    # Manipulate health check for production testing
fi

# Step 2: Trigger DR failover
echo "Triggering DR failover..."
case $TEST_TYPE in
  "pilot-light")
    ./scripts/pilot-light-failover.sh "$ENVIRONMENT"
    ;;
  "warm-standby")
    ./scripts/warm-standby-failover.sh "$ENVIRONMENT"
    ;;
  "full-failover")
    ./scripts/full-failover.sh "$ENVIRONMENT"
    ;;
esac

# Step 3: Validate application availability
echo "Validating application availability..."
DR_URL="https://app-dr.company.com"

# Wait for DNS propagation
sleep 60

# Health check loop
HEALTH_CHECK_START=$(date +%s)
while true; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DR_URL/health" || echo "000")
    
    if [ "$HTTP_STATUS" = "200" ]; then
        RECOVERY_TIME=$(($(date +%s) - START_TIME))
        echo "✅ Application recovered in $RECOVERY_TIME seconds"
        break
    fi
    
    CURRENT_TIME=$(date +%s)
    if [ $((CURRENT_TIME - START_TIME)) -gt $RTO_TARGET ]; then
        echo "❌ RTO target exceeded ($RTO_TARGET seconds)"
        exit 1
    fi
    
    echo "Waiting for application recovery... (${HTTP_STATUS})"
    sleep 10
done

# Step 4: Validate data consistency
echo "Validating data consistency..."
LAST_BACKUP_TIME=$(aws rds describe-db-instances \
  --db-instance-identifier "staging-db-replica-west" \
  --query 'DBInstances[0].LatestRestorableTime' \
  --output text \
  --region us-west-2)

# Calculate RPO
BACKUP_TIMESTAMP=$(date -d "$LAST_BACKUP_TIME" +%s)
FAILURE_TIMESTAMP=$START_TIME
RPO_ACTUAL=$((FAILURE_TIMESTAMP - BACKUP_TIMESTAMP))

echo "Actual RPO: $RPO_ACTUAL seconds"

if [ $RPO_ACTUAL -le $RPO_TARGET ]; then
    echo "✅ RPO target met"
else
    echo "❌ RPO target exceeded"
fi

# Step 5: Generate test report
cat > "dr-test-report-$(date +%Y%m%d-%H%M%S).json" << EOF
{
  "test_type": "$TEST_TYPE",
  "environment": "$ENVIRONMENT",
  "start_time": "$(date -d @$START_TIME)",
  "recovery_time_seconds": $RECOVERY_TIME,
  "rto_target_seconds": $RTO_TARGET,
  "rto_met": $([ $RECOVERY_TIME -le $RTO_TARGET ] && echo "true" || echo "false"),
  "rpo_actual_seconds": $RPO_ACTUAL,
  "rpo_target_seconds": $RPO_TARGET,
  "rpo_met": $([ $RPO_ACTUAL -le $RPO_TARGET ] && echo "true" || echo "false"),
  "test_status": "$([ $RECOVERY_TIME -le $RTO_TARGET ] && [ $RPO_ACTUAL -le $RPO_TARGET ] && echo "PASSED" || echo "FAILED")"
}
EOF

echo "DR test completed. Report generated."

# Step 6: Cleanup (restore primary)
if [ "$ENVIRONMENT" = "staging" ]; then
    echo "Restoring primary region..."
    aws autoscaling update-auto-scaling-group \
      --auto-scaling-group-name "staging-app-asg" \
      --desired-capacity 3 \
      --region us-east-1
fi

echo "DR test finished successfully!"
```

### 2. Monitoring and Alerting:

#### CloudWatch Dashboard for DR Metrics:
```hcl
# CloudWatch dashboard for DR monitoring
resource "aws_cloudwatch_dashboard" "dr_monitoring" {
  dashboard_name = "Production-DR-Monitoring"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/Route53", "HealthCheckStatus", "HealthCheckId", aws_route53_health_check.primary.id],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.app_primary.arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", "LoadBalancer", aws_lb.app_primary.arn_suffix]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "Primary Region Health"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "prod-db-primary"],
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "prod-db-primary"],
            ["AWS/RDS", "ReplicaLag", "DBInstanceIdentifier", "prod-db-replica-west"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "Database Metrics"
          period  = 300
        }
      }
    ]
  })
}
```

---

## Interview Scenarios

### 1. Common DR Interview Questions & Answers:

#### Q: "How would you design DR for a 3-tier application with RTO of 15 minutes and RPO of 5 minutes?"

**Answer:**
"For RTO of 15 minutes and RPO of 5 minutes, I'd implement a **Pilot Light** strategy:

**Database Layer:**
- RDS Multi-AZ in primary region for HA
- Cross-region read replica with 5-minute replication lag
- Automated backups every 5 minutes using snapshots

**Application Layer:**
- Minimal EC2 instances in DR region (pilot light)
- Auto Scaling Groups with desired capacity = 0
- Pre-configured Launch Templates with latest AMIs
- Application Load Balancer pre-deployed but not receiving traffic

**DNS & Routing:**
- Route 53 health checks on primary region
- Failover routing policy with 60-second TTL
- Automated DNS switching via Lambda

**Automation:**
- CloudWatch alarms trigger Lambda function
- Lambda promotes read replica and scales ASGs
- Estimated failover time: 10-12 minutes
- Achieved RPO: 3-5 minutes through read replica

**Cost Impact:** ~30% of primary region cost for standby resources"

#### Q: "What's your approach for EKS workloads DR with stateful applications?"

**Answer:**
"For EKS DR with stateful workloads, I use a multi-layered approach:

**Cluster Level:**
- Identical EKS clusters in primary and DR regions
- Cross-region ECR replication for container images
- GitOps deployment with ArgoCD for consistency

**Stateful Data:**
- **Persistent Volumes:** Velero for backup/restore with EBS snapshots
- **Databases:** RDS cross-region replicas or external managed services
- **Configuration:** External Secrets Operator with AWS Secrets Manager

**Application Level:**
- **Deployment Strategy:** Blue-green with traffic shifting
- **Service Mesh:** Istio for traffic management and observability
- **Monitoring:** Prometheus federation across regions

**Automation:**
- Velero scheduled backups every 4 hours
- Automated cluster scaling via Cluster Autoscaler
- Custom operators for application-specific recovery

**Recovery Process:**
1. Scale DR cluster nodes (2-3 minutes)
2. Restore Velero backup (5-8 minutes)
3. Promote database replicas (3-5 minutes)
4. Update DNS routing (1-2 minutes)

**Total RTO:** 12-15 minutes for complete recovery"

#### Q: "How do you test DR without impacting production?"

**Answer:**
"I implement a comprehensive DR testing strategy:

**Non-Disruptive Testing:**
- **Staging Environment:** Full DR tests monthly
- **Production Validation:** Read-only tests quarterly
- **Component Testing:** Individual service failover weekly

**Testing Framework:**
```bash
# Automated test execution
./dr-test.sh pilot-light staging
./dr-test.sh warm-standby staging  
./dr-test.sh full-failover staging
```

**Validation Methods:**
- **Database:** Test read replica promotion in staging
- **Application:** Blue-green deployment validation
- **Network:** VPC peering and routing verification
- **DNS:** Route 53 health check simulation

**Metrics Tracking:**
- RTO measurement: Target vs Actual
- RPO validation: Data loss assessment  
- Success rate: 99.5% target achievement
- Cost analysis: DR vs production spend ratio

**Production Safety:**
- Route 53 weighted routing for gradual testing
- Feature flags for controlled rollback
- Monitoring dashboards for real-time validation
- Automated rollback on failure detection

**Results Achieved:**
- 15-minute RTO consistently met
- Zero data loss in 24 months
- 99.9% DR test success rate"

### 2. Troubleshooting Scenarios:

#### Scenario: "RDS read replica is lagging behind primary by 2 hours"

**Solution:**
```bash
# Check replica lag
aws rds describe-db-instances \
  --db-instance-identifier prod-db-replica-west \
  --query 'DBInstances[0].StatusInfos' \
  --region us-west-2

# Identify bottlenecks
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ReplicaLag \
  --dimensions Name=DBInstanceIdentifier,Value=prod-db-replica-west \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum

# Resolution steps:
# 1. Scale up replica instance class
# 2. Optimize primary database queries
# 3. Reduce transaction log size
# 4. Consider Multi-AZ read replica
```

This comprehensive guide provides everything needed to confidently discuss DR strategies in senior cloud engineer interviews, with practical implementations and quantified results.