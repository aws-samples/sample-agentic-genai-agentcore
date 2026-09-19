# ============================================================================
# CodeBuild Projects — one per runtime
# ============================================================================

locals {
  codebuild_env_vars_base = [
    { name = "AWS_DEFAULT_REGION", value = local.region },
    { name = "AWS_ACCOUNT_ID", value = local.account_id },
  ]
}

resource "aws_codebuild_project" "mcp" {
  name          = "${local.name_prefix}-mcp-build"
  description   = "Build MCP tools server Docker image"
  service_role  = aws_iam_role.image_build.arn
  build_timeout = 60

  artifacts { type = "NO_ARTIFACTS" }

  environment {
    compute_type                = "BUILD_GENERAL1_LARGE"
    image                       = "aws/codebuild/amazonlinux2-aarch64-standard:3.0"
    type                        = "ARM_CONTAINER"
    privileged_mode             = true
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = local.region
    }
    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = local.account_id
    }
    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = aws_ecr_repository.mcp.name
    }
    environment_variable {
      name  = "IMAGE_TAG"
      value = var.image_tag
    }
  }

  source {
    type      = "S3"
    location  = "${aws_s3_bucket.agent_source.id}/${aws_s3_object.mcp_source.key}"
    buildspec = file("${path.module}/buildspec.yml")
  }

  logs_config {
    cloudwatch_logs { group_name = "/aws/codebuild/${local.name_prefix}-mcp-build" }
  }

  tags = { Name = "${local.name_prefix}-mcp-build" }
}

resource "aws_codebuild_project" "supply_chain" {
  name          = "${local.name_prefix}-supply-chain-build"
  description   = "Build Supply Chain agent Docker image"
  service_role  = aws_iam_role.image_build.arn
  build_timeout = 60

  artifacts { type = "NO_ARTIFACTS" }

  environment {
    compute_type                = "BUILD_GENERAL1_LARGE"
    image                       = "aws/codebuild/amazonlinux2-aarch64-standard:3.0"
    type                        = "ARM_CONTAINER"
    privileged_mode             = true
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = local.region
    }
    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = local.account_id
    }
    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = aws_ecr_repository.supply_chain.name
    }
    environment_variable {
      name  = "IMAGE_TAG"
      value = var.image_tag
    }
  }

  source {
    type      = "S3"
    location  = "${aws_s3_bucket.agent_source.id}/${aws_s3_object.supply_chain_source.key}"
    buildspec = file("${path.module}/buildspec.yml")
  }

  logs_config {
    cloudwatch_logs { group_name = "/aws/codebuild/${local.name_prefix}-supply-chain-build" }
  }

  tags = { Name = "${local.name_prefix}-supply-chain-build" }
}

# ============================================================================
# Trigger Builds via local-exec
# ============================================================================

resource "null_resource" "build_mcp" {
  triggers = {
    source_md5    = data.archive_file.mcp_source.output_md5
    image_tag     = var.image_tag
    ecr_repo      = aws_ecr_repository.mcp.id
    build_project = aws_codebuild_project.mcp.id
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = "${path.module}/scripts/build-image.sh '${aws_codebuild_project.mcp.name}' '${local.region}' '${aws_ecr_repository.mcp.name}' '${var.image_tag}' '${aws_ecr_repository.mcp.repository_url}'"
  }

  depends_on = [
    aws_codebuild_project.mcp,
    aws_iam_role_policy.image_build,
    aws_s3_object.mcp_source,
  ]
}

resource "null_resource" "build_supply_chain" {
  triggers = {
    source_md5    = data.archive_file.supply_chain_source.output_md5
    image_tag     = var.image_tag
    ecr_repo      = aws_ecr_repository.supply_chain.id
    build_project = aws_codebuild_project.supply_chain.id
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = "${path.module}/scripts/build-image.sh '${aws_codebuild_project.supply_chain.name}' '${local.region}' '${aws_ecr_repository.supply_chain.name}' '${var.image_tag}' '${aws_ecr_repository.supply_chain.repository_url}'"
  }

  depends_on = [
    aws_codebuild_project.supply_chain,
    aws_iam_role_policy.image_build,
    aws_s3_object.supply_chain_source,
  ]
}
