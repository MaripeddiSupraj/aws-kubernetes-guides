# Terragrunt Production Guide: Complete Multi-Environment Setup

## 🎯 Understanding Terragrunt: The "Why" Before the "How"

### The Terraform Management Challenge

**Traditional Terraform Problems:**
```
Multi-Environment Terraform Issues:
• Code duplication across environments
• Manual variable management
• Inconsistent state management
• Complex dependency handling
• No standardized project structure
• Difficult remote state configuration
• Manual backend configuration
• Environment drift over time
```

**Real-World Impact:**
```
Terraform Management Statistics:
• 70% of teams struggle with code duplication
• Average setup time: 2-4 weeks per environment
• Configuration drift: 40% of environments
• State management errors: 1 in 5 deployments
• Manual overhead: 60% of DevOps time
• Security misconfigurations: 25% of projects
```

**Business Requirements for Enterprise Terraform:**
```
Operational Requirements:
• DRY (Don't Repeat Yourself) principle
• Consistent environment configurations
• Automated state management
• Dependency orchestration
• Standardized project structure
• Secure remote state handling

Business Requirements:
• Faster environment provisioning
• Reduced operational overhead
• Improved consistency and reliability
• Better team collaboration
• Compliance and governance
• Cost optimization through standardization
```

### What is Terragrunt?

**Terragrunt Defined:**
```
Terragrunt is:
• A thin wrapper around Terraform
• DRY configuration management tool
• Remote state orchestration system
• Dependency management framework
• Configuration templating engine
• Multi-environment deployment tool
```

**Think of Terragrunt as:**
• **Project Manager**: Orchestrates multiple Terraform modules
• **Template Engine**: Generates configurations from templates
• **State Manager**: Handles remote state automatically
• **Dependency Resolver**: Manages module dependencies
• **Environment Controller**: Ensures consistency across environments

### Why Terragrunt Matters

**Business Value Proposition:**

**Operational Benefits:**
• 90% reduction in code duplication
• 80% faster environment setup
• Automated state management
• Consistent configurations
• Simplified dependency handling
• Standardized project structure

**Cost Benefits:**
• 70% reduction in DevOps overhead
• 60% faster deployment cycles
• 85% reduction in configuration errors
• Lower maintenance costs
• Improved team productivity
• Reduced security risks

**Business Impact Examples:**

**FinTech Startup:**
• Challenge: Managing 15 environments across 3 AWS accounts
• Risk: Configuration drift, compliance violations
• Solution: Terragrunt multi-environment structure
• Result: 95% configuration consistency, 50% faster deployments

**Healthcare Platform:**
• Challenge: HIPAA compliance across multiple environments
• Risk: Security misconfigurations, audit failures
• Solution: Standardized Terragrunt templates
• Result: Zero compliance violations, 80% faster audits

**E-commerce Enterprise:**
• Challenge: 50+ microservices across dev/staging/prod
• Risk: Deployment bottlenecks, environment inconsistencies
• Solution: Terragrunt dependency management
• Result: 90% deployment automation, 70% faster releases

## 🏗️ Complete Terragrunt Project Structure

### Production-Ready Folder Structure

