# AWS Disaster Recovery: Complete Planning and Implementation Guide

## 🎯 Understanding Disaster Recovery: The Business Reality

### The Cost of Downtime

**Real-World Downtime Impact:**
```
Industry Downtime Costs (per hour):
• E-commerce: $300,000 - $1,000,000
• Financial Services: $2,600,000 - $5,000,000
• Healthcare: $636,000 - $8,000,000
• Manufacturing: $50,000 - $500,000
• SaaS Platforms: $140,000 - $540,000

Additional Hidden Costs:
• Customer churn: 25% after major outage
• Brand reputation damage: 6-12 months recovery
• Regulatory fines: Up to $10M for financial services
• Employee productivity loss: 40% during recovery
• Legal liability: Class action lawsuits
```

**Disaster Types and Frequency:**
```
Natural Disasters:
• Earthquakes: 1 in 500 year probability per region
• Floods: 1 in 100 year probability
• Hurricanes: Annual in certain regions
• Wildfires: Increasing frequency due to climate change

Human-Caused Disasters:
• Cyber attacks: 1 every 39 seconds globally
• Data center failures: 25% experience outages annually
• Network outages: 88% of companies experience
• Human error: 95% of successful cyber attacks
• Power grid failures: Regional blackouts
```

**Business Continuity Requirements:**
```
Regulatory Compliance:
• SOX: Financial data availability requirements
• HIPAA: Healthcare data protection and availability
• PCI DSS: Payment processing continuity
• GDPR: Data availability and recovery obligations
• Basel III: Banking operational resilience

Business Requirements:
• Revenue protection during outages
• Customer experience continuity
• Competitive advantage maintenance
• Stakeholder confidence preservation
• Market position protection
```

### Why AWS for Disaster Recovery?

**AWS DR Value Proposition:**

**Infrastructure Benefits:**
• 31 regions with 99 availability zones
• Global network with low-latency connections
• 99.99% SLA for most services
• Automated failover capabilities
• Pay-as-you-go DR resources
• Elastic scaling during disasters

**Service Integration:**
• Native backup and replication services
• Cross-region data synchronization
• Automated recovery orchestration
• Infrastructure as Code (IaC) support
• Monitoring and alerting integration
• Compliance and audit capabilities

**Business Impact Examples:**

**Global E-commerce Platform:**
• Challenge: Black Friday traffic with zero tolerance for downtime
• Risk: $50M revenue loss per hour of downtime
• Solution: Multi-region active-active DR with Route 53 failover
• Result: 99.99% uptime during peak season, $200M revenue protected

**Healthcare SaaS Provider:**
• Challenge: HIPAA compliance with 4-hour RTO requirement
• Risk: $1.5M regulatory fines, patient safety concerns
• Solution: Pilot Light DR with automated failover
• Result: 2-hour actual RTO, zero compliance violations

**Financial Services Company:**
• Challenge: Regulatory requirement for 1-hour RTO/15-minute RPO
• Risk: $10M daily regulatory fines, trading license suspension
• Solution: Warm Standby with real-time data replication
• Result: 45-minute RTO, 5-minute RPO achieved

## 🏗️ AWS DR Architecture Patterns

### Understanding RTO and RPO

**Recovery Time Objective (RTO):**
```
Definition: Maximum acceptable time to restore service after disaster

Business Impact by RTO:
• 0-1 hour: Mission-critical systems (trading, emergency services)
• 1-4 hours: High-priority business systems (e-commerce, banking)
• 4-24 hours: Important business systems (CRM, ERP)
• 24+ hours: Non-critical systems (reporting, analytics)

Cost Relationship:
• Lower RTO = Higher DR costs
• Exponential cost increase as RTO approaches zero
• Balance business needs with budget constraints
```

**Recovery Point Objective (RPO):**
```
Definition: Maximum acceptable data loss measured in time

Business Impact by RPO:
• 0-15 minutes: Financial transactions, real-time systems
• 15 minutes-1 hour: Customer-facing applications
• 1-4 hours: Internal business applications
• 4+ hours: Reporting and analytics systems

Data Loss Impact:
• Financial: $5,600 per minute of data loss
• Healthcare: Patient safety and compliance risks
• E-commerce: Customer trust and revenue loss
• Manufacturing: Supply chain disruption
```

### AWS DR Patterns Overview

**Four Main DR Patterns:**

**1. Backup and Restore (Lowest Cost)**
```
What it is: Regular backups with manual restoration process
RTO: 24+ hours
RPO: 1-24 hours
Cost: Lowest (backup storage only)
Use case: Non-critical systems, development environments
```

**2. Pilot Light (Low Cost)**
```
What it is: Minimal DR environment with core components always running
RTO: 1-4 hours
RPO: 15 minutes-1 hour
Cost: Low (minimal infrastructure + data replication)
Use case: Important business systems with moderate availability needs
```

**3. Warm Standby (Medium Cost)**
```
What it is: Scaled-down but functional DR environment
RTO: 5-30 minutes
RPO: 5-15 minutes
Cost: Medium (running infrastructure + data replication)
Use case: High-priority systems with strict availability requirements
```

