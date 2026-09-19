# Autonomous Build Workflow - aws-genai-evaluations-supply-chain

This document tracks the progress of the autonomous build workflow.

## Workflow Status

<workflow-status>
```json
{
  "status": "ready",
  "message": "Ready to begin autonomous build",
  "processPid": null
}
```
</workflow-status>

---

## Status Values

- `ready`: Workflow hasn't started yet
- `in-progress`: Workflow is actively running
- `completed`: Workflow finished successfully
- `failed`: Workflow encountered an error

---

## Instructions for Build Agent

Update the JSON block above with:

- **`status`**: Current workflow state (`ready` | `in-progress` | `completed` | `failed`)
- **`message`**: Brief user-facing message about current activity or result
- **`processPid`**: DO NOT MODIFY - This is managed by the extension

### Example Updates

**Progress update:**
```json
{
  "status": "in-progress",
  "message": "Building and deploying to AWS...",
  "processPid": 12345
}
```

**Note:** Only update `status` and `message`. Leave `processPid` unchanged.

**Progress:**
```json
{
  "status": "in-progress",
  "message": "Building and deploying to AWS...",
  "processPid": 12345
}
```

**Success:**
```json
{
  "status": "completed",
  "message": "Build completed successfully. Deployed to https://example.cloudfront.net",
  "processPid": null
}
```

**Error:**
```json
{
  "status": "failed",
  "message": "Build failed: AWS credentials not configured for us-east-1",
  "processPid": null
}
```
