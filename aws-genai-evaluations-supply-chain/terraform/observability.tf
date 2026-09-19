# ============================================================================
# AgentCore Observability — CloudWatch Transaction Search
# One-time account-level setup to view metrics, spans, and traces
# ============================================================================

# Resource policy allowing X-Ray to send spans to CloudWatch Logs
resource "aws_cloudwatch_log_resource_policy" "xray_transaction_search" {
  policy_name     = "TransactionSearchAccess"
  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "TransactionSearchXRayAccess"
        Effect    = "Allow"
        Principal = { Service = "xray.amazonaws.com" }
        Action    = "logs:PutLogEvents"
        Resource  = [
          "arn:aws:logs:${local.region}:${local.account_id}:log-group:aws/spans:*",
          "arn:aws:logs:${local.region}:${local.account_id}:log-group:/aws/application-signals/data:*",
        ]
        Condition = {
          ArnLike = {
            "aws:SourceArn" = "arn:aws:xray:${local.region}:${local.account_id}:*"
          }
          StringEquals = {
            "aws:SourceAccount" = local.account_id
          }
        }
      }
    ]
  })
}

# NOTE: Commented out — already exists at account level from a previous deploy.
# To re-import: terraform import awscc_xray_transaction_search_config.this us-east-1
# resource "awscc_xray_transaction_search_config" "this" {
#   indexing_percentage = var.xray_indexing_percentage
#   depends_on = [aws_cloudwatch_log_resource_policy.xray_transaction_search]
# }

# ============================================================================
# Vended Log & Trace Delivery for Memory + Runtimes
# ============================================================================

locals {
    observability_resources = {
        memory = {
            resource_arn = aws_bedrockagentcore_memory.agent_memory.arn
            resource_id  = aws_bedrockagentcore_memory.agent_memory.id
            type         = "memory"
        }
        mcp = {
            resource_arn = aws_bedrockagentcore_agent_runtime.mcp.agent_runtime_arn
            resource_id  = aws_bedrockagentcore_agent_runtime.mcp.agent_runtime_id
            type         = "runtime"
        }
        supply_chain = {
            resource_arn = aws_bedrockagentcore_agent_runtime.supply_chain.agent_runtime_arn
            resource_id  = aws_bedrockagentcore_agent_runtime.supply_chain.agent_runtime_id
            type         = "runtime"
        }
    }
}

# Log groups for vended log Delivery
resource "aws_cloudwatch_log_group" "observability" {
    for_each = local.observability_resources

    name = "/aws/vendedlogs/bedrock-agentcore/${each.value.type}/APPLICATION_LOGS/${each.value.resource_id}"
    retention_in_days = var.observability_log_retention_days
}

# --- Delivery Sources ---

resource "aws_cloudwatch_log_delivery_source" "logs" {
    for_each = local.observability_resources

    name         = "${each.key}-logs-source"
    log_type     = "APPLICATION_LOGS"
    resource_arn = each.value.resource_arn
}

resource "aws_cloudwatch_log_delivery_source" "traces" {
    for_each = local.observability_resources

    name         = "${each.key}-traces-source"
    log_type     = "TRACES"
    resource_arn = each.value.resource_arn
}

# --- Delivery Destinations ---

resource "aws_cloudwatch_log_delivery_destination" "logs" {
    for_each = local.observability_resources

    name = "${each.key}-logs-destination"

    delivery_destination_configuration {
        destination_resource_arn = aws_cloudwatch_log_group.observability[each.key].arn
    }
}

resource "aws_cloudwatch_log_delivery_destination" "traces" {
    for_each = local.observability_resources

    name                      = "${each.key}-traces-destination"
    delivery_destination_type = "XRAY"

    depends_on = [aws_cloudwatch_log_resource_policy.xray_transaction_search]
}

# --- Deliveries ---

resource "aws_cloudwatch_log_delivery" "logs" {
    for_each = local.observability_resources

    delivery_source_name     = aws_cloudwatch_log_delivery_source.logs[each.key].name
    delivery_destination_arn = aws_cloudwatch_log_delivery_destination.logs[each.key].arn
}

resource "aws_cloudwatch_log_delivery" "traces" {
    for_each = local.observability_resources

    delivery_source_name     = aws_cloudwatch_log_delivery_source.traces[each.key].name
    delivery_destination_arn = aws_cloudwatch_log_delivery_destination.traces[each.key].arn
}