**4. Multi-Site Active-Active (Highest Cost)**
```
What it is: Full production environment in multiple regions
RTO: 0-5 minutes (automatic failover)
RPO: 0-5 minutes (real-time replication)
Cost: Highest (duplicate infrastructure)
Use case: Mission-critical systems with zero tolerance for downtime
```

## 🚀 Complete Implementation: E-commerce Platform DR

### Business Scenario

**Application Architecture:**
```
E-commerce Platform Components:
• Web Application: React frontend on CloudFront + S3
• API Gateway: RESTful APIs with Lambda functions
• Application Servers: ECS containers with Auto Scaling
• Database: RDS PostgreSQL with read replicas
• Cache: ElastiCache Redis cluster
• Search: OpenSearch cluster
• File Storage: S3 buckets for product images
• CDN: CloudFront for global content delivery
• DNS: Route 53 for traffic routing
```

**Business Requirements:**
```
Availability Requirements:
• Black Friday: 99.99% uptime (5.25 minutes downtime max)
• Regular operations: 99.9% uptime (8.77 hours downtime max)
• Peak traffic: 10x normal load handling
• Global users: <200ms response time worldwide

Recovery Requirements:
• RTO: 15 minutes for critical path (checkout, payments)
• RPO: 5 minutes for transaction data
• RTO: 1 hour for full functionality restoration
• RPO: 15 minutes for product catalog data
```

### Recommended Approach: Warm Standby with Automated Failover

**Why Warm Standby is Recommended:**
```
Business Justification:
• Balances cost with availability requirements
• Meets 15-minute RTO for critical systems
• Provides automated failover capabilities
• Supports compliance requirements
• Enables testing and validation
• Scales cost-effectively with business growth

Technical Benefits:
• Faster recovery than Pilot Light
• Lower cost than Active-Active
• Automated failover reduces human error
• Supports gradual traffic shifting
• Enables blue-green deployments
• Provides disaster recovery testing capability
```

### Step 1: Primary Region Setup (us-east-1)

**VPC and Network Configuration:**
```bash
# Create primary VPC
aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=ecommerce-primary-vpc},{Key=Environment,Value=production}]' \
    --region us-east-1

# Create public subnets for ALB
aws ec2 create-subnet \
    --vpc-id vpc-12345678 \
    --cidr-block 10.0.1.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=primary-public-1a}]'

aws ec2 create-subnet \
    --vpc-id vpc-12345678 \
    --cidr-block 10.0.2.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=primary-public-1b}]'

# Create private subnets for applications
aws ec2 create-subnet \
    --vpc-id vpc-12345678 \
    --cidr-block 10.0.10.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=primary-private-1a}]'

aws ec2 create-subnet \
    --vpc-id vpc-12345678 \
    --cidr-block 10.0.11.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=primary-private-1b}]'

# Create database subnets
aws ec2 create-subnet \
    --vpc-id vpc-12345678 \
    --cidr-block 10.0.20.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=primary-db-1a}]'

aws ec2 create-subnet \
    --vpc-id vpc-12345678 \
    --cidr-block 10.0.21.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=primary-db-1b}]'
```

**RDS Database with Cross-Region Replication:**
```bash
# Create DB subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name ecommerce-primary-subnet-group \
    --db-subnet-group-description "Primary region DB subnet group" \
    --subnet-ids subnet-12345678 subnet-87654321 \
    --region us-east-1

# Create primary RDS instance with automated backups
aws rds create-db-instance \
    --db-instance-identifier ecommerce-primary-db \
    --db-instance-class db.r6g.xlarge \
    --engine postgres \
    --engine-version 14.9 \
    --master-username dbadmin \
    --master-user-password SecurePassword123! \
    --allocated-storage 100 \
    --storage-type gp3 \
    --storage-encrypted \
    --kms-key-id alias/aws/rds \
    --vpc-security-group-ids sg-12345678 \
    --db-subnet-group-name ecommerce-primary-subnet-group \
    --backup-retention-period 7 \
    --backup-window "03:00-04:00" \
    --maintenance-window "sun:04:00-sun:05:00" \
    --multi-az \
    --auto-minor-version-upgrade \
    --deletion-protection \
    --enable-performance-insights \
    --performance-insights-retention-period 7 \
    --region us-east-1

# Create read replica in DR region
aws rds create-db-instance-read-replica \
    --db-instance-identifier ecommerce-dr-replica \
    --source-db-instance-identifier arn:aws:rds:us-east-1:123456789012:db:ecommerce-primary-db \
    --db-instance-class db.r6g.large \
    --storage-encrypted \
    --kms-key-id alias/aws/rds \
    --vpc-security-group-ids sg-87654321 \
    --db-subnet-group-name ecommerce-dr-subnet-group \
    --auto-minor-version-upgrade \
    --region us-west-2
```

