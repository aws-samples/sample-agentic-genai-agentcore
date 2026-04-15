# AWS GenAI Human Parallel Review System

An AI-powered multi-agent campaign review system that combines serverless backend processing with a modern React frontend. The system orchestrates parallel human-perspective reviews using diverse personas to ensure marketing campaigns resonate authentically with target audiences while maintaining legal compliance and brand standards.

## Table of Contents
- [Solution Overview](#solution-overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Dependencies](#dependencies)
- [Step-by-Step Deployment](#step-by-step-deployment)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Cleanup](#cleanup)

---

## Solution Overview

This solution implements an end-to-end AI-powered campaign review workflow:

1. **Document Upload**: Users upload campaign documents via a React frontend
2. **Async Processing**: Backend triggers AI agents asynchronously for long-running analysis
3. **Multi-Agent Review**: Three specialized AI agents analyze the campaign in parallel
4. **Progressive Display**: Frontend polls for results and displays reviews as they become available

### Key Features

| Feature | Description |
|---------|-------------|
| **Parallel Human Perspective Reviews** | 40 diverse personas representing different demographics |
| **Compliance Validation** | Automated legal and brand guideline checks |
| **AI-Powered Analysis** | Amazon Bedrock with Claude Sonnet 4.5 |
| **Serverless Architecture** | Fully managed AWS infrastructure |
| **Async Processing** | Non-blocking API with polling for results |
| **Progressive UI** | Real-time status updates and review display |

### Workflow

```
User Upload → S3 Storage → Agent API (async) → AI Processing → S3 Reviews → Frontend Display
     │            │              │                  │              │              │
     └── Campaign ID ──────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                           │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────────┐   │
│  │  CloudFront │────▶│                  S3 Buckets                          │   │
│  │    (CDN)    │     │  ┌─────────────────┐  ┌─────────────────────────┐   │   │
│  └─────────────┘     │  │ Frontend Bucket │  │    Unified Data Bucket  │   │   │
│         │            │  │  (React App)    │  │ /campaigns/{id}/        │   │   │
│         │            │  └─────────────────┘  │   ├── campaign_brief.md │   │   │
│         ▼            │                       │   ├── status.json       │   │   │
│  ┌─────────────┐     │                       │   └── reviews/          │   │   │
│  │   React     │     │                       │       ├── persona_xxx/  │   │   │
│  │  Frontend   │     │                       │       └── *.md          │   │   │
│  └─────────────┘     │                       └─────────────────────────┘   │   │
│         │            └─────────────────────────────────────────────────────┘   │
│         │                                                                       │
│         ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         API Gateway                                      │   │
│  │  ┌─────────────────────┐    ┌─────────────────────────────────────┐    │   │
│  │  │   HTTP API          │    │         REST API                     │    │   │
│  │  │  POST /upload       │    │    POST /review-campaign             │    │   │
│  │  │  GET  /reviews      │    │    (Agent Orchestrator)              │    │   │
│  │  │  GET  /health       │    │                                      │    │   │
│  │  └─────────────────────┘    └─────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│         │                                    │                                  │
│         ▼                                    ▼                                  │
│  ┌─────────────────────┐          ┌─────────────────────────────────────┐      │
│  │   Lambda Functions  │          │    Campaign Orchestrator Lambda     │      │
│  │  ┌───────────────┐  │          │  ┌─────────────────────────────┐   │      │
│  │  │ Upload Handler│  │          │  │   Strands Agent Framework   │   │      │
│  │  ├───────────────┤  │          │  │  ┌─────────────────────┐    │   │      │
│  │  │Reviews Fetcher│  │          │  │  │ Persona Reviewer    │    │   │      │
│  │  ├───────────────┤  │          │  │  │ Agent               │────┼───┼──────┤
│  │  │ Health Check  │  │          │  │  ├─────────────────────┤    │   │      │
│  │  └───────────────┘  │          │  │  │ Validator Agent     │────┼───┼──────┤
│  └─────────────────────┘          │  │  ├─────────────────────┤    │   │      │
│                                   │  │  │ Finalizer Agent     │────┼───┼──────┤
│                                   │  │  └─────────────────────┘    │   │      │
│                                   │  └─────────────────────────────┘   │      │
│                                   └─────────────────────────────────────┘      │
│                                                    │                           │
│                                                    ▼                           │
│                                   ┌─────────────────────────────────────┐      │
│                                   │         Amazon Bedrock              │      │
│                                   │    Claude Sonnet 4.5 Model          │      │
│                                   └─────────────────────────────────────┘      │
│                                                    │                           │
│                                                    ▼                           │
│                                   ┌─────────────────────────────────────┐      │
│                                   │         Amazon DynamoDB             │      │
│                                   │    PersonaTable (40 personas)       │      │
│                                   └─────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Components

#### 1. Frontend Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| **React Application** | React 18, TypeScript, Vite | Single-page application for document upload and review display |
| **CloudFront CDN** | AWS CloudFront | Global content delivery with HTTPS |
| **S3 Static Hosting** | AWS S3 | Frontend asset storage |

#### 2. API Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| **HTTP API Gateway** | AWS API Gateway v2 | Frontend API endpoints (upload, reviews, health) |
| **REST API Gateway** | AWS API Gateway v1 | Agent orchestrator endpoint |
| **CORS Configuration** | API Gateway | Cross-origin request handling |

#### 3. Processing Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Upload Lambda** | Node.js 20.x | Handles file uploads to S3 |
| **Reviews Lambda** | Node.js 20.x | Fetches reviews from S3 |
| **Orchestrator Lambda** | Python 3.11 | Coordinates AI agent workflow |
| **Health Lambda** | Node.js 20.x | API health checks |

#### 4. AI Agent Layer (Strands Framework)
| Agent | Purpose |
|-------|---------|
| **Persona Reviewer Agent** | Reviews content from diverse demographic perspectives, provides resonance scoring |
| **Validator Agent** | Ensures legal compliance and brand guideline adherence |
| **Finalizer Agent** | Synthesizes feedback into actionable recommendations |

#### 5. Data Layer
| Component | Purpose |
|-----------|---------|
| **Unified S3 Bucket** | Campaign briefs, status files, and generated reviews |
| **DynamoDB PersonaTable** | 40 diverse persona profiles for review perspectives |
| **Amazon Bedrock** | Claude Sonnet 4.5 model for AI analysis |

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| **AWS CLI** | v2.x+ | [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| **AWS SAM CLI** | v1.100.0+ | [Install Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) |
| **Node.js** | v18.x+ | [Download](https://nodejs.org/) |
| **npm** | v9.x+ | Included with Node.js |
| **Docker** | v20.x+ | [Install Guide](https://docs.docker.com/get-docker/) |
| **Python** | v3.11+ | [Download](https://www.python.org/downloads/) |
| **Git** | Latest | [Download](https://git-scm.com/) |

### AWS Account Requirements

1. **Active AWS Account** with administrator access
2. **Amazon Bedrock Access**:
   - Navigate to Amazon Bedrock console
   - Request access to `Claude Sonnet 4.5` model
   - Region: `us-west-2` (recommended)
3. **Service Quotas** (defaults are sufficient):
   - Lambda concurrent executions: 10+
   - API Gateway requests: 10,000/second
   - S3 storage: 5GB+

### IAM Permissions Required

The deployment requires permissions for:
- Lambda (create, update, invoke)
- API Gateway (create, deploy)
- S3 (create buckets, read/write objects)
- CloudFront (create distribution)
- IAM (create roles and policies)
- CloudFormation (create/update stacks)
- DynamoDB (create table, read/write items)
- Bedrock (invoke models)

---

## Dependencies

### Backend Dependencies (Python)

```txt
# lambda/requirements.txt
strands-agents          # AWS Strands multi-agent framework
strands-agents-tools    # Strands agent tools and utilities
requests                # HTTP library for API calls
bedrock-agentcore       # Amazon Bedrock agent core functionality
boto3                   # AWS SDK for Python
```

### Frontend Dependencies (Node.js)

```json
{
  "dependencies": {
    "@aws-sdk/client-s3": "^3.958.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-dropzone": "^14.2.3",
    "zustand": "^4.4.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@vitejs/plugin-react": "^4.0.3",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.27",
    "tailwindcss": "^3.3.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.5"
  }
}
```

### AWS Services Used

| Service | Purpose | Pricing Model |
|---------|---------|---------------|
| AWS Lambda | Serverless compute | Pay per invocation |
| Amazon S3 | Object storage | Pay per GB stored |
| Amazon API Gateway | REST/HTTP APIs | Pay per request |
| Amazon CloudFront | CDN | Pay per GB transferred |
| Amazon Bedrock | AI model inference | Pay per token |
| Amazon DynamoDB | NoSQL database | Pay per request |
| AWS IAM | Access management | Free |
| AWS CloudFormation | Infrastructure as Code | Free |

---

## Step-by-Step Deployment

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd aws-genai-human-parallel-review
```

### Step 2: Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure

# Verify credentials
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AKIAIOSFODNN7EXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-user"
}
```

### Step 3: Enable Amazon Bedrock Model Access

1. Open [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Navigate to **Model access** in the left sidebar
3. Click **Manage model access**
4. Select **Claude Sonnet 4.5** (Anthropic)
5. Click **Request model access**
6. Wait for approval (usually instant)

### Step 4: Set Up DynamoDB Persona Table

```bash
# Make script executable
chmod +x scripts/setup_persona_table.sh

# Run setup script
./scripts/setup_persona_table.sh
```

Expected output:
```
🚀 Starting DynamoDB Persona Table Setup...
📋 Creating PersonaTable...
✅ Table created successfully!
👥 Inserting 40 persona records...
🎉 SUCCESS: All 40 persona records created!
```

### Step 5: Build the SAM Application

```bash
sam build
```

Expected output:
```
Building codeuri: lambda/ runtime: python3.11
Building codeuri: lambda/upload/ runtime: nodejs20.x
Building codeuri: lambda/reviews/ runtime: nodejs20.x
Building codeuri: lambda/health/ runtime: nodejs20.x

Build Succeeded
```

### Step 6: Deploy Infrastructure

**First-time deployment (guided):**
```bash
sam deploy --guided
```

Provide the following inputs:
| Prompt | Value |
|--------|-------|
| Stack Name | `unified-campaign-review` |
| AWS Region | `us-west-2` |
| Confirm changes before deploy | `Y` |
| Allow SAM CLI IAM role creation | `Y` |
| Disable rollback | `N` |
| Save arguments to configuration file | `Y` |

**Subsequent deployments:**
```bash
sam deploy
```

### Step 7: Get Deployment Outputs

```bash
# Get API endpoints
aws cloudformation describe-stacks \
  --stack-name unified-campaign-review \
  --query 'Stacks[0].Outputs' \
  --output table
```

Save these values:
- `ApiEndpoint` - HTTP API URL
- `CampaignOrchestratorApi` - Agent API URL
- `CloudFrontURL` - Frontend URL
- `FrontendBucket` - S3 bucket for frontend

### Step 8: Configure Frontend Environment

```bash
# Get values from CloudFormation outputs
API_URL=$(aws cloudformation describe-stacks --stack-name unified-campaign-review \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)

AGENT_API_URL=$(aws cloudformation describe-stacks --stack-name unified-campaign-review \
  --query 'Stacks[0].Outputs[?OutputKey==`CampaignOrchestratorApi`].OutputValue' --output text)

# Create .env file
cat > .env << EOF
VITE_API_URL=$API_URL
VITE_AGENT_API_URL=$AGENT_API_URL
VITE_AWS_REGION=us-west-2
EOF
```

### Step 9: Build and Deploy Frontend

```bash
# Install dependencies
npm install

# Build frontend
npm run build

# Get frontend bucket name
FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name unified-campaign-review \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' --output text)

# Deploy to S3
aws s3 sync dist/ s3://$FRONTEND_BUCKET --delete

# Invalidate CloudFront cache (optional, for updates)
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Origins.Items[0].DomainName=='${FRONTEND_BUCKET}.s3.us-west-2.amazonaws.com'].Id" \
  --output text)

aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
```

### Step 10: Access the Application

```bash
# Get CloudFront URL
aws cloudformation describe-stacks --stack-name unified-campaign-review \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' --output text
```

Open the URL in your browser to access the application.

---

## Configuration

### Environment Variables

#### Frontend (.env)
```bash
VITE_API_URL=https://xxxxxxxx.execute-api.us-west-2.amazonaws.com
VITE_AGENT_API_URL=https://xxxxxxxx.execute-api.us-west-2.amazonaws.com/Prod/review-campaign
VITE_AWS_REGION=us-west-2
```

#### Lambda (set via SAM template)
```yaml
CAMPAIGN_BUCKET: <auto-generated>
S3_BUCKET: <auto-generated>
S3_REGION: us-west-2
```

### Customization Options

#### Change AI Model
Edit `lambda/orchestrator.py` and agent files:
```python
model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"  # Change as needed
```

#### Adjust Lambda Timeout
Edit `template.yaml`:
```yaml
Globals:
  Function:
    Timeout: 300  # Increase for longer processing
    MemorySize: 1024  # Increase for better performance
```

---

## Usage

1. **Open Application**: Navigate to CloudFront URL
2. **Upload Document**: Drag and drop a campaign document (.md, .txt, .pdf)
3. **Wait for Processing**: Status shows "AI processing... waiting for reviews"
4. **View Results**: Reviews appear in tabbed interface when ready
5. **Start New Review**: Click "Remove" to clear and upload new document

---

## API Reference

### Agent API (REST)

**POST /review-campaign**
```json
// Request
{
  "campaignId": "campaign-1234567890",
  "s3Key": "campaigns/campaign-1234567890/campaign_brief.md"
}

