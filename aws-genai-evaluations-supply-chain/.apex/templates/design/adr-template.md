---
inclusion: manual
---

# Architecture Decision Record Template

## Purpose

This template ensures ADRs include documented research evidence for ALL alternatives considered, preventing decisions based on familiarity rather than evidence.

---

## ADR Template

```markdown
# ADR-XXX: [Decision Title]

**Status**: Proposed | Accepted | Deprecated | Superseded  
**Date**: [YYYY-MM-DD]  
**Decision Maker**: [Role/Name]  
**Category**: [Compute | Database | API Layer | Storage | AI/ML | Authentication | Messaging | Integration]

---

## Context

[Describe the problem, requirements, and constraints that led to this decision]

- **Problem Statement**: [What problem are we solving?]
- **Requirements**: [Which requirements drive this decision? Reference FR-XXX, NFR-XXX]
- **Constraints**: [Technical, budget, timeline, team expertise constraints]

---

## Decision

**We will use [Selected Service/Technology] for [capability/purpose].**

[Brief explanation of what this means for the architecture]

---

## Research Conducted

### Option A: [Selected Service] ✓ SELECTED

**Research Confidence**: High | Medium | Low

| Source | URL | Key Finding |
|--------|-----|-------------|
| [AWS User Guide] | [URL] | [What was learned] |
| [AWS API Reference] | [URL] | [What was learned] |
| [AWS Blog/What's New] | [URL] | [What was learned] |

**Capabilities Verified**:
- [Capability 1] - [Evidence source]
- [Capability 2] - [Evidence source]

### Option B: [Alternative Service]

**Research Confidence**: High | Medium | Low

| Source | URL | Key Finding |
|--------|-----|-------------|
| [AWS User Guide] | [URL] | [What was learned] |
| [AWS API Reference] | [URL] | [What was learned] |
| [AWS Blog/What's New] | [URL] | [What was learned] |

**Capabilities Verified**:
- [Capability 1] - [Evidence source]
- [Capability 2] - [Evidence source]

### Option C: [Additional Alternative] (if applicable)

[Same structure as above]

---

## Capability Mapping

| Requirement | Option A Capability | Evidence | Option B Capability | Evidence |
|-------------|---------------------|----------|---------------------|----------|
| [FR-001: Requirement] | [Capability] | [URL] | [Capability] | [URL] |
| [FR-002: Requirement] | [Capability] | [URL] | [Capability] | [URL] |
| [NFR-001: Requirement] | [Capability] | [URL] | [Capability] | [URL] |

---

## Unknowns and Assumptions

| Item | Type | Impact | Mitigation |
|------|------|--------|------------|
| [Item description] | Unknown / Assumption | High / Medium / Low | [How to address] |

---

## Counter-Argument Analysis

### Q1: What specific evidence would make me choose the alternative instead?

[Answer with specific criteria - e.g., "If Option B supported feature X with <100ms latency, it would be preferable because..."]

### Q2: Is there a managed/integrated AWS service that does this better?

[Answer with specific service evaluation - e.g., "Searched for 'AWS managed [capability]' and found [Service]. Evaluated and rejected because..."]

### Q3: What am I NOT seeing about the alternative that might make it superior?

[Honest assessment of potential blind spots - e.g., "Option B may have better integration with [other service] that I haven't fully explored..."]

---

## Alternative Consideration Checklist

- [ ] Searched for managed/integrated AWS services for this capability domain
- [ ] Researched minimum 2 viable alternatives with equal depth
- [ ] Documented specific AWS documentation URLs for each alternative
- [ ] Created capability mapping with evidence sources
- [ ] Documented unknowns and assumptions
- [ ] Assigned research confidence level to each alternative
- [ ] Completed Counter-Argument analysis

---

## Alternatives Considered

### Option B: [Alternative Service] - REJECTED

**Why Rejected**: [Specific reasons with evidence]

**Pros**:
- [Pro 1]
- [Pro 2]

**Cons**:
- [Con 1 - with evidence source]
- [Con 2 - with evidence source]

### Option C: [Additional Alternative] - REJECTED (if applicable)

[Same structure]

---

## Rationale

[Structured rationale using the format:]

"In the context of [use case/requirement], facing [constraint], we decided for [Option A] and rejected [Option B, C], to achieve [desired outcomes], accepting [trade-offs], because [evidence-based reasoning]."

---

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Trade-off 1]
- [Trade-off 2]

### Neutral
- [Implication 1]

---

## Related Decisions

- **Depends On**: [ADR-XXX]
- **Influences**: [ADR-YYY]
- **Related**: [ADR-ZZZ]

---

## Research Sources

1. [Source 1 Title] - [URL]
2. [Source 2 Title] - [URL]
3. [Source 3 Title] - [URL]
```

---

## Additional Section: Managed Service Evaluation

**Include this section when choosing a custom implementation over an AWS managed service:**

```markdown
## Managed Service Evaluation

### Managed Service Considered: [Service Name]

**Description**: [What the managed service does]

**Documentation Reviewed**:
- [URL 1] - [Key finding]
- [URL 2] - [Key finding]

### Capability Gap Analysis

| Requirement | Managed Service Capability | Gap | Evidence |
|-------------|---------------------------|-----|----------|
| [Requirement] | [What it provides] | [What's missing] | [URL] |

### Trade-off Analysis

| Factor | Managed Service | Custom Implementation |
|--------|-----------------|----------------------|
| Operational Complexity | [Assessment] | [Assessment] |
| Development Effort | [Assessment] | [Assessment] |
| Flexibility | [Assessment] | [Assessment] |
| Cost at Scale | [Assessment] | [Assessment] |

### Decision Justification

[Explain why the capability gap justifies the additional operational complexity of a custom implementation]
```

---

## Research Confidence Level Definitions

| Level | Definition | Action Required |
|-------|------------|-----------------|
| **High** | Official AWS documentation reviewed; capability verified with specific feature references and examples | None - proceed with confidence |
| **Medium** | AWS documentation reviewed but some capabilities inferred or based on general descriptions | Document assumptions; validate during implementation |
| **Low** | Limited documentation found; relying on general knowledge or third-party sources | ⚠️ Additional research REQUIRED before finalizing decision |

---

## Quality Checklist

Before finalizing an ADR, verify:

- [ ] Research conducted for ALL alternatives (not just selected option)
- [ ] Each alternative has specific AWS documentation URLs
- [ ] Capability mapping includes evidence sources for each cell
- [ ] Unknowns and assumptions are documented with mitigation strategies
- [ ] Research confidence level assigned to each alternative
- [ ] No alternative has "Low" confidence without additional research
- [ ] Counter-Argument analysis completed with substantive answers
- [ ] Alternative Consideration Checklist fully completed
- [ ] If custom over managed: Managed Service Evaluation section included