**ECS Cluster and Services:**
```bash
# Create ECS cluster
aws ecs create-cluster \
    --cluster-name ecommerce-primary \
    --capacity-providers EC2 FARGATE \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --region us-east-1

# Create task definition
cat > ecommerce-task-definition.json << 'EOF'
{
    "family": "ecommerce-app",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "1024",
    "memory": "2048",
    "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
    "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
    "containerDefinitions": [
        {
            "name": "ecommerce-app",
            "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/ecommerce-app:latest",
            "portMappings": [
                {
                    "containerPort": 8080,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "DB_HOST",
                    "value": "ecommerce-primary-db.cluster-xyz.us-east-1.rds.amazonaws.com"
                },
                {
                    "name": "REDIS_HOST",
                    "value": "ecommerce-primary-cache.xyz.cache.amazonaws.com"
                },
                {
                    "name": "REGION",
                    "value": "us-east-1"
                }
            ],
            "secrets": [
                {
                    "name": "DB_PASSWORD",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:ecommerce/db/password-xyz"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/ecommerce-app",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
EOF

aws ecs register-task-definition \
    --cli-input-json file://ecommerce-task-definition.json \
    --region us-east-1

# Create ECS service
aws ecs create-service \
    --cluster ecommerce-primary \
    --service-name ecommerce-app-service \
    --task-definition ecommerce-app:1 \
    --desired-count 3 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-12345678,subnet-87654321],securityGroups=[sg-12345678],assignPublicIp=DISABLED}" \
    --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/ecommerce-tg/1234567890123456,containerName=ecommerce-app,containerPort=8080 \
    --health-check-grace-period-seconds 300 \
    --region us-east-1
```

### Step 2: DR Region Setup (us-west-2)

**DR VPC Configuration:**
```bash
# Create DR VPC (similar structure to primary)
aws ec2 create-vpc \
    --cidr-block 10.1.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=ecommerce-dr-vpc},{Key=Environment,Value=dr}]' \
    --region us-west-2

# Create subnets (similar to primary but with 10.1.x.x CIDR)
# ... (subnet creation commands similar to primary)

# Create smaller ECS cluster for DR
aws ecs create-cluster \
    --cluster-name ecommerce-dr \
    --capacity-providers FARGATE \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --region us-west-2

# Create DR service with minimal capacity
aws ecs create-service \
    --cluster ecommerce-dr \
    --service-name ecommerce-app-service \
    --task-definition ecommerce-app:1 \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-dr1,subnet-dr2],securityGroups=[sg-dr],assignPublicIp=DISABLED}" \
    --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/ecommerce-dr-tg/1234567890123456,containerName=ecommerce-app,containerPort=8080 \
    --region us-west-2
```

### Step 3: Data Replication and Backup Strategy

**S3 Cross-Region Replication:**
```bash
# Create replication configuration
cat > s3-replication-config.json << 'EOF'
{
    "Role": "arn:aws:iam::123456789012:role/replication-role",
    "Rules": [
        {
            "ID": "ReplicateEverything",
            "Status": "Enabled",
            "Priority": 1,
            "Filter": {},
            "Destination": {
                "Bucket": "arn:aws:s3:::ecommerce-assets-dr",
                "StorageClass": "STANDARD_IA",
                "ReplicationTime": {
                    "Status": "Enabled",
                    "Time": {
                        "Minutes": 15
                    }
                },
                "Metrics": {
                    "Status": "Enabled",
                    "EventThreshold": {
                        "Minutes": 15
                    }
                }
            }
        }
    ]
}
EOF

aws s3api put-bucket-replication \
    --bucket ecommerce-assets-primary \
    --replication-configuration file://s3-replication-config.json
```

**ElastiCache Backup and Restore:**
```bash
# Create Redis cluster with backup enabled
aws elasticache create-replication-group \
    --replication-group-id ecommerce-primary-cache \
    --description "Primary region Redis cluster" \
    --num-cache-clusters 2 \
    --cache-node-type cache.r6g.large \
    --engine redis \
    --engine-version 7.0 \
    --port 6379 \
    --parameter-group-name default.redis7 \
    --subnet-group-name ecommerce-cache-subnet-group \
    --security-group-ids sg-12345678 \
    --at-rest-encryption-enabled \
    --transit-encryption-enabled \
    --automatic-failover-enabled \
    --multi-az-enabled \
    --snapshot-retention-limit 5 \
    --snapshot-window "03:00-05:00" \
    --region us-east-1

# Create manual snapshot for DR
aws elasticache create-snapshot \
    --replication-group-id ecommerce-primary-cache \
    --snapshot-name ecommerce-cache-dr-snapshot-$(date +%Y%m%d%H%M%S) \
    --region us-east-1
```

### Step 4: Automated Failover Implementation

**Route 53 Health Checks and Failover:**
```bash
# Create health check for primary region
aws route53 create-health-check \
    --caller-reference primary-health-check-$(date +%s) \
    --health-check-config Type=HTTPS,ResourcePath=/health,FullyQualifiedDomainName=api.ecommerce.com,Port=443,RequestInterval=30,FailureThreshold=3 \
    --region us-east-1

# Create DNS records with failover routing
cat > route53-records.json << 'EOF'
{
    "Changes": [
        {
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "api.ecommerce.com",
                "Type": "A",
                "SetIdentifier": "primary",
                "Failover": "PRIMARY",
                "TTL": 60,
                "ResourceRecords": [
                    {
                        "Value": "1.2.3.4"
                    }
                ],
                "HealthCheckId": "12345678-1234-1234-1234-123456789012"
            }
        },
        {
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "api.ecommerce.com",
                "Type": "A",
                "SetIdentifier": "secondary",
                "Failover": "SECONDARY",
                "TTL": 60,
                "ResourceRecords": [
                    {
                        "Value": "5.6.7.8"
                    }
                ]
            }
        }
    ]
}
EOF

aws route53 change-resource-record-sets \
    --hosted-zone-id Z123456789 \
    --change-batch file://route53-records.json
```