// Response (202 Accepted)
{
  "message": "Campaign review started",
  "status": "processing",
  "campaign_id": "campaign-1234567890"
}
```

### Frontend API (HTTP)

**POST /upload**
- Uploads file to S3 with campaign structure

**GET /reviews?campaignId={id}**
- Fetches reviews for a specific campaign

**GET /health**
- Returns API health status

---

## Monitoring & Troubleshooting

### View Lambda Logs

```bash
# Orchestrator logs
sam logs -n CampaignOrchestratorFunction --stack-name unified-campaign-review --tail

# Upload function logs
sam logs -n UploadFunction --stack-name unified-campaign-review --tail
```

### Common Issues

| Issue | Solution |
|-------|----------|
| **502/504 Gateway Timeout** | Agent processing is async; frontend should poll for results |
| **Bedrock Access Denied** | Enable Claude Sonnet 4.5 in Bedrock console |
| **Reviews Not Loading** | Check campaign ID matches between upload and fetch |
| **CORS Errors** | Verify API Gateway CORS configuration |

### Debug Steps

1. Check CloudWatch logs for Lambda errors
2. Verify S3 bucket contents: `aws s3 ls s3://<bucket>/campaigns/`
3. Test API directly with curl
4. Check browser console for frontend errors

---

## Cleanup

