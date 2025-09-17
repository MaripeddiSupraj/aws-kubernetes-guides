# GitHub Actions AWS OIDC Integration Guide

A comprehensive guide to securely connect GitHub Actions with AWS using OpenID Connect (OIDC) instead of long-lived access keys.

## 🎯 Benefits of OIDC over Access Keys

- **No long-lived credentials** stored in GitHub secrets
- **Automatic token rotation** and expiration
- **Fine-grained permissions** based on repository, branch, and environment
- **Enhanced security** with temporary credentials
- **Audit trail** with CloudTrail integration

## 🏗️ Architecture Overview

```
GitHub Actions → OIDC Token → AWS STS → Temporary Credentials → AWS Services
```

## 📋 Prerequisites

- AWS CLI configured with admin permissions
- GitHub repository with Actions enabled
- Basic understanding of IAM roles and policies

## 🚀 Step 1: Create OIDC Identity Provider in AWS

### Using AWS CLI

```bash
# Create the OIDC identity provider
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
    --tags Key=Purpose,Value=GitHubActions Key=Environment,Value=Production
```

### Using CloudFormation

```yaml
# oidc-provider.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'GitHub Actions OIDC Provider'

Resources:
  GitHubOIDCProvider:
    Type: AWS::IAM::OIDCIdentityProvider
    Properties:
      Url: https://token.actions.githubusercontent.com
      ClientIdList:
        - sts.amazonaws.com
      ThumbprintList:
        - 6938fd4d98bab03faadb97b34396831e3780aea1
      Tags:
        - Key: Purpose
          Value: GitHubActions
        - Key: Environment
          Value: Production

Outputs:
  OIDCProviderArn:
    Description: ARN of the OIDC Provider
    Value: !Ref GitHubOIDCProvider
    Export:
      Name: GitHubOIDCProviderArn
```

## 🔐 Step 2: Create IAM Role with Trust Policy

### Trust Policy for Specific Repository

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT-ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR-ORG/YOUR-REPO:*"
        }
      }
    }
  ]
}
```

### Enhanced Trust Policy with Branch/Environment Restrictions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT-ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:YOUR-ORG/YOUR-REPO:ref:refs/heads/main",
            "repo:YOUR-ORG/YOUR-REPO:ref:refs/heads/develop",
            "repo:YOUR-ORG/YOUR-REPO:environment:production",
            "repo:YOUR-ORG/YOUR-REPO:environment:staging"
          ]
        }
      }
    }
  ]
}
```

### Complete CloudFormation Template

```yaml
# github-actions-role.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'GitHub Actions IAM Role with OIDC'

Parameters:
  GitHubOrg:
    Type: String
    Description: GitHub organization name
    Default: your-org
  
  GitHubRepo:
    Type: String
    Description: GitHub repository name
    Default: your-repo
  
  Environment:
    Type: String
    Description: Environment name
    Default: production
    AllowedValues: [production, staging, development]

Resources:
  GitHubActionsRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub 'GitHubActions-${GitHubRepo}-${Environment}'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Federated: !Sub 'arn:aws:iam::${AWS::AccountId}:oidc-provider/token.actions.githubusercontent.com'
            Action: sts:AssumeRoleWithWebIdentity
            Condition:
              StringEquals:
                'token.actions.githubusercontent.com:aud': sts.amazonaws.com
              StringLike:
                'token.actions.githubusercontent.com:sub': !Sub 'repo:${GitHubOrg}/${GitHubRepo}:*'
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/ReadOnlyAccess
      Policies:
        - PolicyName: GitHubActionsPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                  - s3:DeleteObject
                Resource: !Sub 'arn:aws:s3:::${Environment}-deployment-bucket/*'
              - Effect: Allow
                Action:
                  - ecr:GetAuthorizationToken
                  - ecr:BatchCheckLayerAvailability
                  - ecr:GetDownloadUrlForLayer
                  - ecr:BatchGetImage
                  - ecr:InitiateLayerUpload
                  - ecr:UploadLayerPart
                  - ecr:CompleteLayerUpload
                  - ecr:PutImage
                Resource: '*'
              - Effect: Allow
                Action:
                  - ecs:UpdateService
                  - ecs:DescribeServices
                  - ecs:DescribeTaskDefinition
                  - ecs:RegisterTaskDefinition
                Resource: '*'
      Tags:
        - Key: Purpose
          Value: GitHubActions
        - Key: Environment
          Value: !Ref Environment
        - Key: Repository
          Value: !Sub '${GitHubOrg}/${GitHubRepo}'

Outputs:
  RoleArn:
    Description: ARN of the GitHub Actions IAM Role
    Value: !GetAtt GitHubActionsRole.Arn
    Export:
      Name: !Sub 'GitHubActionsRole-${Environment}-Arn'
```

