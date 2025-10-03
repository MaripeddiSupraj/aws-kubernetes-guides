# Terraform Actions: Complete Guide with Real-World Implementation

## 🎯 Understanding Terraform Actions: The "Why" Before the "How"

### The Infrastructure Automation Challenge

**Traditional Infrastructure Management Problems:**
```
Manual Infrastructure Deployment Issues:
• Human error in configuration
• Inconsistent environments (dev vs prod)
• Time-consuming manual processes
• No version control for infrastructure
• Difficult rollback procedures
• Lack of audit trails
• Team coordination challenges
• Knowledge silos and documentation gaps
```

**Real-World Impact:**
```
Infrastructure Deployment Statistics:
• 67% of deployments fail due to configuration drift
• Average deployment time: 4-8 hours manually
• Human error rate: 1 in 10 deployments
• Rollback time: 2-6 hours average
• Cost of failed deployment: $50K-500K per incident
• Team productivity loss: 30% due to manual processes
```

**Business Requirements for Modern Infrastructure:**
```
Operational Requirements:
• Consistent, repeatable deployments
• Version-controlled infrastructure
• Automated testing and validation
• Fast rollback capabilities
• Multi-environment support
• Compliance and audit trails

Business Requirements:
• Faster time-to-market
• Reduced operational costs
• Improved reliability and uptime
• Better team collaboration
• Risk mitigation through automation
• Scalable infrastructure practices
```

### What Are Terraform Actions?

**Terraform Actions Defined:**
```
Terraform Actions are:
• Reusable, modular Terraform configurations
• Pre-built infrastructure components
• Standardized deployment patterns
• Version-controlled infrastructure templates
• Composable building blocks for complex systems
• Best-practice implementations of common patterns
```

**Think of Terraform Actions as:**
• **LEGO Blocks**: Standardized, reusable components that fit together
• **Recipe Cards**: Proven instructions for creating infrastructure
• **Software Libraries**: Pre-built functions for infrastructure
• **Templates**: Starting points for common infrastructure patterns

### Why Terraform Actions Matter

**Business Value Proposition:**

**Operational Benefits:**
• 80% reduction in deployment time
• 95% reduction in configuration errors
• Consistent environments across all stages
• Automated compliance and security
• Simplified team onboarding
• Standardized best practices

**Cost Benefits:**
• 60% reduction in infrastructure management overhead
• 40% faster feature delivery
• 70% reduction in deployment-related incidents
• Lower training costs for new team members
• Reduced vendor lock-in through standardization

**Business Impact Examples:**

**E-commerce Startup:**
• Challenge: Manual AWS infrastructure setup taking 2 weeks per environment
• Risk: Slow product launches, inconsistent environments
• Solution: Terraform Actions for standardized AWS environments
• Result: 2-day environment setup, 5x faster product launches

**Financial Services Company:**
• Challenge: Compliance requirements across 50+ microservices
• Risk: Regulatory violations, audit failures
• Solution: Compliance-ready Terraform Actions
• Result: 100% audit compliance, 80% faster deployments

**Healthcare SaaS Platform:**
• Challenge: HIPAA-compliant infrastructure for multiple clients
• Risk: Data breaches, compliance violations
• Solution: HIPAA-compliant Terraform Actions library
• Result: Zero compliance violations, 90% faster client onboarding

## 🏗️ Terraform Actions Architecture and Concepts

### Understanding Action Components

**Action Structure:**
```
Terraform Action Components:
├── action.yml (Action definition and metadata)
├── main.tf (Primary Terraform configuration)
├── variables.tf (Input parameters)
├── outputs.tf (Return values)
├── versions.tf (Provider requirements)
├── README.md (Documentation and usage)
└── examples/ (Usage examples and patterns)
```

**Action Types:**

**1. Composite Actions**
```
What they are: Multiple Terraform operations combined
Use cases: 
• Complete application stacks
• Multi-service deployments
• Complex infrastructure patterns
• End-to-end environment setup

Example: Full e-commerce platform (VPC + EKS + RDS + Redis + ALB)
```

**2. Atomic Actions**
```
What they are: Single-purpose infrastructure components
Use cases:
• Individual AWS resources
• Specific configurations
• Reusable modules
• Building blocks for larger systems

Example: S3 bucket with encryption and versioning
```