```
terragrunt-infrastructure/
├── terragrunt.hcl                    # Root Terragrunt configuration
├── _envcommon/                       # Common environment configurations
│   ├── vpc.hcl                      # VPC common configuration
│   ├── database.hcl                 # Database common configuration
│   ├── ecs.hcl                      # ECS common configuration
│   ├── monitoring.hcl               # Monitoring common configuration
│   └── security.hcl                 # Security common configuration
├── modules/                          # Terraform modules
│   ├── vpc/                         # VPC module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   ├── database/                    # Database module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   ├── ecs-service/                 # ECS service module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   └── monitoring/                  # Monitoring module
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── versions.tf
├── environments/
│   ├── dev/                         # Development environment
│   │   ├── account.hcl              # Account-level configuration
│   │   ├── region.hcl               # Region-level configuration
│   │   ├── env.hcl                  # Environment-level configuration
│   │   ├── vpc/
│   │   │   └── terragrunt.hcl       # VPC configuration for dev
│   │   ├── database/
│   │   │   └── terragrunt.hcl       # Database configuration for dev
│   │   ├── ecs-cluster/
│   │   │   └── terragrunt.hcl       # ECS cluster for dev
│   │   ├── services/
│   │   │   ├── user-service/
│   │   │   │   └── terragrunt.hcl   # User service for dev
│   │   │   ├── payment-service/
│   │   │   │   └── terragrunt.hcl   # Payment service for dev
│   │   │   └── notification-service/
│   │   │       └── terragrunt.hcl   # Notification service for dev
│   │   └── monitoring/
│   │       └── terragrunt.hcl       # Monitoring for dev
│   ├── staging/                     # Staging environment
│   │   ├── account.hcl
│   │   ├── region.hcl
│   │   ├── env.hcl
│   │   ├── vpc/
│   │   │   └── terragrunt.hcl
│   │   ├── database/
│   │   │   └── terragrunt.hcl
│   │   ├── ecs-cluster/
│   │   │   └── terragrunt.hcl
│   │   ├── services/
│   │   │   ├── user-service/
│   │   │   │   └── terragrunt.hcl
│   │   │   ├── payment-service/
│   │   │   │   └── terragrunt.hcl
│   │   │   └── notification-service/
│   │   │       └── terragrunt.hcl
│   │   └── monitoring/
│   │       └── terragrunt.hcl
│   └── prod/                        # Production environment
│       ├── account.hcl
│       ├── region.hcl
│       ├── env.hcl
│       ├── vpc/
│       │   └── terragrunt.hcl
│       ├── database/
│       │   └── terragrunt.hcl
│       ├── ecs-cluster/
│       │   └── terragrunt.hcl
│       ├── services/
│       │   ├── user-service/
│       │   │   └── terragrunt.hcl
│       │   ├── payment-service/
│       │   │   └── terragrunt.hcl
│       │   └── notification-service/
│       │       └── terragrunt.hcl
│       └── monitoring/
│           └── terragrunt.hcl
└── scripts/                         # Utility scripts
    ├── deploy-environment.sh        # Environment deployment script
    ├── destroy-environment.sh       # Environment destruction script
    └── validate-configs.sh          # Configuration validation script
```

## 🚀 Complete Implementation: E-commerce Platform

### Root Configuration

**Root terragrunt.hcl:**
```hcl
# terragrunt.hcl (root)
locals {
  # Parse the file path to extract environment and component information
  path_parts = split("/", path_relative_to_include())
  environment = local.path_parts[1]
  component = length(local.path_parts) > 2 ? local.path_parts[2] : ""
  
  # Load environment-specific configuration
  env_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  region_vars = read_terragrunt_config(find_in_parent_folders("region.hcl"))
  account_vars = read_terragrunt_config(find_in_parent_folders("account.hcl"))
  
  # Common tags applied to all resources
  common_tags = {
    Environment = local.environment
    ManagedBy   = "terragrunt"
    Project     = "ecommerce-platform"
    Owner       = "devops-team"
    CostCenter  = local.env_vars.locals.cost_center
    Compliance  = local.env_vars.locals.compliance_level
  }
}

# Configure Terragrunt to automatically store tfstate files in an S3 bucket
remote_state {
  backend = "s3"
  
  config = {
    encrypt        = true
    bucket         = "${local.account_vars.locals.state_bucket_prefix}-${local.account_vars.locals.aws_account_id}-${local.region_vars.locals.aws_region}"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = local.region_vars.locals.aws_region
    dynamodb_table = "${local.account_vars.locals.state_bucket_prefix}-${local.account_vars.locals.aws_account_id}-${local.region_vars.locals.aws_region}-lock"
    
    s3_bucket_tags = merge(local.common_tags, {
      Name = "Terraform State Bucket"
      Type = "Infrastructure"
    })
    
    dynamodb_table_tags = merge(local.common_tags, {
      Name = "Terraform State Lock Table"
      Type = "Infrastructure"
    })
  }
  
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}

# Generate an AWS provider block
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "${local.region_vars.locals.aws_region}"
  
  assume_role {
    role_arn = "${local.account_vars.locals.terraform_role_arn}"
  }
  
  default_tags {
    tags = ${jsonencode(local.common_tags)}
  }
}
EOF
}

# Configure root level inputs that all resources can inherit
inputs = merge(
  local.account_vars.locals,
  local.region_vars.locals,
  local.env_vars.locals,
  {
    environment = local.environment
    common_tags = local.common_tags
  }
)
```

