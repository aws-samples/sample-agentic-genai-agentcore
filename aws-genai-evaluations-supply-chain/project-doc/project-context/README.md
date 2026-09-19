<p align="center">
  <img src="https://img.shields.io/badge/AWS-AgentCore_Runtime-FF9900?style=for-the-badge&logo=amazonaws" alt="AWS AgentCore" />
  <img src="https://img.shields.io/badge/AWS-AgentCore_Evaluations-FF9900?style=for-the-badge&logo=amazonaws" alt="AWS AgentCore Evaluations" />
  <img src="https://img.shields.io/badge/MCP-Tools-0ea5e9?style=for-the-badge" alt="MCP" />
  <img src="https://img.shields.io/badge/Strands-Agents-cc785c?style=for-the-badge" alt="Strands Agents" />
  <img src="https://img.shields.io/badge/Terraform-IaC-7b42bc?style=for-the-badge&logo=terraform" alt="Terraform" />
</p>

# 📦 Building helpful, accurate and explainable multi-agent systems on AWS using Amazon Bedrock AgentCore Evaluations

A multi-agent supply chain optimization system built with **Strands SDK**, **Amazon Bedrock AgentCore**, and **Amazon Bedrock AgentCore Evaluations**. An orchestrator agent delegates to four specialized sub-agents — Optimization, Distribution, Routing, and Analytics — each backed by MCP tools that call mock REST APIs serving supply chain data.

We focus specifically on explainability as a first-class evaluation dimension. We demonstrate how built-in evaluators can assess general response clarity, while custom evaluators are used to verify that agents explicitly articulate decision rationale, reference supporting data or tool outputs, and explain tradeoffs such as cost versus service level. By combining these evaluators, we show how AgentCore Evaluations can move beyond surface-level response quality and provide structured, measurable insights into how and why agents arrive at their decisions.

---

## 🏢 Use Case: Northstar Retail Group

**Northstar Retail Group** is a fictitious multinational retailer operating e-commerce channels, regional fulfillment centers, distribution centers, and thousands of physical stores. Northstar experiences frequent inventory imbalances: some regions face stockouts during promotions, while others carry excess inventory. Transportation teams must balance delivery speed, carrier capacity, and cost.

The company needs an agentic assistant that helps planners:
- Optimize inventory allocation across locations
- Recommend distribution adjustments to reduce stockout/overstock risk
- Analyze inventory health and supply chain diagnostics
- Simulate routing and fulfillment scenarios with carrier options

### Supply Chain Schema

The mock data layer serves four API endpoints backed by canned responses. The data is structured around three core entities and four response types.

**Reference Entities:**

| Entity | Records | Columns |
|--------|---------|---------|
| Locations | 9 | location_id, name, location_type (fulfillment_center / store / digital_channel), region |
| Products | 8 | product_id (prod-001 through prod-008) |
| Carriers | 3 | carrier_name (FastShip Express, EcoFreight, CrossCountry Logistics) |

**API Response Tables:**

| Endpoint | Records | Key | Columns |
|----------|---------|-----|---------|
| Optimization | 8 | product_id | product_id, location, time_horizon, demand_forecast, recommended_inventory_level, confidence, budget_limit, budget_used, warehouse_capacity, warehouse_utilization, inventory_holding_cost |
| Distribution | 8 (18 suggestions) | product_id | product_id, source_location, destination_location, transfer_quantity |
| Routing | 10 (22 route options) | (origin, destination) | origin, destination, carrier_name, estimated_transit_days, estimated_cost |
| Analytics | 3 query types (21 rows) | query_type | inventory_turnover: product_id, location_id, turnover_rate, period; demand_trends: product_id, month, units_sold, trend; shipment_performance: carrier, on_time_pct, avg_transit_days, total_shipments |

**Relationships:**

```
Product ──→ Optimization (1:1 — one response per product)
Product ──→ Distribution (1:N — 1–3 rebalancing suggestions per product)
              └── references Location as source and destination
Location pair ──→ Routing (1:N — 1–3 carrier options per origin/destination)
              └── references Carrier
Carrier ──→ Analytics.shipment_performance (appears as row)
Product ──→ Analytics.inventory_turnover, demand_trends (appears as row)
```

See [`supply_chain_data/SCHEMA.md`](supply_chain_data/SCHEMA.md) for full sample data.

---

## 🧩 Solution Overview

The solution is a **multi-agent supply chain decisioning system** with the following components:

