"""
Supply Chain Evaluators — AWS Lambda Handler (Async Pattern)

Exposes AgentCore custom evaluator operations via API Gateway.
Long-running operations (run, run-builtin) use async self-invocation:
  1. API Gateway calls this Lambda
  2. Lambda invokes itself asynchronously (InvocationType='Event') with the work payload
  3. Lambda returns 202 Accepted immediately to the caller
  4. The async invocation runs the actual evaluation (no API Gateway timeout)

POST /evaluators/create         — Create evaluators from metric JSON files (async, returns 202)
POST /evaluators/run            — Run evaluations (async, returns 202)
POST /evaluators/run-builtin    — Run built-in evaluators (async, returns 202)
DELETE /evaluators/delete        — Delete evaluators (sync, fast)
"""

import json
import logging
import os

import boto3
from bedrock_agentcore_starter_toolkit import Evaluation

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get("AWS_REGION_NAME", os.environ.get("AWS_REGION", "us-east-1"))
FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")
RESULTS_BUCKET = os.environ.get("RESULTS_BUCKET", "")

# Metric configs bundled with the Lambda
METRICS_DIR = os.path.join(os.path.dirname(__file__), "metrics")


def _load_metric(filename: str) -> dict:
    with open(os.path.join(METRICS_DIR, filename)) as f:
        return json.load(f)


def _get_eval_client():
    return Evaluation(region=REGION)


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def _invoke_self_async(payload: dict):
    """Invoke this Lambda asynchronously with the given payload."""
    lambda_client = boto3.client("lambda", region_name=REGION)
    lambda_client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="Event",  # Async — returns immediately
        Payload=json.dumps(payload).encode("utf-8"),
    )


# ============================================================================
# Sync handlers (fast operations)
# ============================================================================


def create_evaluators(event, context):
    """Kick off evaluator creation asynchronously and return 202.

    Request body (required):
        {
            "metrics": "optimization_constraint_metric.json,distribution_groundedness_metric.json",
            "level": "TRACE"  // optional, defaults to TRACE
        }
    """
    try:
        body = json.loads(event.get("body", "{}")) if event.get("body") else {}
        metrics_csv = body.get("metrics", "")
        level = body.get("level", "TRACE")

        # Parse comma-separated metric filenames
        metric_files = [f.strip() for f in metrics_csv.split(",") if f.strip()] if metrics_csv else []

        if not metric_files:
            return _response(400, {
                "error": "metrics is required (comma-separated list of metric JSON filenames in the metrics/ directory)"
            })

        # Invoke self asynchronously to do the actual work
        _invoke_self_async({
            "_async_action": "create_evaluators",
            "metric_files": metric_files,
            "level": level,
        })

        return _response(202, {
            "status": "accepted",
            "message": f"Evaluator creation started for {len(metric_files)} metric(s). Results will be saved to S3.",
            "metrics": metric_files,
            "level": level,
        })

    except Exception as e:
        logger.error(f"Failed to start evaluator creation: {e}")
        return _response(500, {"error": str(e)})


def delete_evaluators(event, context):
    """Delete evaluators by ID (async)."""
    try:
        body = json.loads(event.get("body", "{}"))
        evaluator_ids = body.get("evaluator_ids", [])

        if not evaluator_ids:
            return _response(400, {"error": "evaluator_ids is required (list of at least 1 evaluator ID)"})

        _invoke_self_async({
            "_async_action": "delete_evaluators",
            "evaluator_ids": evaluator_ids,
        })

        return _response(202, {
            "status": "accepted",
            "message": f"Deletion started for {len(evaluator_ids)} evaluator(s).",
            "evaluator_ids": evaluator_ids,
        })

    except Exception as e:
        logger.error(f"Failed to start evaluator deletion: {e}")
        return _response(500, {"error": str(e)})


