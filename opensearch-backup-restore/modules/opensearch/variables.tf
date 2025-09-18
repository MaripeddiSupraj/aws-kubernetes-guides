variable "domain_name" {
  description = "OpenSearch domain name"
  type        = string
}

variable "instance_type" {
  description = "OpenSearch instance type"
  type        = string
}

variable "instance_count" {
  description = "Number of data nodes"
  type        = number
}

variable "volume_size" {
  description = "EBS volume size in GB"
  type        = number
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs"
  type        = list(string)
}

variable "allowed_ips" {
  description = "Allowed IP addresses"
  type        = list(string)
}

variable "environment" {
  description = "Environment name"
  type        = string
}