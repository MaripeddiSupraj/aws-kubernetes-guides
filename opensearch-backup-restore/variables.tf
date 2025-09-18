variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "OpenSearch domain name"
  type        = string
  default     = "my-opensearch-domain"
}

variable "instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.small.search"
}

variable "instance_count" {
  description = "Number of data nodes"
  type        = number
  default     = 1
}

variable "volume_size" {
  description = "EBS volume size in GB"
  type        = number
  default     = 20
}

variable "vpc_id" {
  description = "VPC ID for OpenSearch domain"
  type        = string
  default     = "vpc-xxxxxxxxx"
}

variable "subnet_ids" {
  description = "Subnet IDs for OpenSearch domain"
  type        = list(string)
  default     = ["subnet-xxxxxxxxx"]
}

variable "allowed_ips" {
  description = "IP addresses allowed to access OpenSearch"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "s3_bucket_name" {
  description = "S3 bucket for snapshots"
  type        = string
  default     = "my-opensearch-snapshots-bucket"
}

variable "backup_schedule" {
  description = "Backup schedule (cron expression)"
  type        = string
  default     = "cron(0 2 ? * SUN *)"  # Every Sunday at 2 AM
}

variable "retention_days" {
  description = "Snapshot retention in days"
  type        = number
  default     = 30
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}