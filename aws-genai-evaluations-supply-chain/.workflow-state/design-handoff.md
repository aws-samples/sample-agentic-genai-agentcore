# Design Agent Workflow - aws-genai-evaluations-supply-chain

---
## Status Update Protocol

**Workflow Status Values:** `ready` | `in-progress` | `complete` | `gathering_feedback`

**Task Status Values:** `not_started` | `current` | `complete`

**BEFORE task:** Set `status="current"`, update `activeTask`  
**AFTER task:** Set `status="complete"`, increment `completed`, recalc `percentage`, set NEXT to `"current"`  
**Validate:** JSON valid, counts match, percentage = (completed/total)*100, optional tasks excluded from total count

**Cascading Rules (IMPORTANT):**
- When first subtask starts → both subtask AND parent must become `current`
- When last **required** subtask completes → both subtask AND parent must become `complete`
- For middle subtasks → previous becomes `complete`, current becomes `current`, parent stays `current`
- **Optional tasks**: Tasks marked with "(optional)" in taskName do NOT block parent completion

**Feedback Workflow:**
- Stage 1 (Project Setup) may pause for triage clarification questions (project type, region, compute model, document contradictions) — optional, only when critical context is missing or contradictory
- Stage 2 has an explicit review gate (subtask 2.3) after requirements generation and peer review complete — no clarification questions, only feedback on generated requirements
- Stage 3 has a clarification gate (subtask 3.2) after research and a review gate (subtask 3.6) after architecture peer review
- When entering any gate → set status to `gathering_feedback`, set the gate subtask to `current`
- When user approves → set gate subtask to `complete`, status back to `in-progress`
- When user provides feedback → re-invoke the appropriate sub-agent(s) with feedback, then re-present for review
- If session ends during any gate, the next session reads the handoff, sees `gathering_feedback`, and re-presents the review
- **See task-modules/01-project-setup.md for Stage 1 triage clarification details**
- **See task-modules/02-requirements-generation.md for Stage 2 review gate details**
- **See task-modules/03-architecture-generation.md for Stage 3 clarification gate (Task 3.2) and review gate (Task 3.6) details**

*Full protocol in task-modules/00-session-management.md*

---

