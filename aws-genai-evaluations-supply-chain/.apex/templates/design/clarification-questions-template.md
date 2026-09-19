---
inclusion: manual
---

# Clarification Questions Template

## Purpose

This template documents architecture-stage information gaps and decision points surfaced by the research-agent during Stage 3 (Architecture Generation). It captures questions where research found multiple viable options or unresolved gaps that affect architecture decisions. Each question includes a default assumption used if left unanswered.

**Note**: Critical project context questions (project type, region, compute model, document contradictions) are handled earlier during Project Setup triage — not in this file.

## Quality Bar

Every question in this file must pass three gates:
1. A business stakeholder can answer it without deep technical knowledge
2. A different answer would materially change the architecture direction or a key design decision
3. The answer is not already available (even partially) in source documents or customer context

If a gap fails any gate, document it in `appendices/input-assessment-analysis.md` under "Information Gaps" with a default assumption — do NOT create a CQ for it. Target 3-8 questions per project. Fewer, sharper questions are always better than a comprehensive list.

## Template Structure

```markdown
# Clarification Questions

**Project**: [Project name]
**Stage**: 3 — Architecture Generation
**Purpose**: These questions identify architecture decision points and information gaps surfaced during research. Answering them will improve the quality of the architecture design. Each question includes a default assumption that will be used if you choose not to answer.

---

## CQ-001: [Short Title]

**Priority**: Critical | Important | Nice to Have
**Status**: Open | Resolved

**Question**: [Specific, actionable question for the stakeholder]
**Why it matters**: [How the answer affects requirements or architecture — describe both paths]
**Default assumption if not answered**: [Specific assumption that will be used — be concrete]
**Source gap**: [Which source document was checked and what was missing]

---

## CQ-002: [Short Title]

**Priority**: Critical | Important | Nice to Have
**Status**: Open | Resolved

**Question**: [Specific, actionable question for the stakeholder]
**Why it matters**: [How the answer affects requirements or architecture — describe both paths]
**Default assumption if not answered**: [Specific assumption that will be used — be concrete]
**Source gap**: [Which source document was checked and what was missing]

---
```

## Priority Definitions

- **Critical** — blocks a key decision; the default assumption carries significant risk if wrong
- **Important** — influences choices; the default assumption is reasonable but may require rework
- **Nice to Have** — minor impact; the default assumption is safe for most scenarios

## Status Values

- **Open** — awaiting stakeholder input; default assumption will be used if not answered before architecture stage
- **Resolved** — stakeholder provided an answer; record the answer inline and promote to a requirement with source citation `"User-provided answer (Task 2.3)"`

## Resolved Question Format

When a question is answered, update the entry:

```markdown
## CQ-001: [Short Title]

**Priority**: Critical
**Status**: Resolved
**Answer**: [Stakeholder's answer verbatim or paraphrased]

**Question**: [Original question]
**Why it matters**: [Original rationale]
**Default assumption if not answered**: [Original default — kept for audit trail]
**Source gap**: [Original source gap]
```