### Environment-Level Configurations

**environments/dev/account.hcl:**
```hcl
# environments/dev/account.hcl
locals {
  aws_account_id = "123456789012"  # Development AWS Account ID
  terraform_role_arn = "arn:aws:iam::123456789012:role/TerraformExecutionRole"
  state_bucket_prefix = "ecommerce-terraform-state"
  
  # Account-level security settings
  enable_cloudtrail = true
  enable_config = true
  enable_guardduty = true
  
  # Backup and retention policies
  backup_retention_days = 7
  log_retention_days = 30
}
```

**environments/dev/region.hcl:**
```hcl
# environments/dev/region.hcl
locals {
  aws_region = "us-east-1"
  
  # Region-specific settings
  availability_zones = ["us-east-1a", "us-east-1b"]
  
  # Network configuration
  vpc_cidr = "10.0.0.0/16"
  
  # Regional compliance requirements
  data_residency_required = false
  cross_region_backup = false
}
```

**environments/dev/env.hcl:**
```hcl
# environments/dev/env.hcl
locals {
  environment = "dev"
  
  # Environment-specific settings
  cost_center = "development"
  compliance_level = "basic"
  
  # Resource sizing for development
  instance_types = {
    small  = "t3.micro"
    medium = "t3.small"
    large  = "t3.medium"
  }
  
  # Database settings
  db_instance_class = "db.t3.micro"
  db_allocated_storage = 20
  db_max_allocated_storage = 100
  db_backup_retention_period = 1
  db_multi_az = false
  db_deletion_protection = false
  
  # ECS settings
  ecs_desired_count = 1
  ecs_min_capacity = 1
  ecs_max_capacity = 3
  ecs_cpu = 256
  ecs_memory = 512
  
  # Monitoring settings
  enable_detailed_monitoring = false
  log_level = "DEBUG"
  
  # Security settings
  enable_waf = false
  ssl_policy = "ELBSecurityPolicy-TLS-1-2-2017-01"
  
  # Cost optimization
  enable_spot_instances = true
  enable_scheduled_scaling = false
}
```

### Common Environment Configurations

**_envcommon/vpc.hcl:**
```hcl
# _envcommon/vpc.hcl
locals {
  # Load environment configuration
  env_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  region_vars = read_terragrunt_config(find_in_parent_folders("region.hcl"))
}

terraform {
  source = "${get_parent_terragrunt_dir()}/modules/vpc"
}

inputs = {
  vpc_cidr = local.region_vars.locals.vpc_cidr
  availability_zones = local.region_vars.locals.availability_zones
  
  # Environment-specific VPC settings
  enable_nat_gateway = local.env_vars.locals.environment == "prod" ? true : false
  enable_vpn_gateway = local.env_vars.locals.environment == "prod" ? true : false
  enable_dns_hostnames = true
  enable_dns_support = true
  
  # Subnet configuration
  public_subnet_cidrs = [
    cidrsubnet(local.region_vars.locals.vpc_cidr, 8, 1),
    cidrsubnet(local.region_vars.locals.vpc_cidr, 8, 2)
  ]
  
  private_subnet_cidrs = [
    cidrsubnet(local.region_vars.locals.vpc_cidr, 8, 11),
    cidrsubnet(local.region_vars.locals.vpc_cidr, 8, 12)
  ]
  
  database_subnet_cidrs = [
    cidrsubnet(local.region_vars.locals.vpc_cidr, 8, 21),
    cidrsubnet(local.region_vars.locals.vpc_cidr, 8, 22)
  ]
}
```

