# AWS GenAI Human Parallel Review System — Deployment Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| AWS CLI | v2.x+ | AWS resource management |
| AWS SAM CLI | v1.100.0+ | Serverless deployment |
| Node.js | v18.x+ | Frontend build |
| Docker/Finch | v20.x+ | Container image build |
| Python | v3.11+ | Lambda runtime |

AWS account with:
- Administrator access
- Amazon Bedrock access to **Claude Sonnet 4.5** in `us-west-2`

---

## Step 1: Clone and Configure AWS

```bash
git clone <repository-url>
cd aws-genai-human-review-strands

# Configure AWS CLI
aws configure
# Set region to: us-west-2

# Verify credentials
aws sts get-caller-identity
```

## Step 2: Enable Bedrock Model Access

1. Open [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock) in `us-west-2`
2. Go to **Model access** → **Manage model access**
3. Select **Claude Sonnet 4.5** (Anthropic) → **Request model access**

## Step 3: Set Up DynamoDB Persona Table

```bash
chmod +x scripts/setup_persona_table.sh
./scripts/setup_persona_table.sh
```

Expected: `🎉 SUCCESS: All 40 persona records created!`

## Step 4: Authenticate Container Registry

```bash
# For Docker:
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com

# For Finch:
aws ecr get-login-password --region us-west-2 | finch login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com
```

Replace `<ACCOUNT_ID>` with your AWS account ID from `aws sts get-caller-identity`.

## Step 5: Build and Deploy Backend

```bash
sam build
sam deploy --guided
```

Provide these inputs during guided deploy:

| Prompt | Value |
|--------|-------|
| Stack Name | `genai-campaign-agentcore` |
| AWS Region | `us-west-2` |
| Confirm changes before deploy | `Y` |
| Allow SAM CLI IAM role creation | `Y` |
| Disable rollback | `Y` |
| Save arguments to configuration file | `Y` |

For subsequent deploys: `sam build && sam deploy`

## Step 6: Save CloudFormation Outputs

After deployment, note these values from the outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name genai-campaign-agentcore \
  --query 'Stacks[0].Outputs' \
  --output table
```

You'll need:
- `ApiEndpoint` — HTTP API URL (for frontend)
- `CampaignOrchestratorApi` — Agent API URL (for frontend)
- `CloudFrontURL` — Frontend URL
- `FrontendBucket` — S3 bucket for frontend
- `UnifiedBucket` — S3 bucket for campaign data
- `DeployAgentApiEndpoint` — Agent deployment URL

## Step 7: Deploy Agent to AgentCore Runtime

This deploys your Strands agent to Bedrock AgentCore and writes the Agent ARN to SSM:

```bash
curl -X POST <DeployAgentApiEndpoint> \
  -H "Content-Type: application/json" \
  -d '{"action":"deploy","agent_name":"campaign_review_agent"}'
```

This takes ~5 minutes. The API Gateway will timeout (29s) but the Lambda continues running.

Monitor progress:
```bash
aws logs tail /aws/lambda/deploy-agentcore --region us-west-2 --follow
```

Wait until you see: `Agent Core Runtime is READY!` and `Wrote Agent ARN to SSM`.

Verify:
```bash
aws ssm get-parameter --name /agentcore/campaign-review/agent-arn --region us-west-2
```

## Step 8: Configure and Deploy Frontend

```bash
# Get values from CloudFormation outputs
API_URL=$(aws cloudformation describe-stacks --stack-name genai-campaign-agentcore \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)

AGENT_API_URL=$(aws cloudformation describe-stacks --stack-name genai-campaign-agentcore \
  --query 'Stacks[0].Outputs[?OutputKey==`CampaignOrchestratorApi`].OutputValue' --output text)

UNIFIED_BUCKET=$(aws cloudformation describe-stacks --stack-name genai-campaign-agentcore \
  --query 'Stacks[0].Outputs[?OutputKey==`UnifiedBucket`].OutputValue' --output text)

# Create .env
cat > .env << EOF
VITE_API_URL=$API_URL
VITE_AGENT_API_URL=$AGENT_API_URL
VITE_AWS_REGION=us-west-2
VITE_S3_BUCKET=$UNIFIED_BUCKET
EOF

# Install, build, deploy
npm install
npm run build

FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name genai-campaign-agentcore \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' --output text)

aws s3 sync dist/ s3://$FRONTEND_BUCKET --delete

# Invalidate CloudFront cache
DIST_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Origins.Items[0].DomainName=='${FRONTEND_BUCKET}.s3.us-west-2.amazonaws.com'].Id" \
  --output text)

aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

## Step 9: Access the Application

```bash
aws cloudformation describe-stacks --stack-name genai-campaign-agentcore \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' --output text
```

Open the URL in your browser. Upload a campaign document (.md, .txt) and watch the AI reviews appear.

---

## Architecture

```
CloudFront → S3 (React Frontend)
                │
                ├── POST /upload ──────→ UploadFunction ──→ S3 (campaign brief)
                │                        (Node.js)
                │
                ├── POST /review-campaign → ReviewCampaignFunction ──→ AgentCore Runtime
                │                          (Python, returns 202)       (Strands agents)
                │                          reads ARN from SSM          writes reviews to S3
                │
                ├── GET /reviews ──────→ ReviewsFunction ──→ S3 (reads reviews)
                │                        (Node.js)
                │
                └── GET /health ───────→ HealthFunction
                                         (Node.js)

AgentCore Runtime (agent.py):
  ├── Persona Reviewer Agent → diverse demographic reviews
  ├── Validator Agent → legal compliance checks
  └── Finalizer Agent → synthesized recommendations
```

---

## Cleanup

```bash
# Delete CloudFormation stack
sam delete --stack-name genai-campaign-agentcore

# Delete DynamoDB table
aws dynamodb delete-table --table-name PersonaTable --region us-west-2

# Delete AgentCore runtime (get agent ID first)
AGENT_ID=$(aws ssm get-parameter --name /agentcore/campaign-review/agent-arn --region us-west-2 \
  --query 'Parameter.Value' --output text | grep -oP '[^/]+$')
aws bedrock-agentcore-control delete-agent-runtime --agent-runtime-id $AGENT_ID --region us-west-2

# Delete SSM parameter
aws ssm delete-parameter --name /agentcore/campaign-review/agent-arn --region us-west-2
```