**Lambda-based Automated Failover:**
```python
# lambda-failover-function.py
import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Automated DR failover function triggered by CloudWatch alarms
    """
    
    # Initialize AWS clients
    ecs_primary = boto3.client('ecs', region_name='us-east-1')
    ecs_dr = boto3.client('ecs', region_name='us-west-2')
    rds_dr = boto3.client('rds', region_name='us-west-2')
    route53 = boto3.client('route53')
    sns = boto3.client('sns')
    
    try:
        # Step 1: Promote read replica to primary
        logger.info("Promoting read replica to primary database")
        rds_dr.promote_read_replica(
            DBInstanceIdentifier='ecommerce-dr-replica'
        )
        
        # Step 2: Scale up DR ECS service
        logger.info("Scaling up DR ECS service")
        ecs_dr.update_service(
            cluster='ecommerce-dr',
            service='ecommerce-app-service',
            desiredCount=3  # Scale to production capacity
        )
        
        # Step 3: Update Route 53 to point to DR region
        logger.info("Updating DNS to point to DR region")
        route53.change_resource_record_sets(
            HostedZoneId='Z123456789',
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'api.ecommerce.com',
                        'Type': 'A',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': '5.6.7.8'}]  # DR ALB IP
                    }
                }]
            }
        )
        
        # Step 4: Restore Redis cache from snapshot
        logger.info("Restoring Redis cache from latest snapshot")
        # Get latest snapshot
        snapshots = boto3.client('elasticache', region_name='us-east-1').describe_snapshots(
            ReplicationGroupId='ecommerce-primary-cache',
            MaxRecords=1
        )
        
        if snapshots['Snapshots']:
            latest_snapshot = snapshots['Snapshots'][0]['SnapshotName']
            
            # Create new Redis cluster from snapshot in DR region
            boto3.client('elasticache', region_name='us-west-2').create_replication_group(
                ReplicationGroupId='ecommerce-dr-cache',
                Description='DR Redis cluster',
                NumCacheClusters=2,
                CacheNodeType='cache.r6g.large',
                Engine='redis',
                SnapshotName=latest_snapshot,
                SubnetGroupName='ecommerce-dr-cache-subnet-group',
                SecurityGroupIds=['sg-dr-cache']
            )
        
        # Step 5: Send notification
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:dr-notifications',
            Subject='DR Failover Completed Successfully',
            Message=f'''
            DR failover completed at {datetime.now().isoformat()}
            
            Actions taken:
            1. Read replica promoted to primary
            2. ECS service scaled to production capacity
            3. DNS updated to point to DR region
            4. Redis cache restored from snapshot
            
            Please verify all systems are operational.
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
        logger.error(f"DR failover failed: {str(e)}")
        
        # Send failure notification
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:dr-notifications',
            Subject='DR Failover Failed',
            Message=f'DR failover failed at {datetime.now().isoformat()}: {str(e)}'
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'DR failover failed',
                'message': str(e)
            })
        }
```

### Step 5: Monitoring and Alerting

**CloudWatch Alarms for DR Triggering:**
```bash
# Create alarm for high error rate
aws cloudwatch put-metric-alarm \
    --alarm-name "ECommerce-HighErrorRate" \
    --alarm-description "Trigger DR when error rate exceeds 5%" \
    --metric-name "4XXError" \
    --namespace "AWS/ApplicationELB" \
    --statistic "Sum" \
    --period 300 \
    --threshold 50 \
    --comparison-operator "GreaterThanThreshold" \
    --evaluation-periods 2 \
    --alarm-actions "arn:aws:lambda:us-east-1:123456789012:function:dr-failover" \
    --dimensions Name=LoadBalancer,Value=app/ecommerce-alb/1234567890123456 \
    --region us-east-1

# Create alarm for database connectivity
aws cloudwatch put-metric-alarm \
    --alarm-name "ECommerce-DatabaseDown" \
    --alarm-description "Trigger DR when database is unreachable" \
    --metric-name "DatabaseConnections" \
    --namespace "AWS/RDS" \
    --statistic "Average" \
    --period 300 \
    --threshold 1 \
    --comparison-operator "LessThanThreshold" \
    --evaluation-periods 3 \
    --alarm-actions "arn:aws:lambda:us-east-1:123456789012:function:dr-failover" \
    --dimensions Name=DBInstanceIdentifier,Value=ecommerce-primary-db \
    --region us-east-1
```

**DR Testing Automation:**
```bash
# Create EventBridge rule for monthly DR testing
aws events put-rule \
    --name "monthly-dr-test" \
    --schedule-expression "cron(0 2 1 * ? *)" \
    --description "Monthly DR test execution" \
    --state ENABLED

aws events put-targets \
    --rule "monthly-dr-test" \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:dr-test-function"
```

## 🔄 Alternative DR Approaches