**3. Workflow Actions**
```
What they are: Process-oriented infrastructure operations
Use cases:
• CI/CD pipeline infrastructure
• Deployment workflows
• Testing environments
• Rollback procedures

Example: Blue-green deployment infrastructure
```

### Action Lifecycle and Versioning

**Action Versioning Strategy:**
```
Semantic Versioning for Actions:
• Major (v1.0.0): Breaking changes, incompatible updates
• Minor (v1.1.0): New features, backward compatible
• Patch (v1.1.1): Bug fixes, security updates

Version Management:
• Git tags for version control
• Immutable action versions
• Deprecation policies
• Migration guides for major versions
```

**Action Lifecycle:**
```
Development → Testing → Release → Maintenance → Deprecation

1. Development: Create and test action locally
2. Testing: Validate in staging environments
3. Release: Tag and publish to registry
4. Maintenance: Bug fixes and security updates
5. Deprecation: Sunset old versions gracefully
```

## 🚀 Complete Implementation: E-commerce Platform Actions

### Business Scenario

**Application Requirements:**
```
E-commerce Platform Infrastructure Needs:
• Multi-environment support (dev, staging, prod)
• Auto-scaling web application tier
• Managed database with backups
• CDN for global content delivery
• Load balancing and SSL termination
• Monitoring and logging
• Security and compliance (PCI DSS)
• Cost optimization features
```

**Infrastructure Components:**
```
Required AWS Resources:
• VPC with public/private subnets
• Application Load Balancer (ALB)
• ECS Fargate for containerized apps
• RDS PostgreSQL with Multi-AZ
• ElastiCache Redis cluster
• CloudFront CDN
• S3 buckets for assets and backups
• CloudWatch for monitoring
• WAF for security
• Route 53 for DNS
```

### Action 1: VPC Foundation Action

**Action Definition (action.yml):**
```yaml
name: 'AWS VPC Foundation'
description: 'Creates a production-ready VPC with public/private subnets, NAT gateways, and security groups'
author: 'DevOps Team'
branding:
  icon: 'cloud'
  color: 'blue'

inputs:
  environment:
    description: 'Environment name (dev, staging, prod)'
    required: true
  vpc_cidr:
    description: 'CIDR block for VPC'
    required: false
    default: '10.0.0.0/16'
  availability_zones:
    description: 'Number of availability zones'
    required: false
    default: '2'
  enable_nat_gateway:
    description: 'Enable NAT Gateway for private subnets'
    required: false
    default: 'true'
  enable_vpn_gateway:
    description: 'Enable VPN Gateway'
    required: false
    default: 'false'
  tags:
    description: 'Additional tags as JSON'
    required: false
    default: '{}'

outputs:
  vpc_id:
    description: 'ID of the created VPC'
  public_subnet_ids:
    description: 'List of public subnet IDs'
  private_subnet_ids:
    description: 'List of private subnet IDs'
  nat_gateway_ids:
    description: 'List of NAT Gateway IDs'
  internet_gateway_id:
    description: 'Internet Gateway ID'

runs:
  using: 'composite'
  steps:
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.6.0
    
    - name: Terraform Init
      shell: bash
      run: terraform init
      working-directory: ${{ github.action_path }}
    
    - name: Terraform Plan
      shell: bash
      run: |
        terraform plan \
          -var="environment=${{ inputs.environment }}" \
          -var="vpc_cidr=${{ inputs.vpc_cidr }}" \
          -var="availability_zones=${{ inputs.availability_zones }}" \
          -var="enable_nat_gateway=${{ inputs.enable_nat_gateway }}" \
          -var="enable_vpn_gateway=${{ inputs.enable_vpn_gateway }}" \
          -var="tags=${{ inputs.tags }}" \
          -out=tfplan
      working-directory: ${{ github.action_path }}
    
    - name: Terraform Apply
      shell: bash
      run: terraform apply -auto-approve tfplan
      working-directory: ${{ github.action_path }}
```

