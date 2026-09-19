"""
Test Evaluator Client — Invokes the Evaluators API Gateway to create, run, and delete
custom evaluators.

All create/run/delete operations are asynchronous (return 202 Accepted immediately).
Results are saved to S3 by the Lambda's async self-invocation.

Usage:
    # Create evaluators from metric JSON files
    python test_evaluator.py --api-url <evaluators-api-url> create \
        --metrics "optimization_constraint_metric.json,distribution_groundedness_metric.json"

    # Create ALL evaluators from the metrics/ directory
    python test_evaluator.py --api-url <evaluators-api-url> create-all \
        --level TRACE --prefix-filter "sc_"

    # Run evaluations with comma-separated evaluator IDs (custom and/or built-in)
    python test_evaluator.py --api-url <evaluators-api-url> run \
        --agent-id <agent-id> \
        --session-id <session-id> \
        --evaluators "sc_optimization_constraint-abc123,Builtin.Correctness"

    # Run built-in evaluators only
    python test_evaluator.py --api-url <evaluators-api-url> run-builtin \
        --agent-id <agent-id> \
        --session-id <session-id>

    # List all evaluators
    python test_evaluator.py --api-url <evaluators-api-url> list-all

    # List evaluator by name
    python test_evaluator.py --api-url <evaluators-api-url> list-metric --name "sc_optimization_constraint"

    # Delete evaluators
    python test_evaluator.py --api-url <evaluators-api-url> delete \
        --evaluator-ids "sc_optimization_constraint-abc123,sc_distribution_groundedness-def456"

The API URL can be obtained from:
    cd terraform && terraform output evaluators_api_url
"""

import argparse
import json
import sys

import requests


def create_evaluators(api_url: str, metrics: list) -> dict:
    """Create custom evaluators from a list of metric JSON filenames (async)."""
    print("\n--- Creating Evaluators ---\n")
    url = f"{api_url}/evaluators/create"
    payload = {"metrics": ",".join(metrics)}

    print(f"  POST {url}")
    print(f"  Payload: {json.dumps(payload, indent=4)}")

    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    print(f"\n  Status: {resp.status_code}")

    if data.get("status") == "accepted":
        print(f"\n  {data.get('message')}")
        print(f"  Metrics: {data.get('metrics')}")
        print(f"\n  Results will be saved to S3. Check evaluators/creation/ prefix in your results bucket.")
    else:
        if data.get("created"):
            print(f"\n  Created evaluators:")
            for name, eval_id in data["created"].items():
                print(f"    {name}: {eval_id}")
        if data.get("errors"):
            print(f"\n  Errors:")
            for err in data["errors"]:
                print(f"    {err['file']}: {err['error']}")

    return data


def create_all_evaluators(api_url: str, metrics_folder: str = "", level: str = "TRACE", prefix_filter: str = "") -> dict:
    """Create evaluators from ALL metric JSON files in a folder (async)."""
    print("\n--- Creating ALL Evaluators ---\n")
    url = f"{api_url}/evaluators/create-all"

    payload = {"level": level}
    if metrics_folder:
        payload["metrics_folder"] = metrics_folder
    if prefix_filter:
        payload["prefix_filter"] = prefix_filter

    print(f"  POST {url}")
    print(f"  Payload: {json.dumps(payload, indent=4)}")

    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    print(f"\n  Status: {resp.status_code}")

    if data.get("status") == "accepted":
        print(f"\n  {data.get('message')}")
        print(f"  Folder: {data.get('metrics_folder')}")
        print(f"  Metrics ({len(data.get('metrics', []))}):")
        for m in data.get("metrics", []):
            print(f"    - {m}")
        print(f"\n  Results will be saved to S3. Check evaluators/creation/ prefix in your results bucket.")

    return data


def run_evaluations(api_url: str, agent_id: str, session_id: str, evaluator_ids: list) -> dict:
    """Run evaluations against agent traces (async — returns 202)."""
    print("\n--- Running Evaluations ---\n")
    url = f"{api_url}/evaluators/run"

    payload = {
        "agent_id": agent_id,
        "session_id": session_id,
        "evaluator_ids": evaluator_ids,
    }

    print(f"  POST {url}")
    print(f"  Payload: {json.dumps(payload, indent=4)}")

    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    print(f"\n  Status: {resp.status_code}")

    if data.get("status") == "accepted":
        print(f"\n  {data.get('message')}")
        print(f"  Results will be saved to S3.")
    else:
        print(f"\n  Results:")
        print(f"  {'='*60}")
        for result in data.get("results", []):
            print(f"\n  Evaluator: {result.get('evaluator_name')}")
            print(f"  Verdict:   {result.get('label')} ({result.get('value')})")
            print(f"  Explanation: {result.get('explanation', '')[:200]}")
            print(f"  {'-'*60}")

    return data


def run_builtin_evaluations(api_url: str, agent_id: str, session_id: str) -> dict:
    """Run built-in evaluators (async — returns 202)."""
    print("\n--- Running Built-in Evaluations ---\n")
    url = f"{api_url}/evaluators/run-builtin"

    payload = {
        "agent_id": agent_id,
        "session_id": session_id,
    }

    print(f"  POST {url}")
    print(f"  Payload: {json.dumps(payload, indent=4)}")

    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    print(f"\n  Status: {resp.status_code}")

    if data.get("status") == "accepted":
        print(f"\n  {data.get('message')}")
        print(f"  Evaluators: {data.get('evaluators')}")
    else:
        print(f"\n  Results:")
        print(f"  {'='*60}")
        for result in data.get("results", []):
            print(f"\n  Evaluator: {result.get('evaluator_name')}")
            print(f"  Verdict:   {result.get('label')} ({result.get('value')})")
            print(f"  Explanation: {result.get('explanation', '')[:200]}")
            print(f"  {'-'*60}")

    return data


