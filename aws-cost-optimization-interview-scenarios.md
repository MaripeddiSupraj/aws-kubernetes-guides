# AWS Cost Optimization - Real Interview Scenarios & Examples

## How to Answer: "What cost optimization have you done?"

### Template Answer Structure:
1. **Situation**: Describe the cost challenge
2. **Action**: Specific steps you took
3. **Result**: Quantified savings achieved
4. **Tools**: AWS services/tools used

---

## Scenario 1: EC2 Right-Sizing Project

### The Story:
*"In my previous role, I noticed our monthly AWS bill was $15,000, with 60% going to EC2 instances that were consistently running at 10-20% CPU utilization."*

### Actions Taken:
```bash
# 1. Used AWS Cost Explorer to identify top spending resources
aws ce get-cost-and-usage \
  --time-period Start=2023-01-01,End=2023-02-01 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# 2. Analyzed CloudWatch metrics for CPU utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --start-time 2023-01-01T00:00:00Z \
  --end-time 2023-01-31T23:59:59Z \
  --period 3600 \
  --statistics Average

# 3. Used AWS Compute Optimizer recommendations
aws compute-optimizer get-ec2-instance-recommendations \
  --instance-arns arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0
```

### Implementation:
- **Before**: 20 x m5.2xlarge instances (8 vCPU, 32GB RAM)
- **After**: 20 x m5.large instances (2 vCPU, 8GB RAM)
- **Additional**: Implemented Auto Scaling to handle peak loads

### Results:
- **Cost Reduction**: 65% savings on EC2 costs ($9,000 → $3,150/month)
- **Performance**: No impact on application performance
- **Tools Used**: CloudWatch, Compute Optimizer, Cost Explorer

---

## Scenario 2: S3 Storage Class Optimization

### The Story:
*"Our data lake was storing 500TB of data in S3 Standard, costing $11,500/month, but analysis showed 80% of files weren't accessed after 30 days."*

### Actions Taken:
```bash
# 1. Analyzed S3 access patterns
aws s3api get-bucket-analytics-configuration \
  --bucket my-data-lake \
  --id EntireBucket

# 2. Created lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-data-lake \
  --lifecycle-configuration file://lifecycle-policy.json
```

### Lifecycle Policy Implementation:
```json
{
  "Rules": [
    {
      "ID": "DataLakeOptimization",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ]
    }
  ]
}
```

### Results:
- **Cost Reduction**: 70% savings ($11,500 → $3,450/month)
- **Data Distribution**: 
  - Standard (30 days): 100TB
  - Standard-IA (60 days): 150TB  
  - Glacier (275 days): 200TB
  - Deep Archive: 50TB

---

## Scenario 3: Reserved Instance Strategy

### The Story:
*"We had predictable workloads running 24/7 but were paying On-Demand prices, resulting in unnecessary costs of $8,000/month."*

### Actions Taken:
```bash
# 1. Analyzed usage patterns
aws ce get-reservation-coverage \
  --time-period Start=2023-01-01,End=2023-12-31 \
  --group-by Type=DIMENSION,Key=INSTANCE_TYPE

# 2. Got RI recommendations
aws ce get-reservation-purchase-recommendation \
  --service EC2-Instance \
  --account-scope PAYER
```

### Implementation Strategy:
- **1-Year Standard RIs**: For stable production workloads (60% of capacity)
- **1-Year Convertible RIs**: For workloads that might change (25% of capacity)
- **On-Demand**: For variable/peak capacity (15% of capacity)

### Results:
- **Cost Reduction**: 45% savings on compute costs
- **Annual Savings**: $43,200 ($8,000 → $4,400/month)
- **Payback Period**: 8 months

---

## Scenario 4: Spot Instance Implementation

### The Story:
*"Our batch processing jobs were running on On-Demand instances costing $2,500/month, but these jobs were fault-tolerant and could handle interruptions."*

### Implementation:
```yaml
# Auto Scaling Group with Spot Instances
LaunchTemplate:
  Type: AWS::EC2::LaunchTemplate
  Properties:
    LaunchTemplateData:
      InstanceType: m5.large
      InstanceMarketOptions:
        MarketType: spot
        SpotOptions:
          MaxPrice: "0.05"
          SpotInstanceType: one-time

AutoScalingGroup:
  Type: AWS::AutoScaling::AutoScalingGroup
  Properties:
    MixedInstancesPolicy:
      InstancesDistribution:
        OnDemandPercentage: 20
        SpotAllocationStrategy: diversified
      LaunchTemplate:
        LaunchTemplateSpecification:
          LaunchTemplateId: !Ref LaunchTemplate
          Version: !GetAtt LaunchTemplate.LatestVersionNumber
        Overrides:
          - InstanceType: m5.large
          - InstanceType: m5.xlarge
          - InstanceType: m4.large
```

### Results:
- **Cost Reduction**: 75% savings ($2,500 → $625/month)
- **Job Completion**: 99.2% success rate with spot interruption handling
- **Additional Benefit**: Faster processing with multiple instance types

---

## Scenario 5: Database Cost Optimization

### The Story:
*"Our RDS instances were over-provisioned and running 24/7, costing $4,500/month for development and staging environments."*

### Actions Taken:
```bash
# 1. Analyzed RDS performance metrics
aws rds describe-db-instances \
  --db-instance-identifier mydb-prod

# 2. Implemented automated start/stop for non-prod
aws events put-rule \
  --name "StopDevDatabases" \
  --schedule-expression "cron(0 18 ? * MON-FRI *)"

# 3. Right-sized production instances
aws rds modify-db-instance \
  --db-instance-identifier mydb-prod \
  --db-instance-class db.t3.large \
  --apply-immediately
```