**Main Terraform Configuration (main.tf):**
```hcl
# Data sources for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Local values for calculations
locals {
  az_count = min(var.availability_zones, length(data.aws_availability_zones.available.names))
  
  # Calculate subnet CIDRs
  public_subnet_cidrs = [
    for i in range(local.az_count) : 
    cidrsubnet(var.vpc_cidr, 8, i)
  ]
  
  private_subnet_cidrs = [
    for i in range(local.az_count) : 
    cidrsubnet(var.vpc_cidr, 8, i + 10)
  ]
  
  # Merge default and custom tags
  common_tags = merge(
    {
      Environment = var.environment
      ManagedBy   = "terraform-actions"
      CreatedAt   = timestamp()
    },
    var.tags
  )
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${var.environment}-vpc"
    Type = "VPC"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${var.environment}-igw"
    Type = "InternetGateway"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = local.az_count

  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${var.environment}-public-subnet-${count.index + 1}"
    Type = "PublicSubnet"
    Tier = "Public"
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count = local.az_count

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${var.environment}-private-subnet-${count.index + 1}"
    Type = "PrivateSubnet"
    Tier = "Private"
  })
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? local.az_count : 0

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${var.environment}-nat-eip-${count.index + 1}"
    Type = "ElasticIP"
  })
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? local.az_count : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  depends_on    = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${var.environment}-nat-gateway-${count.index + 1}"
    Type = "NATGateway"
  })
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${var.environment}-public-rt"
    Type = "RouteTable"
    Tier = "Public"
  })
}

# Route Tables for Private Subnets
resource "aws_route_table" "private" {
  count = local.az_count

  vpc_id = aws_vpc.main.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.main[count.index].id
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.environment}-private-rt-${count.index + 1}"
    Type = "RouteTable"
    Tier = "Private"
  })
}

# Route Table Associations - Public
resource "aws_route_table_association" "public" {
  count = local.az_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route Table Associations - Private
resource "aws_route_table_association" "private" {
  count = local.az_count

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# VPN Gateway (optional)
resource "aws_vpn_gateway" "main" {
  count = var.enable_vpn_gateway ? 1 : 0

  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${var.environment}-vpn-gateway"
    Type = "VPNGateway"
  })
}

# Default Security Group Rules
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id

  # Remove all default rules
  ingress = []
  egress  = []

  tags = merge(local.common_tags, {
    Name = "${var.environment}-default-sg"
    Type = "SecurityGroup"
  })
}

# VPC Flow Logs
resource "aws_flow_log" "vpc_flow_log" {
  iam_role_arn    = aws_iam_role.flow_log.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  name              = "/aws/vpc/flowlogs/${var.environment}"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${var.environment}-vpc-flow-logs"
    Type = "LogGroup"
  })
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "flow_log" {
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

  tags = local.common_tags
}

# IAM Policy for VPC Flow Logs
resource "aws_iam_role_policy" "flow_log" {
  name = "${var.environment}-vpc-flow-log-policy"
  role = aws_iam_role.flow_log.id

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

**Variables Definition (variables.tf):**
```hcl
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "Number of availability zones to use"
  type        = number
  default     = 2
  
  validation {
    condition     = var.availability_zones >= 2 && var.availability_zones <= 6
    error_message = "Availability zones must be between 2 and 6."
  }
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

**Outputs Definition (outputs.tf):**
```hcl
output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_cidrs" {
  description = "List of public subnet CIDR blocks"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks"
  value       = aws_subnet.private[*].cidr_block
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_ips" {
  description = "List of NAT Gateway public IPs"
  value       = aws_eip.nat[*].public_ip
}

output "vpc_flow_log_id" {
  description = "ID of the VPC Flow Log"
  value       = aws_flow_log.vpc_flow_log.id
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = slice(data.aws_availability_zones.available.names, 0, local.az_count)
}
```

### Action 2: ECS Application Action

