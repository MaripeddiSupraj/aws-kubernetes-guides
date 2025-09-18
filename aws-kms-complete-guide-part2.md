# AWS KMS Complete Guide - Part 2: Advanced Topics

## Multi-Region Keys & Cross-Account Access

### 1. Multi-Region Keys (MRKs)

#### What are Multi-Region Keys?
- **Single key ID** that works across multiple AWS regions
- **Automatic replication** of key material to specified regions
- **Independent key policies** per region
- **Consistent encryption/decryption** across regions

#### When to Use MRKs:
- Global applications requiring consistent encryption
- Cross-region disaster recovery
- Multi-region data replication
- Global content distribution

#### Creating Multi-Region Keys:
```bash
# Create multi-region key
aws kms create-key \
  --description "Multi-region application key" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec SYMMETRIC_DEFAULT \
  --multi-region \
  --tags '[
    {
      "TagKey": "Type",
      "TagValue": "MultiRegion"
    },
    {
      "TagKey": "Application",
      "TagValue": "GlobalApp"
    }
  ]'

# Replicate key to other regions
aws kms replicate-key \
  --key-id mrk-1234567890abcdef1234567890abcdef \
  --replica-region us-west-2 \
  --description "Replica in us-west-2"

aws kms replicate-key \
  --key-id mrk-1234567890abcdef1234567890abcdef \
  --replica-region eu-west-1 \
  --description "Replica in eu-west-1"
```

#### Terraform Multi-Region Key Configuration:
```hcl
# Primary multi-region key
resource "aws_kms_key" "multi_region_primary" {
  description         = "Multi-region application key"
  key_usage          = "ENCRYPT_DECRYPT"
  key_spec           = "SYMMETRIC_DEFAULT"
  multi_region       = true
  enable_key_rotation = true
  
  tags = {
    Name = "multi-region-primary-key"
    Type = "MultiRegion"
  }
}

resource "aws_kms_alias" "multi_region_primary" {
  name          = "alias/multi-region-app-key"
  target_key_id = aws_kms_key.multi_region_primary.key_id
}

# Replica keys in other regions
resource "aws_kms_replica_key" "us_west_2" {
  provider = aws.us_west_2
  
  description             = "Multi-region key replica in us-west-2"
  primary_key_arn        = aws_kms_key.multi_region_primary.arn
  deletion_window_in_days = 30
  
  tags = {
    Name = "multi-region-replica-us-west-2"
    Type = "MultiRegionReplica"
  }
}

resource "aws_kms_alias" "us_west_2" {
  provider = aws.us_west_2
  
  name          = "alias/multi-region-app-key"
  target_key_id = aws_kms_replica_key.us_west_2.key_id
}

resource "aws_kms_replica_key" "eu_west_1" {
  provider = aws.eu_west_1
  
  description             = "Multi-region key replica in eu-west-1"
  primary_key_arn        = aws_kms_key.multi_region_primary.arn
  deletion_window_in_days = 30
  
  tags = {
    Name = "multi-region-replica-eu-west-1"
    Type = "MultiRegionReplica"
  }
}

resource "aws_kms_alias" "eu_west_1" {
  provider = aws.eu_west_1
  
  name          = "alias/multi-region-app-key"
  target_key_id = aws_kms_replica_key.eu_west_1.key_id
}

# Provider configurations
provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
}

provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
}
```

### 2. Cross-Account Access Patterns

#### Scenario 1: Shared Services Account
```json
{
  "Version": "2012-10-17",
  "Id": "shared-services-key-policy",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow production account access",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::222222222222:root",
          "arn:aws:iam::222222222222:role/ProductionApplicationRole"
        ]
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "s3.us-east-1.amazonaws.com",
            "rds.us-east-1.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "Allow staging account access",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::333333333333:role/StagingApplicationRole"
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:EncryptionContext:Environment": "staging"
        }
      }
    }
  ]
}
```

