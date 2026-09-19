---
inclusion: manual
---

# Process Log Template

## Purpose

This template documents what inputs were analyzed, what methods were used, and what changes occurred across iterations. Use it during Documentation Generation to provide transparency about the specification generation process.

## Template Structure

```markdown
# Process Documentation and Analysis Log

## Overview

This document provides complete transparency into the specification generation process, documenting all inputs analyzed, methods applied, and changes made across iterations.

**Generation Date**: [Date]
**Total Iterations**: [Number]
**Process Duration**: [Time/Sessions]

## Input Source Analysis

### Project Documents Analyzed
| Document | Type | Size | Key Information Extracted | Relevance |
|----------|------|------|---------------------------|-----------|
| [filename] | [type] | [size] | [summary] | High/Medium/Low |

**Total Documents**: [Number]
**Analysis Completeness**: [Percentage]% of available information extracted
**Information Gaps Identified**: [List any missing information or clarifications needed]

### Existing Codebase Analysis
[If applicable - document any brownfield systems analyzed]

**Systems Analyzed**: [List of codebases/systems]
**Technical Stack Assessment**: [Summary of technologies and patterns found]
**Integration Requirements**: [Requirements derived from existing systems]
**Technical Debt Assessment**: [Summary of technical debt and modernization needs]

### Customer Context Integration
**Business Goals**: [Summary of captured business objectives]
**Technical Preferences**: [Customer technology preferences and constraints]
**Organizational Context**: [Relevant organizational factors affecting design]
**Success Criteria**: [Customer-defined success metrics and acceptance criteria]

## Analysis Methodology

### Requirements Generation
**Method**: [Systematic analysis/Customer interview/Document extraction/Mixed]
**Traceability Approach**: [How requirements were linked to business goals]
**Validation Method**: [How completeness and accuracy were verified]
**Assumptions Made**: [List key assumptions and their rationale]

### Architecture Design
**Design Approach**: [Intelligence Hub integration/Standard generation/Hybrid]
**Technology Selection Criteria**: [Factors considered in technology choices]
**Reference Architectures Used**: [External references analyzed and their influence]
**Integration Strategy**: [How existing systems integration was planned]

### Quality Assessment
**Scoring Methodology**: [5-category weighted scoring system]
**Iteration Strategy**: [How improvements were prioritized and implemented]
**Validation Approach**: [How implementation readiness was assessed]
**Stakeholder Integration**: [How feedback was incorporated]

## Iteration History

### Iteration 1: Initial Generation
**Date**: [Date]
**Quality Score**: [Score]/100
**Key Components Generated**:
- [List major deliverables created]
**Issues Identified**:
- [List quality gaps or issues found]
**Improvement Areas**:
- [List areas targeted for improvement]

### Iteration X: [Description]
**Date**: [Date]
**Quality Score**: [Score]/100
**Changes Made**:
- [List specific changes and improvements]
**Rationale**:
- [Explain why changes were made]
**Impact Assessment**:
- [Document expected impact of changes]

## Key Insights and Discoveries

### Business Insights
- [Major business insights discovered during analysis]
- [Stakeholder needs clarification or refinement]
- [Business value opportunities identified]

### Technical Insights
- [Technical constraints or opportunities discovered]
- [Architecture pattern insights or recommendations]
- [Integration complexity assessment results]

### Risk Insights
- [Major risks identified during analysis]
- [Risk mitigation strategies developed]
- [Success factor identification]

## Decision Evolution

### Major Architecture Decisions
| Decision | Initial Approach | Final Approach | Rationale for Change |
|----------|------------------|----------------|---------------------|
| [Decision] | [Initial] | [Final] | [Why changed] |

### Requirements Evolution
[Document how requirements changed or were refined across iterations]

### Scope Evolution
[Document any scope changes or clarifications made during the process]

## Interactive Feedback Integration

### Stakeholder Feedback Received
[If applicable - document feedback from stakeholders and how it was addressed]

### Scope Adjustments Made
[Document any scope changes made in response to feedback]

### Trade-off Decisions
[Document trade-offs made and their rationale]

### Approval Status
- **Business Stakeholders**: [Approved/Pending/Needs Review]
- **Technical Team**: [Approved/Pending/Needs Review]
- **Security Team**: [Approved/Pending/Needs Review]
- **Project Management**: [Approved/Pending/Needs Review]

## Lessons Learned

### Process Effectiveness
[Assessment of what worked well in the generation process]

### Areas for Improvement
[Identification of process improvements for future projects]

### Recommendations for Similar Projects
[Guidance for applying similar approaches to comparable projects]

## Validation and Quality Assurance

### Information Source Validation
- All information traced to verifiable sources (project documents, customer context, MCP responses)
- No assumptions made without explicit documentation and rationale
- All recommendations supported by analysis and evidence

### Quality Assurance Process
- [Description of quality checks performed]
- [Validation methods used to ensure accuracy]
- [Review processes applied to deliverables]

### Implementation Readiness Validation
- [Assessment of specification completeness for development]
- [Validation of technical feasibility and resource requirements]
- [Confirmation of stakeholder alignment and approval readiness]

---
*This process log provides complete transparency into the specification generation methodology and ensures all decisions are traceable to their source information and rationale.*
```

## Related Documents

- **Methodology**: `.kiro/specs/design-agent/task-modules/06-documentation-generation.md`
