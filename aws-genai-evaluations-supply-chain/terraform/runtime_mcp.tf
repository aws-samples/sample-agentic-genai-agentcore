# ============================================================================
# MCP Tools Runtime — deployed FIRST (Supply Chain depends on its ARN)
# ============================================================================

resource "aws_bedrockagentcore_agent_runtime" "mcp" {
  agent_runtime_name = var.mcp_agent_name
  description        = "MCP server exposing supply chain data tools (optimization, distribution, routing, analytics)"
  role_arn           = aws_iam_role.agent_execution.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.mcp.repository_url}:${var.image_tag}"
    }
  }

  # MCP protocol
  protocol_configuration {
    server_protocol = "MCP"
  }

  network_configuration {
    network_mode = "VPC"
    network_mode_config {
      subnets         = local.runtime_subnet_ids
      security_groups = [aws_security_group.runtime.id]
    }
  }

  environment_variables = {
    AWS_REGION             = local.region
    AWS_DEFAULT_REGION     = local.region
    SUPPLY_CHAIN_API_URL   = aws_api_gateway_stage.northstar_retail.invoke_url
  }

  depends_on = [
    null_resource.build_mcp,
    aws_iam_role_policy.agent_execution,
    aws_iam_role_policy_attachment.agent_execution_managed,
    aws_vpc_endpoint.interface,
    aws_vpc_endpoint.s3,
    aws_api_gateway_stage.northstar_retail,
  ]

  tags = { Name = "${local.name_prefix}-mcp-runtime" }
}
