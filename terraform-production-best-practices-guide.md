# Terraform Production Best Practices - Complete Interview Guide

## Table of Contents
1. [Production Folder Structure](#production-folder-structure)
2. [Multi-Environment Strategy](#multi-environment-strategy)
3. [State Management](#state-management)
4. [Module Design Patterns](#module-design-patterns)
5. [Security Best Practices](#security-best-practices)
6. [Rollout Strategies](#rollout-strategies)
7. [Real-World Implementation](#real-world-implementation)
8. [Interview Scenarios](#interview-scenarios)

---

## Production Folder Structure

### Enterprise-Grade Structure (Recommended)
```
terraform-infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── terraform.tfvars
│       └── backend.tf
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   ├── eks/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── data.tf
│   │   └── README.md
│   ├── rds/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   └── security-groups/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
├── shared/
│   ├── global/
│   │   ├── iam/
│   │   ├── route53/
│   │   └── cloudtrail/
│   └── common/
│       ├── locals.tf
│       ├── data.tf
│       └── versions.tf
├── scripts/
│   ├── deploy.sh
│   ├── validate.sh
│   └── rollback.sh
├── .github/
│   └── workflows/
│       ├── terraform-plan.yml
│       ├── terraform-apply.yml
│       └── terraform-destroy.yml
├── docs/
│   ├── architecture.md
│   ├── runbooks/
│   └── troubleshooting.md
├── .gitignore
├── .terraform-version
├── .pre-commit-config.yaml
└── README.md
```

### Alternative: Workspace-Based Structure
```
terraform-infrastructure/
├── main.tf
├── variables.tf
├── outputs.tf
├── locals.tf
├── data.tf
├── versions.tf
├── environments/
│   ├── dev.tfvars
│   ├── staging.tfvars
│   └── production.tfvars
├── modules/
│   └── [same as above]
└── backend-configs/
    ├── dev.hcl
    ├── staging.hcl
    └── production.hcl
```

---

## Multi-Environment Strategy

### 1. Environment-Specific Configuration

#### Production Environment Example:
```hcl
# environments/production/main.tf
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "company-terraform-state-prod"
    key            = "production/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock-prod"
    
    assume_role = {
      role_arn = "arn:aws:iam::PROD_ACCOUNT:role/TerraformRole"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  assume_role {
    role_arn = "arn:aws:iam::${var.aws_account_id}:role/TerraformRole"
  }
  
  default_tags {
    tags = local.common_tags
  }
}

locals {
  environment = "production"
  common_tags = {
    Environment   = local.environment
    Project       = var.project_name
    Owner         = var.team_name
    CostCenter    = var.cost_center
    ManagedBy     = "terraform"
    LastModified  = timestamp()
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"
  
  environment         = local.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  
  enable_nat_gateway     = true
  enable_vpn_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true
  
  tags = local.common_tags
}

# EKS Module
module "eks" {
  source = "../../modules/eks"
  
  environment    = local.environment
  cluster_name   = "${var.project_name}-${local.environment}"
  cluster_version = var.eks_cluster_version
  
  vpc_id         = module.vpc.vpc_id
  subnet_ids     = module.vpc.private_subnet_ids
  
  node_groups = var.eks_node_groups
  
  enable_irsa                    = true
  enable_cluster_autoscaler      = true
  enable_aws_load_balancer_controller = true
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}

# RDS Module
module "rds" {
  source = "../../modules/rds"
  
  environment = local.environment
  
  engine         = var.rds_engine
  engine_version = var.rds_engine_version
  instance_class = var.rds_instance_class
  
  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  
  db_name  = var.rds_db_name
  username = var.rds_username
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.database_subnet_ids
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  multi_az               = true
  publicly_accessible    = false
  storage_encrypted      = true
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}
```

#### Production Variables:
```hcl
# environments/production/terraform.tfvars
aws_region     = "us-west-2"
aws_account_id = "123456789012"
project_name   = "ecommerce-platform"
team_name      = "platform-engineering"
cost_center    = "engineering"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = [
  "us-west-2a",
  "us-west-2b", 
  "us-west-2c"
]

# EKS Configuration
eks_cluster_version = "1.28"
eks_node_groups = {
  general = {
    desired_size = 6
    max_size     = 20
    min_size     = 3
    
    instance_types = ["m5.xlarge"]
    capacity_type  = "ON_DEMAND"
    
    k8s_labels = {
      role = "general"
    }
    
    taints = []
  }
  
  compute_optimized = {
    desired_size = 3
    max_size     = 10
    min_size     = 0
    
    instance_types = ["c5.2xlarge"]
    capacity_type  = "SPOT"
    
    k8s_labels = {
      role = "compute"
    }
    
    taints = [
      {
        key    = "compute-optimized"
        value  = "true"
        effect = "NO_SCHEDULE"
      }
    ]
  }
}

# RDS Configuration
rds_engine                = "postgres"
rds_engine_version        = "15.4"
rds_instance_class        = "db.r6g.xlarge"
rds_allocated_storage     = 100
rds_max_allocated_storage = 1000
rds_db_name              = "ecommerce"
rds_username             = "dbadmin"
```

### 2. Environment Promotion Strategy

#### Deployment Pipeline:
```yaml
# .github/workflows/terraform-deploy.yml
name: Terraform Multi-Environment Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  TF_VERSION: "1.5.7"
  AWS_REGION: "us-west-2"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
      
      - name: Terraform Format Check
        run: terraform fmt -check -recursive
      
      - name: Terraform Validate
        run: |
          for env in dev staging production; do
            cd environments/$env
            terraform init -backend=false
            terraform validate
            cd ../..
          done

  plan-dev:
    needs: validate
    runs-on: ubuntu-latest
    environment: development
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN_DEV }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
      
      - name: Terraform Plan - Dev
        run: |
          cd environments/dev
          terraform init
          terraform plan -out=tfplan
      
      - name: Upload Plan Artifact
        uses: actions/upload-artifact@v4
        with:
          name: tfplan-dev
          path: environments/dev/tfplan

  apply-dev:
    needs: plan-dev
    runs-on: ubuntu-latest
    environment: development
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN_DEV }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
      
      - name: Download Plan Artifact
        uses: actions/download-artifact@v4
        with:
          name: tfplan-dev
          path: environments/dev/
      
      - name: Terraform Apply - Dev
        run: |
          cd environments/dev
          terraform init
          terraform apply tfplan

  plan-staging:
    needs: apply-dev
    runs-on: ubuntu-latest
    environment: staging
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN_STAGING }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
      
      - name: Terraform Plan - Staging
        run: |
          cd environments/staging
          terraform init
          terraform plan -out=tfplan

  apply-staging:
    needs: plan-staging
    runs-on: ubuntu-latest
    environment: staging
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN_STAGING }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
      
      - name: Terraform Apply - Staging
        run: |
          cd environments/staging
          terraform init
          terraform apply tfplan

  plan-production:
    needs: apply-staging
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN_PROD }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
      
      - name: Terraform Plan - Production
        run: |
          cd environments/production
          terraform init
          terraform plan -out=tfplan

  apply-production:
    needs: plan-production
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN_PROD }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
      
      - name: Terraform Apply - Production
        run: |
          cd environments/production
          terraform init
          terraform apply tfplan
```

---

## State Management

### 1. Remote State Configuration

#### S3 Backend with DynamoDB Locking:
```hcl
# environments/production/backend.tf
terraform {
  backend "s3" {
    bucket         = "company-terraform-state-prod"
    key            = "production/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock-prod"
    
    # Cross-account access
    assume_role = {
      role_arn = "arn:aws:iam::PROD_ACCOUNT:role/TerraformRole"
    }
  }
}
```

#### State Bucket Setup:
```hcl
# shared/global/state-management/main.tf
resource "aws_s3_bucket" "terraform_state" {
  for_each = toset(["dev", "staging", "production"])
  
  bucket = "company-terraform-state-${each.key}"
  
  tags = {
    Name        = "Terraform State - ${title(each.key)}"
    Environment = each.key
    Purpose     = "terraform-state"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  for_each = aws_s3_bucket.terraform_state
  
  bucket = each.value.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "terraform_state" {
  for_each = aws_s3_bucket.terraform_state
  
  bucket = each.value.id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  for_each = aws_s3_bucket.terraform_state
  
  bucket = each.value.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_state_lock" {
  for_each = toset(["dev", "staging", "production"])
  
  name           = "terraform-state-lock-${each.key}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"
  
  attribute {
    name = "LockID"
    type = "S"
  }
  
  tags = {
    Name        = "Terraform State Lock - ${title(each.key)}"
    Environment = each.key
    Purpose     = "terraform-state-lock"
  }
}
```

### 2. State Management Best Practices

#### State Import Strategy:
```bash
#!/bin/bash
# scripts/import-existing-resources.sh

set -e

ENVIRONMENT=$1
RESOURCE_TYPE=$2
RESOURCE_ID=$3
TERRAFORM_ADDRESS=$4

if [ -z "$ENVIRONMENT" ] || [ -z "$RESOURCE_TYPE" ] || [ -z "$RESOURCE_ID" ] || [ -z "$TERRAFORM_ADDRESS" ]; then
    echo "Usage: $0 <environment> <resource_type> <resource_id> <terraform_address>"
    echo "Example: $0 production vpc vpc-12345678 module.vpc.aws_vpc.main"
    exit 1
fi

cd "environments/$ENVIRONMENT"

echo "Importing $RESOURCE_TYPE with ID $RESOURCE_ID into $TERRAFORM_ADDRESS"
terraform import "$TERRAFORM_ADDRESS" "$RESOURCE_ID"

echo "Running terraform plan to verify import"
terraform plan
```

---

## Module Design Patterns

### 1. VPC Module Example

```hcl
# modules/vpc/main.tf
locals {
  azs = slice(data.aws_availability_zones.available.names, 0, var.max_azs)
  
  public_subnet_cidrs  = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i)]
  private_subnet_cidrs = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 10)]
  database_subnet_cidrs = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 20)]
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support
  
  tags = merge(var.tags, {
    Name = "${var.environment}-vpc"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${var.environment}-igw"
  })
}

resource "aws_subnet" "public" {
  count = length(local.azs)
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_subnet_cidrs[count.index]
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-public-${local.azs[count.index]}"
    Type = "public"
    "kubernetes.io/role/elb" = "1"
  })
}

resource "aws_subnet" "private" {
  count = length(local.azs)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_subnet_cidrs[count.index]
  availability_zone = local.azs[count.index]
  
  tags = merge(var.tags, {
    Name = "${var.environment}-private-${local.azs[count.index]}"
    Type = "private"
    "kubernetes.io/role/internal-elb" = "1"
  })
}

resource "aws_subnet" "database" {
  count = length(local.azs)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.database_subnet_cidrs[count.index]
  availability_zone = local.azs[count.index]
  
  tags = merge(var.tags, {
    Name = "${var.environment}-database-${local.azs[count.index]}"
    Type = "database"
  })
}

resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? length(local.azs) : 0
  
  domain = "vpc"
  
  tags = merge(var.tags, {
    Name = "${var.environment}-nat-eip-${local.azs[count.index]}"
  })
  
  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? length(local.azs) : 0
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = merge(var.tags, {
    Name = "${var.environment}-nat-${local.azs[count.index]}"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-public-rt"
  })
}

resource "aws_route_table" "private" {
  count = length(local.azs)
  
  vpc_id = aws_vpc.main.id
  
  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.main[count.index].id
    }
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-private-rt-${local.azs[count.index]}"
  })
}

resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${var.environment}-database-rt"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "database" {
  count = length(aws_subnet.database)
  
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}

# VPC Flow Logs
resource "aws_flow_log" "vpc" {
  count = var.enable_flow_logs ? 1 : 0
  
  iam_role_arn    = aws_iam_role.flow_log[0].arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log[0].arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${var.environment}-vpc-flow-logs"
  })
}

resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  count = var.enable_flow_logs ? 1 : 0
  
  name              = "/aws/vpc/flowlogs/${var.environment}"
  retention_in_days = var.flow_logs_retention_days
  
  tags = var.tags
}

resource "aws_iam_role" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0
  
  name = "${var.environment}-vpc-flow-log-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0
  
  name = "${var.environment}-vpc-flow-log-policy"
  role = aws_iam_role.flow_log[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}
```

#### VPC Module Variables:
```hcl
# modules/vpc/variables.tf
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "max_azs" {
  description = "Maximum number of availability zones"
  type        = number
  default     = 3
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Enable DNS support in VPC"
  type        = bool
  default     = true
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "CloudWatch log retention for VPC Flow Logs"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

#### VPC Module Outputs:
```hcl
# modules/vpc/outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = aws_subnet.database[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ids" {
  description = "IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = local.azs
}
```

---

## Security Best Practices

### 1. IAM Roles and Policies

#### Terraform Execution Role:
```hcl
# shared/global/iam/terraform-roles.tf
resource "aws_iam_role" "terraform_execution" {
  for_each = toset(["dev", "staging", "production"])
  
  name = "TerraformExecutionRole-${each.key}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = [
            "arn:aws:iam::${var.cicd_account_id}:role/GitHubActionsRole",
            "arn:aws:iam::${var.accounts[each.key]}:root"
          ]
        }
        Condition = {
          StringEquals = {
            "sts:ExternalId" = var.external_id
          }
        }
      }
    ]
  })
  
  tags = {
    Environment = each.key
    Purpose     = "terraform-execution"
  }
}

resource "aws_iam_role_policy_attachment" "terraform_execution" {
  for_each = aws_iam_role.terraform_execution
  
  role       = each.value.name
  policy_arn = aws_iam_policy.terraform_execution[each.key].arn
}

resource "aws_iam_policy" "terraform_execution" {
  for_each = toset(["dev", "staging", "production"])
  
  name = "TerraformExecutionPolicy-${each.key}"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:*",
          "eks:*",
          "rds:*",
          "s3:*",
          "iam:*",
          "route53:*",
          "acm:*",
          "elasticloadbalancing:*",
          "autoscaling:*",
          "cloudwatch:*",
          "logs:*",
          "ssm:*",
          "secretsmanager:*",
          "kms:*"
        ]
        Resource = "*"
      },
      {
        Effect = "Deny"
        Action = [
          "iam:DeleteRole",
          "iam:DeletePolicy",
          "iam:DetachRolePolicy"
        ]
        Resource = [
          "arn:aws:iam::*:role/TerraformExecutionRole-*",
          "arn:aws:iam::*:policy/TerraformExecutionPolicy-*"
        ]
      }
    ]
  })
}
```

### 2. Secrets Management

#### Using AWS Secrets Manager:
```hcl
# modules/rds/secrets.tf
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.environment}-${var.db_name}-password"
  description             = "Database password for ${var.environment} environment"
  recovery_window_in_days = var.environment == "production" ? 30 : 0
  
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = var.username
    password = random_password.db_password.result
  })
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  
  depends_on = [aws_secretsmanager_secret_version.db_password]
}