def create_all_evaluators(event, context):
    """Create evaluators from ALL metric JSON files in a folder (async)."""
    try:
        body = json.loads(event.get("body", "{}")) if event.get("body") else {}
        level = body.get("level", "TRACE")
        metrics_folder = body.get("metrics_folder", "")
        prefix_filter = body.get("prefix_filter", "")

        # Scan metrics directory for JSON files
        scan_dir = METRICS_DIR
        if metrics_folder:
            scan_dir = os.path.join(METRICS_DIR, metrics_folder)

        if not os.path.isdir(scan_dir):
            return _response(400, {"error": f"Metrics directory not found: {scan_dir}"})

        metric_files = [
            f for f in os.listdir(scan_dir)
            if f.endswith(".json") and (not prefix_filter or f.startswith(prefix_filter))
        ]

        if not metric_files:
            return _response(400, {"error": f"No metric JSON files found in {scan_dir}"})

        _invoke_self_async({
            "_async_action": "create_evaluators",
            "metric_files": metric_files,
            "level": level,
        })

        return _response(202, {
            "status": "accepted",
            "message": f"Evaluator creation started for {len(metric_files)} metric(s).",
            "metrics_folder": metrics_folder or "(root)",
            "metrics": metric_files,
            "level": level,
        })

    except Exception as e:
        logger.error(f"Failed to start create-all: {e}")
        return _response(500, {"error": str(e)})


def list_evaluators(event, context):
    """List evaluators, optionally filtered by name."""
    try:
        # HTTP API v2: query params are in queryStringParameters
        params = event.get("queryStringParameters") or {}
        name_filter = params.get("name", "")

        eval_client = _get_eval_client()
        evaluators_list = eval_client.list_evaluators()

        results = []
        for ev in evaluators_list:
            ev_name = ev.get("name", "")
            ev_id = ev.get("evaluatorId", "")
            if name_filter and name_filter.lower() not in ev_name.lower():
                continue
            results.append({
                "name": ev_name,
                "evaluator_id": ev_id,
                "level": ev.get("level", ""),
                "status": ev.get("status", ""),
                "description": ev.get("description", ""),
            })

        return _response(200, {
            "count": len(results),
            "evaluators": results,
        })

    except Exception as e:
        logger.error(f"Failed to list evaluators: {e}")
        return _response(500, {"error": str(e)})


# ============================================================================
# Async handlers (long-running operations)
# ============================================================================