- **Orchestrator Agent** — receives the planner's request and delegates work to specialized agents exposed as tools
- **Optimization Agent** — calls MCP tools backed by mock API Gateway REST interfaces that return demand forecasts and inventory optimization decisions
- **Distribution Agent** — calls recommendation APIs to suggest inventory rebalancing across fulfillment centers, stores, and digital channels
- **Routing Agent** — calls logistics APIs to recommend carrier and route options between locations
- **Analytics Agent** — queries supply chain data to answer diagnostics questions

Each agent runs on **Amazon Bedrock AgentCore Runtime** with **AgentCore Memory** (semantic conversational memory) and **AgentCore Observability** (CloudWatch + X-Ray trace delivery) enabled.

**Amazon Bedrock AgentCore Evaluations** is used in on-demand mode to evaluate selected sessions and traces after agent execution. Built-in evaluators assess general quality dimensions (helpfulness, task completion), while custom evaluators assess supply-chain-specific behavior:
- **Optimization Constraint Satisfaction** — budget, inventory, and warehouse capacity constraint adherence when invoking the Optimizer endpoint
- **Distribution Groundedness** — whether recommendations are grounded in inventory/demand data and improve stockout/overstock risk when invoking the distribution endpoint

---

## 🏗️ Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  VPC (Private — no internet egress)                                         ║
║                                                                             ║
║  ┌───────────────────────────────────────────────────────────────────────┐  ║
║  │  AgentCore Runtime — Supply Chain Orchestrator (Strands + Claude)      │  ║
║  │  protocol = HTTP                                                      │  ║
║  │                                                                       │  ║
║  │    ┌─────────────────────┐  ┌──────────────────────────┐              │  ║
║  │    │ Optimization Agent  │  │ Distribution Agent       │              │  ║
║  │    └─────────────────────┘  └──────────────────────────┘              │  ║
║  │    ┌─────────────────────┐  ┌──────────────────────────┐              │  ║
║  │    │ Routing Agent       │  │ Analytics Agent          │              │  ║
║  │    └─────────────────────┘  └──────────────────────────┘              │  ║
║  │                                                                       │  ║
║  │  ┌──────────────────┐  ┌────────────────────┐                         │  ║
║  │  │ AgentCore Memory │  │ AgentCore          │                         │  ║
║  │  │ (semantic)       │  │ Observability      │                         │  ║
║  │  └──────────────────┘  └────────────────────┘                         │  ║
║  └──────────────────────────────┬────────────────────────────────────────┘  ║
║                                 │ MCP over HTTPS                            ║
║                                 ▼                                           ║
║  ┌───────────────────────────────────────────────────────────────────────┐  ║
║  │  AgentCore Runtime — MCP Tools Server (FastMCP)                       │  ║
║  │  protocol = MCP                                                       │  ║
║  │                                                                       │  ║
║  │  Tools: get_optimization_data, get_distribution_data,                 │  ║
║  │         get_routing_data, get_analytics_data                          │  ║
║  └──────────────────────────────┬────────────────────────────────────────┘  ║
║                                 │ HTTPS                                     ║
║                                 ▼                                           ║
║  ┌───────────────────────────────────────────────────────────────────────┐  ║
║  │  Northstar Retail API (REST API Gateway + Lambda)                     │  ║
║  │                                                                       │  ║
║  │  GET /optimization  GET /distribution  GET /routing  GET /analytics   │  ║
║  │       ↓                   ↓                 ↓              ↓          │  ║
║  │  [Lambda Fn]         [Lambda Fn]       [Lambda Fn]    [Lambda Fn]     │  ║
║  │       └───────────────────┴─────────────────┴──────────────┘          │  ║
║  │                    Shared Layer: supply_chain_mock                     │  ║
║  └───────────────────────────────────────────────────────────────────────┘  ║
║                                                                             ║
║  VPC Endpoints: bedrock-runtime │ bedrock-agentcore │ logs │ xray           ║
║                 sts │ ecr.api │ ecr.dkr │ s3 (gateway)                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

  ┌───────────────────────────────────────────────────────────────────────┐
  │  AgentCore Evaluations (on-demand, post-execution)                    │
  │                                                                       │
  │  Built-in: Correctness, GoalSuccessRate                               │
  │  Custom:   Optimization Constraint Satisfaction                       │
  │            Distribution Groundedness & Risk Impact                     │
  └───────────────────────────────────────────────────────────────────────┘
