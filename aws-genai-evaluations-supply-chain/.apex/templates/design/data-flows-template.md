---
inclusion: manual
---

# Data Flows Document Template

## Purpose

Detailed behavioral specification showing how components interact step by step. This is the companion to `system-architecture.md` — the architecture document defines what exists and why; this document shows how it works in motion.

**Document Objectives**: Illustrate end-to-end interactions via sequence diagrams, document step-level data and error handling, ensure every interface and component from the architecture participates in at least one flow.

---

## Table of Contents

Organize flows by category. Number flows sequentially (1, 2, 3…).

1. [Primary Business Flows](#primary-business-flows)
2. [Authentication and Authorization Flows](#authentication-and-authorization-flows)
3. [Feature-Specific Flows](#feature-specific-flows)
4. [Error Handling Flows](#error-handling-flows)

---

## Template Structure

### Required Flows

At minimum, document:
- Primary business flow (happy path for the core use case)
- Authentication/authorization flow
- One flow per major feature beyond the core use case
- At least one error handling flow showing recovery behavior

### Per-Flow Structure

For each flow, provide all of the following:

**Flow Metadata Block**:
```
**Trigger**: [What initiates this flow]
**Actors**: [All participants — users, components, external systems]
**Outcome**: [What the successful result looks like]
**Requirements**: [Requirement IDs this flow satisfies, e.g., FR-001, NFR-003]
```

**Sequence Diagram** (Mermaid):
- Follow the Mermaid Diagram Guidelines from the apex-architect prompt
- Use `sequenceDiagram` type
- Keep messages single-line (no `<br/>`)
- No self-referencing messages — use `Note over` instead
- Label participants with component name and technology

**Step Details Table**:
| Step | Description | Data | Error Handling |
|------|-------------|------|----------------|

- Every arrow in the sequence diagram must have a corresponding row in the table
- Data column: specify the actual payload (e.g., "JWT + session ID + message JSON"), not vague descriptions
- Error Handling column: specify the concrete behavior (e.g., "401 → redirect to login"), not generic statements like "handle error"

---

## Quality Checklist

**Coverage**:
- Every interface from system-architecture.md Section 5 appears in at least one flow
- Every component from system-architecture.md Section 4 participates in at least one flow
- All flows listed in system-architecture.md Section 6 (Data Flow Summary) are documented here

**Clarity**:
- Each flow has complete metadata (trigger, actors, outcome, requirements)
- Sequence diagrams are readable (no more than 8 participants per diagram)
- Step tables have concrete data and error handling, not vague descriptions

**Consistency**:
- Component names match system-architecture.md exactly
- Protocols and data formats match the Interface Specifications (Section 5)
- Requirements references match functional/non-functional requirements documents

## Anti-Patterns vs Best Practices

| Avoid | Instead |
|-------|---------|
| Only happy path flows | Include auth, error, and feature-specific flows |
| Vague step descriptions ("sends data") | Specific payloads ("JWT + session ID + message JSON") |
| Generic error handling ("handle error") | Concrete behavior ("401 → redirect to Cognito login") |
| Sequence diagrams with 10+ participants | Split into focused diagrams, max 8 participants |
| Flows that don't trace to requirements | Every flow references at least one requirement ID |
| Component names that differ from architecture | Use identical names from system-architecture.md |