### Delete All Resources

```bash
# Delete CloudFormation stack
sam delete --stack-name unified-campaign-review

# Delete DynamoDB table
aws dynamodb delete-table --table-name PersonaTable --region us-west-2
```

### Manual Cleanup (if needed)

```bash
# Empty and delete S3 buckets
aws s3 rm s3://<unified-bucket> --recursive
aws s3 rb s3://<unified-bucket>

aws s3 rm s3://<frontend-bucket> --recursive
aws s3 rb s3://<frontend-bucket>
```

---

## Project Structure

```
aws-genai-human-parallel-review/
├── lambda/                      # Backend Lambda functions
│   ├── orchestrator.py          # Main agent orchestrator
│   ├── requirements.txt         # Python dependencies
│   ├── tools/                   # AI agent implementations
│   │   ├── revieweragent.py     # Persona reviewer agent
│   │   ├── validatoragent.py    # Compliance validator agent
│   │   └── finalizeragent.py    # Finalizer agent
│   ├── utils/                   # Utility modules
│   │   ├── s3.py                # S3 operations
│   │   └── persona_store.py     # DynamoDB persona access
│   ├── upload/                  # Upload Lambda (Node.js)
│   ├── reviews/                 # Reviews Lambda (Node.js)
│   └── health/                  # Health check Lambda (Node.js)
├── src/                         # React frontend
│   ├── components/              # React components
│   │   ├── FileUpload.tsx       # File upload with drag-drop
│   │   ├── OutputPanel.tsx      # Review display panel
│   │   └── ChatInterface.tsx    # Main interface
│   ├── services/                # API services
│   │   └── s3.ts                # S3 and API integration
│   ├── store/                   # State management
│   │   └── reviewStore.ts       # Zustand store
│   └── App.tsx                  # Main app component
├── scripts/                     # Setup scripts
│   └── setup_persona_table.sh   # DynamoDB setup
├── template.yaml                # SAM/CloudFormation template
├── package.json                 # Frontend dependencies
├── samconfig.toml               # SAM configuration
├── deploy.sh                    # One-command deployment
└── README.md                    # This file
```

---

## Cost Estimation

| Service | Free Tier | Estimated Monthly Cost |
|---------|-----------|------------------------|
| Lambda | 1M requests | $0 (within free tier) |
| API Gateway | 1M requests | $0 (within free tier) |
| S3 | 5GB storage | $0-5 |
| CloudFront | 50GB transfer | $0 (within free tier) |
| DynamoDB | 25GB storage | $0 (within free tier) |
| **Bedrock** | Pay per token | **$5-25** |

**Total estimated cost**: $5-30/month (primarily Bedrock usage)

---

## License

MIT License - See LICENSE file for details.