### Approach 1: Backup and Restore (Cost-Optimized)

**When to Use:**
```
Perfect for:
• Non-critical applications
• Development/testing environments
• Applications with >24 hour RTO tolerance
• Cost-sensitive implementations
• Batch processing systems
• Reporting and analytics platforms

Business Scenarios:
• Internal tools and dashboards
• Data warehousing systems
• Development environments
• Legacy applications with low usage
```

**Implementation:**
```bash
# Automated backup strategy
aws backup create-backup-plan \
    --backup-plan '{
        "BackupPlanName": "ecommerce-backup-plan",
        "Rules": [
            {
                "RuleName": "daily-backups",
                "TargetBackupVault": "default",
                "ScheduleExpression": "cron(0 2 ? * * *)",
                "StartWindowMinutes": 60,
                "CompletionWindowMinutes": 120,
                "Lifecycle": {
                    "DeleteAfterDays": 30,
                    "MoveToColdStorageAfterDays": 7
                },
                "RecoveryPointTags": {
                    "Environment": "production",
                    "Application": "ecommerce"
                }
            }
        ]
    }'

# Create backup selection
aws backup create-backup-selection \
    --backup-plan-id "backup-plan-id" \
    --backup-selection '{
        "SelectionName": "ecommerce-resources",
        "IamRoleArn": "arn:aws:iam::123456789012:role/aws-backup-service-role",
        "Resources": [
            "arn:aws:rds:us-east-1:123456789012:db:ecommerce-primary-db",
            "arn:aws:ec2:us-east-1:123456789012:volume/*"
        ],
        "Conditions": {
            "StringEquals": {
                "aws:ResourceTag/Environment": ["production"]
            }
        }
    }'
```

### Approach 2: Pilot Light (Balanced Approach)

**When to Use:**
```
Perfect for:
• Important business applications
• Moderate availability requirements (1-4 hour RTO)
• Cost-conscious implementations
• Applications with predictable recovery procedures
• Systems with clear critical path components

Business Scenarios:
• Customer relationship management (CRM)
• Enterprise resource planning (ERP)
• Content management systems
• Internal business applications
```

**Implementation:**
```bash
# Minimal DR infrastructure - just core components
aws ec2 run-instances \
    --image-id ami-12345678 \
    --count 1 \
    --instance-type t3.micro \
    --key-name dr-key-pair \
    --security-group-ids sg-dr \
    --subnet-id subnet-dr \
    --user-data file://pilot-light-userdata.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=pilot-light-core},{Key=Environment,Value=dr}]' \
    --region us-west-2

# Keep minimal services running
cat > pilot-light-userdata.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker

# Pull essential container images
docker pull nginx:latest
docker pull redis:latest

# Keep containers stopped but ready
docker create --name nginx-ready -p 80:80 nginx:latest
docker create --name redis-ready -p 6379:6379 redis:latest
EOF
```

### Approach 3: Multi-Site Active-Active (Maximum Availability)

**When to Use:**
```
Perfect for:
• Mission-critical applications
• Zero tolerance for downtime
• Global user base requiring low latency
• High-value transactions
• Real-time systems

Business Scenarios:
• Stock trading platforms
• Emergency services systems
• Global e-commerce during peak seasons
• Financial payment processing
• Real-time gaming platforms
```

**Implementation:**
```bash
# Global load balancer with health checks
aws globalaccelerator create-accelerator \
    --name ecommerce-global-accelerator \
    --ip-address-type IPV4 \
    --enabled \
    --attributes FlowLogsEnabled=true,FlowLogsS3Bucket=ecommerce-flow-logs,FlowLogsS3Prefix=global-accelerator/

# Create listeners for both regions
aws globalaccelerator create-listener \
    --accelerator-arn arn:aws:globalaccelerator::123456789012:accelerator/12345678-1234-1234-1234-123456789012 \
    --protocol TCP \
    --port-ranges FromPort=80,ToPort=80 FromPort=443,ToPort=443

# Add endpoint groups for both regions
aws globalaccelerator create-endpoint-group \
    --listener-arn arn:aws:globalaccelerator::123456789012:listener/12345678-1234-1234-1234-123456789012/12345678 \
    --endpoint-group-region us-east-1 \
    --endpoint-configurations EndpointId=arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/ecommerce-alb/1234567890123456,Weight=100 \
    --health-check-interval-seconds 30 \
    --threshold-count 3

aws globalaccelerator create-endpoint-group \
    --listener-arn arn:aws:globalaccelerator::123456789012:listener/12345678-1234-1234-1234-123456789012/12345678 \
    --endpoint-group-region us-west-2 \
    --endpoint-configurations EndpointId=arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/ecommerce-dr-alb/1234567890123456,Weight=100 \
    --health-check-interval-seconds 30 \
    --threshold-count 3
```

## 📊 DR Testing and Validation

### Automated DR Testing Framework

