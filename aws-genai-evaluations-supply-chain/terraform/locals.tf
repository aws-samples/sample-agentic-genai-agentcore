data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_vpc" "selected" { id = var.vpc_id }

# Find the subnet in each selected AZ within the existing VPC
data "aws_subnet" "runtime_subnets" {
  for_each = length(var.runtime_subnet_ids) > 0 ? toset([]) : toset(var.runtime_subnet_azs)
  vpc_id            = var.vpc_id
  availability_zone = each.value
}

data "aws_subnet" "explicit_subnets" {
  for_each = length(var.runtime_subnet_ids) > 0 ? toset(var.runtime_subnet_ids) : toset([])
  id       = each.value
}

# Main route table (used for the S3 gateway endpoint)
data "aws_route_table" "main" {
  vpc_id = var.vpc_id
  filter {
    name   = "association.main"
    values = ["true"]
  }
}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.id

  # Resource name prefix
  name_prefix = "${var.stack_name}-${var.environment}"

  # Subnet IDs for runtimes
  runtime_subnet_ids = length(var.runtime_subnet_ids) > 0 ? var.runtime_subnet_ids : [for s in data.aws_subnet.runtime_subnets : s.id]

  # Interface VPC endpoints needed
  interface_endpoints = {
    bedrock_runtime   = "bedrock-runtime"
    bedrock_agentcore = "bedrock-agentcore"
    logs              = "logs"
    xray              = "xray"
    sts               = "sts"
    ecr_api           = "ecr.api"
    ecr_dkr           = "ecr.dkr"
    execute_api       = "execute-api"
  }

  # Tags applied only in specific places
  common_tags = {
    Stack = var.stack_name
  }
}
