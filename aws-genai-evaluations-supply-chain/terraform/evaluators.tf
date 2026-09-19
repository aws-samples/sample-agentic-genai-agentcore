# ============================================================================
# Supply Chain Evaluators — Docker Lambda + API Gateway
# ============================================================================

# --- ECR Repository for evaluators Lambda image ---

resource "aws_ecr_repository" "evaluators" {
  name                 = "${local.name_prefix}-evaluators"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = { Name = "${local.name_prefix}-evaluators" }
}

resource "aws_ecr_lifecycle_policy" "evaluators" {
  repository = aws_ecr_repository.evaluators.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# --- CodeBuild project to build evaluators Docker image ---

resource "aws_codebuild_project" "evaluators" {
  name          = "${local.name_prefix}-evaluators-build"
  description   = "Build evaluators Lambda Docker image"
  service_role  = aws_iam_role.image_build.arn
  build_timeout = 30

  artifacts { type = "NO_ARTIFACTS" }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type                        = "LINUX_CONTAINER"
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
      value = aws_ecr_repository.evaluators.name
    }
    environment_variable {
      name  = "IMAGE_TAG"
      value = var.image_tag
    }
  }

  source {
    type      = "S3"
    location  = "${aws_s3_bucket.agent_source.id}/${aws_s3_object.evaluators_source.key}"
    buildspec = file("${path.module}/buildspec.yml")
  }

  logs_config {
    cloudwatch_logs { group_name = "/aws/codebuild/${local.name_prefix}-evaluators-build" }
  }

  tags = { Name = "${local.name_prefix}-evaluators-build" }
}

# --- Source archive for evaluators ---

data "archive_file" "evaluators_source" {
  type        = "zip"
  source_dir  = "${path.module}/../evaluators/lambda"
  output_path = "${path.module}/.terraform/evaluators-lambda.zip"
}

resource "aws_s3_object" "evaluators_source" {
  bucket = aws_s3_bucket.agent_source.id
  key    = "evaluators-source-${data.archive_file.evaluators_source.output_md5}.zip"
  source = data.archive_file.evaluators_source.output_path
  etag   = data.archive_file.evaluators_source.output_md5
}

# --- Build trigger ---

resource "null_resource" "build_evaluators" {
  triggers = {
    source_md5    = data.archive_file.evaluators_source.output_md5
    image_tag     = var.image_tag
    ecr_repo      = aws_ecr_repository.evaluators.id
    build_project = aws_codebuild_project.evaluators.id
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command     = <<-EOT
      $projectName = "${aws_codebuild_project.evaluators.name}"
      $region = "${local.region}"
      $repoName = "${aws_ecr_repository.evaluators.name}"
      $imageTag = "${var.image_tag}"
      $repoUrl = "${aws_ecr_repository.evaluators.repository_url}"

      Write-Host "Building evaluators image: $repoUrl`:$imageTag"
      $buildId = aws codebuild start-build --project-name $projectName --region $region --query 'build.id' --output text
      Write-Host "Started build: $buildId"

      while ($true) {
        Start-Sleep -Seconds 10
        $status = aws codebuild batch-get-builds --ids $buildId --region $region --query 'builds[0].buildStatus' --output text
        if ($status -eq "SUCCEEDED") { Write-Host "Build succeeded"; break }
        if ($status -in @("FAILED","FAULT","STOPPED","TIMED_OUT")) { Write-Error "Build $status"; exit 1 }
        Write-Host "  ... status: $status"
      }

      aws ecr describe-images --repository-name $repoName --image-ids "imageTag=$imageTag" --region $region | Out-Null
      Write-Host "Image verified: $repoUrl`:$imageTag"
    EOT
  }

  depends_on = [
    aws_codebuild_project.evaluators,
    aws_iam_role_policy.image_build,
    aws_s3_object.evaluators_source,
  ]
}

# --- Lambda Function (Docker image) ---