**Monthly DR Test Automation:**
```python
# dr-test-automation.py
import boto3
import json
import time
from datetime import datetime

class DRTestFramework:
    def __init__(self):
        self.primary_region = 'us-east-1'
        self.dr_region = 'us-west-2'
        self.test_results = []
    
    def run_comprehensive_dr_test(self):
        """
        Comprehensive DR test including all components
        """
        print(f"Starting DR test at {datetime.now()}")
        
        # Test 1: Database failover
        db_test = self.test_database_failover()
        self.test_results.append(db_test)
        
        # Test 2: Application failover
        app_test = self.test_application_failover()
        self.test_results.append(app_test)
        
        # Test 3: DNS failover
        dns_test = self.test_dns_failover()
        self.test_results.append(dns_test)
        
        # Test 4: Data consistency
        data_test = self.test_data_consistency()
        self.test_results.append(data_test)
        
        # Generate report
        self.generate_test_report()
        
        return self.test_results
    
    def test_database_failover(self):
        """Test RDS read replica promotion"""
        try:
            rds = boto3.client('rds', region_name=self.dr_region)
            
            # Create test read replica
            test_replica_id = f"dr-test-replica-{int(time.time())}"
            
            rds.create_db_instance_read_replica(
                DBInstanceIdentifier=test_replica_id,
                SourceDBInstanceIdentifier='arn:aws:rds:us-east-1:123456789012:db:ecommerce-primary-db',
                DBInstanceClass='db.t3.micro'
            )
            
            # Wait for replica to be available
            waiter = rds.get_waiter('db_instance_available')
            waiter.wait(DBInstanceIdentifier=test_replica_id, WaiterConfig={'Delay': 30, 'MaxAttempts': 20})
            
            # Test promotion
            rds.promote_read_replica(DBInstanceIdentifier=test_replica_id)
            
            # Cleanup
            rds.delete_db_instance(
                DBInstanceIdentifier=test_replica_id,
                SkipFinalSnapshot=True
            )
            
            return {
                'test': 'database_failover',
                'status': 'PASSED',
                'duration': time.time(),
                'message': 'Database failover test completed successfully'
            }
            
        except Exception as e:
            return {
                'test': 'database_failover',
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_application_failover(self):
        """Test ECS service scaling and health"""
        try:
            ecs = boto3.client('ecs', region_name=self.dr_region)
            
            # Scale up DR service temporarily
            ecs.update_service(
                cluster='ecommerce-dr',
                service='ecommerce-app-service',
                desiredCount=2
            )
            
            # Wait for service to stabilize
            waiter = ecs.get_waiter('services_stable')
            waiter.wait(
                cluster='ecommerce-dr',
                services=['ecommerce-app-service'],
                WaiterConfig={'Delay': 15, 'MaxAttempts': 20}
            )
            
            # Test health endpoint
            import requests
            health_response = requests.get('http://dr-alb-endpoint/health', timeout=10)
            
            if health_response.status_code == 200:
                # Scale back down
                ecs.update_service(
                    cluster='ecommerce-dr',
                    service='ecommerce-app-service',
                    desiredCount=1
                )
                
                return {
                    'test': 'application_failover',
                    'status': 'PASSED',
                    'message': 'Application failover test completed successfully'
                }
            else:
                raise Exception(f"Health check failed: {health_response.status_code}")
                
        except Exception as e:
            return {
                'test': 'application_failover',
                'status': 'FAILED',
                'error': str(e)
            }
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        report = {
            'test_date': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'passed_tests': len([t for t in self.test_results if t['status'] == 'PASSED']),
            'failed_tests': len([t for t in self.test_results if t['status'] == 'FAILED']),
            'results': self.test_results
        }
        
        # Send to S3 for record keeping
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket='ecommerce-dr-test-reports',
            Key=f"dr-test-{datetime.now().strftime('%Y-%m-%d')}.json",
            Body=json.dumps(report, indent=2)
        )
        
        # Send notification
        sns = boto3.client('sns')
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:dr-notifications',
            Subject=f'DR Test Report - {report["passed_tests"]}/{report["total_tests"]} Passed',
            Message=json.dumps(report, indent=2)
        )

# Lambda handler for scheduled testing
def lambda_handler(event, context):
    dr_test = DRTestFramework()
    results = dr_test.run_comprehensive_dr_test()
    
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
```

## 💰 Cost Optimization and ROI Analysis

### DR Cost Comparison

**Cost Analysis by DR Pattern:**
```
Backup and Restore:
• Monthly cost: $500-2,000
• Components: S3 storage, backup services
• RTO: 24+ hours
• Use case: Non-critical systems

Pilot Light:
• Monthly cost: $2,000-8,000
• Components: Minimal compute, data replication
• RTO: 1-4 hours
• Use case: Important business systems

Warm Standby:
• Monthly cost: $8,000-25,000
• Components: Scaled-down infrastructure
• RTO: 5-30 minutes
• Use case: High-priority systems

Active-Active:
• Monthly cost: $25,000-100,000+
• Components: Full duplicate infrastructure
• RTO: 0-5 minutes
• Use case: Mission-critical systems
```

**ROI Calculation Example:**
```
E-commerce Platform Analysis:
• Revenue: $100M annually
• Downtime cost: $500K per hour
• Current availability: 99.5% (43.8 hours downtime/year)
• Annual downtime cost: $21.9M

With Warm Standby DR:
• Availability improvement: 99.95% (4.4 hours downtime/year)
• Annual downtime cost: $2.2M
• DR implementation cost: $300K annually
• Net savings: $19.4M annually
• ROI: 6,467%
```

