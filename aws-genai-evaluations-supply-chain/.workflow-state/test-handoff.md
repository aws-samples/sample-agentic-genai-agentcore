# Test Agent Workflow - Progress Tracking

---

## ⚠️ MANDATORY: Before Executing ANY Task

**YOU MUST READ the task module file for the current stage BEFORE starting any task:**

| Stage | Task Module File |
|-------|------------------|
| Stage 0 | `task-modules/00-understand-current-state.md` |
| Stage 1 | `task-modules/01-design-and-implement-tests.md` |
| Stage 2 | `task-modules/02-execute-testing.md` |
| Stage 3 | `task-modules/03-comprehensive-reporting.md` |

**CRITICAL**: The task module file contains ALL instructions, validation checkpoints, and quality gates for each task. Failure to read the task module file will result in incomplete or incorrect task execution.

---

## Status Update Protocol

**Workflow Status Values:** `ready` | `in-progress` | `complete` | `failed`

**Task Status Values:** `not_started` | `current` | `complete`

**BEFORE task:** Set `status="current"`, update `activeTask`  
**AFTER task:** Set `status="complete"`, increment `completed`, recalc `percentage`, set NEXT to `"current"`

---

## Current Status
<workflow-status>
```json
{
  "status": "ready",
  "workflowStage": "Stage 0 - Understand Current State",
  "activeTask": "Ready to start",
  "taskModuleFile": "task-modules/00-understand-current-state.md",
  "codePath": "",
  "overallProgress": {
    "completed": 0,
    "total": 4,
    "percentage": 0
  },
  "currentStageProgress": {
    "stage": 0,
    "stageName": "Understand Current State",
    "stageCompleted": 0,
    "stageTotal": 5
  },
  "taskDetails": [
    {
      "taskNumber": "0",
      "taskName": "Understand Current State",
      "status": "not_started",
      "subtasks": [
        { "taskNumber": "0.1", "taskName": "Read Requirement Documents", "taskModuleFile": "task-modules/00-understand-current-state.md", "status": "not_started" },
        { "taskNumber": "0.2", "taskName": "Check for Existing Properties", "taskModuleFile": "task-modules/00-understand-current-state.md", "status": "not_started" },
        { "taskNumber": "0.3", "taskName": "Extract Resource Names from Code", "taskModuleFile": "task-modules/00-understand-current-state.md", "status": "not_started" },
        { "taskNumber": "0.4", "taskName": "Verify Deployment Status", "taskModuleFile": "task-modules/00-understand-current-state.md", "status": "not_started" },
        { "taskNumber": "0.5", "taskName": "Document Current State", "taskModuleFile": "task-modules/00-understand-current-state.md", "status": "not_started" }
      ]
    },
    {
      "taskNumber": "1",
      "taskName": "Design and Implement Tests",
      "status": "not_started",
      "subtasks": [
        { "taskNumber": "1.1", "taskName": "Setup and Preparation", "taskModuleFile": "task-modules/01-design-and-implement-tests.md", "status": "not_started" },
        { "taskNumber": "1.2", "taskName": "Identify or Use Existing Properties", "taskModuleFile": "task-modules/01-design-and-implement-tests.md", "status": "not_started" },
        { "taskNumber": "1.3", "taskName": "Coordinate Test Implementation", "taskModuleFile": "task-modules/01-design-and-implement-tests.md", "status": "not_started" }
      ]
    },
    {
      "taskNumber": "2",
      "taskName": "Execute Testing",
      "status": "not_started",
      "subtasks": [
        { "taskNumber": "2.1", "taskName": "Initialize", "taskModuleFile": "task-modules/02-execute-testing.md", "status": "not_started" },
        { "taskNumber": "2.2", "taskName": "Delegate Tests to Sub-Agents", "taskModuleFile": "task-modules/02-execute-testing.md", "status": "not_started" },
        { "taskNumber": "2.3", "taskName": "Aggregate Results", "taskModuleFile": "task-modules/02-execute-testing.md", "status": "not_started" },
        { "taskNumber": "2.4", "taskName": "Handle Skipped and Failed Tests", "taskModuleFile": "task-modules/02-execute-testing.md", "status": "not_started" }
      ]
    },
    {
      "taskNumber": "3",
      "taskName": "Comprehensive Reporting",
      "status": "not_started",
      "subtasks": [
        { "taskNumber": "3.1", "taskName": "Calculate Coverage Statistics", "taskModuleFile": "task-modules/03-comprehensive-reporting.md", "status": "not_started" },
        { "taskNumber": "3.2", "taskName": "Create Test Report", "taskModuleFile": "task-modules/03-comprehensive-reporting.md", "status": "not_started" },
        { "taskNumber": "3.3", "taskName": "Verify and Finalize", "taskModuleFile": "task-modules/03-comprehensive-reporting.md", "status": "not_started" }
      ]
    }
  ],
  "lastUpdated": "2025-01-15T10:00:00Z"
}
```
</workflow-status>

## Test Scope Decision
*Updated during Task 1.1*

- **Scope**: *Not yet determined (ALL or PRIORITY)*
- **Estimated Tests**: *To be determined*
- **User Consultation**: *Required if >20 tests*
- **Rationale**: *Document decision rationale*
