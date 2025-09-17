# AWS WAF (Web Application Firewall) - Learning Guide

## What is AWS WAF?

AWS WAF is a web application firewall that helps protect web applications from common web exploits and attacks that could affect application availability, compromise security, or consume excessive resources.

## Key Concepts

### 1. Web ACLs (Access Control Lists)
- Container for rules that define which traffic to allow/block
- Associated with CloudFront, Application Load Balancer, or API Gateway
- Default action: ALLOW or BLOCK

### 2. Rules
- Define conditions to inspect web requests
- Can ALLOW, BLOCK, or COUNT matching requests
- Processed in priority order (lower numbers first)

### 3. Rule Groups
- Reusable collections of rules
- Managed rule groups (AWS/third-party) or custom rule groups
- Help organize and manage rules efficiently

## Core Components

### Rule Types

#### 1. Rate-based Rules
```json
{
  "Name": "RateLimitRule",
  "Priority": 1,
  "Statement": {
    "RateBasedStatement": {
      "Limit": 2000,
      "AggregateKeyType": "IP"
    }
  },
  "Action": {
    "Block": {}
  }
}
```

#### 2. IP Set Rules
```json
{
  "Name": "BlockMaliciousIPs",
  "Priority": 2,
  "Statement": {
    "IPSetReferenceStatement": {
      "ARN": "arn:aws:wafv2:us-east-1:123456789012:global/ipset/malicious-ips/12345"
    }
  },
  "Action": {
    "Block": {}
  }
}
```

#### 3. Geographic Rules
```json
{
  "Name": "BlockCountries",
  "Priority": 3,
  "Statement": {
    "GeoMatchStatement": {
      "CountryCodes": ["CN", "RU", "KP"]
    }
  },
  "Action": {
    "Block": {}
  }
}
```

#### 4. String Match Rules
```json
{
  "Name": "BlockSQLInjection",
  "Priority": 4,
  "Statement": {
    "ByteMatchStatement": {
      "SearchString": "union select",
      "FieldToMatch": {
        "Body": {}
      },
      "TextTransformations": [
        {
          "Priority": 0,
          "Type": "LOWERCASE"
        }
      ],
      "PositionalConstraint": "CONTAINS"
    }
  },
  "Action": {
    "Block": {}
  }
}
```

## AWS Managed Rule Groups

### Core Rule Set (CRS)
```json
{
  "Name": "AWS-AWSManagedRulesCommonRuleSet",
  "Priority": 10,
  "Statement": {
    "ManagedRuleGroupStatement": {
      "VendorName": "AWS",
      "Name": "AWSManagedRulesCommonRuleSet"
    }
  },
  "OverrideAction": {
    "None": {}
  }
}
```

### Popular Managed Rule Groups
- **AWSManagedRulesCommonRuleSet**: OWASP Top 10 protection
- **AWSManagedRulesKnownBadInputsRuleSet**: Known malicious inputs
- **AWSManagedRulesSQLiRuleSet**: SQL injection protection
- **AWSManagedRulesLinuxRuleSet**: Linux-specific attacks
- **AWSManagedRulesWindowsRuleSet**: Windows-specific attacks

## Practical Examples

### Example 1: Basic Web Application Protection

```json
{
  "Name": "WebAppProtection",
  "Scope": "CLOUDFRONT",
  "DefaultAction": {
    "Allow": {}
  },
  "Rules": [
    {
      "Name": "RateLimiting",
      "Priority": 1,
      "Statement": {
        "RateBasedStatement": {
          "Limit": 5000,
          "AggregateKeyType": "IP"
        }
      },
      "Action": {
        "Block": {}
      }
    },
    {
      "Name": "CoreRuleSet",
      "Priority": 2,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "OverrideAction": {
        "None": {}
      }
    }
  ]
}
```

### Example 2: API Protection with Custom Rules

```json
{
  "Name": "APIProtection",
  "Scope": "REGIONAL",
  "DefaultAction": {
    "Allow": {}
  },
  "Rules": [
    {
      "Name": "AllowOnlyPOSTtoAPI",
      "Priority": 1,
      "Statement": {
        "AndStatement": {
          "Statements": [
            {
              "ByteMatchStatement": {
                "SearchString": "/api/",
                "FieldToMatch": {
                  "UriPath": {}
                },
                "TextTransformations": [
                  {
                    "Priority": 0,
                    "Type": "LOWERCASE"
                  }
                ],
                "PositionalConstraint": "STARTS_WITH"
              }
            },
            {
              "NotStatement": {
                "Statement": {
                  "ByteMatchStatement": {
                    "SearchString": "POST",
                    "FieldToMatch": {
                      "Method": {}
                    },
                    "TextTransformations": [
                      {
                        "Priority": 0,
                        "Type": "NONE"
                      }
                    ],
                    "PositionalConstraint": "EXACTLY"
                  }
                }
              }
            }
          ]
        }
      },
      "Action": {
        "Block": {}
      }
    }
  ]
}
```