## 🔧 AWS Disaster Recovery Service (DRS) - Managed Approach

### Understanding AWS DRS

**What is AWS DRS:**
• Managed disaster recovery service (formerly CloudEndure)
• Continuous block-level replication
• Automated failover and failback
• Support for physical, virtual, and cloud servers
• Point-in-time recovery capabilities
• Cross-platform support (Windows, Linux)

**DRS vs Traditional DR:**

**Traditional DR Challenges:**
• Manual replication setup and management
• Complex failover procedures
• Inconsistent recovery testing
• High operational overhead
• Risk of human error during disasters

**AWS DRS Benefits:**
• Automated continuous replication
• One-click failover and failback
• Built-in recovery testing
• Managed service with AWS support
• Consistent recovery procedures

### DRS Implementation

**Step 1: DRS Setup and Configuration:**
```bash
# Install DRS agent on source servers
wget -O ./aws-replication-installer-init.py https://aws-elastic-disaster-recovery-us-east-1.s3.amazonaws.com/latest/linux/aws-replication-installer-init.py

# Run installer with credentials
sudo python3 aws-replication-installer-init.py \
    --region us-east-1 \
    --aws-access-key-id AKIAIOSFODNN7EXAMPLE \
    --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
    --no-prompt

# Verify replication status
aws drs describe-source-servers --region us-east-1
```

**Step 2: Configure Replication Settings:**
```bash
# Create replication configuration template
aws drs create-replication-configuration-template \
    --associate-default-security-group \
    --bandwidth-throttling 0 \
    --create-public-ip false \
    --data-plane-routing PRIVATE_IP \
    --default-large-staging-disk-type GP3 \
    --ebs-encryption ENCRYPTED \
    --ebs-encryption-key-arn arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012 \
    --replication-server-instance-type m5.large \
    --replication-servers-security-groups-i-ds sg-12345678 \
    --staging-area-subnet-id subnet-12345678 \
    --staging-area-tags Environment=DR,Application=ecommerce \
    --use-dedicated-replication-server false
```

## 🏢 Hybrid and On-Premises DR Scenarios

### On-Premises to AWS DR

**Business Scenarios:**
• Legacy data center modernization
• Regulatory requirements for on-premises primary
• Cost optimization (cloud as DR only)
• Gradual cloud migration strategy
• Compliance with data residency laws

**Architecture Pattern:**
```
On-Premises Primary → AWS DR

Components:
• Primary: On-premises data center
• DR: AWS region with VPN/Direct Connect
• Replication: AWS DataSync, Storage Gateway, DMS
• Failover: Route 53, VPN failover
• Failback: Reverse replication capability
```

**Implementation with AWS Storage Gateway:**
```bash
# Deploy Storage Gateway VM on-premises
# Download OVA from AWS console and deploy to VMware/Hyper-V

# Activate Storage Gateway
aws storagegateway activate-gateway \
    --activation-key ACTIVATION_KEY_FROM_VM \
    --gateway-name OnPremStorageGateway \
    --gateway-timezone GMT-5:EST \
    --gateway-region us-east-1 \
    --gateway-type FILE_S3

# Create NFS file share
aws storagegateway create-nfs-file-share \
    --client-token $(uuidgen) \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 \
    --location-arn arn:aws:s3:::onprem-backup-bucket \
    --role arn:aws:iam::123456789012:role/StorageGatewayRole \
    --default-storage-class S3_STANDARD_IA \
    --nfs-file-share-defaults '{"fileMode": "0666", "directoryMode": "0777", "groupId": 0, "ownerId": 0}'
```

## 🔒 Security and Compliance During DR

### Security Considerations

**Data Protection During DR:**
• Data at rest: EBS encryption, S3 encryption
• Data in transit: TLS/SSL for all communications
• Key management: AWS KMS with cross-region keys
• Backup encryption: Encrypted snapshots and backups
• Emergency access procedures
• Break-glass access for DR scenarios
• Audit logging during DR events
• Temporary elevated permissions

**SOX Compliance DR:**
```bash
# Create compliance-specific backup policy
aws backup create-backup-plan \
    --backup-plan '{
        "BackupPlanName": "SOX-Compliance-DR",
        "Rules": [{
            "RuleName": "SOX-Daily-Backup",
            "TargetBackupVault": "sox-compliance-vault",
            "ScheduleExpression": "cron(0 2 ? * * *)",
            "StartWindowMinutes": 60,
            "CompletionWindowMinutes": 120,
            "Lifecycle": {
                "DeleteAfterDays": 2555,
                "MoveToColdStorageAfterDays": 30
            },
            "RecoveryPointTags": {
                "Compliance": "SOX",
                "RetentionPeriod": "7Years",
                "DataClassification": "Financial"
            }
        }]
    }'
```

## 📋 DR Runbooks and Communication Plans

### Executive Summary Runbook

**Immediate Actions (0-15 minutes):**
1. **Incident Commander Assignment**
   - Primary: John Smith (CEO) - +1-555-0101
   - Backup: Jane Doe (CTO) - +1-555-0102

