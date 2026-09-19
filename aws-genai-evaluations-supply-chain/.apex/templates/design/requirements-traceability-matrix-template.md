---
inclusion: manual
---

# Requirements Traceability Matrix Template

## Purpose

This template documents where each requirement comes from and tracks it through implementation. Use it during Requirements Generation to maintain traceability from source documents to requirements to implementation.

## Template Structure

The RTM serves as the authoritative record of requirement origins, conflicts, resolutions, and implementation status, ensuring complete visibility into how project background information informs the specification package.

### Requirement Identification Section
```markdown
| Req ID | Requirement Title | Requirement Type | Priority | Status | Source Document | Source Location |
|--------|------------------|------------------|----------|---------|-----------------|-----------------|
| BR-001 | [Business Requirement Title] | Business | High | Active | SOW v2.1 | Page 12, Section 3.2 |
| FR-001 | [Functional Requirement Title] | Functional | Medium | Active | BRD v1.2 | Page 8, Section 2.1 |
| NFR-001 | [Non-Functional Requirement Title] | Non-Functional | High | Active | Technical Assessment | Page 15, Performance Section |
```

### Source Traceability Section
```markdown
| Req ID | Primary Source | Secondary Sources | Page/Section | Stakeholder | Date |
|--------|---------------|-------------------|--------------|-------------|------|
| BR-001 | SOW v2.1 | Meeting Notes 03/15, OQR | Page 12, Section 3.2 | John Smith (PM) | 2024-03-15 |
```

### Conflict Documentation Section
```markdown
| Req ID | Conflict Description | Conflicting Sources | Conflict Location | Impact Level | Resolution Status | Resolution Details |
|--------|---------------------|-------------------|------------------|--------------|------------------|-------------------|
| FR-001 | Timeline discrepancy: SOW says 6 months, OQR says 4 months | SOW v2.1 vs OQR v1.3 | SOW Page 5, Section 1.3 vs OQR Page 3, Timeline Section | High | Resolved | Stakeholder meeting 03/20: Agreed on 5-month timeline |
```

### Implementation Mapping Section
```markdown
| Req ID | User Story ID | Epic | Sprint | Implementation Status | Test Case ID | Acceptance Status |
|--------|---------------|------|--------|----------------------|--------------|------------------|
| FR-001 | US-001, US-002 | Epic-1 | Sprint 3 | In Progress | TC-001, TC-002 | Pending |
```