## 🔧 Step 3: GitHub Actions Workflow Examples

### Basic Workflow with OIDC

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write   # Required for OIDC
  contents: read    # Required for actions/checkout

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Optional: use GitHub environments
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActions-your-repo-production
          role-session-name: GitHubActions-${{ github.run_id }}
          aws-region: us-east-1

      - name: Verify AWS identity
        run: |
          aws sts get-caller-identity
          echo "AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)" >> $GITHUB_ENV

      - name: Deploy application
        run: |
          echo "Deploying to AWS Account: $AWS_ACCOUNT_ID"
          # Your deployment commands here
```

### Advanced Multi-Environment Workflow

```yaml
# .github/workflows/multi-env-deploy.yml
name: Multi-Environment Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  determine-environment:
    runs-on: ubuntu-latest
    outputs:
      environment: ${{ steps.env.outputs.environment }}
      role-arn: ${{ steps.env.outputs.role-arn }}
    steps:
      - id: env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "environment=production" >> $GITHUB_OUTPUT
            echo "role-arn=arn:aws:iam::123456789012:role/GitHubActions-your-repo-production" >> $GITHUB_OUTPUT
          elif [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
            echo "environment=staging" >> $GITHUB_OUTPUT
            echo "role-arn=arn:aws:iam::123456789012:role/GitHubActions-your-repo-staging" >> $GITHUB_OUTPUT
          else
            echo "environment=development" >> $GITHUB_OUTPUT
            echo "role-arn=arn:aws:iam::123456789012:role/GitHubActions-your-repo-development" >> $GITHUB_OUTPUT
          fi

  deploy:
    needs: determine-environment
    runs-on: ubuntu-latest
    environment: ${{ needs.determine-environment.outputs.environment }}
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ needs.determine-environment.outputs.role-arn }}
          role-session-name: GitHubActions-${{ github.run_id }}-${{ needs.determine-environment.outputs.environment }}
          aws-region: us-east-1
          role-duration-seconds: 3600  # 1 hour

      - name: Build and push Docker image
        run: |
          # Login to ECR
          aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
          
          # Build and tag image
          docker build -t my-app:${{ github.sha }} .
          docker tag my-app:${{ github.sha }} 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:${{ github.sha }}
          docker tag my-app:${{ github.sha }} 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest
          
          # Push image
          docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:${{ github.sha }}
          docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest

      - name: Deploy to ECS
        run: |
          # Update ECS service
          aws ecs update-service \
            --cluster my-cluster-${{ needs.determine-environment.outputs.environment }} \
            --service my-service \
            --force-new-deployment
```

### Terraform Deployment Workflow

```yaml
# .github/workflows/terraform.yml
name: Terraform Deploy

on:
  push:
    branches: [main]
    paths: ['terraform/**']
  pull_request:
    branches: [main]
    paths: ['terraform/**']

permissions:
  id-token: write
  contents: read
  pull-requests: write  # For PR comments