#### Scenario 2: Data Sharing Between Accounts
```bash
#!/bin/bash
# cross-account-data-sharing.sh

SOURCE_ACCOUNT="111111111111"
TARGET_ACCOUNT="222222222222"
SHARED_KEY_ALIAS="alias/shared-data-key"
BUCKET_NAME="cross-account-data-sharing"

echo "Setting up cross-account data sharing..."

# Step 1: Create shared KMS key (in source account)
echo "Creating shared KMS key..."
KEY_ID=$(aws kms create-key \
  --description "Cross-account data sharing key" \
  --key-usage ENCRYPT_DECRYPT \
  --query 'KeyMetadata.KeyId' \
  --output text)

# Step 2: Create key policy allowing cross-account access
cat > cross-account-key-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${SOURCE_ACCOUNT}:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow target account access",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${TARGET_ACCOUNT}:root"
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Apply key policy
aws kms put-key-policy \
  --key-id $KEY_ID \
  --policy-name default \
  --policy file://cross-account-key-policy.json

# Step 3: Create alias
aws kms create-alias \
  --alias-name $SHARED_KEY_ALIAS \
  --target-key-id $KEY_ID

# Step 4: Create S3 bucket with cross-account access
aws s3 mb s3://$BUCKET_NAME

# Step 5: Set bucket policy
cat > bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCrossAccountAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::${SOURCE_ACCOUNT}:root",
          "arn:aws:iam::${TARGET_ACCOUNT}:root"
        ]
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket $BUCKET_NAME \
  --policy file://bucket-policy.json

echo "Cross-account setup complete!"
echo "Key ID: $KEY_ID"
echo "Key Alias: $SHARED_KEY_ALIAS"
echo "Bucket: $BUCKET_NAME"

# Clean up
rm cross-account-key-policy.json bucket-policy.json
```

### 3. Cross-Account Data Access Example

#### Python Script for Cross-Account Data Access:
```python
#!/usr/bin/env python3
# cross_account_data_access.py

import boto3
import json
from botocore.exceptions import ClientError

class CrossAccountDataAccess:
    def __init__(self, source_profile, target_profile, region='us-east-1'):
        # Source account session
        self.source_session = boto3.Session(profile_name=source_profile)
        self.source_s3 = self.source_session.client('s3', region_name=region)
        self.source_kms = self.source_session.client('kms', region_name=region)
        
        # Target account session
        self.target_session = boto3.Session(profile_name=target_profile)
        self.target_s3 = self.target_session.client('s3', region_name=region)
        self.target_kms = self.target_session.client('kms', region_name=region)
        
        self.region = region
    
    def encrypt_and_upload(self, bucket_name, key_name, data, kms_key_id):
        """Encrypt data and upload to S3 from source account"""
        try:
            # Upload with server-side encryption
            response = self.source_s3.put_object(
                Bucket=bucket_name,
                Key=key_name,
                Body=data,
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=kms_key_id,
                Metadata={
                    'source-account': 'true',
                    'encryption-context': 'cross-account-sharing'
                }
            )
            
            print(f"Successfully uploaded {key_name} to {bucket_name}")
            return response
            
        except ClientError as e:
            print(f"Error uploading data: {e}")
            return None
    
    def download_and_decrypt(self, bucket_name, key_name):
        """Download and decrypt data from target account"""
        try:
            # Download object
            response = self.target_s3.get_object(
                Bucket=bucket_name,
                Key=key_name
            )
            
            # Data is automatically decrypted by S3 if target account has KMS permissions
            decrypted_data = response['Body'].read()
            
            print(f"Successfully downloaded and decrypted {key_name}")
            return decrypted_data
            
        except ClientError as e:
            print(f"Error downloading data: {e}")
            return None
    
    def test_cross_account_access(self, bucket_name, kms_key_alias):
        """Test complete cross-account data sharing workflow"""
        test_data = "This is sensitive data shared across AWS accounts"
        test_key = "test-data/sensitive-file.txt"
        
        print("=== Cross-Account Data Sharing Test ===")
        
        # Step 1: Encrypt and upload from source account
        print("1. Uploading encrypted data from source account...")
        upload_result = self.encrypt_and_upload(
            bucket_name, 
            test_key, 
            test_data, 
            kms_key_alias
        )
        
        if not upload_result:
            return False
        
        # Step 2: Download and decrypt from target account
        print("2. Downloading and decrypting data from target account...")
        downloaded_data = self.download_and_decrypt(bucket_name, test_key)
        
        if not downloaded_data:
            return False
        
        # Step 3: Verify data integrity
        if downloaded_data.decode('utf-8') == test_data:
            print("✅ Cross-account data sharing test successful!")
            print(f"Original: {test_data}")
            print(f"Retrieved: {downloaded_data.decode('utf-8')}")
            return True
        else:
            print("❌ Data integrity check failed!")
            return False

# Usage example
if __name__ == "__main__":
    # Configure AWS profiles for source and target accounts
    cross_account = CrossAccountDataAccess(
        source_profile='source-account',
        target_profile='target-account'
    )
    
    # Test cross-account access
    success = cross_account.test_cross_account_access(
        bucket_name='cross-account-data-sharing',
        kms_key_alias='alias/shared-data-key'
    )
    
    if success:
        print("Cross-account setup is working correctly!")
    else:
        print("Cross-account setup needs troubleshooting.")
```

