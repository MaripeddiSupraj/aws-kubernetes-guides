# AWS Organizations Service Control Policies (SCP) Complete Guide

A comprehensive guide for implementing AWS Organizations with Service Control Policies, including real-world enterprise examples and step-by-step implementation.

## 📋 Table of Contents

1. [Organizations Setup](#organizations-setup)
2. [SCP Fundamentals](#scp-fundamentals)
3. [Real-World Enterprise Example](#real-world-enterprise-example)
4. [SCP Policy Examples](#scp-policy-examples)
5. [Implementation Steps](#implementation-steps)
6. [Monitoring & Compliance](#monitoring--compliance)
7. [Troubleshooting](#troubleshooting)

## 🏢 Real-World Enterprise Example: TechCorp Inc.

### Organization Structure
```
TechCorp Root Organization
├── Security OU
│   ├── Log Archive Account (123456789012)
│   └── Audit Account (123456789013)
├── Production OU
│   ├── Prod-Web Account (123456789014)
│   ├── Prod-DB Account (123456789015)
│   └── Prod-Analytics Account (123456789016)
├── Development OU
│   ├── Dev-Team-A Account (123456789017)
│   ├── Dev-Team-B Account (123456789018)
│   └── Staging Account (123456789019)
└── Sandbox OU
    ├── Sandbox-1 Account (123456789020)
    └── Sandbox-2 Account (123456789021)
```

### Business Requirements
- **Security**: Prevent data exfiltration, enforce encryption
- **Cost Control**: Limit expensive services in dev/sandbox
- **Compliance**: SOC2, PCI-DSS requirements
- **Regional Restrictions**: Only US regions allowed
- **Resource Tagging**: Mandatory cost center tags

## 🚀 Organizations Setup

### Step 1: Create Organization
```bash
# Create organization
aws organizations create-organization --feature-set ALL

# Get organization details
aws organizations describe-organization
```

### Step 2: Create Organizational Units
```bash
# Create Security OU
aws organizations create-organizational-unit \
  --parent-id r-exampleRootId \
  --name "Security"

# Create Production OU
aws organizations create-organizational-unit \
  --parent-id r-exampleRootId \
  --name "Production"

# Create Development OU
aws organizations create-organizational-unit \
  --parent-id r-exampleRootId \
  --name "Development"

# Create Sandbox OU
aws organizations create-organizational-unit \
  --parent-id r-exampleRootId \
  --name "Sandbox"
```

### Step 3: Move Accounts to OUs
```bash
# Move account to Production OU
aws organizations move-account \
  --account-id 123456789014 \
  --source-parent-id r-exampleRootId \
  --destination-parent-id ou-exampleProdId

# List accounts in OU
aws organizations list-accounts-for-parent --parent-id ou-exampleProdId
```

## 📜 SCP Policy Examples

### 1. Root Organization Policy - Foundation Security
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAllOutsideUSRegions",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "us-east-1",
            "us-east-2",
            "us-west-1",
            "us-west-2"
          ]
        },
        "ForAnyValue:StringNotEquals": {
          "aws:PrincipalServiceName": [
            "cloudfront.amazonaws.com",
            "route53.amazonaws.com",
            "iam.amazonaws.com",
            "waf.amazonaws.com",
            "support.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "DenyRootUserAccess",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalType": "Root"
        }
      }
    },
    {
      "Sid": "RequireSSLRequestsOnly",
      "Effect": "Deny",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::*/*",
        "arn:aws:s3:::*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

### 2. Production OU Policy - High Security
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedEBSVolumes",
      "Effect": "Deny",
      "Action": [
        "ec2:CreateVolume",
        "ec2:RunInstances"
      ],
      "Resource": "*",
      "Condition": {
        "Bool": {
          "ec2:Encrypted": "false"
        }
      }
    },
    {
      "Sid": "DenyUnencryptedRDSInstances",
      "Effect": "Deny",
      "Action": [
        "rds:CreateDBInstance",
        "rds:CreateDBCluster"
      ],
      "Resource": "*",
      "Condition": {
        "Bool": {
          "rds:StorageEncrypted": "false"
        }
      }
    },
    {
      "Sid": "RequireMandatoryTags",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "rds:CreateDBInstance",
        "s3:CreateBucket"
      ],
      "Resource": "*",
      "Condition": {
        "Null": {
          "aws:RequestTag/CostCenter": "true"
        }
      }
    },
    {
      "Sid": "DenyInstanceTermination",
      "Effect": "Deny",
      "Action": [
        "ec2:TerminateInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalArn": [
            "arn:aws:iam::*:role/ProductionAdminRole"
          ]
        }
      }
    },
    {
      "Sid": "DenyPublicS3Buckets",
      "Effect": "Deny",
      "Action": [
        "s3:PutBucketPublicAccessBlock",
        "s3:PutBucketAcl",
        "s3:PutBucketPolicy",
        "s3:PutObjectAcl"
      ],
      "Resource": "*",
      "Condition": {
        "Bool": {
          "s3:PublicAccessBlockConfiguration": "false"
        }
      }
    }
  ]
}
```

### 3. Development OU Policy - Balanced Control
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyExpensiveInstances",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "ForAnyValue:StringNotEquals": {
          "ec2:InstanceType": [
            "t3.nano",
            "t3.micro",
            "t3.small",
            "t3.medium",
            "t3.large"
          ]
        }
      }
    },
    {
      "Sid": "DenyProductionDataAccess",
      "Effect": "Deny",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::prod-*",
        "arn:aws:s3:::prod-*/*"
      ]
    },
    {
      "Sid": "LimitRDSInstanceSize",
      "Effect": "Deny",
      "Action": [
        "rds:CreateDBInstance"
      ],
      "Resource": "*",
      "Condition": {
        "ForAnyValue:StringNotEquals": {
          "rds:db-instance-class": [
            "db.t3.micro",
            "db.t3.small",
            "db.t3.medium"
          ]
        }
      }
    },
    {
      "Sid": "DenyVPCModification",
      "Effect": "Deny",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:ModifyVpcAttribute",
        "ec2:CreateInternetGateway",
        "ec2:AttachInternetGateway"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4. Sandbox OU Policy - Maximum Restrictions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAllExpensiveServices",
      "Effect": "Deny",
      "Action": [
        "redshift:*",
        "sagemaker:*",
        "emr:*",
        "databrew:*",
        "glue:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LimitEC2InstanceTypes",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "ForAnyValue:StringNotEquals": {
          "ec2:InstanceType": [
            "t3.nano",
            "t3.micro"
          ]
        }
      }
    },
    {
      "Sid": "DenyNetworkingChanges",
      "Effect": "Deny",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:CreateInternetGateway",
        "ec2:CreateNatGateway",
        "directconnect:*",
        "route53:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyIAMModifications",
      "Effect": "Deny",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LimitS3Storage",
      "Effect": "Deny",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "*",
      "Condition": {
        "NumericGreaterThan": {
          "s3:object-size": "104857600"
        }
      }
    }
  ]
}
```

### 5. Security OU Policy - Audit & Logging
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyCloudTrailDisabling",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail",
        "cloudtrail:PutEventSelectors"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyConfigDisabling",
      "Effect": "Deny",
      "Action": [
        "config:DeleteConfigurationRecorder",
        "config:DeleteDeliveryChannel",
        "config:StopConfigurationRecorder"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyGuardDutyDisabling",
      "Effect": "Deny",
      "Action": [
        "guardduty:DeleteDetector",
        "guardduty:DeleteMembers",
        "guardduty:DisassociateFromMasterAccount",
        "guardduty:StopMonitoringMembers"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ProtectLogGroups",
      "Effect": "Deny",
      "Action": [
        "logs:DeleteLogGroup",
        "logs:DeleteLogStream",
        "logs:PutRetentionPolicy"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalArn": [
            "arn:aws:iam::*:role/SecurityAdminRole"
          ]
        }
      }
    }
  ]
}
```

## 🔧 Implementation Steps

### Step 1: Create and Attach SCPs
```bash
# Create Root Organization Policy
aws organizations create-policy \
  --name "RootSecurityPolicy" \
  --description "Foundation security controls for all accounts" \
  --type SERVICE_CONTROL_POLICY \
  --content file://root-security-policy.json

# Get policy ID
POLICY_ID=$(aws organizations list-policies --filter SERVICE_CONTROL_POLICY --query 'Policies[?Name==`RootSecurityPolicy`].Id' --output text)

# Attach to root
aws organizations attach-policy \
  --policy-id $POLICY_ID \
  --target-id r-exampleRootId
```

### Step 2: Create OU-Specific Policies
```bash
# Create Production Policy
aws organizations create-policy \
  --name "ProductionSecurityPolicy" \
  --description "High security controls for production workloads" \
  --type SERVICE_CONTROL_POLICY \
  --content file://production-policy.json

# Attach to Production OU
PROD_POLICY_ID=$(aws organizations list-policies --filter SERVICE_CONTROL_POLICY --query 'Policies[?Name==`ProductionSecurityPolicy`].Id' --output text)
aws organizations attach-policy \
  --policy-id $PROD_POLICY_ID \
  --target-id ou-exampleProdId

# Create Development Policy
aws organizations create-policy \
  --name "DevelopmentPolicy" \
  --description "Balanced controls for development environments" \
  --type SERVICE_CONTROL_POLICY \
  --content file://development-policy.json

# Attach to Development OU
DEV_POLICY_ID=$(aws organizations list-policies --filter SERVICE_CONTROL_POLICY --query 'Policies[?Name==`DevelopmentPolicy`].Id' --output text)
aws organizations attach-policy \
  --policy-id $DEV_POLICY_ID \
  --target-id ou-exampleDevId
```

### Step 3: Account-Specific Policies
```bash
# Create policy for specific high-risk account
aws organizations create-policy \
  --name "HighRiskAccountPolicy" \
  --description "Additional restrictions for high-risk account" \
  --type SERVICE_CONTROL_POLICY \
  --content file://high-risk-policy.json

# Attach to specific account
RISK_POLICY_ID=$(aws organizations list-policies --filter SERVICE_CONTROL_POLICY --query 'Policies[?Name==`HighRiskAccountPolicy`].Id' --output text)
aws organizations attach-policy \
  --policy-id $RISK_POLICY_ID \
  --target-id 123456789020
```

## 📊 Advanced SCP Patterns

### 1. Time-Based Restrictions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyOutsideBusinessHours",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "rds:CreateDBInstance"
      ],
      "Resource": "*",
      "Condition": {
        "DateGreaterThan": {
          "aws:CurrentTime": "18:00Z"
        },
        "DateLessThan": {
          "aws:CurrentTime": "08:00Z"
        }
      }
    }
  ]
}
```

### 2. IP-Based Restrictions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAccessOutsideCorporateNetwork",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "IpAddressIfExists": {
          "aws:SourceIp": [
            "203.0.113.0/24",
            "198.51.100.0/24"
          ]
        },
        "Bool": {
          "aws:ViaAWSService": "false"
        }
      }
    }
  ]
}
```

