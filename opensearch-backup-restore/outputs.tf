output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = module.opensearch.domain_endpoint
}

output "opensearch_arn" {
  description = "OpenSearch domain ARN"
  value       = module.opensearch.domain_arn
}

output "s3_bucket_name" {
  description = "S3 bucket for snapshots"
  value       = var.s3_bucket_name
}

output "restore_lambda_name" {
  description = "Restore Lambda function name"
  value       = module.restore.restore_lambda_name
}