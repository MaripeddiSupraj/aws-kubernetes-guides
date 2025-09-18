variable "opensearch_domain_arn" {
  description = "OpenSearch domain ARN"
  type        = string
}

variable "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket for snapshots"
  type        = string
}

variable "backup_schedule" {
  description = "Backup schedule (cron expression)"
  type        = string
}

variable "retention_days" {
  description = "Snapshot retention in days"
  type        = number
}

variable "environment" {
  description = "Environment name"
  type        = string
}