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

variable "environment" {
  description = "Environment name"
  type        = string
}