---

## Monitoring, Auditing & Best Practices

### 1. CloudTrail Integration

#### KMS CloudTrail Events:
```json
{
  "eventVersion": "1.05",
  "userIdentity": {
    "type": "IAMUser",
    "principalId": "AIDACKCEVSQ6C2EXAMPLE",
    "arn": "arn:aws:iam::123456789012:user/alice",
    "accountId": "123456789012",
    "userName": "alice"
  },
  "eventTime": "2024-01-15T10:30:00Z",
  "eventSource": "kms.amazonaws.com",
  "eventName": "Decrypt",
  "awsRegion": "us-east-1",
  "sourceIPAddress": "192.168.1.100",
  "userAgent": "aws-cli/2.0.0",
  "requestParameters": {
    "keyId": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
    "encryptionContext": {
      "Department": "Finance",
      "Project": "Audit2024"
    }
  },
  "responseElements": null,
  "requestID": "12345678-1234-1234-1234-123456789012",
  "eventID": "87654321-4321-4321-4321-210987654321",
  "eventType": "AwsApiCall",
  "recipientAccountId": "123456789012",
  "serviceEventDetails": {
    "connectTime": 1642248600000,
    "disconnectTime": 1642248601000
  }
}
```

#### CloudTrail Analysis Script:
```python
#!/usr/bin/env python3
# kms_cloudtrail_analyzer.py

import boto3
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class KMSCloudTrailAnalyzer:
    def __init__(self, region='us-east-1'):
        self.cloudtrail = boto3.client('cloudtrail', region_name=region)
        self.kms = boto3.client('kms', region_name=region)
    
    def get_kms_events(self, start_time, end_time, event_names=None):
        """Retrieve KMS events from CloudTrail"""
        if event_names is None:
            event_names = [
                'Encrypt', 'Decrypt', 'GenerateDataKey', 'GenerateDataKeyWithoutPlaintext',
                'CreateKey', 'DeleteKey', 'DisableKey', 'EnableKey', 'ScheduleKeyDeletion'
            ]
        
        events = []
        
        for event_name in event_names:
            try:
                paginator = self.cloudtrail.get_paginator('lookup_events')
                
                for page in paginator.paginate(
                    LookupAttributes=[
                        {
                            'AttributeKey': 'EventName',
                            'AttributeValue': event_name
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time
                ):
                    events.extend(page['Events'])
            
            except Exception as e:
                print(f"Error retrieving {event_name} events: {e}")
        
        return events
    
    def analyze_key_usage(self, days=30):
        """Analyze KMS key usage patterns"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        print(f"Analyzing KMS usage from {start_time} to {end_time}")
        
        # Get KMS events
        events = self.get_kms_events(start_time, end_time)
        
        # Analysis results
        analysis = {
            'total_events': len(events),
            'events_by_type': Counter(),
            'events_by_user': Counter(),
            'events_by_key': Counter(),
            'events_by_source_ip': Counter(),
            'encryption_contexts': defaultdict(int),
            'suspicious_activities': []
        }
        
        for event in events:\n            event_name = event['EventName']\n            username = event.get('Username', 'Unknown')\n            source_ip = event.get('SourceIPAddress', 'Unknown')\n            \n            # Parse CloudTrail record\n            if 'CloudTrailEvent' in event:\n                ct_event = json.loads(event['CloudTrailEvent'])\n                \n                # Extract key information\n                key_id = 'Unknown'\n                if 'requestParameters' in ct_event and ct_event['requestParameters']:\n                    key_id = ct_event['requestParameters'].get('keyId', 'Unknown')\n                \n                # Extract encryption context\n                if 'requestParameters' in ct_event and ct_event['requestParameters']:\n                    enc_context = ct_event['requestParameters'].get('encryptionContext', {})\n                    if enc_context:\n                        context_str = json.dumps(enc_context, sort_keys=True)\n                        analysis['encryption_contexts'][context_str] += 1\n                \n                # Count events\n                analysis['events_by_type'][event_name] += 1\n                analysis['events_by_user'][username] += 1\n                analysis['events_by_key'][key_id] += 1\n                analysis['events_by_source_ip'][source_ip] += 1\n                \n                # Detect suspicious activities\n                self._detect_suspicious_activity(ct_event, analysis['suspicious_activities'])\n        \n        return analysis\n    \n    def _detect_suspicious_activity(self, event, suspicious_list):\n        \"\"\"Detect potentially suspicious KMS activities\"\"\"\n        event_name = event.get('eventName')\n        source_ip = event.get('sourceIPAddress')\n        user_identity = event.get('userIdentity', {})\n        \n        # Check for suspicious patterns\n        suspicious_patterns = [\n            # Multiple key deletions\n            {\n                'condition': event_name in ['ScheduleKeyDeletion', 'DeleteKey'],\n                'reason': 'Key deletion attempt',\n                'severity': 'HIGH'\n            },\n            # Access from unusual IP ranges\n            {\n                'condition': source_ip and not any([\n                    source_ip.startswith('10.'),\n                    source_ip.startswith('172.'),\n                    source_ip.startswith('192.168.'),\n                    source_ip.startswith('127.')\n                ]),\n                'reason': 'Access from external IP',\n                'severity': 'MEDIUM'\n            },\n            # Root user activity\n            {\n                'condition': user_identity.get('type') == 'Root',\n                'reason': 'Root user KMS activity',\n                'severity': 'MEDIUM'\n            },\n            # Bulk encryption operations\n            {\n                'condition': event_name in ['Encrypt', 'GenerateDataKey'],\n                'reason': 'Bulk encryption activity',\n                'severity': 'LOW'\n            }\n        ]\n        \n        for pattern in suspicious_patterns:\n            if pattern['condition']:\n                suspicious_list.append({\n                    'event_time': event.get('eventTime'),\n                    'event_name': event_name,\n                    'source_ip': source_ip,\n                    'user': user_identity.get('userName', user_identity.get('type', 'Unknown')),\n                    'reason': pattern['reason'],\n                    'severity': pattern['severity']\n                })\n    \n    def generate_usage_report(self, analysis):\n        \"\"\"Generate comprehensive usage report\"\"\"\n        report = f\"\"\"\n=== KMS Usage Analysis Report ===\nGenerated: {datetime.utcnow().isoformat()}\n\n📊 SUMMARY\nTotal Events: {analysis['total_events']}\nSuspicious Activities: {len(analysis['suspicious_activities'])}\n\n📈 EVENTS BY TYPE\n{self._format_counter(analysis['events_by_type'])}\n\n👥 TOP USERS\n{self._format_counter(analysis['events_by_user'], top=10)}\n\n🔑 TOP KEYS\n{self._format_counter(analysis['events_by_key'], top=10)}\n\n🌐 SOURCE IPs\n{self._format_counter(analysis['events_by_source_ip'], top=10)}\n\n🔒 ENCRYPTION CONTEXTS\n{self._format_counter(analysis['encryption_contexts'], top=5)}\n\"\"\"\n        \n        if analysis['suspicious_activities']:\n            report += \"\\n🚨 SUSPICIOUS ACTIVITIES\\n\"\n            for activity in analysis['suspicious_activities']:\n                report += f\"[{activity['severity']}] {activity['event_time']} - {activity['reason']}\\n\"\n                report += f\"  User: {activity['user']}, IP: {activity['source_ip']}, Event: {activity['event_name']}\\n\\n\"\n        \n        return report\n    \n    def _format_counter(self, counter, top=None):\n        \"\"\"Format Counter object for display\"\"\"\n        items = counter.most_common(top) if top else counter.most_common()\n        return \"\\n\".join([f\"  {item}: {count}\" for item, count in items])\n\n# Usage example\nif __name__ == \"__main__\":\n    analyzer = KMSCloudTrailAnalyzer()\n    \n    # Analyze last 7 days\n    analysis = analyzer.analyze_key_usage(days=7)\n    \n    # Generate report\n    report = analyzer.generate_usage_report(analysis)\n    print(report)\n    \n    # Save report to file\n    with open(f'kms-usage-report-{datetime.now().strftime(\"%Y%m%d\")}.txt', 'w') as f:\n        f.write(report)\n```