**_envcommon/database.hcl:**
```hcl
# _envcommon/database.hcl
locals {
  env_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))
}

terraform {
  source = "${get_parent_terragrunt_dir()}/modules/database"
}

dependency "vpc" {
  config_path = "../vpc"
  
  mock_outputs = {
    vpc_id = "vpc-12345678"
    database_subnet_ids = ["subnet-12345678", "subnet-87654321"]
    database_subnet_group_name = "mock-db-subnet-group"
  }
  
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  # VPC dependencies
  vpc_id = dependency.vpc.outputs.vpc_id
  subnet_ids = dependency.vpc.outputs.database_subnet_ids
  
  # Database configuration from environment
  instance_class = local.env_vars.locals.db_instance_class
  allocated_storage = local.env_vars.locals.db_allocated_storage
  max_allocated_storage = local.env_vars.locals.db_max_allocated_storage
  backup_retention_period = local.env_vars.locals.db_backup_retention_period
  multi_az = local.env_vars.locals.db_multi_az
  deletion_protection = local.env_vars.locals.db_deletion_protection
  
  # Database credentials (use AWS Secrets Manager in production)
  database_name = "ecommerce"
  master_username = "dbadmin"
  
  # Security settings
  storage_encrypted = true
  kms_key_id = "alias/aws/rds"
  
  # Backup and maintenance
  backup_window = "03:00-04:00"
  maintenance_window = "sun:04:00-sun:05:00"
  
  # Performance settings
  performance_insights_enabled = local.env_vars.locals.environment == "prod" ? true : false
  monitoring_interval = local.env_vars.locals.environment == "prod" ? 60 : 0
}
```

**_envcommon/ecs.hcl:**
```hcl
# _envcommon/ecs.hcl
locals {
  env_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))
}

terraform {
  source = "${get_parent_terragrunt_dir()}/modules/ecs-service"
}

dependency "vpc" {
  config_path = "../vpc"
  
  mock_outputs = {
    vpc_id = "vpc-12345678"
    private_subnet_ids = ["subnet-12345678", "subnet-87654321"]
    public_subnet_ids = ["subnet-11111111", "subnet-22222222"]
  }
}

dependency "database" {
  config_path = "../database"
  
  mock_outputs = {
    endpoint = "mock-db-endpoint.rds.amazonaws.com"
    port = 5432
  }
}

inputs = {
  # VPC dependencies
  vpc_id = dependency.vpc.outputs.vpc_id
  private_subnet_ids = dependency.vpc.outputs.private_subnet_ids
  public_subnet_ids = dependency.vpc.outputs.public_subnet_ids
  
  # Database connection
  database_endpoint = dependency.database.outputs.endpoint
  database_port = dependency.database.outputs.port
  
  # ECS configuration from environment
  desired_count = local.env_vars.locals.ecs_desired_count
  min_capacity = local.env_vars.locals.ecs_min_capacity
  max_capacity = local.env_vars.locals.ecs_max_capacity
  cpu = local.env_vars.locals.ecs_cpu
  memory = local.env_vars.locals.ecs_memory
  
  # Load balancer settings
  ssl_policy = local.env_vars.locals.ssl_policy
  enable_waf = local.env_vars.locals.enable_waf
  
  # Monitoring and logging
  enable_detailed_monitoring = local.env_vars.locals.enable_detailed_monitoring
  log_level = local.env_vars.locals.log_level
}
```

### Environment-Specific Configurations

**environments/dev/vpc/terragrunt.hcl:**
```hcl
# environments/dev/vpc/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

include "envcommon" {
  path   = "${dirname(find_in_parent_folders())}//_envcommon//vpc.hcl"
  expose = true
}

inputs = {
  # Development-specific VPC overrides
  enable_flow_logs = false  # Disable for cost savings in dev
  flow_logs_retention_days = 1
  
  # Development-specific tags
  additional_tags = {
    Purpose = "development"
    AutoShutdown = "true"
    BackupRequired = "false"
  }
}
```

**environments/dev/database/terragrunt.hcl:**
```hcl
# environments/dev/database/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

include "envcommon" {
  path   = "${dirname(find_in_parent_folders())}//_envcommon//database.hcl"
  expose = true
}

inputs = {
  # Development-specific database overrides
  skip_final_snapshot = true  # Allow easy cleanup in dev
  copy_tags_to_snapshot = false
  
  # Development database credentials (use Secrets Manager in prod)
  master_password = "dev-password-123"  # Use AWS Secrets Manager in production
  
  # Development-specific settings
  auto_minor_version_upgrade = true
  apply_immediately = true
  
  # Cost optimization for development
  storage_type = "gp2"  # Use cheaper storage in dev
}
```

