resource "aws_s3_bucket" "snapshots" {
  bucket = var.s3_bucket_name

  tags = {
    Name        = var.s3_bucket_name
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "snapshots" {
  bucket = aws_s3_bucket.snapshots.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "snapshots" {
  bucket = aws_s3_bucket.snapshots.id

  rule {
    id     = "snapshot_lifecycle"
    status = "Enabled"

    expiration {
      days = var.retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

resource "aws_iam_role" "backup_lambda" {
  name = "${var.environment}-opensearch-backup-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "backup_lambda" {
  name = "${var.environment}-opensearch-backup-policy"
  role = aws_iam_role.backup_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "es:ESHttpPost",
          "es:ESHttpPut"
        ]
        Resource = "${var.opensearch_domain_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.snapshots.arn,
          "${aws_s3_bucket.snapshots.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_lambda_function" "backup" {
  filename         = data.archive_file.backup_lambda.output_path
  function_name    = "${var.environment}-opensearch-backup"
  role            = aws_iam_role.backup_lambda.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = var.opensearch_endpoint
      S3_BUCKET          = var.s3_bucket_name
    }
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_rule" "backup_schedule" {
  name                = "${var.environment}-opensearch-backup-schedule"
  description         = "Trigger OpenSearch backup"
  schedule_expression = var.backup_schedule
}

resource "aws_cloudwatch_event_target" "backup_lambda" {
  rule      = aws_cloudwatch_event_rule.backup_schedule.name
  target_id = "BackupLambdaTarget"
  arn       = aws_lambda_function.backup.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backup.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.backup_schedule.arn
}

data "archive_file" "backup_lambda" {
  type        = "zip"
  output_path = "${path.module}/backup_lambda.zip"
  source {
    content = file("${path.module}/backup_lambda.py")
    filename = "index.py"
  }
}