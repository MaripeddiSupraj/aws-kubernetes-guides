# AWS Disaster Recovery & Business Continuity Complete Guide

## Table of Contents
1. [DR Fundamentals & Concepts](#dr-fundamentals--concepts)
2. [AWS DR Strategies & Patterns](#aws-dr-strategies--patterns)
3. [RTO/RPO Requirements & SLA Design](#rtorpo-requirements--sla-design)
4. [Multi-Region Architecture](#multi-region-architecture)
5. [Database DR Strategies](#database-dr-strategies)
6. [Application-Level DR](#application-level-dr)
7. [Infrastructure as Code for DR](#infrastructure-as-code-for-dr)
8. [Monitoring & Alerting](#monitoring--alerting)
9. [Testing & Validation](#testing--validation)
10. [Cost Optimization](#cost-optimization)
11. [Interview Scenarios](#interview-scenarios)

---

## DR Fundamentals & Concepts

### Key Metrics
- **RTO (Recovery Time Objective)**: Maximum acceptable downtime
- **RPO (Recovery Point Objective)**: Maximum acceptable data loss
- **MTTR (Mean Time To Recovery)**: Average time to restore service
- **MTBF (Mean Time Between Failures)**: Average time between incidents

### DR Strategy Categories

#### 1. Backup & Restore (Pilot Light)
- **RTO**: Hours to days
- **RPO**: Hours
- **Cost**: Lowest
- **Use Case**: Non-critical applications

```bash
# Example: Automated S3 backup
aws s3 sync /data s3://dr-backup-bucket/$(date +%Y-%m-%d) \
  --storage-class GLACIER_IR \
  --exclude "*.tmp"
```

#### 2. Pilot Light
- **RTO**: 10 minutes to hours
- **RPO**: Minutes to hours
- **Cost**: Low-Medium
- **Use Case**: Critical data, minimal infrastructure

#### 3. Warm Standby
- **RTO**: Minutes
- **RPO**: Seconds to minutes
- **Cost**: Medium-High
- **Use Case**: Business-critical applications

#### 4. Hot Standby (Multi-Site Active/Active)
- **RTO**: Seconds
- **RPO**: Near-zero
- **Cost**: Highest
- **Use Case**: Mission-critical applications

---

## AWS DR Strategies & Patterns

### 1. Cross-Region Backup Strategy

```yaml
# CloudFormation Template: Cross-Region Backup
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Cross-region backup infrastructure'

Parameters:
  PrimaryRegion:
    Type: String
    Default: 'us-east-1'
  DRRegion:
    Type: String
    Default: 'us-west-2'

Resources:
  # Primary Region S3 Bucket
  PrimaryBackupBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::StackName}-primary-backup-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      ReplicationConfiguration:
        Role: !GetAtt ReplicationRole.Arn
        Rules:
          - Id: ReplicateToSecondaryRegion
            Status: Enabled
            Prefix: ''
            Destination:
              Bucket: !Sub 'arn:aws:s3:::${AWS::StackName}-dr-backup-${AWS::AccountId}'
              StorageClass: STANDARD_IA

  # Cross-Region Replication Role
  ReplicationRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: s3.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: ReplicationPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObjectVersionForReplication
                  - s3:GetObjectVersionAcl
                Resource: !Sub '${PrimaryBackupBucket}/*'
              - Effect: Allow
                Action:
                  - s3:ReplicateObject
                  - s3:ReplicateDelete
                Resource: !Sub 'arn:aws:s3:::${AWS::StackName}-dr-backup-${AWS::AccountId}/*'
```

### 2. Database DR with RDS

```bash
# Create RDS with automated backups and cross-region read replica
aws rds create-db-instance \
  --db-instance-identifier myapp-primary \
  --db-instance-class db.r5.large \
  --engine mysql \
  --master-username admin \
  --master-user-password SecurePassword123! \
  --allocated-storage 100 \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted \
  --region us-east-1

# Create cross-region read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier myapp-dr-replica \
  --source-db-instance-identifier arn:aws:rds:us-east-1:123456789012:db:myapp-primary \
  --db-instance-class db.r5.large \
  --region us-west-2
```

### 3. Application Load Balancer Health Checks

```json
{
  "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
  "Properties": {
    "Name": "app-primary-tg",
    "Port": 80,
    "Protocol": "HTTP",
    "VpcId": {"Ref": "VPC"},
    "HealthCheckPath": "/health",
    "HealthCheckIntervalSeconds": 30,
    "HealthCheckTimeoutSeconds": 5,
    "HealthyThresholdCount": 2,
    "UnhealthyThresholdCount": 3,
    "Matcher": {
      "HttpCode": "200"
    }
  }
}
```

---

## RTO/RPO Requirements & SLA Design

### Business Impact Analysis

```python
# Python script for RTO/RPO calculation
class BusinessImpactAnalysis:
    def __init__(self):
        self.applications = {}
    
    def add_application(self, name, revenue_per_hour, data_criticality):
        self.applications[name] = {
            'revenue_per_hour': revenue_per_hour,
            'data_criticality': data_criticality,
            'recommended_rto': self.calculate_rto(revenue_per_hour),
            'recommended_rpo': self.calculate_rpo(data_criticality)
        }
    
    def calculate_rto(self, revenue_per_hour):
        if revenue_per_hour > 100000:
            return "< 15 minutes"
        elif revenue_per_hour > 10000:
            return "< 1 hour"
        elif revenue_per_hour > 1000:
            return "< 4 hours"
        else:
            return "< 24 hours"
    
    def calculate_rpo(self, criticality):
        if criticality == "critical":
            return "< 5 minutes"
        elif criticality == "important":
            return "< 1 hour"
        else:
            return "< 24 hours"

# Usage example
bia = BusinessImpactAnalysis()
bia.add_application("e-commerce", 50000, "critical")
bia.add_application("analytics", 5000, "important")
print(bia.applications)
```

### SLA Tier Design

| Tier | RTO | RPO | Availability | Use Case |
|------|-----|-----|--------------|----------|
| Platinum | < 5 min | < 1 min | 99.99% | Revenue-critical |
| Gold | < 30 min | < 15 min | 99.9% | Business-critical |
| Silver | < 4 hours | < 1 hour | 99.5% | Important |
| Bronze | < 24 hours | < 24 hours | 99% | Non-critical |

---

## Multi-Region Architecture

### 1. Route 53 Health Checks & Failover

```bash
# Create health check for primary region
aws route53 create-health-check \
  --caller-reference "primary-$(date +%s)" \
  --health-check-config '{
    "Type": "HTTPS",
    "ResourcePath": "/health",
    "FullyQualifiedDomainName": "api.myapp.com",
    "Port": 443,
    "RequestInterval": 30,
    "FailureThreshold": 3
  }'

# Create DNS records with failover routing
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.myapp.com",
        "Type": "A",
        "SetIdentifier": "primary",
        "Failover": "PRIMARY",
        "TTL": 60,
        "ResourceRecords": [{"Value": "1.2.3.4"}],
        "HealthCheckId": "abc123-def456-ghi789"
      }
    }]
  }'
```

### 2. Global Load Balancer Setup

```yaml
# Terraform configuration for Global Accelerator
resource "aws_globalaccelerator_accelerator" "main" {
  name            = "myapp-global-accelerator"
  ip_address_type = "IPV4"
  enabled         = true

  attributes {
    flow_logs_enabled   = true
    flow_logs_s3_bucket = aws_s3_bucket.flow_logs.bucket
    flow_logs_s3_prefix = "flow-logs/"
  }
}

resource "aws_globalaccelerator_listener" "main" {
  accelerator_arn = aws_globalaccelerator_accelerator.main.id
  client_affinity = "SOURCE_IP"
  protocol        = "TCP"

  port_range {
    from_port = 80
    to_port   = 80
  }

  port_range {
    from_port = 443
    to_port   = 443
  }
}

resource "aws_globalaccelerator_endpoint_group" "us_east_1" {
  listener_arn = aws_globalaccelerator_listener.main.id
  endpoint_group_region = "us-east-1"
  traffic_dial_percentage = 100
  health_check_grace_period_seconds = 30
  health_check_interval_seconds = 30
  health_check_path = "/health"
  health_check_protocol = "HTTP"
  health_check_port = 80
  threshold_count = 3

  endpoint_configuration {
    endpoint_id = aws_lb.primary.arn
    weight      = 100
  }
}
```

---

## Database DR Strategies

### 1. RDS Multi-AZ with Cross-Region Replica

```bash
# Enable automated backups and point-in-time recovery
aws rds modify-db-instance \
  --db-instance-identifier myapp-prod \
  --backup-retention-period 35 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:04:00-sun:05:00" \
  --apply-immediately

# Create manual snapshot before major changes
aws rds create-db-snapshot \
  --db-instance-identifier myapp-prod \
  --db-snapshot-identifier myapp-prod-pre-migration-$(date +%Y%m%d)

# Restore from point-in-time
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier myapp-prod \
  --target-db-instance-identifier myapp-restored \
  --restore-time 2024-01-15T10:30:00.000Z
```

### 2. DynamoDB Global Tables

```python
import boto3

def setup_dynamodb_global_tables():
    dynamodb = boto3.client('dynamodb')
    
    # Create table in primary region
    table_name = 'UserProfiles'
    
    # Enable streams for global tables
    dynamodb.update_table(
        TableName=table_name,
        StreamSpecification={
            'StreamEnabled': True,
            'StreamViewType': 'NEW_AND_OLD_IMAGES'
        }
    )
    
    # Create global table
    dynamodb.create_global_table(
        GlobalTableName=table_name,
        ReplicationGroup=[
            {'RegionName': 'us-east-1'},
            {'RegionName': 'us-west-2'},
            {'RegionName': 'eu-west-1'}
        ]
    )
    
    return f"Global table {table_name} created successfully"

# Enable point-in-time recovery
def enable_pitr(table_name):
    dynamodb = boto3.client('dynamodb')
    
    dynamodb.update_continuous_backups(
        TableName=table_name,
        PointInTimeRecoverySpecification={
            'PointInTimeRecoveryEnabled': True
        }
    )
```

### 3. Aurora Global Database

```sql
-- Create Aurora Global Database
CREATE GLOBAL DATABASE myapp_global_db
    CLUSTER_IDENTIFIER myapp_primary_cluster
    ENGINE aurora-mysql
    ENGINE_VERSION 8.0.mysql_aurora.3.02.0;

-- Add secondary region
ALTER GLOBAL DATABASE myapp_global_db
    ADD REGION 'us-west-2'
    CLUSTER_IDENTIFIER myapp_secondary_cluster;

-- Promote secondary to primary (failover)
ALTER GLOBAL DATABASE myapp_global_db
    PROMOTE REGION 'us-west-2';
```

---

## Application-Level DR

### 1. ECS/Fargate Multi-Region Deployment

```yaml
# docker-compose.yml for multi-region deployment
version: '3.8'
services:
  web:
    image: myapp:latest
    ports:
      - "80:8080"
    environment:
      - REGION=${AWS_REGION}
      - DB_ENDPOINT=${DB_ENDPOINT}
      - REDIS_ENDPOINT=${REDIS_ENDPOINT}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

### 2. Lambda Function DR

```python
# Lambda function with cross-region deployment
import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Get region from environment
    region = os.environ.get('AWS_REGION')
    
    # Initialize clients with retry configuration
    config = boto3.session.Config(
        retries={'max_attempts': 3, 'mode': 'adaptive'},
        region_name=region
    )
    
    dynamodb = boto3.resource('dynamodb', config=config)
    
    try:
        # Primary operation
        table = dynamodb.Table('UserData')
        response = table.get_item(Key={'userId': event['userId']})
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'data': response.get('Item', {}),
                'region': region
            })
        }
        
    except ClientError as e:
        # Log error and return graceful failure
        print(f"Error in region {region}: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Service temporarily unavailable',
                'region': region
            })
        }

# SAM template for multi-region deployment
```

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  Environment:
    Type: String
    Default: prod
  Region:
    Type: String
    Default: us-east-1

Globals:
  Function:
    Timeout: 30
    MemorySize: 512
    Runtime: python3.9
    Environment:
      Variables:
        ENVIRONMENT: !Ref Environment
        REGION: !Ref Region

Resources:
  UserDataFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: app.lambda_handler
      Events:
        Api:
          Type: Api
          Properties:
            Path: /users/{userId}
            Method: get
      DeadLetterQueue:
        Type: SQS
        TargetArn: !GetAtt ErrorQueue.Arn
      ReservedConcurrencyLimit: 100

  ErrorQueue:
    Type: AWS::SQS::Queue
    Properties:
      MessageRetentionPeriod: 1209600  # 14 days
      VisibilityTimeoutSeconds: 60
```

---

## Infrastructure as Code for DR

### 1. Terraform Multi-Region Module

```hcl
# modules/multi-region-app/main.tf
variable "regions" {
  description = "List of regions to deploy to"
  type        = list(string)
  default     = ["us-east-1", "us-west-2"]
}

variable "primary_region" {
  description = "Primary region"
  type        = string
  default     = "us-east-1"
}

# Deploy to multiple regions
module "app_deployment" {
  for_each = toset(var.regions)
  source   = "./region-deployment"
  
  region         = each.value
  is_primary     = each.value == var.primary_region
  app_name       = var.app_name
  environment    = var.environment
  
  providers = {
    aws = aws.region[each.value]
  }
}

# Configure providers for each region
provider "aws" {
  for_each = toset(var.regions)
  alias    = "region.${each.value}"
  region   = each.value
}

# Route 53 health checks and failover
resource "aws_route53_health_check" "primary" {
  fqdn                            = module.app_deployment[var.primary_region].load_balancer_dns
  port                            = 443
  type                            = "HTTPS"
  resource_path                   = "/health"
  failure_threshold               = "3"
  request_interval                = "30"
  cloudwatch_alarm_region         = var.primary_region
  cloudwatch_alarm_name           = "healthcheck-failed"
  insufficient_data_health_status = "Failure"

  tags = {
    Name = "${var.app_name}-primary-health-check"
  }
}

resource "aws_route53_record" "primary" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"
  
  set_identifier = "primary"
  failover_routing_policy {
    type = "PRIMARY"
  }
  
  health_check_id = aws_route53_health_check.primary.id
  ttl             = 60
  
  records = [module.app_deployment[var.primary_region].load_balancer_ip]
}
```

### 2. CloudFormation StackSets for Multi-Account DR

```yaml
# stackset-template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Multi-account DR infrastructure'

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
  PrimaryAccount:
    Type: String
    Description: 'Primary AWS Account ID'
  DRAccount:
    Type: String
    Description: 'DR AWS Account ID'

Conditions:
  IsPrimaryAccount: !Equals [!Ref 'AWS::AccountId', !Ref PrimaryAccount]
  IsDRAccount: !Equals [!Ref 'AWS::AccountId', !Ref DRAccount]

Resources:
  # VPC Configuration
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !If 
        - IsPrimaryAccount
        - '10.0.0.0/16'
        - '10.1.0.0/16'
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-${AWS::Region}-vpc'

  # Cross-account role for DR operations
  DRRole:
    Type: AWS::IAM::Role
    Condition: IsDRAccount
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${PrimaryAccount}:root'
            Action: sts:AssumeRole
            Condition:
              StringEquals:
                'sts:ExternalId': 'dr-operations'
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/PowerUserAccess

  # SNS Topic for DR notifications
  DRNotificationTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub '${Environment}-dr-notifications'
      DisplayName: 'DR Operations Notifications'
```

---

## Monitoring & Alerting

### 1. CloudWatch Alarms for DR

```python
import boto3
import json

def create_dr_monitoring():
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    
    # Create SNS topic for DR alerts
    topic_response = sns.create_topic(Name='dr-critical-alerts')
    topic_arn = topic_response['TopicArn']
    
    # Database connection alarm
    cloudwatch.put_metric_alarm(
        AlarmName='RDS-Connection-Failures',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='DatabaseConnections',
        Namespace='AWS/RDS',
        Period=300,
        Statistic='Average',
        Threshold=0.0,
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        AlarmDescription='RDS connection failures detected',
        Dimensions=[
            {
                'Name': 'DBInstanceIdentifier',
                'Value': 'myapp-primary'
            }
        ]
    )
    
    # Application health check alarm
    cloudwatch.put_metric_alarm(
        AlarmName='Application-Health-Check-Failed',
        ComparisonOperator='LessThanThreshold',
        EvaluationPeriods=3,
        MetricName='HealthyHostCount',
        Namespace='AWS/ApplicationELB',
        Period=60,
        Statistic='Average',
        Threshold=1.0,
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        AlarmDescription='Application health check failures',
        Dimensions=[
            {
                'Name': 'TargetGroup',
                'Value': 'app-primary-tg'
            }
        ]
    )
    
    # Cross-region replication lag alarm
    cloudwatch.put_metric_alarm(
        AlarmName='RDS-Replica-Lag',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='ReplicaLag',
        Namespace='AWS/RDS',
        Period=300,
        Statistic='Average',
        Threshold=300.0,  # 5 minutes
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        AlarmDescription='RDS replica lag exceeds threshold'
    )

# Custom metric for application-level monitoring
def publish_custom_metrics():
    cloudwatch = boto3.client('cloudwatch')
    
    # Business metric: Orders per minute
    cloudwatch.put_metric_data(
        Namespace='MyApp/Business',
        MetricData=[
            {
                'MetricName': 'OrdersPerMinute',
                'Value': get_orders_count(),
                'Unit': 'Count',
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': 'production'
                    },
                    {
                        'Name': 'Region',
                        'Value': boto3.Session().region_name
                    }
                ]
            }
        ]
    )
```

### 2. AWS Config Rules for DR Compliance

```json
{
  "ConfigRuleName": "rds-multi-az-enabled",
  "Description": "Checks if RDS instances are configured for Multi-AZ",
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "RDS_MULTI_AZ_SUPPORT"
  },
  "Scope": {
    "ComplianceResourceTypes": [
      "AWS::RDS::DBInstance"
    ]
  }
}
```

---

## Testing & Validation

### 1. Automated DR Testing Script

```bash
#!/bin/bash
# dr-test.sh - Automated DR testing script

set -e

# Configuration
PRIMARY_REGION="us-east-1"
DR_REGION="us-west-2"
APP_NAME="myapp"
TEST_DURATION=300  # 5 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Test 1: Health Check Validation
test_health_checks() {
    log "Testing health checks..."
    
    # Primary region health check
    PRIMARY_HEALTH=$(aws route53 get-health-check \
        --health-check-id $(aws route53 list-health-checks \
        --query "HealthChecks[?contains(FullyQualifiedDomainName, '${APP_NAME}')].Id" \
        --output text) \
        --query 'HealthCheck.HealthCheckConfig.FullyQualifiedDomainName' \
        --output text)
    
    if curl -f "https://${PRIMARY_HEALTH}/health" > /dev/null 2>&1; then
        log "✓ Primary region health check passed"
    else
        error "✗ Primary region health check failed"
    fi
}

# Test 2: Database Failover
test_database_failover() {
    log "Testing database failover..."
    
    # Get RDS instance identifier
    DB_INSTANCE=$(aws rds describe-db-instances \
        --region $PRIMARY_REGION \
        --query "DBInstances[?contains(DBInstanceIdentifier, '${APP_NAME}')].DBInstanceIdentifier" \
        --output text)
    
    if [ -z "$DB_INSTANCE" ]; then
        error "No RDS instance found for $APP_NAME"
    fi
    
    # Initiate failover
    log "Initiating RDS failover for $DB_INSTANCE..."
    aws rds reboot-db-instance \
        --db-instance-identifier $DB_INSTANCE \
        --force-failover \
        --region $PRIMARY_REGION
    
    # Wait for failover to complete
    log "Waiting for failover to complete..."
    aws rds wait db-instance-available \
        --db-instance-identifier $DB_INSTANCE \
        --region $PRIMARY_REGION
    
    log "✓ Database failover completed"
}

# Test 3: Application Failover
test_application_failover() {
    log "Testing application failover..."
    
    # Get current primary endpoint
    CURRENT_PRIMARY=$(dig +short ${APP_NAME}.example.com)
    log "Current primary endpoint: $CURRENT_PRIMARY"
    
    # Simulate primary region failure by updating Route 53 health check
    HEALTH_CHECK_ID=$(aws route53 list-health-checks \
        --query "HealthChecks[?contains(FullyQualifiedDomainName, '${APP_NAME}')].Id" \
        --output text)
    
    # Temporarily disable health check to trigger failover
    aws route53 update-health-check \
        --health-check-id $HEALTH_CHECK_ID \
        --disabled
    
    log "Waiting for DNS failover..."
    sleep 120  # Wait for DNS propagation
    
    # Check if traffic is now going to DR region
    NEW_ENDPOINT=$(dig +short ${APP_NAME}.example.com)
    if [ "$NEW_ENDPOINT" != "$CURRENT_PRIMARY" ]; then
        log "✓ DNS failover successful. New endpoint: $NEW_ENDPOINT"
    else
        warn "DNS failover may not have completed yet"
    fi
    
    # Re-enable health check
    aws route53 update-health-check \
        --health-check-id $HEALTH_CHECK_ID \
        --no-disabled
}

# Test 4: Data Consistency Check
test_data_consistency() {
    log "Testing data consistency between regions..."
    
    # Compare S3 bucket contents
    PRIMARY_OBJECTS=$(aws s3api list-objects-v2 \
        --bucket ${APP_NAME}-primary-backup \
        --region $PRIMARY_REGION \
        --query 'Contents | length(@)')
    
    DR_OBJECTS=$(aws s3api list-objects-v2 \
        --bucket ${APP_NAME}-dr-backup \
        --region $DR_REGION \
        --query 'Contents | length(@)')
    
    if [ "$PRIMARY_OBJECTS" -eq "$DR_OBJECTS" ]; then
        log "✓ S3 data consistency check passed"
    else
        warn "S3 data consistency check failed. Primary: $PRIMARY_OBJECTS, DR: $DR_OBJECTS"
    fi
}

# Test 5: Recovery Time Measurement
measure_recovery_time() {
    log "Measuring recovery time..."
    
    START_TIME=$(date +%s)
    
    # Simulate service restoration
    # This would typically involve:
    # 1. Promoting read replica to primary
    # 2. Updating DNS records
    # 3. Scaling up DR infrastructure
    # 4. Running database migrations if needed
    
    # For demo purposes, we'll simulate these steps
    log "Simulating service restoration steps..."
    sleep 30  # Simulate promotion time
    
    END_TIME=$(date +%s)
    RECOVERY_TIME=$((END_TIME - START_TIME))
    
    log "✓ Recovery completed in ${RECOVERY_TIME} seconds"
    
    # Check if RTO is met
    if [ $RECOVERY_TIME -le 900 ]; then  # 15 minutes
        log "✓ RTO requirement met (< 15 minutes)"
    else
        warn "RTO requirement not met. Recovery took ${RECOVERY_TIME} seconds"
    fi
}

# Main test execution
main() {
    log "Starting DR test for $APP_NAME"
    log "Primary Region: $PRIMARY_REGION"
    log "DR Region: $DR_REGION"
    
    # Run tests
    test_health_checks
    test_data_consistency
    test_database_failover
    test_application_failover
    measure_recovery_time
    
    log "DR testing completed successfully!"
}

# Execute main function
main "$@"
```

### 2. Chaos Engineering with AWS Fault Injection Simulator

```yaml
# FIS experiment template
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Chaos engineering experiment for DR testing'

Resources:
  DRChaosExperiment:
    Type: AWS::FIS::ExperimentTemplate
    Properties:
      Description: 'Test application resilience by stopping EC2 instances'
      RoleArn: !GetAtt FISRole.Arn
      Actions:
        StopInstances:
          ActionId: 'aws:ec2:stop-instances'
          Parameters:
            startInstancesAfterDuration: 'PT10M'  # 10 minutes
          Targets:
            Instances: 'WebServerInstances'
      Targets:
        WebServerInstances:
          ResourceType: 'aws:ec2:instance'
          ResourceTags:
            Environment: 'production'
            Application: 'myapp'
          SelectionMode: 'PERCENT(50)'  # Stop 50% of instances
      StopConditions:
        - Source: 'aws:cloudwatch:alarm'
          Value: !Ref HighErrorRateAlarm
      Tags:
        - Key: 'Name'
          Value: 'DR-Chaos-Test'

  FISRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: fis.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorEC2Access
```

---

## Cost Optimization

### 1. DR Cost Analysis Script

```python
import boto3
import json
from datetime import datetime, timedelta

class DRCostAnalyzer:
    def __init__(self):
        self.ce_client = boto3.client('ce')
        self.ec2_client = boto3.client('ec2')
        self.rds_client = boto3.client('rds')
        
    def get_dr_costs(self, days=30):
        """Get DR-related costs for the last N days"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        response = self.ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'TAG', 'Key': 'Purpose'}
            ],
            Filter={
                'Tags': {
                    'Key': 'Purpose',
                    'Values': ['DR', 'DisasterRecovery']
                }
            }
        )
        
        return response
    
    def analyze_unused_dr_resources(self):
        """Identify unused DR resources that can be optimized"""
        unused_resources = []
        
        # Check for unused EBS volumes
        volumes = self.ec2_client.describe_volumes(
            Filters=[
                {'Name': 'state', 'Values': ['available']},
                {'Name': 'tag:Purpose', 'Values': ['DR']}
            ]
        )
        
        for volume in volumes['Volumes']:
            unused_resources.append({
                'type': 'EBS Volume',
                'id': volume['VolumeId'],
                'size': volume['Size'],
                'cost_per_month': volume['Size'] * 0.10  # Approximate cost
            })
        
        # Check for stopped instances that could be terminated
        instances = self.ec2_client.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['stopped']},
                {'Name': 'tag:Purpose', 'Values': ['DR']}
            ]
        )
        
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                unused_resources.append({
                    'type': 'EC2 Instance',
                    'id': instance['InstanceId'],
                    'instance_type': instance['InstanceType'],
                    'estimated_monthly_cost': self.get_instance_cost(instance['InstanceType'])
                })
        
        return unused_resources
    
    def get_instance_cost(self, instance_type):
        """Get approximate monthly cost for instance type"""
        # Simplified cost calculation - in reality, use AWS Pricing API
        cost_map = {
            't3.micro': 8.47,
            't3.small': 16.94,
            't3.medium': 33.89,
            'm5.large': 70.08,
            'm5.xlarge': 140.16
        }
        return cost_map.get(instance_type, 50.0)
    
    def recommend_optimizations(self):
        """Provide cost optimization recommendations"""
        recommendations = []
        
        # Check RDS instances for right-sizing opportunities
        db_instances = self.rds_client.describe_db_instances()
        
        for db in db_instances['DBInstances']:
            if 'DR' in db.get('DBInstanceIdentifier', ''):
                # Get CloudWatch metrics to determine if instance is oversized
                recommendations.append({
                    'resource': db['DBInstanceIdentifier'],
                    'current_class': db['DBInstanceClass'],
                    'recommendation': 'Consider using smaller instance class for DR replica',
                    'potential_savings': '30-50%'
                })
        
        return recommendations

# Usage example
analyzer = DRCostAnalyzer()
costs = analyzer.get_dr_costs()
unused = analyzer.analyze_unused_dr_resources()
recommendations = analyzer.recommend_optimizations()

print(f"DR costs: {json.dumps(costs, indent=2, default=str)}")
print(f"Unused resources: {json.dumps(unused, indent=2)}")
print(f"Recommendations: {json.dumps(recommendations, indent=2)}")
```

### 2. Automated DR Resource Scheduling

```python
import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    """
    Lambda function to automatically start/stop DR resources based on schedule
    """
    ec2 = boto3.client('ec2')
    rds = boto3.client('rds')
    
    action = event.get('action', 'stop')  # 'start' or 'stop'
    
    if action == 'stop':
        # Stop non-critical DR resources during off-hours
        stop_dr_resources(ec2, rds)
    elif action == 'start':
        # Start DR resources during business hours
        start_dr_resources(ec2, rds)
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'DR resources {action} operation completed')
    }

def stop_dr_resources(ec2, rds):
    """Stop DR resources to save costs"""
    
    # Stop EC2 instances tagged for DR (non-critical)
    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Purpose', 'Values': ['DR']},
            {'Name': 'tag:Critical', 'Values': ['false']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            ec2.stop_instances(InstanceIds=[instance['InstanceId']])
            print(f"Stopped instance: {instance['InstanceId']}")
    
    # Stop RDS instances (non-production DR replicas)
    db_instances = rds.describe_db_instances()
    for db in db_instances['DBInstances']:
        if ('dr' in db['DBInstanceIdentifier'].lower() and 
            'non-prod' in db.get('TagList', [])):
            rds.stop_db_instance(DBInstanceIdentifier=db['DBInstanceIdentifier'])
            print(f"Stopped RDS instance: {db['DBInstanceIdentifier']}")

def start_dr_resources(ec2, rds):
    """Start DR resources for business hours"""
    
    # Start EC2 instances
    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Purpose', 'Values': ['DR']},
            {'Name': 'tag:Critical', 'Values': ['false']},
            {'Name': 'instance-state-name', 'Values': ['stopped']}
        ]
    )
    
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            ec2.start_instances(InstanceIds=[instance['InstanceId']])
            print(f"Started instance: {instance['InstanceId']}")
    
    # Start RDS instances
    db_instances = rds.describe_db_instances()
    for db in db_instances['DBInstances']:
        if (db['DBInstanceStatus'] == 'stopped' and 
            'dr' in db['DBInstanceIdentifier'].lower()):
            rds.start_db_instance(DBInstanceIdentifier=db['DBInstanceIdentifier'])
            print(f"Started RDS instance: {db['DBInstanceIdentifier']}")
```

---

## Interview Scenarios

### Scenario 1: E-commerce Platform DR Design

**Question**: "Design a DR solution for an e-commerce platform that processes $1M in revenue per hour during peak times. The platform uses microservices architecture with RDS MySQL, Redis, and S3. What's your approach?"

**Answer Framework**:

1. **Requirements Analysis**:
   - RTO: < 15 minutes (high revenue impact)
   - RPO: < 5 minutes (financial transactions)
   - Availability: 99.99% (4 minutes downtime/month)

2. **Architecture Design**:
```
Primary Region (us-east-1):
├── ALB → ECS Fargate (3 AZs)
├── RDS MySQL Multi-AZ
├── ElastiCache Redis (Cluster Mode)
└── S3 with Cross-Region Replication

DR Region (us-west-2):
├── ALB → ECS Fargate (Scaled down)
├── RDS Read Replica
├── ElastiCache Redis (Standby)
└── S3 Replica Bucket
```

3. **Implementation Steps**:
```bash
# 1. Set up cross-region RDS replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier ecommerce-dr-replica \
  --source-db-instance-identifier arn:aws:rds:us-east-1:123456789012:db:ecommerce-primary

# 2. Configure Route 53 health checks
aws route53 create-health-check \
  --caller-reference "ecommerce-primary-$(date +%s)" \
  --health-check-config '{
    "Type": "HTTPS",
    "ResourcePath": "/api/health",
    "FullyQualifiedDomainName": "api.ecommerce.com",
    "Port": 443,
    "RequestInterval": 30,
    "FailureThreshold": 2
  }'

# 3. Set up automated failover
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://failover-config.json
```

4. **Cost Optimization**:
   - Use Spot Instances for DR region (60% cost savings)
   - Implement automated scaling based on health checks
   - Use S3 Intelligent Tiering for backup data

5. **Testing Strategy**:
   - Monthly failover tests during maintenance windows
   - Chaos engineering with AWS FIS
   - Automated recovery time measurement

**Expected Results**:
- RTO: 10-12 minutes
- RPO: 2-3 minutes
- Cost: 40% of primary region
- Availability: 99.995%

### Scenario 2: Multi-Tier Application with Compliance Requirements

**Question**: "A healthcare application needs DR with HIPAA compliance. It has a web tier, application tier, and database tier. How do you ensure both DR and compliance?"

**Answer Framework**:

1. **Compliance Requirements**:
   - Data encryption at rest and in transit
   - Audit logging for all access
   - Data residency requirements
   - Access controls and authentication

2. **DR Architecture with Compliance**:
```yaml
# CloudFormation template snippet
Resources:
  # Encrypted RDS with automated backups
  PrimaryDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      StorageEncrypted: true
      KmsKeyId: !Ref DatabaseKMSKey
      BackupRetentionPeriod: 35
      DeletionProtection: true
      EnableCloudwatchLogsExports:
        - error
        - general
        - slow-query

  # Cross-region encrypted backup
  BackupBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: aws:kms
              KMSMasterKeyID: !Ref BackupKMSKey
      VersioningConfiguration:
        Status: Enabled
      LoggingConfiguration:
        DestinationBucketName: !Ref AccessLogsBucket
        LogFilePrefix: backup-access-logs/
```

3. **Security Controls**:
```python
# Automated compliance checking
def check_compliance():
    checks = []
    
    # Verify encryption
    rds_client = boto3.client('rds')
    instances = rds_client.describe_db_instances()
    
    for db in instances['DBInstances']:
        if not db.get('StorageEncrypted', False):
            checks.append({
                'resource': db['DBInstanceIdentifier'],
                'issue': 'Storage not encrypted',
                'severity': 'HIGH'
            })
    
    # Verify backup retention
    for db in instances['DBInstances']:
        if db.get('BackupRetentionPeriod', 0) < 30:
            checks.append({
                'resource': db['DBInstanceIdentifier'],
                'issue': 'Backup retention < 30 days',
                'severity': 'MEDIUM'
            })
    
    return checks
```

### Scenario 3: Global Application with Active-Active DR

**Question**: "Design an active-active DR solution for a global SaaS application with users in US, Europe, and Asia. How do you handle data consistency and routing?"

**Answer Framework**:

1. **Global Architecture**:
```
US East (Primary):
├── CloudFront → ALB → ECS
├── Aurora Global Database (Writer)
├── DynamoDB Global Tables
└── S3 Cross-Region Replication

Europe (Active):
├── CloudFront → ALB → ECS  
├── Aurora Global Database (Reader)
├── DynamoDB Global Tables
└── S3 Cross-Region Replication

Asia (Active):
├── CloudFront → ALB → ECS
├── Aurora Global Database (Reader)  
├── DynamoDB Global Tables
└── S3 Cross-Region Replication
```

2. **Data Consistency Strategy**:
```python
# Implement eventual consistency with conflict resolution
class GlobalDataManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('UserProfiles')
    
    def update_user_profile(self, user_id, updates):
        # Add timestamp and region for conflict resolution
        item = {
            'userId': user_id,
            'lastModified': int(time.time() * 1000),
            'modifiedBy': boto3.Session().region_name,
            **updates
        }
        
        # Use conditional writes to prevent conflicts
        try:
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(lastModified) OR lastModified < :timestamp',
                ExpressionAttributeValues={':timestamp': item['lastModified']}
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                # Handle conflict - implement last-writer-wins or custom logic
                return self.resolve_conflict(user_id, item)
            raise
```

3. **Traffic Routing**:
```bash
# Route 53 geolocation routing
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.myapp.com",
        "Type": "A",
        "SetIdentifier": "US",
        "GeoLocation": {"CountryCode": "US"},
        "TTL": 60,
        "ResourceRecords": [{"Value": "1.2.3.4"}]
      }
    }, {
      "Action": "CREATE", 
      "ResourceRecordSet": {
        "Name": "api.myapp.com",
        "Type": "A",
        "SetIdentifier": "EU",
        "GeoLocation": {"ContinentCode": "EU"},
        "TTL": 60,
        "ResourceRecords": [{"Value": "5.6.7.8"}]
      }
    }]
  }'
```

### Scenario 4: Cost-Optimized DR for Startup

**Question**: "A startup needs DR but has budget constraints. They can tolerate 4-hour RTO and 1-hour RPO. Design a cost-effective solution."

**Answer Framework**:

1. **Budget-Conscious Architecture**:
```
Primary Region:
├── Single AZ deployment
├── RDS with automated backups
├── EBS snapshots
└── S3 Standard storage

DR Strategy:
├── Cross-region S3 replication (IA storage)
├── RDS automated backups only
├── AMI snapshots for quick recovery
└── Infrastructure as Code for rapid deployment
```

2. **Cost Optimization Techniques**:
```python
# Automated backup lifecycle management
def setup_cost_optimized_backups():
    s3_client = boto3.client('s3')
    
    # Configure S3 lifecycle policy
    lifecycle_config = {
        'Rules': [
            {
                'ID': 'DR-Backup-Lifecycle',
                'Status': 'Enabled',
                'Filter': {'Prefix': 'backups/'},
                'Transitions': [
                    {
                        'Days': 30,
                        'StorageClass': 'STANDARD_IA'
                    },
                    {
                        'Days': 90,
                        'StorageClass': 'GLACIER'
                    },
                    {
                        'Days': 365,
                        'StorageClass': 'DEEP_ARCHIVE'
                    }
                ]
            }
        ]
    }
    
    s3_client.put_bucket_lifecycle_configuration(
        Bucket='startup-dr-backups',
        LifecycleConfiguration=lifecycle_config
    )

# Spot instance recovery script
def deploy_dr_infrastructure():
    ec2 = boto3.client('ec2')
    
    # Launch spot instances for cost savings
    response = ec2.request_spot_instances(
        SpotPrice='0.05',  # 70% savings vs on-demand
        InstanceCount=2,
        LaunchSpecification={
            'ImageId': 'ami-12345678',  # Pre-configured AMI
            'InstanceType': 't3.medium',
            'KeyName': 'startup-key',
            'SecurityGroups': ['dr-security-group'],
            'UserData': base64.b64encode(startup_script.encode()).decode()
        }
    )
    
    return response
```

3. **Recovery Automation**:
```bash
#!/bin/bash
# Quick recovery script for startup DR

# 1. Restore RDS from latest automated backup
LATEST_BACKUP=$(aws rds describe-db-snapshots \
  --db-instance-identifier startup-prod \
  --snapshot-type automated \
  --query 'DBSnapshots | sort_by(@, &SnapshotCreateTime) | [-1].DBSnapshotIdentifier' \
  --output text)

aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier startup-dr-restored \
  --db-snapshot-identifier $LATEST_BACKUP

# 2. Launch application instances from AMI
aws ec2 run-instances \
  --image-id ami-12345678 \
  --count 2 \
  --instance-type t3.medium \
  --key-name startup-key \
  --security-group-ids sg-12345678 \
  --user-data file://startup-script.sh

# 3. Update DNS to point to DR region
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://dr-dns-update.json
```

**Expected Results**:
- Monthly DR cost: < $200
- RTO: 2-3 hours (within 4-hour requirement)
- RPO: 30 minutes (better than 1-hour requirement)
- Recovery success rate: 95%

---

## Key Interview Talking Points

### 1. Business Impact Quantification
- "Reduced potential revenue loss from $1M/hour to $50K during DR events"
- "Achieved 99.99% availability, exceeding SLA requirements"
- "Optimized DR costs by 60% through automated resource scheduling"

### 2. Technical Depth
- "Implemented Aurora Global Database with <1 second cross-region replication"
- "Used Route 53 health checks with 30-second intervals and 3-failure threshold"
- "Automated failover reduces manual intervention from 45 minutes to 5 minutes"

### 3. Operational Excellence
- "Conducted monthly DR tests with automated rollback procedures"
- "Implemented chaos engineering to validate system resilience"
- "Created runbooks with step-by-step recovery procedures"

### 4. Cost Optimization
- "Used S3 Intelligent Tiering to reduce backup storage costs by 40%"
- "Implemented spot instances in DR region for 70% compute cost savings"
- "Automated resource scheduling saves $10K/month in off-hours"

### 5. Compliance & Security
- "Ensured HIPAA compliance with end-to-end encryption and audit logging"
- "Implemented cross-account IAM roles for secure DR operations"
- "Maintained data residency requirements across all regions"

This comprehensive guide covers all aspects of AWS DR and business continuity, providing practical examples and real-world scenarios perfect for interview preparation. Each section includes working code, CLI commands, and quantified results that demonstrate deep technical knowledge and business impact understanding.