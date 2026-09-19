variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "demo"
}

variable "stack_name" {
  description = "Stack name prefix for all resources"
  type        = string
  default     = "agentcore-supply-chain"
}

# ============================================================================
# VPC Configuration — uses an EXISTING VPC
# ============================================================================

variable "vpc_id" {
  description = "Existing VPC ID to deploy runtimes into"
  type        = string
}

variable "runtime_subnet_azs" {
  description = <<-EOT
    Availability zones (logical names like us-east-1c) to use for AgentCore runtimes.
    MUST be in both:
      - AgentCore-supported AZs (physical IDs use1-az1, use1-az2, use1-az4)
      - VPC endpoint-supported AZs for all services we need
    For us-east-1: us-east-1c and us-east-1d are the safe choices.
  EOT
  type        = list(string)
  default     = ["us-east-1c", "us-east-1d"]
}

variable "runtime_subnet_ids" {
  description = "Explicit subnet IDs for AgentCore runtimes (overrides AZ-based lookup)"
  type        = list(string)
  default     = []
}

# ============================================================================
# Agent Configuration
# ============================================================================

variable "mcp_agent_name" {
  description = "Name for the MCP tools agent runtime"
  type        = string
  default     = "mcp_tools_server"
}

variable "supply_chain_agent_name" {
  description = "Name for the Supply Chain agent runtime"
  type        = string
  default     = "supply_chain_orchestrator_agent"
}

variable "image_tag" {
  description = "Docker image tag for both agent runtimes"
  type        = string
  default     = "latest"
}

# ============================================================================
# Memory Configuration
# ============================================================================

variable "agent_memory_name" {
  description = "Name for the AgentCore Memory resource"
  type        = string
  default     = "supply_chain_agent_memory"
}

variable "event_expiry_duration" {
  description = "Number of days to retain memory events"
  type        = number
  default     = 30
}

# ============================================================================
# Observability Configuration
# ============================================================================

variable "xray_indexing_percentage" {
  description = "Percentage of spans indexed for X-Ray Transaction Search (0-100)"
  type        = number
  default     = 1
}

variable "observability_log_retention_days" {
  description = "Retention period in days for observability log groups"
  type        = number
  default     = 30
}