locals {
  db_credentials = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)
}
```

---

## Rollout Strategies

### 1. Blue-Green Deployment Strategy

#### Infrastructure Versioning:
```hcl
# environments/production/main.tf
locals {
  deployment_version = var.deployment_version
  is_blue_active     = var.active_deployment == "blue"
  
  blue_suffix  = "blue"
  green_suffix = "green"
  
  active_suffix   = local.is_blue_active ? local.blue_suffix : local.green_suffix
  inactive_suffix = local.is_blue_active ? local.green_suffix : local.blue_suffix
}

# Blue Environment
module "eks_blue" {
  source = "../../modules/eks"
  
  environment    = "${local.environment}-${local.blue_suffix}"
  cluster_name   = "${var.project_name}-${local.environment}-${local.blue_suffix}"
  cluster_version = var.eks_cluster_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  
  node_groups = var.eks_node_groups
  
  tags = merge(local.common_tags, {
    DeploymentColor = "blue"
    IsActive        = local.is_blue_active ? "true" : "false"
  })
  
  count = var.enable_blue_green ? 1 : 0
}

# Green Environment
module "eks_green" {
  source = "../../modules/eks"
  
  environment    = "${local.environment}-${local.green_suffix}"
  cluster_name   = "${var.project_name}-${local.environment}-${local.green_suffix}"
  cluster_version = var.eks_cluster_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  
  node_groups = var.eks_node_groups
  
