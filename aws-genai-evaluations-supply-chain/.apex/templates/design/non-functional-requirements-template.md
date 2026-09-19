---
inclusion: manual
---

# Non-Functional Requirements Template

## Purpose

This template documents non-functional requirements that define quality attributes, constraints, and implementation standards. Use it during Requirements Generation to create clear, testable NFRs with explicit P0/P1/P2 categorization.

## Template Structure

```markdown
# Non-Functional Requirements

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

### NFR-001: [Requirement Title]
- **Category**: Non-negotiable (P0)
- **Description**: Clear description of the quality attribute or constraint
- **Business Justification**: Why this constraint is necessary
- **Source**: [Document name, section/page]
- **Source Quote**: "[Exact quote from source document that establishes this as non-negotiable]"
- **Acceptance Criteria**:
  - Specific, measurable conditions that must be met
  - Include thresholds and measurement methods
- **Dependencies**: Other requirements this depends on
- **Assumptions**: Any assumptions made about this requirement

---

## Recommended Requirements (P1)

### NFR-100: [Requirement Title]
- **Category**: Recommended (P1)
- **Description**: Clear description of the quality attribute or constraint
- **Business Justification**: Why this constraint is necessary
- **Source**: [Document name, section/page]
- **Source Quote**: "[Exact quote from source document]"
- **Flexibility Notes**: [What aspects can be adjusted if needed]
- **Acceptance Criteria**:
  - Specific, measurable conditions that must be met
- **Dependencies**: Other requirements this depends on
- **Assumptions**: Any assumptions made about this requirement

---

## Inferred Requirements (P2)

### NFR-200: [Requirement Title]
- **Category**: Inferred (P2)
- **Description**: Clear description of the quality attribute or constraint
- **Inference Rationale**: Why this requirement was inferred and from what source context
- **Source Context**: [Document name, section/page] — the context that led to this inference
- **Acceptance Criteria**:
  - Specific, measurable conditions that must be met
- **Dependencies**: Other requirements this depends on
- **Validation Needed**: Yes — stakeholder confirmation recommended before implementation

---

## Requirements by Domain

### Security Requirements
[List security-related NFRs with their category codes]

### Performance Requirements
[List performance-related NFRs with their category codes]

### Scalability Requirements
[List scalability-related NFRs with their category codes]

### Technology Stack Requirements
[List technology-related NFRs with their category codes]

### Operational Requirements
[List operational NFRs with their category codes]

---

## Document Metadata
**Requirements Source:** [Source documents]
**Traceability:** All requirements traced to specific source documents with quotes
**Categorization:** P0 (Non-negotiable), P1 (Recommended), P2 (Inferred)
```