**Action Definition for ECS Service:**
```yaml
name: 'ECS Fargate Application'
description: 'Deploys a containerized application on ECS Fargate with ALB, auto-scaling, and monitoring'
author: 'DevOps Team'

inputs:
  environment:
    description: 'Environment name'
    required: true
  app_name:
    description: 'Application name'
    required: true
  vpc_id:
    description: 'VPC ID where to deploy'
    required: true
  private_subnet_ids:
    description: 'Private subnet IDs for ECS tasks'
    required: true
  public_subnet_ids:
    description: 'Public subnet IDs for ALB'
    required: true
  container_image:
    description: 'Docker image URI'
    required: true
  container_port:
    description: 'Container port'
    required: false
    default: '8080'
  desired_count:
    description: 'Desired number of tasks'
    required: false
    default: '2'
  cpu:
    description: 'CPU units (256, 512, 1024, 2048, 4096)'
    required: false
    default: '512'
  memory:
    description: 'Memory in MB'
    required: false
    default: '1024'
  health_check_path:
    description: 'Health check path'
    required: false
    default: '/health'

outputs:
  cluster_name:
    description: 'ECS cluster name'
  service_name:
    description: 'ECS service name'
  load_balancer_dns:
    description: 'Application Load Balancer DNS name'
  load_balancer_url:
    description: 'Application URL'

runs:
  using: 'composite'
  steps:
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.6.0
    
    - name: Terraform Init
      shell: bash
      run: terraform init
      working-directory: ${{ github.action_path }}
    
    - name: Terraform Apply
      shell: bash
      run: |
        terraform apply -auto-approve \
          -var="environment=${{ inputs.environment }}" \
          -var="app_name=${{ inputs.app_name }}" \
          -var="vpc_id=${{ inputs.vpc_id }}" \
          -var="private_subnet_ids=${{ inputs.private_subnet_ids }}" \
          -var="public_subnet_ids=${{ inputs.public_subnet_ids }}" \
          -var="container_image=${{ inputs.container_image }}" \
          -var="container_port=${{ inputs.container_port }}" \
          -var="desired_count=${{ inputs.desired_count }}" \
          -var="cpu=${{ inputs.cpu }}" \
          -var="memory=${{ inputs.memory }}" \
          -var="health_check_path=${{ inputs.health_check_path }}"
      working-directory: ${{ github.action_path }}
```

**ECS Application Main Configuration:**
```hcl
# Local values
locals {
  app_full_name = "${var.environment}-${var.app_name}"
  
  common_tags = {
    Environment = var.environment
    Application = var.app_name
    ManagedBy   = "terraform-actions"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = local.app_full_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

# ECS Cluster Capacity Providers
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = local.app_full_name
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod" ? true : false

  tags = local.common_tags
}

# ALB Target Group
resource "aws_lb_target_group" "main" {
  name        = local.app_full_name
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = var.health_check_path
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = local.common_tags
}

# ALB Listener
resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "${local.app_full_name}-alb"
  description = "Security group for ${local.app_full_name} ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_full_name}-alb-sg"
  })
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${local.app_full_name}-ecs-tasks"
  description = "Security group for ${local.app_full_name} ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "HTTP from ALB"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_full_name}-ecs-tasks-sg"
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = local.app_full_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = var.app_name
      image = var.container_image
      
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "APP_NAME"
          value = var.app_name
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.main.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
      
      healthCheck = {
        command = [
          "CMD-SHELL",
          "curl -f http://localhost:${var.container_port}${var.health_check_path} || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
      
      essential = true
    }
  ])

  tags = local.common_tags
}

# ECS Service
resource "aws_ecs_service" "main" {
  name            = local.app_full_name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = var.private_subnet_ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = var.app_name
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.main]

  tags = local.common_tags
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.desired_count * 3
  min_capacity       = var.desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "ecs_policy_cpu" {
  name               = "${local.app_full_name}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Auto Scaling Policy - Memory
resource "aws_appautoscaling_policy" "ecs_policy_memory" {
  name               = "${local.app_full_name}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 80.0
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${local.app_full_name}"
  retention_in_days = 30

  tags = local.common_tags
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${local.app_full_name}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Role Policy Attachment for ECS Task Execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task_role" {
  name = "${local.app_full_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Data source for current AWS region
data "aws_region" "current" {}
```

### Action 3: Complete E-commerce Stack Action

