output "restore_lambda_arn" {
  description = "Restore Lambda function ARN"
  value       = aws_lambda_function.restore.arn
}

output "restore_lambda_name" {
  description = "Restore Lambda function name"
  value       = aws_lambda_function.restore.function_name
}