jobs:
  terraform:
    runs-on: ubuntu-latest
    environment: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
    
    defaults:
      run:
        working-directory: terraform

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.6.0

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ github.ref == 'refs/heads/main' && 
            'arn:aws:iam::123456789012:role/GitHubActions-terraform-production' || 
            'arn:aws:iam::123456789012:role/GitHubActions-terraform-staging' }}
          role-session-name: Terraform-${{ github.run_id }}
          aws-region: us-east-1

      - name: Terraform Init
        run: terraform init

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        id: plan
        run: |
          terraform plan -no-color -out=tfplan
          terraform show -no-color tfplan > plan.txt
        continue-on-error: true

      - name: Comment PR with Plan
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('terraform/plan.txt', 'utf8');
            const maxGitHubBodyCharacters = 65536;
            
            function chunkSubstr(str, size) {
              const numChunks = Math.ceil(str.length / size)
              const chunks = new Array(numChunks)
              for (let i = 0, o = 0; i < numChunks; ++i, o += size) {
                chunks[i] = str.substr(o, size)
              }
              return chunks
            }
            
            const planChunks = chunkSubstr(plan, maxGitHubBodyCharacters);
            
            for (let i = 0; i < planChunks.length; i++) {
              const output = `### Terraform Plan Part ${i + 1}
              
              \`\`\`
              ${planChunks[i]}
              \`\`\`
              
              *Pusher: @${{ github.actor }}, Action: \`${{ github.event_name }}\`, Working Directory: \`terraform\`, Workflow: \`${{ github.workflow }}\`*`;
              
              await github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: output
              });
            }

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: terraform apply -auto-approve tfplan
```

## 🔒 Security Best Practices

### 1. Principle of Least Privilege

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::specific-bucket/specific-path/*"
    },
    {
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["us-east-1", "us-west-2"]
        }
      }
    }
  ]
}
```

### 2. Time-based Access Control

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT-ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR-ORG/YOUR-REPO:*"
        },
        "DateGreaterThan": {
          "aws:CurrentTime": "2024-01-01T00:00:00Z"
        },
        "DateLessThan": {
          "aws:CurrentTime": "2024-12-31T23:59:59Z"
        }
      }
    }
  ]
}
```

### 3. IP Address Restrictions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT-ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR-ORG/YOUR-REPO:*"
        },
        "IpAddress": {
          "aws:SourceIp": [
            "140.82.112.0/20",
            "185.199.108.0/22",
            "192.30.252.0/22"
          ]
        }
      }
    }
  ]
}
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. "No OpenIDConnect provider found"
```bash
# Verify OIDC provider exists
aws iam list-open-id-connect-providers

# Check thumbprint is correct
aws iam get-open-id-connect-provider \
    --open-id-connect-provider-arn arn:aws:iam::ACCOUNT-ID:oidc-provider/token.actions.githubusercontent.com
```

#### 2. "AssumeRoleWithWebIdentity is not authorized"
- Check trust policy conditions match exactly
- Verify repository name and organization
- Ensure `permissions: id-token: write` is set

#### 3. "Token audience validation failed"
- Ensure `aud` condition is set to `sts.amazonaws.com`
- Check client ID list includes `sts.amazonaws.com`

### Debug Workflow

```yaml
- name: Debug OIDC Token
  run: |
    echo "GitHub Token Claims:"
    echo "Repository: ${{ github.repository }}"
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
    echo "Actor: ${{ github.actor }}"
    echo "Event: ${{ github.event_name }}"
    echo "Run ID: ${{ github.run_id }}"
    echo "Environment: ${{ github.environment }}"
```

## 📊 Monitoring and Auditing

### CloudTrail Events to Monitor

```json
{
  "eventName": "AssumeRoleWithWebIdentity",
  "sourceIPAddress": "GitHub Actions IP",
  "userIdentity": {
    "type": "WebIdentityUser",
    "principalId": "arn:aws:sts::ACCOUNT-ID:assumed-role/GitHubActions-Role/GitHubActions-SESSION"
  }
}
```

### CloudWatch Metrics

```yaml
# Custom metric filter for failed assumptions
aws logs put-metric-filter \
    --log-group-name CloudTrail/GitHubActions \
    --filter-name FailedAssumeRole \
    --filter-pattern '{ ($.errorCode = "*UnauthorizedOperation") || ($.errorCode = "AccessDenied*") }' \
    --metric-transformations \
        metricName=GitHubActionsFailedAssumeRole,metricNamespace=Security,metricValue=1
```

## 🎯 Production Checklist

- [ ] OIDC provider created with correct thumbprint
- [ ] IAM roles follow least privilege principle
- [ ] Trust policies restrict to specific repositories/branches
- [ ] Session duration appropriately configured
- [ ] CloudTrail logging enabled
- [ ] Monitoring and alerting configured
- [ ] Regular access reviews scheduled
- [ ] Documentation updated with role ARNs
- [ ] Emergency access procedures documented
- [ ] Backup authentication method available

## 📚 Additional Resources

- [GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [AWS IAM OIDC Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

---

**Security Note**: Always test OIDC configurations in a non-production environment first. Regularly review and rotate IAM policies to maintain security posture.