```

### Key design decisions

| Decision | Why |
|----------|-----|
| **Orchestrator + sub-agent pattern** | Each domain (optimization, distribution, routing, analytics) scales and evolves independently |
| **Separate MCP Tools runtime** | Supply chain data tools are reusable across all agents via standard MCP protocol |
| **Northstar Retail mock API** | Lambda + API Gateway provides realistic REST endpoints without external dependencies |
| **VPC isolation** | All agent-to-agent and agent-to-service traffic stays private via VPC endpoints |
| **AgentCore Memory** | Semantic memory strategy retains key facts across planner conversations |
| **AgentCore Evaluations** | Custom LLM-as-judge evaluators validate domain-specific correctness post-execution |
| **Full Terraform IaC** | One `terraform apply` provisions the entire stack — reproducible and version-controlled |

---

## 📁 Project Structure

```
.
├── agents/supply_chain/                 Supply Chain orchestrator agent
│   ├── orchestrator_agent.py            Main orchestrator logic (Strands + Claude)
│   ├── entrypoint/                      HTTP entrypoint (BedrockAgentCoreApp)
│   ├── tools/                           Sub-agent definitions
│   │   ├── optimization_agent.py
│   │   ├── distribution_agent.py
│   │   ├── routing_agent.py
│   │   └── analytics_agent.py
│   └── utils/                           MCP client + agent helpers
│
├── mcp/                                 MCP Tools Server (FastMCP)
│   └── mcp_tools_server.py             Supply chain tools calling Northstar API
│
├── northstar_retail/                    Lambda handlers for mock API
│   ├── optimization/handler.py
│   ├── distribution/handler.py
│   ├── routing/handler.py
│   └── analytics/handler.py
│
├── supply_chain_data/                   Shared mock data package (Lambda layer)
│   ├── schema.py                        Pydantic models for domain entities
│   ├── canned_data.py                   Static response data
│   └── serialization.py                 Serialization utilities
│
├── evaluators/                          AgentCore Evaluations
│   ├── supply_chain_evaluators.ipynb    Notebook: create & run custom evaluators
│   ├── optimization_constraint_metric.json
│   ├── distribution_groundedness_metric.json
│   └── lambda/                          Evaluator Lambda (HTTP API Gateway)
│       ├── handler.py
│       └── metrics/
│
├── terraform/                           Infrastructure as Code
│   ├── versions.tf                      Terraform + provider versions
│   ├── variables.tf                     Inputs (vpc_id, AZs, stack_name)
│   ├── locals.tf                        Data sources + computed values
│   ├── network.tf                       Security groups + VPC endpoints
│   ├── iam.tf                           AgentCore execution + CodeBuild roles
│   ├── ecr.tf                           ECR repos for agent containers
│   ├── s3.tf                            Source bucket + ZIP archives
│   ├── codebuild.tf                     CodeBuild projects (ARM64 Docker)
│   ├── runtime_mcp.tf                   MCP Tools AgentCore runtime
│   ├── runtime_supply_chain.tf          Supply Chain orchestrator runtime
│   ├── northstar_retail.tf              Lambda functions + REST API Gateway
│   ├── memory.tf                        AgentCore Memory + semantic strategy
│   ├── observability.tf                 CloudWatch + X-Ray trace delivery
│   ├── evaluators.tf                    Evaluator Lambda + HTTP API Gateway
│   ├── outputs.tf                       Runtime ARNs, API URLs, memory ARN
│   └── terraform.tfvars.example         Template for local config
│
└── README.md                            ← you are here
```

---

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured (`aws sts get-caller-identity` works)
- Terraform ≥ 1.5
- Bedrock model access enabled in `us-east-1` (Claude Sonnet)
- An existing VPC with private subnets in supported AZs

### Deploy

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: set vpc_id and runtime_subnet_azs

terraform init
terraform apply
```

Outputs include runtime ARNs, Northstar Retail API URL, evaluator API URL, and memory ARN.

### Tear down

```bash
terraform destroy
```

---

## 🧪 Evaluations

The project includes custom AgentCore Evaluators for assessing supply-chain-specific agent behavior. Evaluators are managed via an HTTP API Gateway backed by a Lambda function.

### Custom Evaluators