resource "aws_lambda_function" "evaluators" {
  function_name = "${local.name_prefix}-evaluators"
  role          = aws_iam_role.evaluators_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.evaluators.repository_url}:${var.image_tag}"
  timeout       = 600
  memory_size   = 512

  environment {
    variables = {
      AWS_REGION_NAME = local.region
      RESULTS_BUCKET  = aws_s3_bucket.agent_source.id
    }
  }

  depends_on = [null_resource.build_evaluators]

  tags = { Name = "${local.name_prefix}-evaluators" }
}

# --- IAM Role for Lambda ---

resource "aws_iam_role" "evaluators_lambda" {
  name = "${local.name_prefix}-evaluators-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Name = "${local.name_prefix}-evaluators-lambda-role" }
}

resource "aws_iam_role_policy" "evaluators_lambda" {
  name = "${local.name_prefix}-evaluators-lambda-policy"
  role = aws_iam_role.evaluators_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:StartQuery",
          "logs:StopQuery",
          "logs:GetQueryResults",
          "logs:DescribeLogGroups",
          "logs:GetLogEvents",
          "logs:FilterLogEvents",
        ]
        Resource = "arn:aws:logs:${local.region}:${local.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:*",
          "bedrock-agentcore:*",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction",
        ]
        Resource = "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.name_prefix}-evaluators"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
        ]
        Resource = "${aws_s3_bucket.agent_source.arn}/evaluations/*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:GetTraceSummaries",
          "xray:BatchGetTraces",
          "xray:GetTraceGraph",
        ]
        Resource = "*"
      },
    ]
  })
}

# --- API Gateway (HTTP API) ---

resource "aws_apigatewayv2_api" "evaluators" {
  name          = "${local.name_prefix}-evaluators-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 3600
  }

  tags = { Name = "${local.name_prefix}-evaluators-api" }
}

resource "aws_apigatewayv2_stage" "evaluators" {
  api_id      = aws_apigatewayv2_api.evaluators.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "evaluators" {
  api_id                 = aws_apigatewayv2_api.evaluators.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.evaluators.invoke_arn
  payload_format_version = "2.0"
}

# Routes
resource "aws_apigatewayv2_route" "create_evaluators" {
  api_id    = aws_apigatewayv2_api.evaluators.id
  route_key = "POST /evaluators/create"
  target    = "integrations/${aws_apigatewayv2_integration.evaluators.id}"
}

resource "aws_apigatewayv2_route" "run_evaluators" {
  api_id    = aws_apigatewayv2_api.evaluators.id
  route_key = "POST /evaluators/run"
  target    = "integrations/${aws_apigatewayv2_integration.evaluators.id}"
}

resource "aws_apigatewayv2_route" "run_builtin_evaluators" {
  api_id    = aws_apigatewayv2_api.evaluators.id
  route_key = "POST /evaluators/run-builtin"
  target    = "integrations/${aws_apigatewayv2_integration.evaluators.id}"
}

resource "aws_apigatewayv2_route" "delete_evaluators" {
  api_id    = aws_apigatewayv2_api.evaluators.id
  route_key = "DELETE /evaluators/delete"
  target    = "integrations/${aws_apigatewayv2_integration.evaluators.id}"
}

resource "aws_apigatewayv2_route" "create_all_evaluators" {
  api_id    = aws_apigatewayv2_api.evaluators.id
  route_key = "POST /evaluators/create-all"
  target    = "integrations/${aws_apigatewayv2_integration.evaluators.id}"
}

resource "aws_apigatewayv2_route" "list_evaluators" {
  api_id    = aws_apigatewayv2_api.evaluators.id
  route_key = "GET /evaluators/list"
  target    = "integrations/${aws_apigatewayv2_integration.evaluators.id}"
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "evaluators_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.evaluators.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.evaluators.execution_arn}/*/*"
}

# --- Outputs ---

output "evaluators_api_url" {
  description = "API Gateway URL for the evaluators endpoint"
  value       = aws_apigatewayv2_api.evaluators.api_endpoint
}

output "evaluators_lambda_arn" {
  description = "ARN of the evaluators Lambda function"
  value       = aws_lambda_function.evaluators.arn
}
