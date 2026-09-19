# AgentCore AGUI Demo — Terraform

Full end-to-end Terraform for the AGUI collaborative document generator on
AWS Bedrock AgentCore Runtime.

## What this deploys

```
                         ┌─────────────┐
                Browser  │ CloudFront  │
                  │   ──▶│ + S3 (SPA)  │
                  │      └─────────────┘
           Cognito JWT
                  │
                  ▼
         ┌────────────────────┐
         │ AgentCore Service  │
         └────────┬───────────┘
                  │
  ╔═══════════════▼═══════════════════════════════════╗
  ║  Existing VPC (vpc-xxxxx)                           ║
  ║                                                     ║
  ║  ┌────────────────────┐     ┌────────────────────┐ ║
  ║  │ AGUI Runtime        │────▶│ MCP Tools Runtime   │ ║
  ║  │ (Strands + Claude)  │ MCP │ (FastMCP)           │ ║
  ║  └────────────────────┘     └────────────────────┘ ║
  ║            │                                         ║
  ║            ├──▶ bedrock-runtime VPCE                ║
  ║            ├──▶ cognito-idp VPCE                    ║
  ║            ├──▶ bedrock-agentcore VPCE              ║
  ║            ├──▶ logs / xray / sts VPCE              ║
  ║            ├──▶ ecr.api / ecr.dkr VPCE              ║
  ║            └──▶ s3 Gateway VPCE                     ║
  ╚══════════════════════════════════════════════════════╝
```

Resources created:

| Category | Resources |
|---|---|
| **Networking** | 2 SGs, 8 Interface VPC endpoints, 1 S3 Gateway endpoint |
| **Identity** | Cognito User Pool, App Client, Demo User |
| **IAM** | AgentCore execution role, CodeBuild service role |
| **Container** | 2 ECR repos (MCP + AGUI), 2 CodeBuild projects |
| **Source staging** | 1 S3 bucket (versioned), 2 ZIP archives |
| **AgentCore** | MCP runtime (`protocol=MCP`), AGUI runtime (`protocol=AGUI`) |
| **Frontend** | S3 bucket, CloudFront distribution (OAC), auto build+deploy |

## Prerequisites

1. **Terraform ≥ 1.6** (`tfenv install 1.9.0`)
2. **AWS CLI** configured with credentials (`aws sts get-caller-identity`)
3. **Docker** not required locally — CodeBuild does it
4. **Node.js + npm** (for frontend build, only if `deploy_frontend = true`)
5. **An existing VPC** that covers at least two of these AZs: `us-east-1c`, `us-east-1d`

## Deploy

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars: set vpc_id and runtime_subnet_azs

terraform init
terraform plan
terraform apply
```

Total deploy time: **~8–12 minutes** (mostly CodeBuild image builds + AgentCore CREATE).

## What you'll see

```
Outputs:

agui_runtime_arn   = "arn:aws:bedrock-agentcore:us-east-1:030540333189:runtime/agui_document_agent-XXXX"
mcp_runtime_arn    = "arn:aws:bedrock-agentcore:us-east-1:030540333189:runtime/mcp_tools_server-XXXX"
cognito_client_id  = "1n76a3qs3k4jkeudoei8q9tkcb"
frontend_url       = "https://dXXXXXXX.cloudfront.net"
```

Open `frontend_url` in a browser, sign in with the demo credentials, and chat.

## Why certain AZs?

AgentCore runtime supports only physical AZs `use1-az1`, `use1-az2`, `use1-az4`.
The `cognito-idp` interface VPC endpoint supports only `us-east-1a`, `us-east-1c`,
`us-east-1d`. The intersection is **`us-east-1c`** and **`us-east-1d`** — so we
use those by default. Adjust `runtime_subnet_azs` if deploying in another region.

## Cost (us-east-1, approximate)

| Item | Monthly |
|---|---|
| 8 Interface VPC endpoints × 2 AZs × $7.30 | ~$117 |
| 2 AgentCore runtimes (idle) | pay per invocation |
| CloudFront + S3 frontend | < $1 |
| Cognito (< 50k MAU free) | $0 |
| ECR storage (< 1GB) | ~$0.10 |
| **Total (idle)** | **~$118/month** |

The VPC endpoints are the largest fixed cost. For demo/testing you can set
`network_mode = "PUBLIC"` in `runtime_*.tf` and delete `network.tf` to avoid them.

## Layout

```
terraform/
├── versions.tf           Providers
├── variables.tf          Inputs
├── locals.tf             Data sources + computed values
├── network.tf            SGs + 9 VPC endpoints
├── cognito.tf            User pool, client, demo user
├── iam.tf                Execution + CodeBuild roles
├── ecr.tf                2 ECR repos
├── s3.tf                 Source-code bucket + ZIPs
├── codebuild.tf          2 CodeBuild projects + triggers
├── runtime_mcp.tf        MCP tools AgentCore runtime
├── runtime_agui.tf       AGUI agent AgentCore runtime (depends on MCP)
├── frontend.tf           S3 + CloudFront + auto-deploy
├── outputs.tf
├── buildspec.yml         CodeBuild spec (shared)
├── scripts/
│   └── build-image.sh    Triggers CodeBuild and waits
└── agents/
    ├── mcp/              MCP runtime source (Dockerfile + code)
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── mcp_tools_server.py
    └── agui/             AGUI runtime source
        ├── Dockerfile
        ├── requirements.txt
        └── agui_agent.py
```

## Updating code

Edit the Python files under `agents/mcp/` or `agents/agui/`, then:

```bash
terraform apply
```

The `archive_file` data source re-zips, the MD5 changes, which triggers
`null_resource.build_*`, which runs CodeBuild, pushes a new image, and updates
the runtime in place.

## Cleanup

```bash
terraform destroy
```

⚠ This deletes everything including the Cognito user pool and all runtime
history. The existing VPC is **not** touched.

## Differences from the upstream `basic-runtime` sample

| Sample | This |
|---|---|
| 1 agent | 2 agents (AGUI + MCP), wired together |
| Public network | VPC-isolated with 9 VPC endpoints |
| No auth | Cognito JWT authorizer on both runtimes |
| No frontend | React SPA on CloudFront with auto-generated `config.ts` |
| `protocol = DEFAULT` | `MCP` and `AGUI` protocols |