## Current Status
<workflow-status>
```json
{
  "workflowStage": "Not Started",
  "activeTask": "Not Started",
  "overallProgress": {
    "completed": 0,
    "total": 7,
    "percentage": 0
  },
  "currentFeedbackIteration": 0,
  "currentStageProgress": {
    "stage": 0,
    "stageName": "Session Management",
    "stageCompleted": 0,
    "stageTotal": 3
  },
  "taskDetails": [
    {
      "taskNumber": "0",
      "taskName": "Session Management",
      "status": "not_started",
      "subtasks": [
        {
          "taskNumber": "0.1",
          "taskName": "Prepare Workflow",
          "status": "not_started"
        },
        {
          "taskNumber": "0.2",
          "taskName": "Collect Project Information",
          "status": "not_started"
        },
        {
          "taskNumber": "0.3",
          "taskName": "Verify Setup Complete",
          "status": "not_started"
        }
      ]
    },
    {
      "taskNumber": "1",
      "taskName": "Project Analysis",
      "status": "not_started",
      "subtasks": [
        {
          "taskNumber": "1.1",
          "taskName": "Project Complexity Assessment",
          "status": "not_started"
        }
      ]
    },
    {
      "taskNumber": "2",
      "taskName": "Requirements Generation",
      "status": "not_started",
      "subtasks": [
        {
          "taskNumber": "2.1",
          "taskName": "Analysis and Generation",
          "status": "not_started"
        },
        {
          "taskNumber": "2.2",
          "taskName": "Peer Review",
          "status": "not_started"
        },
        {
          "taskNumber": "2.3",
          "taskName": "User Review",
          "status": "not_started"
        }
      ]
    },
    {
      "taskNumber": "3",
      "taskName": "Architecture Generation",
      "status": "not_started",
      "subtasks": [
        {
          "taskNumber": "3.1",
          "taskName": "Research Phase",
          "status": "not_started"
        },
        {
          "taskNumber": "3.2",
          "taskName": "Clarification Questions",
          "status": "not_started"
        },
        {
          "taskNumber": "3.3",
          "taskName": "Design Phase",
          "status": "not_started"
        },
        {
          "taskNumber": "3.4",
          "taskName": "Peer Review Phase",
          "status": "not_started"
        },
        {
          "taskNumber": "3.5",
          "taskName": "Diagram Export",
          "status": "not_started"
        },
        {
          "taskNumber": "3.6",
          "taskName": "User Review",
          "status": "not_started"
        }
      ]
    },
    {
      "taskNumber": "4",
      "taskName": "Security Assessment",
      "status": "not_started",
      "subtasks": [
        {
          "taskNumber": "4.1",
          "taskName": "Generate Threat Model",
          "status": "not_started"
        },
        {
          "taskNumber": "4.2",
          "taskName": "Map Security Controls to Threats",
          "status": "not_started"
        },
        {
          "taskNumber": "4.3",
          "taskName": "Integrate Security into Specification",
          "status": "not_started"
        }
      ]
    },
    {
      "taskNumber": "5",
      "taskName": "Documentation Generation",
      "status": "not_started",
      "subtasks": [
        {
          "taskNumber": "5.0",
          "taskName": "Load Output Structure Specification",
          "status": "not_started"
        },
        {
          "taskNumber": "5.1",
          "taskName": "Executive Summary and Navigation Documentation Generation",
          "status": "not_started"
        },
        {
          "taskNumber": "5.2",
          "taskName": "Project Risk Analysis",
          "status": "not_started"
        },
        {
          "taskNumber": "5.3",
          "taskName": "Documentation Quality Validation",
          "status": "not_started"
        }
      ]
    },
    {
      "taskNumber": "6",
      "taskName": "Output Organization",
      "status": "not_started",
      "subtasks": [
        {
          "taskNumber": "6.0",
          "taskName": "Load Output Structure Specification",
          "status": "not_started"
        },
        {
          "taskNumber": "6.1",
          "taskName": "Create Project Folders",
          "status": "not_started"
        },
        {
          "taskNumber": "6.2",
          "taskName": "Structure Specialized Content",
          "status": "not_started"
        },
        {
          "taskNumber": "6.3",
          "taskName": "Prepare Final Package",
          "status": "not_started"
        },
        {
          "taskNumber": "6.4",
          "taskName": "HTML Documentation Generation",
          "status": "not_started"
        },
        {
          "taskNumber": "6.5",
          "taskName": "PPTX Summary Generation",
          "status": "not_started"
        }
      ]
    }
  ],
  "lastUpdated": "2025-10-01T00:00:00Z",
  "status": "ready"
}
```
</workflow-status>

## Stage Completion Status
- [ ] Stage 0: Session Management
- [ ] Stage 1: Project Analysis
- [ ] Stage 2: Requirements Generation
- [ ] Stage 3: Architecture Generation
- [ ] Stage 4: Security Assessment
- [ ] Stage 5: Documentation Generation
- [ ] Stage 6: Output Organization
- [ ] Stage 7+: Feedback Integration (when feedback provided)

## Project Information
- **Project Name**: *To be determined during session management*
- **Project Folder**: `generated/design/`
- **Input Scenario**: *To be determined during project analysis*

## Files Created/Updated
*Workflow not started*

## Key Insights & Decisions
*Workflow not started*

## Issues Encountered
*Workflow not started*

## Next Stage Details
- **Stage**: Ready to begin with Stage 0: Session Management
- **Objective**: Initialize workflow, capture context, determine execution mode
- **Dependencies**: None - workflow initialization

## Session Instructions
### To Start: Execute design agent workflow - will read this handoff and begin with Stage 0
### Progress Updates: Update taskDetails status when completing each stage (not_started → current → complete)