### Implementation:
- **Production**: Right-sized from db.r5.2xlarge to db.r5.large
- **Development**: Automated stop at 6 PM, start at 8 AM (weekdays only)
- **Staging**: Converted to Aurora Serverless v2

### Results:
- **Production**: 40% reduction ($2,000 → $1,200/month)
- **Development**: 70% reduction (runs 50 hours/week vs 168 hours)
- **Total Savings**: $2,700/month ($4,500 → $1,800)

---

## Scenario 6: CloudWatch Logs Optimization

### The Story:
*"Our application was generating excessive CloudWatch logs, costing $1,200/month with most logs never being accessed."*

### Actions Taken:
```bash
# 1. Analyzed log group usage
aws logs describe-log-groups \
  --query 'logGroups[?storedBytes>`10737418240`].[logGroupName,storedBytes]'

# 2. Implemented log retention policies
aws logs put-retention-policy \
  --log-group-name /aws/lambda/my-function \
  --retention-in-days 7

# 3. Set up log filtering at source
aws logs put-metric-filter \
  --log-group-name /aws/lambda/my-function \
  --filter-name ErrorCount \
  --filter-pattern "ERROR" \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=MyApp,metricValue=1
```

### Implementation:
- **Application Logs**: 30 days → 7 days retention
- **Debug Logs**: Disabled in production
- **Error Logs**: 90 days retention with alerts
- **Access Logs**: Moved to S3 with lifecycle policies

### Results:
- **Cost Reduction**: 85% savings ($1,200 → $180/month)
- **Storage Reduced**: From 2TB to 300GB
- **Better Monitoring**: Focused on critical errors only

---

## Scenario 7: Data Transfer Optimization

### The Story:
*"High data transfer costs of $800/month due to inefficient architecture with cross-region and internet data transfers."*

### Actions Taken:
```bash
# 1. Analyzed data transfer costs
aws ce get-cost-and-usage \
  --time-period Start=2023-01-01,End=2023-02-01 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=USAGE_TYPE \
  --filter file://data-transfer-filter.json

# 2. Implemented VPC Endpoints
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345678 \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-12345678
```

### Implementation:
- **VPC Endpoints**: For S3 and DynamoDB access
- **CloudFront**: For static content delivery
- **Regional Consolidation**: Moved resources to single region
- **Compression**: Enabled gzip compression

### Results:
- **Cost Reduction**: 60% savings ($800 → $320/month)
- **Performance**: 40% faster S3 access via VPC endpoint
- **Security**: Eliminated internet gateway dependency

---

## Tools and Commands for Cost Analysis

### 1. Cost Explorer CLI Commands
```bash
# Get top 10 services by cost
aws ce get-cost-and-usage \
  --time-period Start=2023-01-01,End=2023-02-01 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[0].Groups[?Metrics.BlendedCost.Amount>`100`]' \
  --output table

# Get daily costs for specific service
aws ce get-cost-and-usage \
  --time-period Start=2023-01-01,End=2023-01-31 \
  --granularity DAILY \
  --metrics BlendedCost \
  --filter file://ec2-filter.json
```

### 2. Trusted Advisor Checks
```bash
# Get cost optimization recommendations
aws support describe-trusted-advisor-checks \
  --language en \
  --query 'checks[?category==`cost_optimizing`].[name,id]' \
  --output table
```

### 3. Billing Alerts Setup
```bash
# Create billing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "BillingAlarm" \
  --alarm-description "Alarm when AWS bill exceeds $1000" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD \
  --evaluation-periods 1
```

## Key Metrics to Track

### Cost Optimization KPIs
- **Monthly cost reduction percentage**
- **Cost per transaction/user**
- **Reserved Instance utilization rate**
- **Spot Instance savings percentage**
- **Storage cost per GB**

### Sample Dashboard Metrics
```json
{
  "metrics": [
    ["AWS/Billing", "EstimatedCharges", "Currency", "USD"],
    ["AWS/EC2", "CPUUtilization", "InstanceId", "i-1234567890abcdef0"],
    ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "my-alb"],
    ["AWS/S3", "BucketSizeBytes", "BucketName", "my-bucket", "StorageType", "StandardStorage"]
  ]
}
```

## Interview Tips

### What Interviewers Want to Hear:
1. **Specific numbers**: "Reduced costs by 65% saving $5,400/month"
2. **Methodology**: "Used CloudWatch metrics and Cost Explorer to identify..."
3. **Business impact**: "Freed up budget for new feature development"
4. **Ongoing monitoring**: "Set up alerts to prevent cost drift"

### Red Flags to Avoid:
- Vague statements like "optimized some instances"
- No quantified results
- Not mentioning monitoring/alerting
- Ignoring performance impact

### Follow-up Questions You Might Get:
- "How did you ensure performance wasn't impacted?"
- "What tools did you use to monitor the changes?"
- "How do you prevent cost drift in the future?"
- "What was the business stakeholder reaction?"

## Cost Optimization Checklist

### Monthly Reviews:
- [ ] Analyze Cost Explorer reports
- [ ] Review Trusted Advisor recommendations
- [ ] Check Reserved Instance utilization
- [ ] Validate Auto Scaling policies
- [ ] Review S3 storage classes
- [ ] Audit unused resources

### Quarterly Actions:
- [ ] Evaluate Reserved Instance renewals
- [ ] Review architecture for optimization opportunities
- [ ] Update cost allocation tags
- [ ] Benchmark against industry standards
- [ ] Present savings report to stakeholders