**Composite Action for Full Stack:**
```yaml
name: 'E-commerce Platform Stack'
description: 'Complete e-commerce platform with VPC, ECS, RDS, Redis, and monitoring'
author: 'DevOps Team'

inputs:
  environment:
    description: 'Environment name (dev, staging, prod)'
    required: true
  app_name:
    description: 'Application name'
    required: true
    default: 'ecommerce'
  container_image:
    description: 'Docker image for the application'
    required: true
  domain_name:
    description: 'Domain name for the application'
    required: false
  enable_https:
    description: 'Enable HTTPS with ACM certificate'
    required: false
    default: 'false'
  database_password:
    description: 'Database password (use secrets manager in production)'
    required: true

outputs:
  application_url:
    description: 'Application URL'
  database_endpoint:
    description: 'RDS database endpoint'
  redis_endpoint:
    description: 'Redis cluster endpoint'

runs:
  using: 'composite'
  steps:
    - name: Deploy VPC Foundation
      id: vpc
      uses: ./vpc-foundation-action
      with:
        environment: ${{ inputs.environment }}
        vpc_cidr: '10.0.0.0/16'
        availability_zones: 2
        enable_nat_gateway: true
    
    - name: Deploy RDS Database
      id: database
      uses: ./rds-postgres-action
      with:
        environment: ${{ inputs.environment }}
        vpc_id: ${{ steps.vpc.outputs.vpc_id }}
        private_subnet_ids: ${{ steps.vpc.outputs.private_subnet_ids }}
        database_name: ${{ inputs.app_name }}
        master_password: ${{ inputs.database_password }}
        instance_class: ${{ inputs.environment == 'prod' && 'db.r6g.large' || 'db.t3.micro' }}
        multi_az: ${{ inputs.environment == 'prod' && 'true' || 'false' }}
    
    - name: Deploy Redis Cache
      id: redis
      uses: ./elasticache-redis-action
      with:
        environment: ${{ inputs.environment }}
        vpc_id: ${{ steps.vpc.outputs.vpc_id }}
        private_subnet_ids: ${{ steps.vpc.outputs.private_subnet_ids }}
        node_type: ${{ inputs.environment == 'prod' && 'cache.r6g.large' || 'cache.t3.micro' }}
        num_cache_nodes: ${{ inputs.environment == 'prod' && '2' || '1' }}
    
    - name: Deploy Application
      id: app
      uses: ./ecs-fargate-action
      with:
        environment: ${{ inputs.environment }}
        app_name: ${{ inputs.app_name }}
        vpc_id: ${{ steps.vpc.outputs.vpc_id }}
        private_subnet_ids: ${{ steps.vpc.outputs.private_subnet_ids }}
        public_subnet_ids: ${{ steps.vpc.outputs.public_subnet_ids }}
        container_image: ${{ inputs.container_image }}
        desired_count: ${{ inputs.environment == 'prod' && '3' || '1' }}
        cpu: ${{ inputs.environment == 'prod' && '1024' || '512' }}
        memory: ${{ inputs.environment == 'prod' && '2048' || '1024' }}
        database_endpoint: ${{ steps.database.outputs.endpoint }}
        redis_endpoint: ${{ steps.redis.outputs.endpoint }}
    
    - name: Setup Monitoring
      id: monitoring
      uses: ./cloudwatch-monitoring-action
      with:
        environment: ${{ inputs.environment }}
        app_name: ${{ inputs.app_name }}
        ecs_cluster_name: ${{ steps.app.outputs.cluster_name }}
        ecs_service_name: ${{ steps.app.outputs.service_name }}
        alb_arn: ${{ steps.app.outputs.load_balancer_arn }}
        rds_instance_id: ${{ steps.database.outputs.instance_id }}
    
    - name: Setup SSL Certificate (if enabled)
      if: inputs.enable_https == 'true'
      uses: ./acm-certificate-action
      with:
        domain_name: ${{ inputs.domain_name }}
        load_balancer_arn: ${{ steps.app.outputs.load_balancer_arn }}
```

## 📋 Real-World Usage Examples

### Example 1: Development Environment

