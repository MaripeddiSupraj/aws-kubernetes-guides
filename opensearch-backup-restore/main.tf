terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "YOUR_TERRAFORM_STATE_BUCKET"
    key    = "opensearch/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

module "opensearch" {
  source = "./modules/opensearch"
  
  domain_name     = var.domain_name
  instance_type   = var.instance_type
  instance_count  = var.instance_count
  volume_size     = var.volume_size
  vpc_id          = var.vpc_id
  subnet_ids      = var.subnet_ids
  allowed_ips     = var.allowed_ips
  environment     = var.environment
}

module "backup" {
  source = "./modules/backup"
  
  opensearch_domain_arn = module.opensearch.domain_arn
  opensearch_endpoint   = module.opensearch.domain_endpoint
  s3_bucket_name       = var.s3_bucket_name
  backup_schedule      = var.backup_schedule
  retention_days       = var.retention_days
  environment          = var.environment
}

module "restore" {
  source = "./modules/restore"
  
  opensearch_domain_arn = module.opensearch.domain_arn
  opensearch_endpoint   = module.opensearch.domain_endpoint
  s3_bucket_name       = var.s3_bucket_name
  environment          = var.environment
}