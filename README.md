# AWS GenAI Human Parallel Review System

An AI-powered multi-agent campaign review system that combines serverless backend processing with a modern React frontend. The system uses LangGraph to orchestrate parallel human-perspective reviews using diverse personas to ensure marketing campaigns resonate authentically with target audiences while maintaining legal compliance and brand standards.

## Table of Contents
- [Solution Overview](#solution-overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Dependencies](#dependencies)
- [Step-by-Step Deployment](#step-by-step-deployment)
- [Configuration](#configuration)
- [Observability](#observability)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Cleanup](#cleanup)

---

## Solution Overview

This solution implements an end-to-end AI-powered campaign review workflow:

1. **Document Upload**: Users upload campaign documents via a React frontend
2. **Async Processing**: Backend triggers AI agents asynchronously for long-running analysis
3. **Multi-Agent Review**: Three specialized AI agents analyze the campaign sequentially via LangGraph
4. **Progressive Display**: Frontend polls for results and displays reviews as they become available

### Key Features

| Feature | Description |
|---------|-------------|
| **Parallel Human Perspective Reviews** | 40 diverse personas representing different demographics |
| **Compliance Validation** | Automated legal and brand guideline checks |
| **AI-Powered Analysis** | Amazon Bedrock with Claude Sonnet 4.5 |
| **Serverless Architecture** | Lambda + Lambda Layer (no Docker required) |
| **LangGraph Orchestration** | StateGraph-based workflow with LangChain agents |
| **AgentCore Observability** | OpenTelemetry tracing with session correlation |
| **Async Processing** | Non-blocking API with polling for results |
| **Progressive UI** | Real-time status updates and review display |

### Workflow

```
User Upload → S3 Storage → Agent API (async) → LangGraph Orchestration → S3 Reviews → Frontend Display
     │            │              │                       │                     │              │
     │            │              │            ┌──────────┼──────────┐          │              │
     │            │              │            ▼          ▼          ▼          │              │
     │            │              │        Reviewer   Validator  Finalizer     │              │
     │            │              │         Agent      Agent      Agent        │              │
     └── Campaign ID ──────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                           │
│                                                                                  │
│  ┌─────────────┐     ┌──────────────────────────────────────────────────────┐   │
│  │  CloudFront │────▶│                  S3 Buckets                           │   │
│  │    (CDN)    │     │  ┌─────────────────┐  ┌──────────────────────────┐   │   │
│  └─────────────┘     │  │ Frontend Bucket │  │    Unified Data Bucket   │   │   │
│         │            │  │  (React App)    │  │ /campaigns/{id}/         │   │   │
│         ▼            │  └─────────────────┘  │   ├── campaign_brief.md  │   │   │
│  ┌─────────────┐     │                       │   ├── status.json        │   │   │
│  │   React     │     │                       │   └── reviews/           │   │   │
│  │  Frontend   │     │                       │       ├── persona_xxx/   │   │   │
│  └─────────────┘     │                       │       └── *.md           │   │   │
│         │            │                       └──────────────────────────┘   │   │
│         │            └──────────────────────────────────────────────────────┘   │
│         ▼                                                                       │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         API Gateway                                       │   │
│  │  ┌─────────────────────┐    ┌────────────────────────────────────────┐   │   │
│  │  │   HTTP API          │    │         REST API                       │   │   │
│  │  │  POST /upload       │    │    POST /review-campaign               │   │   │
│  │  │  GET  /reviews      │    │    (LangGraph Orchestrator)            │   │   │
│  │  │  GET  /health       │    │                                        │   │   │
│  │  └─────────────────────┘    └────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│         │                                    │                                  │
│         ▼                                    ▼                                  │
│  ┌─────────────────────┐    ┌───────────────────────────────────────────────┐  │
│  │   Lambda Functions  │    │  Campaign Orchestrator Lambda (Python 3.12)   │  │
│  │  ┌───────────────┐  │    │  ┌─────────────────────────────────────────┐  │  │
│  │  │ Upload Handler│  │    │  │         LangGraph StateGraph            │  │  │
│  │  ├───────────────┤  │    │  │  ┌───────────┐ ┌───────────┐ ┌──────┐  │  │  │
│  │  │Reviews Fetcher│  │    │  │  │ Persona   │→│ Validator │→│Final-│  │  │  │
│  │  ├───────────────┤  │    │  │  │ Reviewer  │ │  Agent    │ │izer  │  │  │  │
│  │  │ Health Check  │  │    │  │  └───────────┘ └───────────┘ └──────┘  │  │  │
│  │  └───────────────┘  │    │  └─────────────────────────────────────────┘  │  │
│  └─────────────────────┘    │  ┌─────────────────────────────────────────┐  │  │
│                             │  │      Lambda Layer (Dependencies)        │  │  │
│                             │  │  langgraph, langchain-aws, langchain-   │  │  │
│                             │  │  core, opentelemetry, aws-otel-distro   │  │  │
│                             │  └─────────────────────────────────────────┘  │  │
│                             └───────────────────────────────────────────────┘  │
│                                          │              │                      │
│                    ┌─────────────────────┘              └──────────────┐       │
│                    ▼                                                   ▼       │
│  ┌──────────────────────────────┐          ┌──────────────────────────────┐   │
│  │       Amazon Bedrock         │          │    Amazon DynamoDB           │   │
│  │  Claude Sonnet 4.5 Model     │          │  PersonaTable (40 personas)  │   │
│  └──────────────────────────────┘          └──────────────────────────────┘   │
│                    │                                                          │
│                    ▼                                                          │
│  ┌──────────────────────────────┐                                            │
│  │  AgentCore Observability     │                                            │
│  │  OpenTelemetry + CloudWatch  │                                            │
│  └──────────────────────────────┘                                            │
└──────────────────────────────────────────────────────────────────────────────┘
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

#### 3. Processing Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Upload Lambda** | Node.js 20.x | Handles file uploads to S3 |
| **Reviews Lambda** | Node.js 20.x | Fetches reviews from S3 |
| **Orchestrator Lambda** | Python 3.12 + Lambda Layer | Coordinates AI agent workflow via LangGraph |
| **Health Lambda** | Node.js 20.x | API health checks |

#### 4. AI Agent Layer (LangGraph + LangChain)
| Agent | Purpose |
|-------|---------|
| **Persona Reviewer Agent** | Reviews content from diverse demographic perspectives using a random persona from DynamoDB |
| **Validator Agent** | Ensures legal compliance and brand guideline adherence |
| **Finalizer Agent** | Synthesizes persona feedback and validation into final campaign recommendations |

#### 5. Data & Observability Layer
| Component | Purpose |
|-----------|---------|
| **Unified S3 Bucket** | Campaign briefs, status files, and generated reviews |
| **DynamoDB PersonaTable** | 40 diverse persona profiles for review perspectives |
| **Amazon Bedrock** | Claude Sonnet 4.5 model for AI analysis |
| **AgentCore Observability** | OpenTelemetry tracing with session correlation via CloudWatch |

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| **AWS CLI** | v2.x+ | [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| **AWS SAM CLI** | v1.100.0+ | [Install Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) |
| **Node.js** | v18.x+ | [Download](https://nodejs.org/) |
| **npm** | v9.x+ | Included with Node.js |
| **Python** | v3.12+ | [Download](https://www.python.org/downloads/) |
| **Git** | Latest | [Download](https://git-scm.com/) |

> **Note**: Docker is NOT required. The orchestrator Lambda uses a Lambda Layer for dependencies instead of a container image.

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

---

## Dependencies

### Backend Dependencies

#### Lambda Layer (`lambda/layer/requirements.txt`)
```txt
langgraph                    # LangGraph workflow orchestration
langchain-aws                # LangChain AWS integrations (ChatBedrock)
langchain-core               # LangChain core (messages, callbacks)
opentelemetry-api            # OpenTelemetry tracing API
opentelemetry-instrumentation # OpenTelemetry auto-instrumentation
aws-opentelemetry-distro     # AWS OTEL distro for AgentCore observability
```

> **Note**: `lambda/requirements.txt` is intentionally empty — all Python dependencies are in the Lambda Layer to stay within the 250MB deployment limit. `boto3` is provided by the Lambda runtime.

### Frontend Dependencies (Node.js)

```json
{
  "dependencies": {
    "@aws-sdk/client-s3": "^3.958.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-dropzone": "^14.2.3",
    "zustand": "^4.4.1"
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
| AWS CloudFormation | Infrastructure as Code | Free |

---

## Step-by-Step Deployment

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd aws-genai-human-review-langraph
```

### Step 2: Configure AWS Credentials

```bash
aws configure
aws sts get-caller-identity
```

### Step 3: Enable Amazon Bedrock Model Access

1. Open [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Navigate to **Model access** → **Manage model access**
3. Select **Claude Sonnet 4.5** (Anthropic)
4. Click **Request model access**

### Step 4: Set Up DynamoDB Persona Table

```bash
chmod +x scripts/setup_persona_table.sh
./scripts/setup_persona_table.sh
```

### Step 5: Build and Deploy

```bash
# Build (no Docker required)
sam build

# First-time deployment
sam deploy --guided

# Subsequent deployments
sam deploy --no-confirm-changeset
```

SAM deploy prompts:
| Prompt | Value |
|--------|-------|
| Stack Name | `genai-campaign-lg` |
| AWS Region | `us-west-2` |
| Allow SAM CLI IAM role creation | `Y` |

### Step 6: Configure and Deploy Frontend

```bash
# Get stack outputs
STACK_NAME=genai-campaign-lg

API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)

AGENT_API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`CampaignOrchestratorApi`].OutputValue' --output text)

FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' --output text)

# Create .env
cat > .env << EOF
VITE_API_URL=$API_URL
VITE_AGENT_API_URL=$AGENT_API_URL
VITE_AWS_REGION=us-west-2
EOF

# Build and deploy frontend
npm install
npm run build
aws s3 sync dist/ s3://$FRONTEND_BUCKET --delete
```

### Step 7: Access the Application

```bash
aws cloudformation describe-stacks --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' --output text
```

---

## Configuration

### Environment Variables

#### Frontend (.env)
```bash
VITE_API_URL=https://xxxxxxxx.execute-api.us-west-2.amazonaws.com
VITE_AGENT_API_URL=https://xxxxxxxx.execute-api.us-west-2.amazonaws.com/Prod/review-campaign/
VITE_AWS_REGION=us-west-2
```

#### Orchestrator Lambda (set via SAM template)
```yaml
CAMPAIGN_BUCKET: <auto-generated>
AGENT_OBSERVABILITY_ENABLED: "true"
LANGSMITH_OTEL_ENABLED: "true"
OTEL_PYTHON_DISTRO: "aws_distro"
OTEL_PYTHON_CONFIGURATOR: "aws_configurator"
OTEL_EXPORTER_OTLP_PROTOCOL: "http/protobuf"
OTEL_TRACES_EXPORTER: "otlp"
OTEL_PROPAGATORS: "tracecontext,baggage,xray"
OTEL_PYTHON_LOG_CORRELATION: "true"
OTEL_RESOURCE_ATTRIBUTES: "service.name=campaign-review-orchestrator"
OTEL_EXPORTER_OTLP_LOGS_HEADERS: "x-aws-log-group=agents/campaign-review-logs,x-aws-log-stream=default,x-aws-metric-namespace=bedrock-agentcore"
```

### Customization Options

#### Change AI Model
Edit agent files in `lambda/tools/`:
```python
model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"  # Change as needed
```

#### Adjust Lambda Timeout
The orchestrator runs 3 sequential agents (~2-3 min total). Default timeout is 600s (10 min):
```yaml
# template.yaml - CampaignOrchestratorLanggraphFn
Timeout: 600
```

---

## Observability

### Amazon Bedrock AgentCore Observability

The system integrates with AgentCore Observability via OpenTelemetry for end-to-end tracing.

#### How It Works

1. **Auto-instrumentation**: `auto_instrumentation.initialize()` patches boto3 to capture S3, DynamoDB, and Bedrock API calls as spans
2. **Session correlation**: Each invocation creates a unique session ID set via OpenTelemetry baggage (`session.id`)
3. **Manual spans**: LangGraph workflow nodes are wrapped with explicit tracer spans for the full call chain
4. **Lazy tracer**: The tracer is initialized after `auto_instrumentation.initialize()` to ensure proper provider setup

#### Trace Structure

```
campaign_review_workflow (parent span)
  ├── S3.PutObject (write status)
  ├── S3.GetObject (read campaign brief)
  ├── persona_review_node
  │     ├── DynamoDB.GetItem (fetch persona)
  │     ├── chat claude-sonnet-4-5 (generate review)
  │     └── S3.PutObject (save review)
  ├── validation_node
  │     ├── chat claude-sonnet-4-5 (compliance check)
  │     └── S3.PutObject (save validation)
  └── finalizer_node
        ├── chat claude-sonnet-4-5 (synthesize recommendations)
        └── S3.PutObject (save final report)
```

#### Viewing Traces

1. Open **Amazon Bedrock Console** → **AgentCore** → **Observability**
2. Find agent `campaign-review-orchestrator`
3. Click a session to see traces with nested spans, token counts, and latencies

---

## Usage

1. **Open Application**: Navigate to CloudFront URL
2. **Upload Document**: Drag and drop a campaign document (.md, .txt)
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

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Uploads file to S3 with campaign structure |
| `/reviews?campaignId={id}` | GET | Fetches reviews for a specific campaign |
| `/health` | GET | Returns API health status |

---

## Monitoring & Troubleshooting

### View Lambda Logs

```bash
# Orchestrator logs
sam logs -n CampaignOrchestratorLanggraphFn --stack-name genai-campaign-lg --tail

# Upload function logs
sam logs -n UploadFunction --stack-name genai-campaign-lg --tail
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **502 Gateway Error** | Lambda timeout or import error | Check CloudWatch logs for errors |
| **Bedrock Access Denied** | Model not enabled | Enable Claude Sonnet 4.5 in Bedrock console |
| **Reviews Not Loading** | Campaign ID mismatch | Check campaign ID matches between upload and fetch |
| **Finalizer not completing** | Lambda timeout (< 600s) | Ensure orchestrator timeout is 600s in template.yaml |
| **No spans in AgentCore** | Tracer initialized before auto_instrumentation | Ensure `get_tracer()` is used (lazy init) |
| **Sessions showing 0** | Wrong baggage key | Must use `session.id` (dot notation), not `session_id` |
| **Layer too large (>250MB)** | Too many deps in layer | Keep `lambda/requirements.txt` empty; deps only in `lambda/layer/` |

---

## Cleanup

```bash
# Empty S3 buckets first
STACK_NAME=genai-campaign-lg
UNIFIED=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`UnifiedBucket`].OutputValue' --output text)
FRONTEND=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' --output text)

aws s3 rm s3://$UNIFIED --recursive
aws s3 rm s3://$FRONTEND --recursive

# Delete stack
sam delete --stack-name $STACK_NAME

# Delete DynamoDB table
aws dynamodb delete-table --table-name PersonaTable --region us-west-2
```

---

## Project Structure

```
aws-genai-human-review-langraph/
├── lambda/                      # Backend Lambda functions
│   ├── orchestrator.py          # LangGraph orchestrator (handler)
│   ├── langgraph_hooks.py       # Workflow hooks for memory & logging
│   ├── requirements.txt         # Empty (deps in layer)
│   ├── layer/                   # Lambda Layer dependencies
│   │   └── requirements.txt     # langgraph, langchain-aws, otel, etc.
│   ├── tools/                   # AI agent implementations
│   │   ├── revieweragent.py     # Persona reviewer (LangChain + Bedrock)
│   │   ├── validatoragent.py    # Compliance validator (LangChain + Bedrock)
│   │   └── finalizeragent.py    # Finalizer agent (LangChain + Bedrock)
│   ├── utils/                   # Utility modules
│   │   ├── s3.py                # S3 read/write operations
│   │   └── persona_store.py     # In-memory persona ID store
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
│   └── setup_persona_table.sh   # DynamoDB persona table setup
├── template.yaml                # SAM/CloudFormation template
├── samconfig.toml               # SAM deployment configuration
├── package.json                 # Frontend dependencies
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