  tags = merge(local.common_tags, {
    DeploymentColor = "green"
    IsActive        = local.is_blue_active ? "false" : "true"
  })
  
  count = var.enable_blue_green ? 1 : 0
}

# Route53 Weighted Routing
resource "aws_route53_record" "app" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "app.${var.domain_name}"
  type    = "A"
  
  set_identifier = "blue"
  weighted_routing_policy {
    weight = local.is_blue_active ? 100 : 0
  }
  
  alias {
    name                   = module.eks_blue[0].load_balancer_dns_name
    zone_id                = module.eks_blue[0].load_balancer_zone_id
    evaluate_target_health = true
  }
  
  count = var.enable_blue_green ? 1 : 0
}

resource "aws_route53_record" "app_green" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "app.${var.domain_name}"
  type    = "A"
  
  set_identifier = "green"
  weighted_routing_policy {
    weight = local.is_blue_active ? 0 : 100
  }
  
  alias {
    name                   = module.eks_green[0].load_balancer_dns_name
    zone_id                = module.eks_green[0].load_balancer_zone_id
    evaluate_target_health = true
  }
  
  count = var.enable_blue_green ? 1 : 0
}
```

### 2. Canary Deployment Script

```bash
#!/bin/bash
# scripts/canary-deploy.sh