## CloudFormation Template Example

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  WebACL:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: MyWebACL
      Scope: CLOUDFRONT
      DefaultAction:
        Allow: {}
      Rules:
        - Name: RateLimitRule
          Priority: 1
          Statement:
            RateBasedStatement:
              Limit: 2000
              AggregateKeyType: IP
          Action:
            Block: {}
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: RateLimitRule
        - Name: ManagedRuleGroup
          Priority: 2
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesCommonRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: ManagedRuleGroup

  IPSet:
    Type: AWS::WAFv2::IPSet
    Properties:
      Name: MaliciousIPs
      Scope: CLOUDFRONT
      IPAddressVersion: IPV4
      Addresses:
        - 192.0.2.44/32
        - 198.51.100.0/24
```

## CLI Commands

### Create Web ACL
```bash
aws wafv2 create-web-acl \
  --name "MyWebACL" \
  --scope CLOUDFRONT \
  --default-action Allow={} \
  --rules file://rules.json
```

### Associate with CloudFront
```bash
aws wafv2 associate-web-acl \
  --web-acl-arn arn:aws:wafv2:us-east-1:123456789012:global/webacl/MyWebACL/12345 \
  --resource-arn arn:aws:cloudfront::123456789012:distribution/E1234567890123
```

### Get sampled requests
```bash
aws wafv2 get-sampled-requests \
  --web-acl-arn arn:aws:wafv2:us-east-1:123456789012:global/webacl/MyWebACL/12345 \
  --rule-metric-name RateLimitRule \
  --scope CLOUDFRONT \
  --time-window StartTime=2023-01-01T00:00:00Z,EndTime=2023-01-01T01:00:00Z \
  --max-items 100
```

## Monitoring and Logging

### CloudWatch Metrics
- `AllowedRequests`: Requests allowed by rules
- `BlockedRequests`: Requests blocked by rules
- `CountedRequests`: Requests counted by rules
- `SampledRequests`: Sample of requests for analysis

### Web ACL Logging
```json
{
  "ResourceArn": "arn:aws:wafv2:us-east-1:123456789012:global/webacl/MyWebACL/12345",
  "LogDestinationConfigs": [
    "arn:aws:logs:us-east-1:123456789012:log-group:aws-waf-logs-cloudfront"
  ]
}
```

## Best Practices

### 1. Start with COUNT Mode
```json
{
  "Action": {
    "Count": {}
  }
}
```
- Test rules before blocking traffic
- Analyze logs to reduce false positives

### 2. Use Appropriate Rate Limits
- **Web browsing**: 2,000-10,000 requests per 5 minutes
- **API endpoints**: 100-1,000 requests per 5 minutes
- **Login pages**: 10-50 requests per 5 minutes

### 3. Layer Security Controls
```
Internet → CloudFront → WAF → ALB → Security Groups → Application
```

### 4. Regular Rule Updates
- Monitor AWS managed rule group updates
- Review and update custom rules based on attack patterns
- Use AWS Security Hub for centralized security findings

## Common Use Cases

### 1. DDoS Protection
```json
{
  "Name": "DDoSProtection",
  "Statement": {
    "RateBasedStatement": {
      "Limit": 2000,
      "AggregateKeyType": "IP"
    }
  }
}
```

### 2. Geographic Blocking
```json
{
  "Name": "GeoBlock",
  "Statement": {
    "GeoMatchStatement": {
      "CountryCodes": ["CN", "RU"]
    }
  }
}
```

### 3. Bot Protection
```json
{
  "Name": "BotProtection",
  "Statement": {
    "ManagedRuleGroupStatement": {
      "VendorName": "AWS",
      "Name": "AWSManagedRulesBotControlRuleSet"
    }
  }
}
```

## Pricing Considerations

- **Web ACL**: $1.00 per month
- **Rules**: $0.60 per rule per month
- **Requests**: $0.60 per million requests
- **Rule group usage**: $1.00 per month per rule group
- **Bot Control**: Additional $1.00 per million requests

## Integration Points

### CloudFront Distribution
```json
{
  "WebACLId": "arn:aws:wafv2:us-east-1:123456789012:global/webacl/MyWebACL/12345"
}
```

### Application Load Balancer
```bash
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/1234567890123456 \
  --attributes Key=waf.fail_open.enabled,Value=false
```

### API Gateway
```json
{
  "webAclArn": "arn:aws:wafv2:us-east-1:123456789012:regional/webacl/MyWebACL/12345"
}
```

## Troubleshooting Tips

1. **Check rule priority order** - Lower numbers execute first
2. **Review CloudWatch metrics** - Monitor blocked vs allowed requests
3. **Analyze sampled requests** - Understand what's being blocked
4. **Use COUNT mode first** - Test before implementing BLOCK actions
5. **Check text transformations** - Ensure proper data normalization