### 3. MFA Enforcement
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAllExceptListedIfNoMFA",
      "Effect": "Deny",
      "NotAction": [
        "iam:CreateVirtualMFADevice",
        "iam:EnableMFADevice",
        "iam:GetUser",
        "iam:ListMFADevices",
        "iam:ListVirtualMFADevices",
        "iam:ResyncMFADevice",
        "sts:GetSessionToken"
      ],
      "Resource": "*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
  ]
}
```

## 🔍 Monitoring & Compliance

### CloudTrail Integration
```bash
# Create CloudTrail for SCP monitoring
aws cloudtrail create-trail \
  --name scp-compliance-trail \
  --s3-bucket-name scp-audit-logs-bucket \
  --include-global-service-events \
  --is-multi-region-trail \
  --enable-log-file-validation

# Start logging
aws cloudtrail start-logging --name scp-compliance-trail
```

### Config Rules for SCP Compliance
```json
{
  "ConfigRuleName": "scp-compliance-check",
  "Description": "Checks if resources comply with SCP policies",
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "REQUIRED_TAGS"
  },
  "InputParameters": "{\"requiredTagKeys\":\"CostCenter,Environment\"}"
}
```

### CloudWatch Alarms
```bash
# Create alarm for SCP violations
aws cloudwatch put-metric-alarm \
  --alarm-name "SCP-Violations" \
  --alarm-description "Alert on SCP policy violations" \
  --metric-name "ErrorCount" \
  --namespace "AWS/CloudTrail" \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1