2. **Stakeholder Notification**
   - Board of Directors: board@company.com
   - Legal Team: legal@company.com
   - PR Team: pr@company.com
   - Insurance: insurance-contact@company.com

3. **Customer Communication**
   - Status Page Update: status.company.com
   - Social Media: @company_support
   - Email Notification: customer-alerts@company.com

**Decision Matrix:**
| Scenario | RTO Target | Action Required |
|----------|------------|----------------|
| Regional AWS Outage | 15 minutes | Automatic failover to DR region |
| Database Corruption | 1 hour | Restore from point-in-time backup |
| Security Breach | 4 hours | Isolate systems, forensic analysis |
| Natural Disaster | 24 hours | Activate full DR site |

**Success Criteria:**
- [ ] All critical systems operational
- [ ] Customer-facing services restored
- [ ] Data integrity verified
- [ ] Security posture maintained
- [ ] Stakeholders notified

### Technical Runbook

```bash
#!/bin/bash
# DR Activation Script - Technical Runbook

set -e

echo "=== DISASTER RECOVERY ACTIVATION ==="
echo "Timestamp: $(date)"
echo "Operator: $USER"
echo "======================================"

# Step 1: Verify DR readiness
echo "Step 1: Verifying DR environment readiness..."
aws sts get-caller-identity --region us-west-2
aws rds describe-db-instances --db-instance-identifier ecommerce-dr-replica --region us-west-2
aws ecs describe-services --cluster ecommerce-dr --services ecommerce-app-service --region us-west-2

# Step 2: Promote database replica
echo "Step 2: Promoting database replica to primary..."
aws rds promote-read-replica \
    --db-instance-identifier ecommerce-dr-replica \
    --region us-west-2

# Wait for promotion to complete
echo "Waiting for database promotion to complete..."
aws rds wait db-instance-available \
    --db-instance-identifier ecommerce-dr-replica \
    --region us-west-2

# Step 3: Scale up application services
echo "Step 3: Scaling up application services..."
aws ecs update-service \
    --cluster ecommerce-dr \
    --service ecommerce-app-service \
    --desired-count 5 \
    --region us-west-2

# Step 4: Update DNS to point to DR region
echo "Step 4: Updating DNS to DR region..."
aws route53 change-resource-record-sets \
    --hosted-zone-id Z123456789 \
    --change-batch file://dns-failover.json

# Step 5: Verify application health
echo "Step 5: Verifying application health..."
for i in {1..10}; do
    if curl -f -s https://api.company.com/health > /dev/null; then
        echo "Health check passed"
        break
    else
        echo "Health check failed, attempt $i/10"
        sleep 30
    fi
done

# Step 6: Send notifications
echo "Step 6: Sending notifications..."
aws sns publish \
    --topic-arn arn:aws:sns:us-east-1:123456789012:dr-notifications \
    --subject "DR Activation Completed" \
    --message "DR activation completed successfully at $(date). All systems operational in DR region."

echo "=== DR ACTIVATION COMPLETED ==="
echo "Timestamp: $(date)"
echo "Status: SUCCESS"
echo "Next Steps: Monitor systems and prepare for failback when primary region is restored"
```

### Communication Templates

**Internal Communication Template:**
```
SUBJECT: [URGENT] Disaster Recovery Activation - Action Required

Team,

We have activated our disaster recovery procedures due to [INCIDENT_TYPE] affecting our primary systems.

CURRENT STATUS:
- Incident Start Time: [TIME]
- Estimated Recovery Time: [ETA]
- Systems Affected: [SYSTEMS_LIST]
- Customer Impact: [IMPACT_DESCRIPTION]

ACTIONS TAKEN:
- [ACTION_1]
- [ACTION_2]
- [ACTION_3]

NEXT STEPS:
- [NEXT_STEP_1] - Owner: [NAME] - ETA: [TIME]
- [NEXT_STEP_2] - Owner: [NAME] - ETA: [TIME]

COMMUNICATION SCHEDULE:
Next update in 30 minutes or upon significant change.

POINT OF CONTACT:
Incident Commander: [NAME] - [PHONE] - [EMAIL]

[SIGNATURE]
```

**Customer Communication Template:**
```
SUBJECT: Service Update - Temporary Service Disruption

Dear Valued Customers,

We are currently experiencing a service disruption that began at [TIME] [TIMEZONE]. We want to keep you informed about the situation and our response.

WHAT HAPPENED:
[Brief, non-technical explanation of the issue]

CURRENT STATUS:
- Services Affected: [LIST]
- Services Operating Normally: [LIST]
- Estimated Resolution Time: [ETA]

WHAT WE'RE DOING:
Our engineering team has activated our disaster recovery procedures and is working to restore full service. We have implemented our backup systems to minimize disruption.

WHAT YOU CAN DO:
- [WORKAROUND_1]
- [WORKAROUND_2]
- Monitor our status page: status.company.com

We sincerely apologize for any inconvenience and will provide updates every 30 minutes until resolution.

For urgent support needs, please contact: support@company.com

Thank you for your patience.

[COMPANY_NAME] Team
```

This comprehensive guide now covers every aspect of AWS disaster recovery, making it the ultimate go-to reference for DR planning and implementation across all scenarios and compliance requirements.