**environments/dev/services/user-service/terragrunt.hcl:**
```hcl
# environments/dev/services/user-service/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

include "envcommon" {
  path   = "${dirname(find_in_parent_folders())}//_envcommon//ecs.hcl"
  expose = true
}

inputs = {
  # Service-specific configuration
  service_name = "user-service"
  container_image = "ecommerce/user-service:dev-latest"
  container_port = 8080
  
  # Health check configuration
  health_check_path = "/health"
  health_check_interval = 30
  health_check_timeout = 5
  health_check_healthy_threshold = 2
  health_check_unhealthy_threshold = 3
  
  # Environment variables for the service
  environment_variables = {
    LOG_LEVEL = "DEBUG"
    DATABASE_NAME = "ecommerce"
    REDIS_ENABLED = "false"  # Disable Redis in dev for cost savings
    FEATURE_FLAGS = "dev-features-enabled"
  }
  
  # Development-specific settings
  enable_execute_command = true  # Allow ECS Exec for debugging
  enable_logging = true
  log_retention_days = 7
}
```

### Production Environment Configurations

**environments/prod/env.hcl:**
```hcl
# environments/prod/env.hcl
locals {
  environment = "prod"
  
  # Environment-specific settings
  cost_center = "production"
  compliance_level = "strict"
  
  # Resource sizing for production
  instance_types = {
    small  = "m5.large"
    medium = "m5.xlarge"
    large  = "m5.2xlarge"
  }
  
  # Database settings
  db_instance_class = "db.r6g.xlarge"
  db_allocated_storage = 100
  db_max_allocated_storage = 1000
  db_backup_retention_period = 30
  db_multi_az = true
  db_deletion_protection = true
  
  # ECS settings
  ecs_desired_count = 3
  ecs_min_capacity = 3
  ecs_max_capacity = 20
  ecs_cpu = 1024
  ecs_memory = 2048
  
  # Monitoring settings
  enable_detailed_monitoring = true
  log_level = "INFO"
  
  # Security settings
  enable_waf = true
  ssl_policy = "ELBSecurityPolicy-TLS-1-2-Ext-2018-06"
  
  # Cost optimization
  enable_spot_instances = false
  enable_scheduled_scaling = true
}
```

**environments/prod/services/user-service/terragrunt.hcl:**
```hcl
# environments/prod/services/user-service/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

include "envcommon" {
  path   = "${dirname(find_in_parent_folders())}//_envcommon//ecs.hcl"
  expose = true
}

inputs = {
  # Service-specific configuration
  service_name = "user-service"
  container_image = "ecommerce/user-service:v1.2.3"  # Use specific version in prod
  container_port = 8080
  
  # Production health check configuration
  health_check_path = "/health"
  health_check_interval = 15  # More frequent checks in prod
  health_check_timeout = 3
  health_check_healthy_threshold = 2
  health_check_unhealthy_threshold = 2
  
  # Production environment variables
  environment_variables = {
    LOG_LEVEL = "INFO"
    DATABASE_NAME = "ecommerce"
    REDIS_ENABLED = "true"
    FEATURE_FLAGS = "prod-features-enabled"
    METRICS_ENABLED = "true"
    TRACING_ENABLED = "true"
  }
  
  # Production-specific settings
  enable_execute_command = false  # Disable for security in prod
  enable_logging = true
  log_retention_days = 90
  
  # Auto-scaling configuration
  auto_scaling_target_cpu = 70
  auto_scaling_target_memory = 80
  scale_up_cooldown = 300
  scale_down_cooldown = 600
  
  # Security settings
  enable_container_insights = true
  enable_service_connect = true
}
```

This comprehensive guide provides a complete production-ready Terragrunt setup with multi-environment support, showing exactly how to structure and manage infrastructure as code at enterprise scale.