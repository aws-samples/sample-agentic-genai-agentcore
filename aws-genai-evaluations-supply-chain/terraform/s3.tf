# ============================================================================
# S3 Bucket for Agent Source Code (all runtimes)
# ============================================================================

resource "aws_s3_bucket" "agent_source" {
  bucket_prefix = "${var.stack_name}-src-"
  force_destroy = true

  tags = { Name = "${local.name_prefix}-agent-source" }
}

resource "aws_s3_bucket_public_access_block" "agent_source" {
  bucket                  = aws_s3_bucket.agent_source.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "agent_source" {
  bucket = aws_s3_bucket.agent_source.id
  versioning_configuration { status = "Enabled" }
}

# ============================================================================
# Archive & upload each agent's code as a separate ZIP
# ============================================================================

data "archive_file" "mcp_source" {
  type        = "zip"
  source_dir  = "${path.module}/../mcp"
  output_path = "${path.module}/.terraform/mcp-source.zip"
}

data "archive_file" "supply_chain_source" {
  type        = "zip"
  source_dir  = "${path.module}/../agents/supply_chain"
  output_path = "${path.module}/.terraform/supply-chain-source.zip"
}

resource "aws_s3_object" "mcp_source" {
  bucket = aws_s3_bucket.agent_source.id
  key    = "mcp-source-${data.archive_file.mcp_source.output_md5}.zip"
  source = data.archive_file.mcp_source.output_path
  etag   = data.archive_file.mcp_source.output_md5
}

resource "aws_s3_object" "supply_chain_source" {
  bucket = aws_s3_bucket.agent_source.id
  key    = "supply-chain-source-${data.archive_file.supply_chain_source.output_md5}.zip"
  source = data.archive_file.supply_chain_source.output_path
  etag   = data.archive_file.supply_chain_source.output_md5
}