| Evaluator | What it assesses |
|-----------|-----------------|
| **Optimization Constraint Satisfaction** | Whether optimization recommendations satisfy budget limits, inventory coverage (demand forecast), and warehouse capacity constraints |
| **Distribution Groundedness & Risk Impact** | Whether distribution rebalancing recommendations are grounded in inventory/demand data and reduce stockout/overstock risk |

**Optimization Constraint Satisfaction** evaluates whether a *stocking recommendation* (e.g., "stock 1,500 units of prod-001") satisfies three constraints simultaneously:
- Budget: does the incremental holding cost fit within remaining budget (budget_limit - budget_used)?
- Inventory: is the recommended level ≥ demand forecast (avoids stockout) and ≤ 2× demand (avoids excess)?
- Capacity: does the recommended level fit within available warehouse space?

Scored on a 5-point scale from Very Good (all constraints satisfied with >20% headroom) to Very Poor (multiple constraints violated).

**Distribution Groundedness & Risk Impact** evaluates whether a *transfer recommendation* (e.g., "move 200 units from East FC to NYC Store") is factually supported by the data the agent received. It checks two dimensions:
- Groundedness: does the source actually have enough inventory to give away? Does the destination have capacity to receive? Is the transfer quantity proportional to demand?
- Risk Impact: does the transfer reduce stockout risk at the destination AND reduce overstock risk at the source, without creating new problems?

These evaluators are complementary — the optimization evaluator checks stocking decisions against budget/capacity/demand constraints, while the groundedness evaluator checks transfer decisions against actual inventory data. Together they validate both "what to stock" and "where to move it."

See [`evaluators/OPTIMIZATION_CONSTRAINT_EVALUATOR.md`](evaluators/OPTIMIZATION_CONSTRAINT_EVALUATOR.md) and [`evaluators/DISTRIBUTION_GROUNDEDNESS_EVALUATOR.md`](evaluators/DISTRIBUTION_GROUNDEDNESS_EVALUATOR.md) for detailed scoring examples.

### Additional Custom Evaluators (Layer 2 — Business Accuracy)

| Evaluator | Agents | What it checks |
|-----------|--------|----------------|
| **Plan Coherence** | Orchestrator | Did it combine sub-agent outputs into a valid, non-contradictory recommendation? |
| **Route Feasibility** | Routing | Does the route respect delivery window, cost, carrier capacity, and region constraints? Does expected delivery meet target service level? |
| **SQL Correctness** | Analytics | Does the query match user intent? Is the response supported by query results? |

### Explainability Evaluators (Layer 3 — Trust & Auditability)

These are cross-cutting evaluators applied independently across agents. They assess whether agents articulate reasoning, cite evidence, explain constraints and trade-offs, and disclose assumptions — measured separately from accuracy so teams can distinguish unexplainable-but-correct responses from well-explained-but-wrong ones.

| Evaluator | Agents | What it checks |
|-----------|--------|----------------|
| **Decision Rationale Quality** | All | Did the agent explain why it made the recommendation? |
| **Evidence Attribution** | Analytics, Distribution, Routing | Did it cite the data fields, API response, or SQL result used? |
| **Constraint Reasoning** | Optimization, Routing | Did it explain which constraints shaped the final answer? |
| **Trade-off Explanation** | Optimization, Distribution, Routing | Did it explain cost vs. service level vs. inventory risk? |
| **Tool-use Explainability** | Orchestrator | Did it explain why each sub-agent or MCP tool was invoked? |
| **Assumption Disclosure** | All | Did it clearly state assumptions when data was incomplete? |

---

## 🖥️ Test Client

The `test_client/` folder contains a Python script that invokes the deployed Supply Chain agent with 20 sample queries (5 per sub-agent) to validate end-to-end functionality. Each category runs as a multi-turn session, and session IDs are printed at the end for use with the evaluators API.

### Prerequisites

- The infrastructure must be fully deployed (`terraform apply` completed successfully)
- AWS CLI configured with credentials that can invoke AgentCore runtimes
- Python 3.10+ with `boto3` installed

### Setup

```bash
cd test_client
pip install -r requirements.txt
```

### Get the Runtime ARN

```bash
cd terraform
terraform output supply_chain_arn
# Output: "arn:aws:bedrock-agentcore:us-east-1:689069515280:runtime/supply_chain_orchestrator_agent-YK657xBNWi"
```

### Run All Queries (20 total, 4 sessions)

```bash
cd test_client
python test_agent.py --runtime-arn "arn:aws:bedrock-agentcore:us-east-1:689069515280:runtime/supply_chain_orchestrator_agent-YK657xBNWi" --region us-east-1
```