**GitHub Workflow for Dev Environment:**
```yaml
name: Deploy Development Environment

on:
  push:
    branches: [develop]
  pull_request:
    branches: [develop]

jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Build and push Docker image
      run: |
        docker build -t ecommerce-app:${{ github.sha }} .
        docker tag ecommerce-app:${{ github.sha }} ${{ secrets.ECR_REGISTRY }}/ecommerce-app:${{ github.sha }}
        docker push ${{ secrets.ECR_REGISTRY }}/ecommerce-app:${{ github.sha }}
    
    - name: Deploy E-commerce Stack
      uses: ./terraform-actions/ecommerce-stack
      with:
        environment: 'dev'
        app_name: 'ecommerce'
        container_image: '${{ secrets.ECR_REGISTRY }}/ecommerce-app:${{ github.sha }}'
        database_password: ${{ secrets.DEV_DB_PASSWORD }}
        enable_https: 'false'
    
    - name: Run Integration Tests
      run: |
        # Wait for deployment to be ready
        sleep 60
        
        # Run tests against the deployed environment
        npm test -- --env=dev
    
    - name: Cleanup on failure
      if: failure()
      uses: ./terraform-actions/cleanup-environment
      with:
        environment: 'dev'
        app_name: 'ecommerce'
```

### Example 2: Production Deployment

**Production Deployment Workflow:**
```yaml
name: Deploy Production Environment

on:
  release:
    types: [published]

jobs:
  deploy-prod:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.PROD_AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.PROD_AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Deploy Production Stack
      uses: ./terraform-actions/ecommerce-stack
      with:
        environment: 'prod'
        app_name: 'ecommerce'
        container_image: '${{ secrets.ECR_REGISTRY }}/ecommerce-app:${{ github.event.release.tag_name }}'
        database_password: ${{ secrets.PROD_DB_PASSWORD }}
        domain_name: 'shop.company.com'
        enable_https: 'true'
    
    - name: Run Smoke Tests
      run: |
        # Wait for deployment
        sleep 120
        
        # Run production smoke tests
        npm run test:smoke -- --env=prod
    
    - name: Update DNS (Blue-Green Deployment)
      uses: ./terraform-actions/route53-update
      with:
        domain_name: 'shop.company.com'
        target_alb: ${{ steps.deploy.outputs.load_balancer_dns }}
    
    - name: Notify Slack
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'Production deployment completed successfully!'
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Example 3: Multi-Environment Pipeline

**Complete CI/CD Pipeline:**
```yaml
name: Multi-Environment Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run Unit Tests
      run: npm test
    
    - name: Run Security Scan
      uses: securecodewarrior/github-action-add-sarif@v1
      with:
        sarif-file: security-scan-results.sarif

  deploy-dev:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Development
      uses: ./terraform-actions/ecommerce-stack
      with:
        environment: 'dev'
        app_name: 'ecommerce'
        container_image: '${{ secrets.ECR_REGISTRY }}/ecommerce-app:dev-${{ github.sha }}'
        database_password: ${{ secrets.DEV_DB_PASSWORD }}

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Staging
      uses: ./terraform-actions/ecommerce-stack
      with:
        environment: 'staging'
        app_name: 'ecommerce'
        container_image: '${{ secrets.ECR_REGISTRY }}/ecommerce-app:staging-${{ github.sha }}'
        database_password: ${{ secrets.STAGING_DB_PASSWORD }}
        domain_name: 'staging.shop.company.com'
        enable_https: 'true'
    
    - name: Run E2E Tests
      run: |
        npm run test:e2e -- --env=staging
    
    - name: Performance Tests
      run: |
        npm run test:performance -- --env=staging

  deploy-prod:
    needs: [deploy-staging]
    if: github.event_name == 'release'
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Production
      uses: ./terraform-actions/ecommerce-stack
      with:
        environment: 'prod'
        app_name: 'ecommerce'
        container_image: '${{ secrets.ECR_REGISTRY }}/ecommerce-app:${{ github.event.release.tag_name }}'
        database_password: ${{ secrets.PROD_DB_PASSWORD }}
        domain_name: 'shop.company.com'
        enable_https: 'true'
```

## 🔧 Advanced Terraform Actions Patterns

### Pattern 1: Conditional Resource Creation

**Environment-Specific Resources:**
```hcl
# Create different resources based on environment
resource "aws_rds_cluster" "aurora" {
  count = var.environment == "prod" ? 1 : 0
  
  cluster_identifier = "${var.environment}-${var.app_name}-aurora"
  engine             = "aurora-postgresql"
  engine_version     = "13.7"
  database_name      = var.database_name
  master_username    = var.master_username
  master_password    = var.master_password
  
  # Production-specific settings
  backup_retention_period = 30
  preferred_backup_window = "03:00-04:00"
  deletion_protection     = true
  
  tags = local.common_tags
}

