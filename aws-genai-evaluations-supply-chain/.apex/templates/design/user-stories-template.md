---
inclusion: manual
---

# User Stories Template

## Purpose

This template documents user stories that translate requirements into implementable work items. Use it during Requirements Generation to create user-focused stories with acceptance criteria and P0/P1/P2 categorization inherited from source requirements.

## Template Structure

```markdown
# User Stories

**Project:** [Project Name]  
**Document Version:** [Version]  
**Last Updated:** [Date]  
**Status:** [Status]

---

## Stories Summary by Category

| Category | Count |
|----------|-------|
| **Non-negotiable (P0)** | [N] |
| **Recommended (P1)** | [N] |
| **Inferred (P2)** | [N] |
| **Total** | [N] |

---

## Epic Overview

### Epic 1: [Epic Name]
[Epic description and business value]
**Stories**: [List story IDs with categories]

### Epic 2: [Epic Name]
[Epic description and business value]
**Stories**: [List story IDs with categories]

---

## Non-negotiable Stories (P0)

### US-001: [Story Title]
**Category**: Non-negotiable (P0)  
**Source Requirement**: FR-00X / NFR-00X

**As a** [specific persona]  
**I want** [functionality]  
**So that** [business value]

#### Acceptance Criteria:
- **Given** [context] **When** [action] **Then** [outcome]
- **Given** [context] **When** [action] **Then** [outcome]
- **Given** [edge case] **When** [action] **Then** [error handling]

#### Definition of Done:
- [ ] [Specific deliverable]
- [ ] [Quality requirement]
- [ ] [Testing requirement]

#### Size: [XS/S/M/L/XL]
#### Dependencies: [Story IDs or external dependencies]

---

## Recommended Stories (P1)

### US-100: [Story Title]
**Category**: Recommended (P1)  
**Source Requirement**: FR-1XX / NFR-1XX  
**Flexibility Notes**: [What aspects can be adjusted if needed]

**As a** [specific persona]  
**I want** [functionality]  
**So that** [business value]

#### Acceptance Criteria:
- **Given** [context] **When** [action] **Then** [outcome]
- **Given** [context] **When** [action] **Then** [outcome]

#### Definition of Done:
- [ ] [Specific deliverable]
- [ ] [Quality requirement]

#### Size: [XS/S/M/L/XL]
#### Dependencies: [Story IDs or external dependencies]

---

## Inferred Stories (P2)

### US-200: [Story Title]
**Category**: Inferred (P2)  
**Source Requirement**: FR-2XX / NFR-2XX  
**Validation Needed**: Yes — stakeholder confirmation recommended

**As a** [specific persona]  
**I want** [functionality]  
**So that** [business value]

#### Acceptance Criteria:
- **Given** [context] **When** [action] **Then** [outcome]

#### Definition of Done:
- [ ] [Specific deliverable]

#### Size: [XS/S/M/L/XL]
#### Dependencies: [Story IDs or external dependencies]

---

## Story Prioritization and Sprint Planning

### Sprint 1: [Sprint Name]
**Focus**: [Sprint focus area]
| Story ID | Category | Title | Size |
|----------|----------|-------|------|
| US-001 | P0 | [Title] | [Size] |
| US-002 | P0 | [Title] | [Size] |

### Sprint 2: [Sprint Name]
**Focus**: [Sprint focus area]
| Story ID | Category | Title | Size |
|----------|----------|-------|------|
| US-003 | P0 | [Title] | [Size] |
| US-100 | P1 | [Title] | [Size] |

### Future Backlog
| Story ID | Category | Title | Size |
|----------|----------|-------|------|
| US-200 | P2 | [Title] | [Size] |

---

## Acceptance Criteria Summary

### Definition of Ready Checklist
- [ ] User story follows INVEST criteria
- [ ] Acceptance criteria are specific and testable
- [ ] Dependencies are identified and resolved
- [ ] Size estimated (XS/S/M/L/XL)
- [ ] Category (P0/P1/P2) assigned based on source requirement

### Definition of Done Checklist
- [ ] All acceptance criteria met
- [ ] Code review completed
- [ ] Tests written and passing
- [ ] Documentation updated

---

## Traceability to Requirements

### P0 Stories → P0 Requirements
| Story ID | Requirement ID | Requirement Title |
|----------|----------------|-------------------|
| US-001 | FR-001 | [Title] |

### P1 Stories → P1 Requirements
| Story ID | Requirement ID | Requirement Title |
|----------|----------------|-------------------|
| US-100 | FR-100 | [Title] |

### P2 Stories → P2 Requirements
| Story ID | Requirement ID | Requirement Title |
|----------|----------------|-------------------|
| US-200 | FR-200 | [Title] |

---

## Success Metrics
[Measurable success criteria organized by category]

---

## Document Metadata
**Stories Source:** Requirements documents (functional-requirements.md, non-functional-requirements.md)
**Traceability:** All stories traced to specific requirements with category inheritance
**Categorization:** P0 (Non-negotiable), P1 (Recommended), P2 (Inferred)
```