set -e

ENVIRONMENT=${1:-production}
CANARY_PERCENTAGE=${2:-10}
MONITORING_DURATION=${3:-300}  # 5 minutes

echo "Starting canary deployment for $ENVIRONMENT environment"
echo "Canary traffic: $CANARY_PERCENTAGE%"
echo "Monitoring duration: $MONITORING_DURATION seconds"

# Deploy to canary environment
cd "environments/$ENVIRONMENT"

# Update canary weight
terraform apply -var="canary_weight=$CANARY_PERCENTAGE" -auto-approve

echo "Canary deployment started. Monitoring for $MONITORING_DURATION seconds..."

# Monitor metrics
MONITORING_START=$(date +%s)
MONITORING_END=$((MONITORING_START + MONITORING_DURATION))

while [ $(date +%s) -lt $MONITORING_END ]; do
    # Check error rate
    ERROR_RATE=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/ApplicationELB" \
        --metric-name "HTTPCode_Target_5XX_Count" \
        --dimensions Name=LoadBalancer,Value="app/production-alb/1234567890" \
        --start-time "$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)" \
        --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
        --period 300 \
        --statistics Sum \
        --query 'Datapoints[0].Sum' \
        --output text)
    
    # Check response time
    RESPONSE_TIME=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/ApplicationELB" \
        --metric-name "TargetResponseTime" \
        --dimensions Name=LoadBalancer,Value="app/production-alb/1234567890" \
        --start-time "$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)" \
        --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
        --period 300 \
        --statistics Average \
        --query 'Datapoints[0].Average' \
        --output text)
    
    echo "Current metrics - Error rate: $ERROR_RATE, Response time: ${RESPONSE_TIME}s"
    
    # Check thresholds
    if (( $(echo "$ERROR_RATE > 10" | bc -l) )); then
        echo "ERROR: High error rate detected ($ERROR_RATE). Rolling back..."
        terraform apply -var="canary_weight=0" -auto-approve
        exit 1
    fi
    
    if (( $(echo "$RESPONSE_TIME > 2.0" | bc -l) )); then
        echo "ERROR: High response time detected (${RESPONSE_TIME}s). Rolling back..."
        terraform apply -var="canary_weight=0" -auto-approve
        exit 1
    fi
    
    sleep 30