### Run Specific Sub-Agent Categories

```bash
# Only optimization queries (1 session, 5 turns)
python test_agent.py --runtime-arn "<runtime-arn>" --category optimization

# Only routing and analytics (2 sessions, 5 turns each)
python test_agent.py --runtime-arn "<runtime-arn>" --category routing analytics
```

### Sample Queries

| Sub-Agent | Example Query |
|-----------|--------------|
| Optimization | "What is the optimal inventory level for prod-001 over the next 30 days?" |
| Distribution | "Recommend inventory transfers to rebalance prod-006 to reduce overstock risk" |
| Routing | "What are the shipping options from the East Fulfillment Center to the NYC store?" |
| Analytics | "Show me inventory turnover rates across all products for Q1 2025" |

### Output

The test client prints each query and the full agent response. At the end it prints all session IDs for use with the evaluators:

```
======================================================================
  SESSIONS CREATED
======================================================================
  Optimization: test-optimization-a1b2c3d4-...
  Distribution: test-distribution-e5f6a7b8-...
  Routing: test-routing-c9d0e1f2-...
  Analytics: test-analytics-a3b4c5d6-...

  Use these session IDs with the evaluators API to assess response quality.
======================================================================
```

---

### Test Evaluator Client

The `test_evaluators/` folder contains scripts to run evaluations against agent sessions. Evaluations run asynchronously — results are saved as markdown files in S3.

#### Prerequisites

- You must run the **Test Client** (above) first to generate agent sessions with traces
- Note down the session IDs printed at the end of the test client run — you'll need them for the evaluator
- Wait 3-5 minutes after running the test client for traces to propagate to CloudWatch

#### Setup

```bash
cd test_evaluators
pip install -r requirements.txt
```

#### Get the API URL

```bash
cd terraform
terraform output evaluators_api_url
```

#### Step 1: Create Custom Evaluators

```bash
python test_evaluator.py --api-url "https://<evaluators-api-url>" create
```

This registers both custom evaluators and prints their IDs. Save these for use with the `run` command.

#### Step 2: Run Evaluations

Pass a comma-separated list of evaluator IDs (custom and/or built-in). At least 1 is required:

```bash
# Run custom + built-in evaluators
python test_evaluator.py --api-url "https://<evaluators-api-url>" run \
    --agent-id "supply_chain_orchestrator_agent-YK657xBNWi" \
    --session-id "<session-id-from-test-client>" \
    --evaluators "sc_optimization_constraint-abc123,sc_distribution_groundedness-def456,Builtin.Correctness,Builtin.GoalSuccessRate"

# Run only built-in evaluators
python test_evaluator.py --api-url "https://<evaluators-api-url>" run \
    --agent-id "supply_chain_orchestrator_agent-YK657xBNWi" \
    --session-id "<session-id>" \
    --evaluators "Builtin.Correctness,Builtin.GoalSuccessRate"

# Run only one custom evaluator
python test_evaluator.py --api-url "https://<evaluators-api-url>" run \
    --agent-id "supply_chain_orchestrator_agent-YK657xBNWi" \
    --session-id "<session-id>" \
    --evaluators "sc_optimization_constraint-abc123"
```

The API returns 202 immediately. Results are saved asynchronously to S3 at:
```
s3://<agent-source-bucket>/evaluations/<session-id>/<timestamp>/EvaluationResults.md
```

#### Step 3: Delete Evaluators (cleanup)

```bash
python test_evaluator.py --api-url "https://<evaluators-api-url>" delete \
    --evaluator-ids "sc_optimization_constraint-abc123,sc_distribution_groundedness-def456"
```

---

## 🧪 Testing

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v
```


---

## 📚 Further Reading

- [terraform/README.md](terraform/README.md) — Terraform-specific deploy notes
- [Amazon Bedrock AgentCore Docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [Strands Agents](https://strandsagents.com)
- [Model Context Protocol](https://modelcontextprotocol.io)

---

<p align="center">
  Built with
  <a href="https://docs.aws.amazon.com/bedrock-agentcore/">Amazon Bedrock AgentCore</a> ·
  <a href="https://strandsagents.com">Strands Agents</a> ·
  <a href="https://modelcontextprotocol.io">MCP</a> ·
  <a href="https://terraform.io">Terraform</a>
</p>
