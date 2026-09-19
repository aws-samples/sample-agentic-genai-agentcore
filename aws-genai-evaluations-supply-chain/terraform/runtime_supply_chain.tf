# ============================================================================
# Supply Chain Agent Runtime — depends on MCP runtime being deployed
# ============================================================================

resource "aws_bedrockagentcore_agent_runtime" "supply_chain" {
  agent_runtime_name = var.supply_chain_agent_name
  description        = "Supply Chain orchestrator agent using remote MCP tools"
  role_arn           = aws_iam_role.agent_execution.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.supply_chain.repository_url}:${var.image_tag}"
    }
  }

  # Supply Chain runtime uses HTTP protocol (BedrockAgentCoreApp)
  protocol_configuration {
    server_protocol = "HTTP"
  }

  network_configuration {
    network_mode = "VPC"
    network_mode_config {
      subnets         = local.runtime_subnet_ids
      security_groups = [aws_security_group.runtime.id]
    }
  }

  environment_variables = {
    AWS_REGION         = local.region
    AWS_DEFAULT_REGION = local.region

    # Point at the MCP tools runtime (cross-runtime MCP call)
    MCP_SERVER_ARN = aws_bedrockagentcore_agent_runtime.mcp.agent_runtime_arn

    # Points to agent memory resource
    MEMORY_ID = aws_bedrockagentcore_memory.agent_memory.id
  }

  depends_on = [
    null_resource.build_supply_chain,
    aws_bedrockagentcore_agent_runtime.mcp,
    aws_iam_role_policy.agent_execution,
    aws_iam_role_policy_attachment.agent_execution_managed,
    aws_vpc_endpoint.interface,
    aws_vpc_endpoint.s3,
  ]

  tags = { Name = "${local.name_prefix}-supply-chain-runtime" }
}