done

echo "Canary deployment successful. Promoting to full traffic..."
terraform apply -var="canary_weight=100" -auto-approve

echo "Deployment completed successfully!"
```

### 3. Rollback Strategy

```bash
#!/bin/bash
# scripts/rollback.sh

set -e

ENVIRONMENT=${1:-production}
TARGET_VERSION=${2}

if [ -z "$TARGET_VERSION" ]; then
    echo "Usage: $0 <environment> <target_version>"
    echo "Example: $0 production v1.2.3"
    exit 1
fi

echo "Rolling back $ENVIRONMENT to version $TARGET_VERSION"

cd "environments/$ENVIRONMENT"

# Get current state backup
BACKUP_FILE="terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)"
aws s3 cp "s3://company-terraform-state-$ENVIRONMENT/production/terraform.tfstate" "$BACKUP_FILE"

echo "Current state backed up to $BACKUP_FILE"

# Checkout target version
git fetch --all --tags
git checkout "tags/$TARGET_VERSION"

# Initialize and plan
terraform init
terraform plan -out=rollback.tfplan

echo "Rollback plan created. Review the plan above."
read -p "Do you want to proceed with rollback? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled"
    exit 1
fi

# Apply rollback
terraform apply rollback.tfplan

echo "Rollback to $TARGET_VERSION completed successfully"

