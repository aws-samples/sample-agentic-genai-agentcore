# ============================================================================
# Security Groups
# ============================================================================

# SG for VPC interface endpoints — allows HTTPS from inside the VPC
resource "aws_security_group" "vpc_endpoints" {
  name        = "${local.name_prefix}-vpc-endpoints"
  description = "Allow HTTPS from VPC for AgentCore VPC endpoints"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from VPC CIDR"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }

  egress {
    description = "All egress"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-vpc-endpoints" }
}

# SG attached to AgentCore runtime ENIs — default egress allows outbound HTTPS
resource "aws_security_group" "runtime" {
  name        = "${local.name_prefix}-runtime"
  description = "AgentCore runtime egress to VPC endpoints"
  vpc_id      = var.vpc_id

  egress {
    description = "All egress (reaches VPC endpoints)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-runtime" }
}

# ============================================================================
# VPC Endpoints — 8 Interface + 1 Gateway
# ============================================================================

# S3 Gateway endpoint (free)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${local.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [data.aws_route_table.main.id]

  tags = { Name = "${local.name_prefix}-s3" }
}

# Interface endpoints — one resource per service
resource "aws_vpc_endpoint" "interface" {
  for_each = local.interface_endpoints

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${local.region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = local.runtime_subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = { Name = "${local.name_prefix}-${each.key}" }
}