def delete_evaluators(api_url: str, evaluator_ids: list) -> dict:
    """Delete evaluators by ID (async — returns 202)."""
    print("\n--- Deleting Evaluators ---\n")
    url = f"{api_url}/evaluators/delete"

    payload = {"evaluator_ids": evaluator_ids}

    print(f"  DELETE {url}")
    print(f"  Payload: {json.dumps(payload, indent=4)}")

    resp = requests.delete(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    print(f"\n  Status: {resp.status_code}")
    if data.get("status") == "accepted":
        print(f"\n  {data.get('message')}")
    else:
        print(f"  Deleted: {data.get('deleted')}")
    return data


def list_all_evaluators(api_url: str) -> dict:
    """List all evaluator IDs."""
    print("\n--- Listing All Evaluators ---\n")
    url = f"{api_url}/evaluators/list"

    print(f"  GET {url}")

    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    print(f"\n  Status: {resp.status_code}")
    print(f"  Count: {data.get('count', 0)}")
    print()

    for ev in data.get("evaluators", []):
        print(f"  {ev['name']}")
        print(f"    ID:     {ev['evaluator_id']}")
        print(f"    Level:  {ev.get('level', 'N/A')}")
        print(f"    Status: {ev.get('status', 'N/A')}")
        print()

    return data


def list_evaluator_by_name(api_url: str, name: str) -> dict:
    """List evaluator ID for a specific metric name."""
    print(f"\n--- Listing Evaluator: {name} ---\n")
    url = f"{api_url}/evaluators/list"

    print(f"  GET {url}?name={name}")

    resp = requests.get(url, params={"name": name}, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    print(f"\n  Status: {resp.status_code}")

    if data.get("evaluators"):
        for ev in data["evaluators"]:
            print(f"\n  Name:   {ev['name']}")
            print(f"  ID:     {ev['evaluator_id']}")
            print(f"  Level:  {ev.get('level', 'N/A')}")
            print(f"  Status: {ev.get('status', 'N/A')}")
            print(f"  Desc:   {ev.get('description', '')[:100]}")
    else:
        print(f"\n  No evaluator found matching: {name}")

    return data


def main():
    parser = argparse.ArgumentParser(description="Test the Evaluators API Gateway")
    parser.add_argument("--api-url", required=True, help="Evaluators API Gateway URL (from terraform output evaluators_api_url)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create custom evaluators from metric JSON files")
    create_parser.add_argument("--metrics", required=True, help="Comma-separated list of metric JSON filenames")

    # Create-all command
    create_all_parser = subparsers.add_parser("create-all", help="Create evaluators from ALL metric JSON files")
    create_all_parser.add_argument("--metrics-folder", default="", help="Subfolder within metrics/ to scan (default: root)")
    create_all_parser.add_argument("--level", default="TRACE", help="Evaluation level: TRACE or SESSION (default: TRACE)")
    create_all_parser.add_argument("--prefix-filter", default="", help="Only process files starting with this prefix")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run evaluations against a session")
    run_parser.add_argument("--agent-id", required=True, help="Agent runtime name")
    run_parser.add_argument("--session-id", required=True, help="Session ID to evaluate")
    run_parser.add_argument("--evaluators", required=True, help="Comma-separated list of evaluator IDs")

    # Run-builtin command
    run_builtin_parser = subparsers.add_parser("run-builtin", help="Run built-in evaluators")
    run_builtin_parser.add_argument("--agent-id", required=True, help="Agent runtime name")
    run_builtin_parser.add_argument("--session-id", required=True, help="Session ID to evaluate")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete evaluators by ID")
    delete_parser.add_argument("--evaluator-ids", required=True, help="Comma-separated list of evaluator IDs to delete")

    # List commands
    subparsers.add_parser("list-all", help="List all evaluator IDs")
    list_metric_parser = subparsers.add_parser("list-metric", help="List evaluator by name")
    list_metric_parser.add_argument("--name", required=True, help="Evaluator name to search for")

    args = parser.parse_args()

    try:
        if args.command == "create":
            metrics = [m.strip() for m in args.metrics.split(",") if m.strip()]
            if not metrics:
                print("ERROR: --metrics must contain at least 1 metric JSON filename")
                sys.exit(1)
            create_evaluators(args.api_url, metrics=metrics)
        elif args.command == "create-all":
            create_all_evaluators(
                args.api_url,
                metrics_folder=args.metrics_folder,
                level=args.level,
                prefix_filter=args.prefix_filter,
            )
        elif args.command == "run":
            evaluator_ids = [e.strip() for e in args.evaluators.split(",") if e.strip()]
            if not evaluator_ids:
                print("ERROR: --evaluators must contain at least 1 evaluator ID")
                sys.exit(1)
            run_evaluations(args.api_url, args.agent_id, args.session_id, evaluator_ids)
        elif args.command == "run-builtin":
            run_builtin_evaluations(args.api_url, args.agent_id, args.session_id)
        elif args.command == "delete":
            evaluator_ids = [e.strip() for e in args.evaluator_ids.split(",") if e.strip()]
            if not evaluator_ids:
                print("ERROR: --evaluator-ids must contain at least 1 evaluator ID")
                sys.exit(1)
            delete_evaluators(args.api_url, evaluator_ids)
        elif args.command == "list-all":
            list_all_evaluators(args.api_url)
        elif args.command == "list-metric":
            list_evaluator_by_name(args.api_url, args.name)
    except requests.HTTPError as e:
        print(f"\n  ERROR: {e}")
        print(f"  Response: {e.response.text}")
        sys.exit(1)
    except requests.ConnectionError as e:
        print(f"\n  ERROR: Could not connect to {args.api_url}")
        print(f"  Details: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