# Verify deployment
echo "Verifying rollback..."
sleep 30

# Health check
HEALTH_CHECK_URL="https://app.${ENVIRONMENT}.company.com/health"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "Health check passed. Rollback successful!"
else
    echo "Health check failed (HTTP $HTTP_STATUS). Manual intervention required."
    exit 1
fi
```

---

## Real-World Implementation

### 1. E-commerce Platform Example

#### Complete Production Setup:
```hcl
# environments/production/main.tf - E-commerce Platform
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
}

locals {
  environment = "production"
  project     = "ecommerce-platform"
  
  common_tags = {
    Environment = local.environment
    Project     = local.project
    Owner       = "platform-team"
    CostCenter  = "engineering"
    ManagedBy   = "terraform"
  }
}

# VPC for multi-tier architecture
module "vpc" {
  source = "../../modules/vpc"
  
  environment = local.environment
  vpc_cidr    = "10.0.0.0/16"
  
  enable_nat_gateway = true
  enable_flow_logs   = true
  
  tags = local.common_tags
}

# EKS cluster for microservices
module "eks" {
  source = "../../modules/eks"
  
  environment     = local.environment
  cluster_name    = "${local.project}-${local.environment}"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  
  node_groups = {
    general = {
      desired_size   = 6
      max_size      = 20
      min_size      = 3
      instance_types = ["m5.xlarge"]
      capacity_type  = "ON_DEMAND"
      
      k8s_labels = {
        role = "general"
      }
    }
    
    compute = {
      desired_size   = 3
      max_size      = 15
      min_size      = 0
      instance_types = ["c5.2xlarge"]
      capacity_type  = "SPOT"
      
      k8s_labels = {
        role = "compute-intensive"
      }
      
      taints = [
        {
          key    = "compute-optimized"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }
  }
  
  enable_cluster_autoscaler           = true
  enable_aws_load_balancer_controller = true
  enable_external_dns                 = true
  
  tags = local.common_tags
}

# RDS for primary database
module "rds_primary" {
  source = "../../modules/rds"
  
  environment = local.environment
  identifier  = "${local.project}-primary"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.2xlarge"
  
  allocated_storage     = 500
  max_allocated_storage = 2000
  storage_encrypted     = true
  
  db_name  = "ecommerce"
  username = "dbadmin"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.database_subnet_ids
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  multi_az               = true
  publicly_accessible    = false
  
  performance_insights_enabled = true
  monitoring_interval         = 60
  
  tags = local.common_tags
}

# ElastiCache for Redis
module "elasticache" {
  source = "../../modules/elasticache"
  
  environment = local.environment
  
  engine               = "redis"
  node_type           = "cache.r6g.xlarge"
  num_cache_clusters  = 3
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = local.common_tags
}

# S3 buckets for static assets
module "s3_assets" {
  source = "../../modules/s3"
  
  environment = local.environment
  
  buckets = {
    "static-assets" = {
      versioning_enabled = true
      lifecycle_rules = [
        {
          id     = "delete_old_versions"
          status = "Enabled"
          noncurrent_version_expiration = {
            days = 90
          }
        }
      ]
    }
    
    "user-uploads" = {
      versioning_enabled = true
      cors_rules = [
        {
          allowed_headers = ["*"]
          allowed_methods = ["GET", "PUT", "POST"]
          allowed_origins = ["https://*.company.com"]
          max_age_seconds = 3000
        }
      ]
    }
  }
  
  tags = local.common_tags
}

# CloudFront for CDN
module "cloudfront" {
  source = "../../modules/cloudfront"
  
  environment = local.environment
  
  origins = [
    {
      domain_name = module.s3_assets.bucket_domain_names["static-assets"]
      origin_id   = "S3-static-assets"
      s3_origin_config = {
        origin_access_identity = module.s3_assets.origin_access_identities["static-assets"]
      }
    }
  ]
  
  default_cache_behavior = {
    target_origin_id       = "S3-static-assets"
    viewer_protocol_policy = "redirect-to-https"
    
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]
    
    forwarded_values = {
      query_string = false
      cookies = {
        forward = "none"
      }
    }
    
    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }
  
  tags = local.common_tags
}

# WAF for application protection
module "waf" {
  source = "../../modules/waf"
  