### 2. CloudWatch Monitoring

#### KMS CloudWatch Metrics Setup:
```bash\n# Create CloudWatch dashboard for KMS monitoring\naws cloudwatch put-dashboard \\\n  --dashboard-name \"KMS-Monitoring\" \\\n  --dashboard-body '{\n    \"widgets\": [\n      {\n        \"type\": \"metric\",\n        \"properties\": {\n          \"metrics\": [\n            [\"AWS/KMS\", \"NumberOfRequestsSucceeded\", \"KeyId\", \"12345678-1234-1234-1234-123456789012\"],\n            [\"AWS/KMS\", \"NumberOfRequestsFailed\", \"KeyId\", \"12345678-1234-1234-1234-123456789012\"]\n          ],\n          \"period\": 300,\n          \"stat\": \"Sum\",\n          \"region\": \"us-east-1\",\n          \"title\": \"KMS API Requests\"\n        }\n      }\n    ]\n  }'\n\n# Create alarm for failed KMS requests\naws cloudwatch put-metric-alarm \\\n  --alarm-name \"KMS-Failed-Requests\" \\\n  --alarm-description \"Alert on KMS request failures\" \\\n  --metric-name NumberOfRequestsFailed \\\n  --namespace AWS/KMS \\\n  --statistic Sum \\\n  --period 300 \\\n  --threshold 10 \\\n  --comparison-operator GreaterThanThreshold \\\n  --evaluation-periods 2\n```

