---
inclusion: manual
---

# System Architecture Document Template

## Purpose

Primary high-level design artifact describing:
- what is the purpose of the system
- what problem does it solve 
- how a system satisfies functional and non-functional requirements.

**Document Objectives**: Establish system context, describe components, illustrate behavior via flows, trace requirements, define interfaces.

**Abstraction Level**: This is a high-level design document. Reference AWS services, tools, and frameworks by name but do NOT include implementation-level details such as CDK construct names, SDK package imports, API property names, or library version pinning. Those belong in implementation documentation.

---

## Table of Contents

1. [Executive Summary](#section-1-executive-summary)
2. [Technology Summary](#section-2-technology-summary)
3. [System Context](#section-3-system-context)
4. [Core Components](#section-4-core-components)
5. [Interface Specifications](#section-5-interface-specifications)
6. [Security Architecture](#section-6-security-architecture)
7. [Deployment Architecture](#section-7-deployment-architecture)
8. [Service Limits and Scaling Considerations](#section-8-service-limits-and-scaling-considerations)
9. [Observability](#section-9-observability)

---

## Template Structure

### Section 1: Executive Summary

Concise overview describing: 
- system purpose
- what problem does it solve
- key architectural decisions (3-5 bullets)
- primary technologies
- deployment environment.

### Section 2: Technology Summary

**AWS Services Inventory**:
| Service | Purpose | Configuration | ADR Reference |
|---------|---------|---------------|---------------|

**Implementation Technologies** (when applicable):

| Category | Technology | Scope |
|----------|------------|-------|
| Language | e.g., Python, TypeScript | Backend services, Lambda functions |
| IaC | e.g., Terraform, CDK, CloudFormation | Infrastructure provisioning | 
| Framework | e.g., FastAPI, Express | API layer |

**External Dependencies**:
| Dependency | Purpose | Version/Endpoint |
|------------|---------|------------------|

### Section 3: System Context

**Purpose**: Define system boundary and external entities.

**CRITICAL - What is "External"**:
- **External**: Users, third-party APIs, external services
- **NOT External**: AWS services used to BUILD the system (shown in Component Architecture)

**Required**: External systems list, user/actor identification, trust boundaries.

**Diagram**: System as single box, only truly external actors outside, arrows with interaction labels.

**External Dependencies Table**:
| External Entity | Type | Interaction | Data Exchanged | Criticality |
|----------------|------|-------------|----------------|-------------|

### Section 4: Core Components

**Purpose**: Detail internal components, responsibilities, relationships.

**Required**: Layer Overview diagram + one Component Detail diagram per layer + component catalog.

#### Progressive Zoom Diagram Model

Architecture diagrams use a three-level progressive zoom approach to keep diagrams readable at any complexity:

| Zoom Level | Name | What it shows | Max nodes | Mermaid type |
|------------|------|---------------|-----------|--------------|
| 1 | System Context | System as black box + external actors | 6-8 | `graph TB` |
| 2 | Layer Overview | Architectural layers as opaque boxes, aggregate connections between them | 8-10 | `graph TB` |
| 3 | Component Detail | Individual AWS services/components within ONE layer + connections to adjacent layers | 8-10 | `graph TB` or `graph LR` |

**⛔ CRITICAL — Diagram Complexity Rules**:
- NEVER put all components into a single diagram. If a diagram exceeds 12 nodes or 15 edges, it MUST be decomposed.
- The Layer Overview diagram shows ONLY layer boxes (e.g., "Frontend Layer", "Compute Layer") with aggregate arrows between them. No internal nodes.
- Each layer then gets its own Component Detail diagram showing internal components + connections to immediate adjacent layers only.
- Component Detail diagrams are placed inline within the corresponding layer subsection (e.g., the Frontend Layer Component Detail diagram appears inside Section 4.1).

**Layer Overview Diagram** (required — placed at the top of Section 4):

Shows all architectural layers as single labeled nodes with technology summary in the label (e.g., `Frontend["Frontend Layer\n(CloudFront + S3)"]`). Arrows show aggregate data flow between layers. No subgraphs, no internal components.

**Component Detail Diagrams** (required — one per layer subsection):

Each layer subsection (4.1, 4.2, etc.) includes a focused diagram showing:
- All components within that layer
- Connections to components in immediately adjacent layers (shown as simplified external nodes)
- Maximum 8-10 nodes per diagram

#### [Component Name]

**Component Overview**: For each component provide a brief description of its purpose, responsibilities and dependencies.

**Tech stack**: Recommended technologies, frameworks, AWS Services. Describe briefly which alternatives have been considered and why this one was chosen. This needs to be aligned with the Architecture Decision Record (ADR)

### Section 5: Interface Specifications

**Interface Matrix**:
| Source | Target | Interface Type | Protocol | Authentication | Data Format |
|--------|--------|---------------|----------|----------------|-------------|

### Section 6: Security Architecture

**Required**: Security zones diagram, authentication architecture, authorization model, data protection controls.

**Tables**:
- Authentication: Component, Method, Token Type, Validation
- Authorization: Resource, Actor, Permissions, Enforcement Point
- Data Protection: Data Type, At Rest, In Transit, Access Control
- Network Security Controls: Zone/Boundary, Control Type (SG, NACL, WAF, endpoint policy), Rule Summary

### Section 7: Deployment Architecture

**Purpose**: Document how the system is deployed, network layout, environment strategy, and infrastructure provisioning approach.

**Network Architecture**:
- VPC layout: VPCs, subnets (public/private), availability zone distribution
- Connectivity: VPC endpoints for AWS services, NAT gateways, load balancers
- Service placement: which components run in VPC vs managed/public services
- DNS and service discovery approach (if applicable)

**Network Architecture Table**:
| Component | Network Location | Subnet Type | Connectivity |
|-----------|-----------------|-------------|--------------|
| e.g., Lambda functions | VPC | Private | VPC endpoints for DynamoDB, S3 |
| e.g., Amplify Hosting | Managed (CloudFront) | N/A | Public HTTPS |

**Notes**: For fully managed/serverless architectures where some services cannot be VPC-attached (CloudFront, Amplify, AgentCore), document which services are managed and why VPC placement is not applicable.

**Environment Strategy**:
| Environment | Purpose | Region/AZ | Key Differences from Production |
|-------------|---------|-----------|--------------------------------|

**Infrastructure Provisioning**:
- IaC tool and approach (CDK, CloudFormation, Terraform) — reference ADR
- Deployment method per component (e.g., direct deploy, container image, static assets)
- CI/CD pipeline overview (if applicable)

**Disaster Recovery** (scale to project type):
- POC: Note that DR is out of scope; document what would be lost in a failure
- Production: RTO/RPO targets, backup strategy, failover approach

**Notes**: Keep this proportional to the project. A POC needs a paragraph; a production multi-region system needs a full environment topology. Do not over-engineer for POC/MVP.

### Section 8: Service Limits and Scaling Considerations

**Purpose**: Document AWS service limits relevant to the architecture and mitigation strategies.

**Service Limits Table** (include only services with medium or high risk):
| Service | Limit | Default Value | Adjustable | Estimated Usage | Risk | Mitigation |
|---------|-------|---------------|------------|-----------------|------|------------|

**Risk Levels**: Low (<50% of limit), Medium (50-80%), High (>80%)

**Notes**: Include only limits that could realistically constrain the system. Reference research files for full limits inventory.

### Section 9: Observability

**Purpose**: Document monitoring, logging, tracing, and alerting strategy.

**Monitoring Strategy Table**:
| Category | Tool/Service | What is Monitored | Alert Threshold |
|----------|-------------|-------------------|-----------------|
| Metrics | e.g., CloudWatch | e.g., Error rate, latency | e.g., >5% errors over 5 min |
| Logging | e.g., CloudWatch Logs | e.g., Application logs, access logs | — |
| Tracing | e.g., X-Ray, OTEL | e.g., Request traces | — |
| Alerting | e.g., SNS, PagerDuty | e.g., Alarm notifications | — |

**Incident Response Basics** (scale to project type):
- Detection mechanism and notification channel
- Escalation path (team channel for POC, on-call rotation for production)
- Common failure scenarios and expected response

**Backup and Recovery** (if not covered in Deployment Architecture):
- Data at risk and backup approach
- RTO/RPO targets

**Notes**: For POC/MVP, a brief strategy with CloudWatch basics is sufficient. Do not add enterprise observability patterns unless explicitly required by NFRs.


---

## Quality Checklist

**Completeness**: Executive summary, system context diagram, all components documented, interfaces specified, service limits for critical services, security architecture, deployment architecture, observability strategy, requirements traceability. Data flows documented in companion `data-flows.md`.

**Clarity**: Readable diagrams, clear non-overlapping responsibilities, data shown at each flow step.

**Consistency**: Component names consistent across diagrams, interfaces match flows, tech aligns with ADRs.

**Implementability**: Sufficient detail for dev team, unambiguous boundaries, clear contracts, actionable security controls.

---

## Anti-Patterns vs Best Practices

| Avoid | Instead |
|----------|-----------|
| Vague descriptions ("handles business logic") | Specific responsibilities per component |
| Missing external dependencies | Complete system context diagram with all external entities |
| Inconsistent naming across sections | Same component names in diagrams, tables, and prose |
| Missing security boundaries | Clear trust zones in security architecture diagram |
| Single monolithic diagram with all components | Progressive zoom: layer overview + per-layer detail diagrams |
| Sections without tables or diagrams | Every section uses its prescribed table format |
| Deployment/observability detail mismatched to project type | Scale sections 7-9 proportionally (paragraph for POC, full topology for production) |