  environment = local.environment
  
  web_acl_name = "${local.project}-${local.environment}-waf"
  
  rules = [
    {
      name     = "AWSManagedRulesCommonRuleSet"
      priority = 1
      
      managed_rule_group = {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
      }
    },
    {
      name     = "AWSManagedRulesKnownBadInputsRuleSet"
      priority = 2
      
      managed_rule_group = {
        vendor_name = "AWS"
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    },
    {
      name     = "RateLimitRule"
      priority = 3
      
      rate_based_rule = {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
  ]
  
  tags = local.common_tags
}

# Route53 for DNS
module "route53" {
  source = "../../modules/route53"
  
  environment = local.environment
  
  hosted_zone_name = "company.com"
  
  records = [
    {
      name = "api"
      type = "A"
      alias = {
        name                   = module.eks.load_balancer_dns_name
        zone_id               = module.eks.load_balancer_zone_id
        evaluate_target_health = true
      }
    },
    {
      name = "cdn"
      type = "A"
      alias = {
        name                   = module.cloudfront.domain_name
        zone_id               = module.cloudfront.hosted_zone_id
        evaluate_target_health = false
      }
    }
  ]
  
  tags = local.common_tags
}
```

---

## Interview Scenarios

### 1. Common Interview Questions & Answers

#### Q: "How do you structure Terraform code for a large organization with multiple teams and environments?"

**Answer:**
"I follow a hierarchical structure with clear separation of concerns:

1. **Environment Isolation**: Each environment (dev/staging/prod) has its own directory with separate state files
2. **Reusable Modules**: Common infrastructure patterns are abstracted into modules stored in a `modules/` directory
3. **Shared Resources**: Global resources like IAM roles and Route53 zones are managed in a `shared/` directory
4. **Version Control**: Each environment pins module versions to ensure consistency and controlled updates

The structure looks like:
```
terraform-infrastructure/
├── environments/          # Environment-specific configurations
├── modules/              # Reusable infrastructure modules  
├── shared/               # Global/shared resources
└── scripts/              # Deployment and utility scripts
```

This approach provides:
- **Isolation**: Changes in dev don't affect production
- **Reusability**: Modules can be shared across teams
- **Scalability**: New environments can be added easily
- **Maintainability**: Clear ownership and responsibility boundaries"

#### Q: "How do you handle Terraform state management in production?"

**Answer:**
"For production environments, I implement a robust state management strategy:

1. **Remote State Storage**: Use S3 with versioning enabled and encryption at rest
2. **State Locking**: DynamoDB table prevents concurrent modifications
3. **Cross-Account Access**: IAM roles with assume role for secure access
4. **Backup Strategy**: Automated state backups before each apply
5. **Environment Separation**: Separate state files per environment

Configuration example:
```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state-prod"
    key            = "production/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock-prod"
  }
}
```

Key benefits:
- **Consistency**: Single source of truth for infrastructure state
- **Collaboration**: Multiple team members can work safely
- **Disaster Recovery**: State can be restored from backups
- **Audit Trail**: All changes are tracked and versioned"

#### Q: "Describe your rollout strategy for infrastructure changes in production."

**Answer:**
"I implement a multi-stage rollout strategy with safety mechanisms:

1. **Environment Progression**: Changes flow through dev → staging → production
2. **Automated Testing**: Each stage includes validation and testing
3. **Approval Gates**: Manual approval required for production deployments
4. **Canary Deployments**: Gradual traffic shifting for high-risk changes
5. **Rollback Procedures**: Automated rollback on failure detection

The pipeline includes:
- **Plan Phase**: Generate and review execution plans
- **Apply Phase**: Execute changes with monitoring
- **Validation Phase**: Health checks and smoke tests
- **Monitoring Phase**: Continuous monitoring for issues

For critical changes, I use blue-green deployments:
- Deploy to inactive environment
- Run comprehensive tests
- Switch traffic gradually
- Keep previous version for quick rollback

This approach achieved:
- **99.9% deployment success rate**
- **< 2 minute rollback time**
- **Zero production outages** from infrastructure changes"

#### Q: "How do you manage secrets and sensitive data in Terraform?"

**Answer:**
"I never store secrets directly in Terraform code. Instead, I use:

1. **AWS Secrets Manager**: For database passwords and API keys
2. **Parameter Store**: For configuration values and non-sensitive data
3. **External Data Sources**: Fetch secrets at runtime
4. **Random Providers**: Generate passwords within Terraform
5. **IAM Roles**: Avoid hardcoded credentials

Example implementation:
```hcl
resource "aws_secretsmanager_secret" "db_password" {
  name = "${var.environment}-db-password"
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
}
```

Security measures:
- **Encryption**: All secrets encrypted at rest and in transit
- **Access Control**: Least privilege IAM policies
- **Rotation**: Automated secret rotation where possible
- **Audit Logging**: All secret access is logged
- **State Protection**: Sensitive values marked as sensitive"

### 2. Troubleshooting Scenarios

#### Scenario: "Terraform state is corrupted, how do you recover?"

**Solution Steps:**
1. **Assess Damage**: Check state file integrity and identify corruption
2. **Restore from Backup**: Use S3 versioning to restore previous state
3. **Import Resources**: Re-import any resources not in restored state
4. **Validate State**: Run terraform plan to verify state accuracy
5. **Prevent Recurrence**: Implement additional safeguards

```bash
# Recovery script
#!/bin/bash
ENVIRONMENT=$1
BACKUP_VERSION=$2

# Download corrupted state for analysis
aws s3 cp "s3://terraform-state-${ENVIRONMENT}/terraform.tfstate" ./corrupted-state.json

# Restore from backup
aws s3api get-object-version \
  --bucket "terraform-state-${ENVIRONMENT}" \
  --key "terraform.tfstate" \
  --version-id "$BACKUP_VERSION" \
  ./restored-state.json

# Replace current state
aws s3 cp ./restored-state.json "s3://terraform-state-${ENVIRONMENT}/terraform.tfstate"

# Verify recovery
terraform plan
```

#### Scenario: "How do you handle Terraform drift in production?"

**Solution:**
1. **Detection**: Regular drift detection using terraform plan
2. **Analysis**: Identify root cause of drift
3. **Remediation**: Choose between importing changes or reverting drift
4. **Prevention**: Implement policies to prevent manual changes

```bash
# Drift detection script
#!/bin/bash
cd environments/production

# Generate plan and check for changes
terraform plan -detailed-exitcode -out=drift-check.plan

EXIT_CODE=$?
if [ $EXIT_CODE -eq 2 ]; then
    echo "DRIFT DETECTED: Infrastructure has drifted from Terraform state"
    terraform show drift-check.plan
    
    # Send alert
    aws sns publish \
      --topic-arn "arn:aws:sns:us-west-2:123456789012:terraform-drift-alerts" \
      --message "Terraform drift detected in production environment"
fi
```

This comprehensive guide covers all aspects of production Terraform usage that interviewers typically ask about, with real-world examples and quantified results that demonstrate expertise.