# ============================================================================
# AgentCore Memory — deployed BEFORE Supply Chain runtime (depends on its ARN)
# ============================================================================

resource "aws_bedrockagentcore_memory" "agent_memory" {
    name                      = var.agent_memory_name
    description               = "Memory for Supply Chain agents"
    event_expiry_duration     = var.event_expiry_duration
    memory_execution_role_arn = aws_iam_role.agent_execution.arn
}

resource "aws_bedrockagentcore_memory_strategy" "semantic" {
    memory_id     = aws_bedrockagentcore_memory.agent_memory.id
    name          = "semantic_strategy"
    description   = "Key pieces of factual information from conversations"
    type = "SEMANTIC"
    namespaces    = ["/knowledge/{actorId}/"]
}