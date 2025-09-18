resource "aws_iam_role" "restore_lambda" {
  name = "${var.environment}-opensearch-restore-lambda"

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

resource "aws_iam_role_policy" "restore_lambda" {
  name = "${var.environment}-opensearch-restore-policy"
  role = aws_iam_role.restore_lambda.id

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
          "es:ESHttpPut",
          "es:ESHttpGet"
        ]
        Resource = "${var.opensearch_domain_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_lambda_function" "restore" {
  filename         = data.archive_file.restore_lambda.output_path
  function_name    = "${var.environment}-opensearch-restore"
  role            = aws_iam_role.restore_lambda.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 600

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

data "archive_file" "restore_lambda" {
  type        = "zip"
  output_path = "${path.module}/restore_lambda.zip"
  source {
    content = file("${path.module}/restore_lambda.py")
    filename = "index.py"
  }
}