```

## 🛠️ SCP Testing & Validation

### Policy Simulator
```bash
# Test policy using IAM Policy Simulator
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/testuser \
  --action-names ec2:RunInstances \
  --resource-arns arn:aws:ec2:us-east-1:123456789012:instance/*
```

### Testing Script
```bash
#!/bin/bash
# scp-test.sh - Test SCP policies

echo "Testing SCP Policies..."

# Test 1: Try to create unencrypted EBS volume (should fail in prod)
echo "Test 1: Creating unencrypted EBS volume..."
aws ec2 create-volume \
  --size 10 \
  --availability-zone us-east-1a \
  --encrypted false 2>&1 | grep -q "AccessDenied" && echo "✓ PASS: Unencrypted volume blocked" || echo "✗ FAIL: Unencrypted volume allowed"

# Test 2: Try to create expensive instance (should fail in dev/sandbox)
echo "Test 2: Creating expensive instance..."
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type m5.24xlarge \
  --min-count 1 \
  --max-count 1 2>&1 | grep -q "AccessDenied" && echo "✓ PASS: Expensive instance blocked" || echo "✗ FAIL: Expensive instance allowed"

# Test 3: Try to access without MFA (should fail)
echo "Test 3: Accessing without MFA..."
aws s3 ls 2>&1 | grep -q "AccessDenied" && echo "✓ PASS: Access without MFA blocked" || echo "✗ FAIL: Access without MFA allowed"
```

## 🚨 Troubleshooting Common Issues

### Issue 1: SCP Blocking Legitimate Actions
```bash
# Check effective policies
aws organizations list-policies-for-target --target-id 123456789012 --filter SERVICE_CONTROL_POLICY

# Describe policy details
aws organizations describe-policy --policy-id p-examplePolicyId
```

### Issue 2: Policy Inheritance Conflicts
```bash
# List all policies affecting an account
aws organizations list-parents --child-id 123456789012
aws organizations list-policies-for-target --target-id ou-exampleOuId --filter SERVICE_CONTROL_POLICY
```

### Issue 3: Emergency Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EmergencyBreakGlass",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/EmergencyAccessRole"
      },
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/Emergency": "true"
        }
      }
    }
  ]
}
```

## 📈 SCP Governance Framework

### Policy Lifecycle Management
```bash
# Version control for policies
git init scp-policies
git add *.json
git commit -m "Initial SCP policies"
git tag v1.0

# Automated policy deployment
#!/bin/bash
# deploy-scp.sh
for policy in policies/*.json; do
  policy_name=$(basename "$policy" .json)
  aws organizations create-policy \
    --name "$policy_name" \
    --type SERVICE_CONTROL_POLICY \
    --content "file://$policy"
done
```

### Compliance Reporting
```python
# scp-compliance-report.py
import boto3
import json

def generate_scp_report():
    org_client = boto3.client('organizations')
    
    # Get all accounts
    accounts = org_client.list_accounts()['Accounts']
    
    report = []
    for account in accounts:
        account_id = account['Id']
        
        # Get policies for account
        policies = org_client.list_policies_for_target(
            TargetId=account_id,
            Filter='SERVICE_CONTROL_POLICY'
        )['Policies']
        
        report.append({
            'AccountId': account_id,
            'AccountName': account['Name'],
            'PolicyCount': len(policies),
            'Policies': [p['Name'] for p in policies]
        })
    
    return report

if __name__ == "__main__":
    report = generate_scp_report()
    print(json.dumps(report, indent=2))
```

## 📋 Implementation Checklist

### Pre-Implementation
- [ ] Document current organization structure
- [ ] Identify compliance requirements
- [ ] Map business requirements to SCP controls
- [ ] Create test environment
- [ ] Define emergency access procedures

### Implementation Phase
- [ ] Create organization and OUs
- [ ] Develop and test SCP policies
- [ ] Implement policies in stages (least restrictive first)
- [ ] Set up monitoring and alerting
- [ ] Train teams on new restrictions

### Post-Implementation
- [ ] Monitor for policy violations
- [ ] Regular policy reviews and updates
- [ ] Compliance reporting
- [ ] Incident response procedures
- [ ] Documentation maintenance

## 🎯 Best Practices Summary

1. **Start Small**: Begin with least restrictive policies
2. **Test Thoroughly**: Use policy simulator and test accounts
3. **Monitor Continuously**: Set up CloudTrail and CloudWatch
4. **Document Everything**: Maintain policy documentation
5. **Regular Reviews**: Quarterly policy assessments
6. **Emergency Access**: Always have break-glass procedures
7. **Version Control**: Track all policy changes
8. **Stakeholder Buy-in**: Ensure business alignment

## 🔗 Additional Resources

- [AWS Organizations User Guide](https://docs.aws.amazon.com/organizations/latest/userguide/)
- [SCP Policy Examples](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_examples.html)
- [AWS Config for Compliance](https://aws.amazon.com/config/)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)

---

**Note**: Always test SCP policies in non-production environments first. SCPs are preventive controls and can block legitimate business operations if not properly designed and tested.