resource "aws_db_instance" "postgres" {
  count = var.environment != "prod" ? 1 : 0
  
  identifier = "${var.environment}-${var.app_name}-postgres"
  engine     = "postgres"
  engine_version = "13.7"
  instance_class = var.instance_class
  
  # Development/staging settings
  backup_retention_period = 7
  deletion_protection     = false
  skip_final_snapshot    = true
  
  tags = local.common_tags
}
```

### Pattern 2: Dynamic Configuration

**Dynamic Scaling Based on Environment:**
```hcl
locals {
  # Environment-specific configurations
  environment_config = {
    dev = {
      instance_count = 1
      instance_type  = "t3.micro"
      storage_size   = 20
      backup_days    = 1
    }
    staging = {
      instance_count = 2
      instance_type  = "t3.small"
      storage_size   = 50
      backup_days    = 7
    }
    prod = {
      instance_count = 3
      instance_type  = "m5.large"
      storage_size   = 100
      backup_days    = 30
    }
  }
  
  # Get current environment config
  current_config = local.environment_config[var.environment]
}

resource "aws_instance" "app" {
  count = local.current_config.instance_count
  
  ami           = data.aws_ami.amazon_linux.id
  instance_type = local.current_config.instance_type
  
  root_block_device {
    volume_size = local.current_config.storage_size
    volume_type = "gp3"
    encrypted   = true
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-${var.app_name}-${count.index + 1}"
  })
}
```

### Pattern 3: Cross-Action Data Sharing

**Using Terraform Remote State:**
```hcl
# In dependent action, read outputs from VPC action
data "terraform_remote_state" "vpc" {
  backend = "s3"
  
  config = {
    bucket = "${var.environment}-terraform-state"
    key    = "vpc/terraform.tfstate"
    region = "us-east-1"
  }
}

# Use VPC outputs in current action
resource "aws_security_group" "app" {
  name   = "${var.environment}-${var.app_name}-sg"
  vpc_id = data.terraform_remote_state.vpc.outputs.vpc_id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [data.terraform_remote_state.vpc.outputs.vpc_cidr_block]
  }
}
```

## 💰 Cost Optimization and ROI Analysis

### Cost Comparison: Manual vs Terraform Actions

**Manual Infrastructure Management Costs:**
```
Traditional Manual Approach:
• DevOps engineer time: 160 hours/month × $100/hour = $16,000/month
• Deployment errors: 2/month × $25,000 = $50,000/month
• Environment inconsistencies: 1/month × $15,000 = $15,000/month
• Security misconfigurations: 1/quarter × $100,000 = $33,333/month
• Documentation and knowledge transfer: 40 hours/month × $100/hour = $4,000/month
• Total monthly cost: $118,333
• Total annual cost: $1,420,000
```

**Terraform Actions Implementation Costs:**
```
Terraform Actions Approach:
• Initial development: 200 hours × $100/hour = $20,000 (one-time)
• Maintenance: 20 hours/month × $100/hour = $2,000/month
• Training: 40 hours × $100/hour = $4,000 (one-time)
• Tool licensing: $500/month
• Total first-year cost: $54,000
• Total ongoing annual cost: $30,000

ROI Calculation:
• Traditional approach: $1,420,000/year
• Terraform Actions approach: $30,000/year
• Annual savings: $1,390,000
• ROI: 4,633% in first year, 4,733% ongoing
```

### Performance Improvements

**Deployment Speed Comparison:**
```
Manual Deployment:
• Environment setup: 2-4 weeks
• Application deployment: 4-8 hours
• Configuration changes: 2-4 hours
• Rollback time: 4-12 hours

Terraform Actions Deployment:
• Environment setup: 30-60 minutes
• Application deployment: 10-20 minutes
• Configuration changes: 5-15 minutes
• Rollback time: 5-10 minutes

Speed Improvements:
• Environment setup: 95% faster
• Application deployment: 92% faster
• Configuration changes: 90% faster
• Rollback operations: 95% faster
```

This comprehensive guide provides everything needed to understand, implement, and optimize Terraform Actions for enterprise infrastructure automation, delivering significant business value through standardization, automation, and best practices.