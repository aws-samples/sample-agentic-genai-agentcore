# ============================================================================
# Northstar Retail Lambda API — Supply Chain Mock Data Services
# ============================================================================

# --- Lambda Layer: supply_chain_mock package ---

# Package supply_chain_data/ as a Lambda layer with the import name "supply_chain_mock"
data "archive_file" "supply_chain_mock_layer" {
  type        = "zip"
  output_path = "${path.module}/.terraform/supply-chain-mock-layer.zip"

  source {
    content  = file("${path.module}/../supply_chain_data/__init__.py")
    filename = "python/supply_chain_mock/__init__.py"
  }
  source {
    content  = file("${path.module}/../supply_chain_data/schema.py")
    filename = "python/supply_chain_mock/schema.py"
  }
  source {
    content  = file("${path.module}/../supply_chain_data/canned_data.py")
    filename = "python/supply_chain_mock/canned_data.py"
  }
  source {
    content  = file("${path.module}/../supply_chain_data/serialization.py")
    filename = "python/supply_chain_mock/serialization.py"
  }
}

resource "aws_lambda_layer_version" "supply_chain_mock" {
  filename            = data.archive_file.supply_chain_mock_layer.output_path
  layer_name          = "${local.name_prefix}-supply-chain-mock"
  compatible_runtimes = ["python3.12"]
  description         = "Shared supply_chain_mock package (schema, canned data, serialization)"
  source_code_hash    = data.archive_file.supply_chain_mock_layer.output_base64sha256
}

# --- IAM Role for Northstar Retail Lambda functions ---

resource "aws_iam_role" "northstar_retail_lambda" {
  name = "${local.name_prefix}-northstar-retail-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Name = "${local.name_prefix}-northstar-retail-lambda-role" }
}

resource "aws_iam_role_policy" "northstar_retail_lambda" {
  name = "${local.name_prefix}-northstar-retail-lambda-policy"
  role = aws_iam_role.northstar_retail_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:${local.region}:${local.account_id}:*"
      },
    ]
  })
}

# --- Lambda Functions ---

locals {
  northstar_retail_functions = {
    optimization = "${path.module}/../northstar_retail/optimization"
    distribution = "${path.module}/../northstar_retail/distribution"
    routing      = "${path.module}/../northstar_retail/routing"
    analytics    = "${path.module}/../northstar_retail/analytics"
  }
}

data "archive_file" "northstar_retail" {
  for_each    = local.northstar_retail_functions
  type        = "zip"
  source_dir  = each.value
  output_path = "${path.module}/.terraform/northstar-retail-${each.key}.zip"
}

resource "aws_lambda_function" "northstar_retail" {
  for_each = local.northstar_retail_functions

  function_name    = "${local.name_prefix}-supply-chain-${each.key}"
  role             = aws_iam_role.northstar_retail_lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 10
  memory_size      = 128
  architectures    = ["x86_64"]
  filename         = data.archive_file.northstar_retail[each.key].output_path
  source_code_hash = data.archive_file.northstar_retail[each.key].output_base64sha256

  layers = [aws_lambda_layer_version.supply_chain_mock.arn]

  tags = { Name = "${local.name_prefix}-supply-chain-${each.key}" }
}

# --- REST API Gateway ---

resource "aws_api_gateway_rest_api" "northstar_retail" {
  name        = "SupplyChainMockApi"
  description = "REST API for Northstar Retail supply chain mock data"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = "*"
      Action    = "execute-api:Invoke"
      Resource  = "*"
    }]
  })

  tags = { Name = "${local.name_prefix}-northstar-retail-api" }
}

# API Gateway resources (one per endpoint)
resource "aws_api_gateway_resource" "northstar_retail" {
  for_each = local.northstar_retail_functions

  rest_api_id = aws_api_gateway_rest_api.northstar_retail.id
  parent_id   = aws_api_gateway_rest_api.northstar_retail.root_resource_id
  path_part   = each.key
}

# GET methods
resource "aws_api_gateway_method" "northstar_retail" {
  for_each = local.northstar_retail_functions

  rest_api_id   = aws_api_gateway_rest_api.northstar_retail.id
  resource_id   = aws_api_gateway_resource.northstar_retail[each.key].id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda integrations
resource "aws_api_gateway_integration" "northstar_retail" {
  for_each = local.northstar_retail_functions

  rest_api_id             = aws_api_gateway_rest_api.northstar_retail.id
  resource_id             = aws_api_gateway_resource.northstar_retail[each.key].id
  http_method             = aws_api_gateway_method.northstar_retail[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.northstar_retail[each.key].invoke_arn
}

# Lambda permissions for API Gateway invocation
resource "aws_lambda_permission" "northstar_retail" {
  for_each = local.northstar_retail_functions

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.northstar_retail[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.northstar_retail.execution_arn}/*/*"
}

# Deployment and stage
resource "aws_api_gateway_deployment" "northstar_retail" {
  rest_api_id = aws_api_gateway_rest_api.northstar_retail.id

  triggers = {
    redeployment = timestamp()
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.northstar_retail,
  ]
}

resource "aws_api_gateway_stage" "northstar_retail" {
  deployment_id = aws_api_gateway_deployment.northstar_retail.id
  rest_api_id   = aws_api_gateway_rest_api.northstar_retail.id
  stage_name    = "dev"

  tags = { Name = "${local.name_prefix}-northstar-retail-dev" }
}
