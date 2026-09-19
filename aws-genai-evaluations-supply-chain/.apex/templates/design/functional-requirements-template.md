---
inclusion: manual
---

# Functional Requirements Template

## Purpose

This template documents functional requirements that define what the system must do. Use it during Requirements Generation to create clear, testable requirements with explicit P0/P1/P2 categorization.

## Template Structure

```markdown
# Functional Requirements

**Project:** [Project Name]  
**Document Version:** [Version]  
**Last Updated:** [Date]  
**Status:** [Status]

---

## Requirements Summary by Category

| Category | Count |
|----------|-------|
| **Non-negotiable (P0)** | [N] |
| **Recommended (P1)** | [N] |
| **Inferred (P2)** | [N] |
| **Total** | [N] |

---

## Non-negotiable Requirements (P0)

### FR-001: [Requirement Title]
- **Category**: Non-negotiable (P0)
- **Description**: Clear, concise description of what the system must do
- **Business Justification**: Why this requirement is necessary
- **Source**: [Document name, section/page]
- **Source Quote**: "[Exact quote from source document that establishes this as non-negotiable]"
- **Acceptance Criteria**:
  - Specific, testable conditions that must be met
  - Include happy path and edge case scenarios
  - Define input/output specifications
- **Dependencies**: Other requirements this depends on
- **Assumptions**: Any assumptions made about this requirement

---

## Recommended Requirements (P1)

### FR-100: [Requirement Title]
- **Category**: Recommended (P1)
- **Description**: Clear, concise description of what the system must do
- **Business Justification**: Why this requirement is necessary
- **Source**: [Document name, section/page]
- **Source Quote**: "[Exact quote from source document]"
- **Flexibility Notes**: [What aspects can be adjusted if needed]
- **Acceptance Criteria**:
  - Specific, testable conditions that must be met
- **Dependencies**: Other requirements this depends on
- **Assumptions**: Any assumptions made about this requirement

---

## Inferred Requirements (P2)

### FR-200: [Requirement Title]
- **Category**: Inferred (P2)
- **Description**: Clear, concise description of what the system must do
- **Inference Rationale**: Why this requirement was inferred and from what source context
- **Source Context**: [Document name, section/page] — the context that led to this inference
- **Acceptance Criteria**:
  - Specific, testable conditions that must be met
- **Dependencies**: Other requirements this depends on
- **Assumptions**: Any assumptions made about this requirement

---

## Non-Goals
[Explicitly out of scope items]

---

## Requirement Dependencies
[Critical path and integration dependencies]

---

## Document Metadata
**Requirements Source:** [Source documents]
**Traceability:** All requirements traced to specific source documents with quotes
**Categorization:** P0 (Non-negotiable), P1 (Recommended), P2 (Inferred)
```