#### Terraform CloudWatch Configuration:\n```hcl\n# CloudWatch dashboard for KMS\nresource \"aws_cloudwatch_dashboard\" \"kms_monitoring\" {\n  dashboard_name = \"KMS-Monitoring\"\n  \n  dashboard_body = jsonencode({\n    widgets = [\n      {\n        type   = \"metric\"\n        x      = 0\n        y      = 0\n        width  = 12\n        height = 6\n        \n        properties = {\n          metrics = [\n            [\"AWS/KMS\", \"NumberOfRequestsSucceeded\"],\n            [\"AWS/KMS\", \"NumberOfRequestsFailed\"]\n          ]\n          view    = \"timeSeries\"\n          stacked = false\n          region  = var.aws_region\n          title   = \"KMS API Requests\"\n          period  = 300\n        }\n      },\n      {\n        type   = \"metric\"\n        x      = 0\n        y      = 6\n        width  = 12\n        height = 6\n        \n        properties = {\n          metrics = [\n            [\"AWS/KMS\", \"NumberOfRequestsSucceeded\", \"Operation\", \"Encrypt\"],\n            [\"AWS/KMS\", \"NumberOfRequestsSucceeded\", \"Operation\", \"Decrypt\"],\n            [\"AWS/KMS\", \"NumberOfRequestsSucceeded\", \"Operation\", \"GenerateDataKey\"]\n          ]\n          view   = \"timeSeries\"\n          region = var.aws_region\n          title  = \"KMS Operations\"\n          period = 300\n        }\n      }\n    ]\n  })\n}\n\n# CloudWatch alarms\nresource \"aws_cloudwatch_metric_alarm\" \"kms_failed_requests\" {\n  alarm_name          = \"kms-failed-requests\"\n  comparison_operator = \"GreaterThanThreshold\"\n  evaluation_periods  = \"2\"\n  metric_name         = \"NumberOfRequestsFailed\"\n  namespace           = \"AWS/KMS\"\n  period              = \"300\"\n  statistic           = \"Sum\"\n  threshold           = \"10\"\n  alarm_description   = \"This metric monitors KMS failed requests\"\n  alarm_actions       = [aws_sns_topic.alerts.arn]\n}\n\nresource \"aws_cloudwatch_metric_alarm\" \"kms_key_deletion\" {\n  alarm_name          = \"kms-key-deletion-scheduled\"\n  comparison_operator = \"GreaterThanThreshold\"\n  evaluation_periods  = \"1\"\n  metric_name         = \"NumberOfRequestsSucceeded\"\n  namespace           = \"AWS/KMS\"\n  period              = \"300\"\n  statistic           = \"Sum\"\n  threshold           = \"0\"\n  alarm_description   = \"Alert when KMS key deletion is scheduled\"\n  alarm_actions       = [aws_sns_topic.critical_alerts.arn]\n  \n  dimensions = {\n    Operation = \"ScheduleKeyDeletion\"\n  }\n}\n\n# SNS topics for alerts\nresource \"aws_sns_topic\" \"alerts\" {\n  name = \"kms-alerts\"\n}\n\nresource \"aws_sns_topic\" \"critical_alerts\" {\n  name = \"kms-critical-alerts\"\n}\n```\n\n### 3. Security Best Practices\n\n#### KMS Security Checklist:\n```markdown\n# KMS Security Best Practices Checklist\n\n## ✅ Key Management\n- [ ] Use customer managed keys for sensitive data\n- [ ] Enable automatic key rotation where possible\n- [ ] Implement proper key lifecycle management\n- [ ] Use meaningful key descriptions and tags\n- [ ] Regularly audit unused keys\n\n## ✅ Access Control\n- [ ] Follow principle of least privilege\n- [ ] Use key policies in addition to IAM policies\n- [ ] Implement encryption context for additional security\n- [ ] Avoid using root user for KMS operations\n- [ ] Use cross-account access carefully\n\n## ✅ Monitoring & Auditing\n- [ ] Enable CloudTrail for all KMS operations\n- [ ] Set up CloudWatch alarms for suspicious activities\n- [ ] Monitor key usage patterns\n- [ ] Implement automated compliance checking\n- [ ] Regular security assessments\n\n## ✅ Operational Security\n- [ ] Use infrastructure as code (Terraform/CloudFormation)\n- [ ] Implement proper backup and disaster recovery\n- [ ] Test key deletion and recovery procedures\n- [ ] Document key usage and ownership\n- [ ] Train team on KMS best practices\n\n## ✅ Application Integration\n- [ ] Use envelope encryption for large data\n- [ ] Implement proper error handling\n- [ ] Cache decrypted data keys appropriately\n- [ ] Use encryption context in applications\n- [ ] Validate certificate chains properly\n```\n\n#### Automated Security Assessment:\n```python\n#!/usr/bin/env python3\n# kms_security_assessment.py\n\nimport boto3\nimport json\nfrom datetime import datetime, timedelta\n\nclass KMSSecurityAssessment:\n    def __init__(self, region='us-east-1'):\n        self.kms = boto3.client('kms', region_name=region)\n        self.iam = boto3.client('iam', region_name=region)\n        self.cloudtrail = boto3.client('cloudtrail', region_name=region)\n    \n    def assess_key_security(self):\n        \"\"\"Perform comprehensive KMS security assessment\"\"\"\n        assessment = {\n            'timestamp': datetime.utcnow().isoformat(),\n            'total_keys': 0,\n            'findings': [],\n            'recommendations': [],\n            'compliance_score': 0\n        }\n        \n        try:\n            # Get all customer managed keys\n            paginator = self.kms.get_paginator('list_keys')\n            \n            for page in paginator.paginate():\n                for key in page['Keys']:\n                    key_id = key['KeyId']\n                    \n                    # Get key details\n                    key_details = self.kms.describe_key(KeyId=key_id)\n                    key_metadata = key_details['KeyMetadata']\n                    \n                    # Skip AWS managed keys\n                    if key_metadata['KeyManager'] == 'AWS':\n                        continue\n                    \n                    assessment['total_keys'] += 1\n                    \n                    # Assess individual key\n                    key_findings = self._assess_individual_key(key_id, key_metadata)\n                    assessment['findings'].extend(key_findings)\n            \n            # Generate recommendations\n            assessment['recommendations'] = self._generate_recommendations(assessment['findings'])\n            \n            # Calculate compliance score\n            assessment['compliance_score'] = self._calculate_compliance_score(assessment['findings'])\n            \n        except Exception as e:\n            assessment['findings'].append({\n                'type': 'ERROR',\n                'severity': 'HIGH',\n                'message': f\"Assessment failed: {e}\"\n            })\n        \n        return assessment\n    \n    def _assess_individual_key(self, key_id, key_metadata):\n        \"\"\"Assess security of individual KMS key\"\"\"\n        findings = []\n        \n        try:\n            # Check key state\n            if key_metadata['KeyState'] != 'Enabled':\n                findings.append({\n                    'key_id': key_id,\n                    'type': 'KEY_STATE',\n                    'severity': 'MEDIUM',\n                    'message': f\"Key is in {key_metadata['KeyState']} state\"\n                })\n            \n            # Check key rotation\n            try:\n                rotation_status = self.kms.get_key_rotation_status(KeyId=key_id)\n                if not rotation_status['KeyRotationEnabled']:\n                    findings.append({\n                        'key_id': key_id,\n                        'type': 'ROTATION_DISABLED',\n                        'severity': 'MEDIUM',\n                        'message': 'Automatic key rotation is disabled'\n                    })\n            except:\n                pass  # Some keys don't support rotation\n            \n            # Check key policy\n            try:\n                policy_response = self.kms.get_key_policy(KeyId=key_id, PolicyName='default')\n                policy = json.loads(policy_response['Policy'])\n                \n                # Check for overly permissive policies\n                for statement in policy.get('Statement', []):\n                    if statement.get('Effect') == 'Allow':\n                        # Check for wildcard principals\n                        principal = statement.get('Principal', {})\n                        if principal == '*' or (isinstance(principal, dict) and principal.get('AWS') == '*'):\n                            findings.append({\n                                'key_id': key_id,\n                                'type': 'OVERLY_PERMISSIVE_POLICY',\n                                'severity': 'HIGH',\n                                'message': 'Key policy allows access to all principals (*)'\n                            })\n                        \n                        # Check for wildcard actions\n                        actions = statement.get('Action', [])\n                        if isinstance(actions, str):\n                            actions = [actions]\n                        \n                        if 'kms:*' in actions:\n                            findings.append({\n                                'key_id': key_id,\n                                'type': 'WILDCARD_ACTIONS',\n                                'severity': 'MEDIUM',\n                                'message': 'Key policy allows all KMS actions (kms:*)'\n                            })\n            \n            except Exception as e:\n                findings.append({\n                    'key_id': key_id,\n                    'type': 'POLICY_CHECK_FAILED',\n                    'severity': 'LOW',\n                    'message': f\"Could not check key policy: {e}\"\n                })\n            \n            # Check key age\n            key_age = (datetime.now(key_metadata['CreationDate'].tzinfo) - key_metadata['CreationDate']).days\n            if key_age > 365:  # Older than 1 year\n                findings.append({\n                    'key_id': key_id,\n                    'type': 'OLD_KEY',\n                    'severity': 'LOW',\n                    'message': f'Key is {key_age} days old, consider rotation'\n                })\n            \n            # Check key description\n            if not key_metadata.get('Description') or key_metadata['Description'] == '':\n                findings.append({\n                    'key_id': key_id,\n                    'type': 'MISSING_DESCRIPTION',\n                    'severity': 'LOW',\n                    'message': 'Key has no description'\n                })\n        \n        except Exception as e:\n            findings.append({\n                'key_id': key_id,\n                'type': 'ASSESSMENT_ERROR',\n                'severity': 'MEDIUM',\n                'message': f\"Key assessment failed: {e}\"\n            })\n        \n        return findings\n    \n    def _generate_recommendations(self, findings):\n        \"\"\"Generate security recommendations based on findings\"\"\"\n        recommendations = []\n        \n        # Count findings by type\n        finding_counts = {}\n        for finding in findings:\n            finding_type = finding['type']\n            finding_counts[finding_type] = finding_counts.get(finding_type, 0) + 1\n        \n        # Generate recommendations\n        if finding_counts.get('ROTATION_DISABLED', 0) > 0:\n            recommendations.append({\n                'priority': 'MEDIUM',\n                'action': 'Enable automatic key rotation for all eligible keys',\n                'impact': 'Improves security by regularly changing key material'\n            })\n        \n        if finding_counts.get('OVERLY_PERMISSIVE_POLICY', 0) > 0:\n            recommendations.append({\n                'priority': 'HIGH',\n                'action': 'Review and restrict key policies to follow principle of least privilege',\n                'impact': 'Reduces risk of unauthorized key access'\n            })\n        \n        if finding_counts.get('OLD_KEY', 0) > 0:\n            recommendations.append({\n                'priority': 'LOW',\n                'action': 'Consider manual rotation or replacement of old keys',\n                'impact': 'Reduces risk from long-term key exposure'\n            })\n        \n        if finding_counts.get('MISSING_DESCRIPTION', 0) > 0:\n            recommendations.append({\n                'priority': 'LOW',\n                'action': 'Add meaningful descriptions to all KMS keys',\n                'impact': 'Improves key management and auditing'\n            })\n        \n        return recommendations\n    \n    def _calculate_compliance_score(self, findings):\n        \"\"\"Calculate overall compliance score (0-100)\"\"\"\n        if not findings:\n            return 100\n        \n        # Weight findings by severity\n        severity_weights = {\n            'HIGH': 10,\n            'MEDIUM': 5,\n            'LOW': 1\n        }\n        \n        total_weight = sum(severity_weights.get(f['severity'], 1) for f in findings)\n        max_possible_weight = len(findings) * 10  # Assuming all HIGH severity\n        \n        # Calculate score (higher is better)\n        score = max(0, 100 - (total_weight / max_possible_weight * 100))\n        return round(score, 2)\n    \n    def generate_report(self, assessment):\n        \"\"\"Generate human-readable assessment report\"\"\"\n        report = f\"\"\"\n=== KMS Security Assessment Report ===\nGenerated: {assessment['timestamp']}\nTotal Keys Assessed: {assessment['total_keys']}\nCompliance Score: {assessment['compliance_score']}/100\n\n📊 FINDINGS SUMMARY\nTotal Findings: {len(assessment['findings'])}\n\"\"\"\n        \n        # Count by severity\n        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}\n        for finding in assessment['findings']:\n            severity_counts[finding['severity']] += 1\n        \n        report += f\"\"\"\nHigh Severity: {severity_counts['HIGH']}\nMedium Severity: {severity_counts['MEDIUM']}\nLow Severity: {severity_counts['LOW']}\n\n🔍 DETAILED FINDINGS\n\"\"\"\n        \n        for finding in assessment['findings']:\n            report += f\"[{finding['severity']}] {finding.get('key_id', 'N/A')} - {finding['message']}\\n\"\n        \n        if assessment['recommendations']:\n            report += \"\\n💡 RECOMMENDATIONS\\n\"\n            for i, rec in enumerate(assessment['recommendations'], 1):\n                report += f\"{i}. [{rec['priority']}] {rec['action']}\\n\"\n                report += f\"   Impact: {rec['impact']}\\n\\n\"\n        \n        return report\n\n# Usage example\nif __name__ == \"__main__\":\n    assessor = KMSSecurityAssessment()\n    \n    print(\"Running KMS security assessment...\")\n    assessment = assessor.assess_key_security()\n    \n    # Generate and display report\n    report = assessor.generate_report(assessment)\n    print(report)\n    \n    # Save report\n    filename = f'kms-security-assessment-{datetime.now().strftime(\"%Y%m%d\")}.txt'\n    with open(filename, 'w') as f:\n        f.write(report)\n    \n    print(f\"\\nReport saved to: {filename}\")\n    print(f\"Compliance Score: {assessment['compliance_score']}/100\")\n```\n\nThis completes the comprehensive AWS KMS guide covering all aspects from fundamentals to advanced topics including multi-region keys, cross-account access, monitoring, auditing, and security best practices with practical implementation examples.