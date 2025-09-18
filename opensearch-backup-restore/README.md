# OpenSearch Backup & Restore with Terraform

Complete Terraform solution for OpenSearch domain with automated weekly backups to S3 and Lambda-based restore functionality.

## Architecture

- **OpenSearch Domain**: VPC-based with encryption and security groups
- **S3 Bucket**: Snapshot storage with lifecycle policies
- **Backup Lambda**: Weekly automated snapshots via EventBridge
- **Restore Lambda**: On-demand restore from latest snapshot

## Quick Start

1. **Configure Variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Update Backend Configuration**:
   ```bash
   # Edit main.tf backend block with your S3 bucket
   ```

3. **Deploy Infrastructure**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Trigger Manual Restore**:
   ```bash
   aws lambda invoke --function-name dev-opensearch-restore response.json
   ```

## Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `vpc_id` | VPC ID for OpenSearch | `vpc-12345678` |
| `subnet_ids` | Subnet IDs (list) | `["subnet-12345678"]` |
| `s3_bucket_name` | Unique S3 bucket name | `my-company-opensearch-snapshots` |
| `allowed_ips` | IP ranges for access | `["10.0.0.0/8"]` |

## Features

- ✅ Weekly automated backups (configurable schedule)
- ✅ S3 lifecycle management (30-day retention)
- ✅ VPC security with IP restrictions
- ✅ Encryption at rest and in transit
- ✅ Lambda-based restore from latest snapshot
- ✅ CloudWatch logging and monitoring

## Manual Operations

**Create Backup**:
```bash
aws lambda invoke --function-name dev-opensearch-backup response.json
```

**Restore Latest**:
```bash
aws lambda invoke --function-name dev-opensearch-restore response.json
```

**List Snapshots**:
```bash
curl -X GET "https://YOUR_OPENSEARCH_ENDPOINT/_snapshot/s3-snapshot-repo/_all"
```

## Cost Optimization

- Use `t3.small.search` for development
- Adjust `retention_days` based on compliance needs
- Consider S3 Intelligent Tiering for long-term storage

## Security Notes

- OpenSearch access restricted by IP ranges
- Lambda functions use least-privilege IAM policies
- All data encrypted at rest and in transit
- VPC-only deployment (no internet access)