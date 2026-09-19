# ============================================================================
# Runtime ARNs
# ============================================================================

output "mcp_runtime_arn" {
  description = "ARN of the MCP tools AgentCore runtime"
  value       = aws_bedrockagentcore_agent_runtime.mcp.agent_runtime_arn
}

output "supply_chain_arn" {
  description = "ARN of the Supply Chain AgentCore runtime"
  value       = aws_bedrockagentcore_agent_runtime.supply_chain.agent_runtime_arn
}

# ============================================================================
# Memory ARN
# ============================================================================

output "agent_memory_arn" {
  description = "ARN of the AgentCore Memory resource used by agents"
  value       = aws_bedrockagentcore_memory.agent_memory.arn
}

# ============================================================================
# ECR / Networking
# ============================================================================

output "mcp_ecr_repository_url" {
  value = aws_ecr_repository.mcp.repository_url
}

output "supply_chain_ecr_repository_url" {
  value = aws_ecr_repository.supply_chain.repository_url
}

output "runtime_subnet_ids" {
  value = local.runtime_subnet_ids
}

output "runtime_security_group_id" {
  value = aws_security_group.runtime.id
}

output "vpc_endpoints_security_group_id" {
  value = aws_security_group.vpc_endpoints.id
}

output "vpc_endpoint_ids" {
  value = merge(
    { for k, v in aws_vpc_endpoint.interface : k => v.id },
    { s3 = aws_vpc_endpoint.s3.id }
  )
}


# ============================================================================
# Northstar Retail API
# ============================================================================

output "northstar_retail_api_url" {
  description = "Base invoke URL for the Northstar Retail API Gateway (dev stage)"
  value       = aws_api_gateway_stage.northstar_retail.invoke_url
}

output "northstar_retail_optimization_url" {
  description = "URL for the optimization endpoint"
  value       = "${aws_api_gateway_stage.northstar_retail.invoke_url}/optimization"
}

output "northstar_retail_distribution_url" {
  description = "URL for the distribution endpoint"
  value       = "${aws_api_gateway_stage.northstar_retail.invoke_url}/distribution"
}

output "northstar_retail_routing_url" {
  description = "URL for the routing endpoint"
  value       = "${aws_api_gateway_stage.northstar_retail.invoke_url}/routing"
}

output "northstar_retail_analytics_url" {
  description = "URL for the analytics endpoint"
  value       = "${aws_api_gateway_stage.northstar_retail.invoke_url}/analytics"
}
