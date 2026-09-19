# ============================================================================
# ECR Repositories — one per runtime
# ============================================================================

resource "aws_ecr_repository" "mcp" {
  name                 = "${local.name_prefix}-mcp-tools"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration { scan_on_push = true }

  tags = { Name = "${local.name_prefix}-mcp-tools" }
}

resource "aws_ecr_repository" "supply_chain" {
  name                 = "${local.name_prefix}-supply-chain-agent"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration { scan_on_push = true }

  tags = { Name = "${local.name_prefix}-supply-chain-agent" }
}

# Lifecycle: keep the last 5 images per repo
resource "aws_ecr_lifecycle_policy" "mcp" {
  repository = aws_ecr_repository.mcp.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 5 }
      action       = { type = "expire" }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "supply_chain" {
  repository = aws_ecr_repository.supply_chain.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 5 }
      action       = { type = "expire" }
    }]
  })
}