def _do_create_evaluators(payload: dict):
    """Actually create evaluators (called asynchronously). Saves results to S3."""
    metric_files = payload["metric_files"]
    level = payload.get("level", "TRACE")

    logger.info(f"Creating evaluators: {len(metric_files)} metrics, level={level}")

    eval_client = _get_eval_client()
    created = {}
    errors = []

    for filename in metric_files:
        try:
            config = _load_metric(filename)

            # Derive evaluator name from filename:
            # e.g., 'mp_constraint_satisfaction_metric.json' -> 'mp_constraint_satisfaction'
            # e.g., 'optimization_constraint_metric.json' -> 'sc_optimization_constraint'
            name = filename.replace("_metric.json", "").replace(".json", "")
            if not name.startswith(("sc_", "mp_")):
                name = f"sc_{name}"

            # Derive description from the config instructions (first sentence)
            description = f"Custom evaluator: {name}"
            instructions = (
                config.get("llmAsAJudge", {})
                .get("instructions", "")
            )
            if instructions:
                first_line = instructions.split("\n")[0].strip()
                if first_line:
                    description = first_line[:200]

            evaluator = eval_client.create_evaluator(
                name=name,
                level=level,
                description=description,
                config=config,
            )
            created[name] = evaluator["evaluatorId"]
            logger.info(f"Created evaluator: {name} -> {evaluator['evaluatorId']}")

        except FileNotFoundError:
            errors.append({"file": filename, "error": "File not found in metrics/ directory"})
            logger.error(f"Metric file not found: {filename}")
        except Exception as e:
            errors.append({"file": filename, "error": str(e)})
            logger.error(f"Failed to create evaluator from {filename}: {e}")

    # Save creation results to S3
    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    result_body = {"created": created}
    if errors:
        result_body["errors"] = errors

    if RESULTS_BUCKET:
        s3_client = boto3.client("s3", region_name=REGION)
        s3_key = f"evaluators/creation/{timestamp.replace(' ', '_').replace(':', '-')}/results.json"
        s3_client.put_object(
            Bucket=RESULTS_BUCKET,
            Key=s3_key,
            Body=json.dumps(result_body, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        logger.info(f"Creation results saved to s3://{RESULTS_BUCKET}/{s3_key}")
    else:
        logger.warning("RESULTS_BUCKET not set — creation results not saved to S3")

    logger.info(f"Evaluator creation complete: {len(created)} created, {len(errors)} errors")


def _do_run_evaluations(payload: dict):
    """Actually run evaluations (called asynchronously). Saves results as markdown to S3."""
    agent_id = payload["agent_id"]
    session_id = payload["session_id"]
    evaluator_ids = payload["evaluator_ids"]

    logger.info(f"Running evaluations: agent={agent_id}, session={session_id}, evaluators={evaluator_ids}")

    eval_client = _get_eval_client()
    results = eval_client.run(
        agent_id=agent_id,
        session_id=session_id,
        evaluators=evaluator_ids,
    )

    # Generate markdown report
    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    md_lines = [
        f"# Evaluation Results",
        f"",
        f"**Agent ID:** {agent_id}  ",
        f"**Session ID:** {session_id}  ",
        f"**Timestamp:** {timestamp}  ",
        f"**Evaluators:** {', '.join(evaluator_ids)}  ",
        f"",
        f"---",
        f"",
        f"## Results",
        f"",
        f"| Evaluator | Verdict | Score |",
        f"|-----------|---------|-------|",
    ]

    for result in results.results:
        md_lines.append(
            f"| {result.evaluator_name} | {result.label} | {result.value} |"
        )

    md_lines.extend([
        f"",
        f"---",
        f"",
        f"## Detailed Explanations",
        f"",
    ])

    for i, result in enumerate(results.results, 1):
        md_lines.extend([
            f"### {i}. {result.evaluator_name}",
            f"",
            f"**Verdict:** {result.label} ({result.value})  ",
            f"**Token Usage:** {result.token_usage if hasattr(result, 'token_usage') else 'N/A'}  ",
            f"",
            f"{result.explanation}",
            f"",
            f"---",
            f"",
        ])

    markdown_content = "\n".join(md_lines)

    # Save to S3
    if RESULTS_BUCKET:
        s3_client = boto3.client("s3", region_name=REGION)
        s3_key = f"evaluations/{session_id}/{timestamp.replace(' ', '_').replace(':', '-')}/EvaluationResults.md"
        s3_client.put_object(
            Bucket=RESULTS_BUCKET,
            Key=s3_key,
            Body=markdown_content.encode("utf-8"),
            ContentType="text/markdown",
        )
        logger.info(f"Results saved to s3://{RESULTS_BUCKET}/{s3_key}")
    else:
        logger.warning("RESULTS_BUCKET not set — results not saved to S3")
        logger.info(f"Markdown report:\n{markdown_content}")

    logger.info(f"Evaluation complete: {len(results.results)} results for session {session_id}")


def _do_delete_evaluators(payload: dict):
    """Actually delete evaluators (called asynchronously)."""
    evaluator_ids = payload["evaluator_ids"]
    logger.info(f"Deleting evaluators: {evaluator_ids}")

    eval_client = _get_eval_client()
    deleted = []
    errors = []

    for evaluator_id in evaluator_ids:
        try:
            eval_client.delete_evaluator(evaluator_id=evaluator_id)
            deleted.append(evaluator_id)
            logger.info(f"Deleted evaluator: {evaluator_id}")
        except Exception as e:
            errors.append({"evaluator_id": evaluator_id, "error": str(e)})
            logger.error(f"Failed to delete {evaluator_id}: {e}")

    logger.info(f"Deletion complete: {len(deleted)} deleted, {len(errors)} errors")


def run_evaluations(event, context):
    """Kick off evaluations asynchronously and return 202."""
    try:
        body = json.loads(event.get("body", "{}"))
        agent_id = body.get("agent_id")
        session_id = body.get("session_id")
        evaluator_ids = body.get("evaluator_ids", [])

        if not agent_id or not session_id:
            return _response(400, {"error": "agent_id and session_id are required"})

        if not evaluator_ids:
            return _response(400, {"error": "evaluator_ids is required (list of at least 1 evaluator ID)"})

        # Invoke self asynchronously to do the actual work
        _invoke_self_async({
            "_async_action": "run_evaluations",
            "agent_id": agent_id,
            "session_id": session_id,
            "evaluator_ids": evaluator_ids,
        })

        return _response(202, {
            "status": "accepted",
            "message": f"Evaluation started for session {session_id}. Results will be saved to S3.",
            "agent_id": agent_id,
            "session_id": session_id,
            "evaluators": evaluator_ids,
        })

    except Exception as e:
        logger.error(f"Failed to start evaluations: {e}")
        return _response(500, {"error": str(e)})


def run_builtin_evaluations(event, context):
    """Kick off built-in evaluations asynchronously and return 202."""
    try:
        body = json.loads(event.get("body", "{}"))
        agent_id = body.get("agent_id")
        session_id = body.get("session_id")

        if not agent_id or not session_id:
            return _response(400, {"error": "agent_id and session_id are required"})

        evaluator_ids = ["Builtin.Correctness", "Builtin.GoalSuccessRate"]

        _invoke_self_async({
            "_async_action": "run_evaluations",
            "agent_id": agent_id,
            "session_id": session_id,
            "evaluator_ids": evaluator_ids,
        })

        return _response(202, {
            "status": "accepted",
            "message": f"Built-in evaluation started for session {session_id}. Results will be saved to S3.",
            "agent_id": agent_id,
            "session_id": session_id,
            "evaluators": evaluator_ids,
        })

    except Exception as e:
        logger.error(f"Failed to start built-in evaluations: {e}")
        return _response(500, {"error": str(e)})


# ============================================================================
# Main router
# ============================================================================


def handler(event, context):
    """Main router — dispatches based on path/method or async action."""

    # Check if this is an async self-invocation
    if "_async_action" in event:
        action = event["_async_action"]
        if action == "run_evaluations":
            _do_run_evaluations(event)
            return
        elif action == "create_evaluators":
            _do_create_evaluators(event)
            return
        elif action == "delete_evaluators":
            _do_delete_evaluators(event)
            return
        else:
            logger.error(f"Unknown async action: {action}")
            return

    # Normal API Gateway request
    path = event.get("path", "") or event.get("rawPath", "")
    method = event.get("httpMethod", "") or event.get("requestContext", {}).get("http", {}).get("method", "")

    logger.info(f"Request: {method} {path}")

    if path == "/evaluators/create" and method == "POST":
        return create_evaluators(event, context)
    elif path == "/evaluators/create-all" and method == "POST":
        return create_all_evaluators(event, context)
    elif path == "/evaluators/run" and method == "POST":
        return run_evaluations(event, context)
    elif path == "/evaluators/run-builtin" and method == "POST":
        return run_builtin_evaluations(event, context)
    elif path == "/evaluators/delete" and method == "DELETE":
        return delete_evaluators(event, context)
    elif path == "/evaluators/list" and method == "GET":
        return list_evaluators(event, context)
    else:
        return _response(404, {"error": f"Not found: {method} {path}"})
