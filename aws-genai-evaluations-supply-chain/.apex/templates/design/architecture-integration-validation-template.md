---
inclusion: manual
---

# Architecture Integration Validation Template

## Purpose

This template documents validation of architecture completeness, integration feasibility, and technical readiness. Use it during Architecture Generation to validate the architecture before quality assessment.

## Validation Framework

### Validation Criteria

| Criterion | Target | Pass Threshold | Critical |
|-----------|--------|----------------|----------|
| **Requirements Traceability** | 100% | 95%+ | Yes |
| **Architecture & Integration** | All interfaces defined | 90%+ | Yes |
| **Security & Operations** | Controls match project type | 90%+ | Yes |
| **Technical Feasibility** | All technologies validated | 90%+ | Yes |
| **Documentation & Decisions** | All docs complete | 85%+ | No |

### Quality Scoring Matrix

| Category | Weight | Description |
|----------|--------|-------------|
| **Requirements Traceability** | 25% | FR/NFR coverage, user story mapping, RTM validation |
| **Architecture & Integration** | 25% | Interface compatibility, data flow validation, integration patterns |
| **Security & Operations** | 20% | Security foundation, operations readiness, deployment review |
| **Technical Feasibility** | 15% | Technology maturity, service limits, implementation complexity |
| **Documentation & Decisions** | 15% | ADR coverage, evidence quality, documentation completeness |

**Overall Pass Threshold**: 85/100 (Good) | **Excellence Threshold**: 90/100

## Template Structure

```markdown
# Architecture Validation Report
## [Project Name]

**Validation Date**: [Date]
**Validation Status**: PASSED / CONDITIONAL / FAILED
**Quality Score**: [Score]/100

---

## Executive Summary
[2-3 sentences: overall status, key strengths, critical findings if any]

## Issues Found and Resolutions

### Resolved During Review
| Issue | Severity | Category | Resolution | Files Changed |
|-------|----------|----------|------------|---------------|

### Open Recommendations
| Issue | Severity | Category | Recommendation |
|-------|----------|----------|----------------|

**Severity**: Critical / High / Medium / Low
**Categories**: Requirements, Integration, Security, Operations, Feasibility, Documentation

## Quality Score

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Requirements Traceability | 25% | /100 | |
| Architecture & Integration | 25% | /100 | |
| Security & Operations | 20% | /100 | |
| Technical Feasibility | 15% | /100 | |
| Documentation & Decisions | 15% | /100 | |
| **Overall** | | | **/100** |

**Determination**: PROCEED / CONDITIONAL / STOP

## Determination Rationale
[Brief explanation of the score and any conditions that must be met before implementation]
```

**Notes**:
- Detailed requirements-to-component traceability lives in `appendices/requirements-traceability-matrix.md` (created by apex-requirements-gatherer, validated and updated by reviewer)
- The reviewer's execution steps (1-10) are the validation work; this report is the summary receipt
- Keep the report concise — if the score is 90+ and no critical issues, the Executive Summary and Score table are sufficient

## Examples

### Quality Scoring Example

```markdown
| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Requirements Traceability | 25% | 100/100 | 25.0 |
| Architecture & Integration | 25% | 95/100 | 23.75 |
| Security & Operations | 20% | 90/100 | 18.0 |
| Technical Feasibility | 15% | 95/100 | 14.25 |
| Documentation & Decisions | 15% | 85/100 | 12.75 |
| **Overall** | | | **93.75/100** |
```

### Issues Table Example

```markdown
| Issue | Severity | Category | Resolution | Files Changed |
|-------|----------|----------|------------|---------------|
| ADR-001 deployment method contradicts architecture | High | Documentation | Updated ADR to match ZIP deployment | ADR-001 |
| Missing CloudTrail in security section | Medium | Security | Added to security controls summary | system-architecture.md |
```

## Coverage Thresholds

| Coverage Level | Functional Req | Non-Functional Req | User Stories | Status |
|---------------|----------------|-------------------|--------------|--------|
| **Complete** | 95-100% | 95-100% | 100% | PASS |
| **Acceptable** | 90-94% | 90-94% | 95-99% | CONDITIONAL |
| **Insufficient** | <90% | <90% | <95% | FAIL |

## Score Thresholds

| Score | Rating | Action |
|-------|--------|--------|
| 90-100 | Excellent | PROCEED |
| 85-89 | Good | PROCEED |
| 70-84 | Conditional | Address issues before handoff |
| <70 | Failed | Escalate to user |
