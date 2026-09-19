"""
Test Client — Invokes the Supply Chain orchestrator agent with sample queries
targeting each of the 4 sub-agents (Optimization, Distribution, Routing, Analytics).

Usage:
    python test_agent.py --runtime-arn <supply-chain-runtime-arn> --region us-east-1

    # Run only specific categories:
    python test_agent.py --runtime-arn <arn> --category optimization routing

The runtime ARN can be obtained from:
    cd terraform && terraform output supply_chain_arn
"""

import argparse
import json
import sys
import uuid

import boto3
from botocore.config import Config


# --- Sample queries for each sub-agent (5 each) ---

OPTIMIZATION_QUERIES = [
    "What is the optimal inventory level for prod-001 over the next 30 days?",
    "Analyze the budget and capacity constraints for prod-003. Is the recommended level feasible?",
    "For prod-005, what inventory level do you recommend given current warehouse utilization?",
    "Compare optimization recommendations for prod-002 and prod-007. Which has tighter constraints?",
    "What is the demand forecast and recommended stock level for prod-006?",
]

DISTRIBUTION_QUERIES = [
    "Recommend inventory transfers to rebalance prod-001 across our locations.",
    "What rebalancing suggestions do you have for prod-006 to reduce overstock risk?",
    "Should we move any prod-004 inventory from the Central FC to retail stores?",
    "Analyze distribution suggestions for prod-003. Where should we transfer stock?",
    "What transfers are recommended for prod-007 to reduce stockout risk at stores?",
]

ROUTING_QUERIES = [
    "What are the shipping options from the East Fulfillment Center to the NYC store?",
    "Compare carrier options for shipping from Central FC to the Chicago store.",
    "What is the fastest route from the Southern DC to the East Fulfillment Center?",
    "Find the cheapest shipping option from the West FC to the LA store.",
    "What routes are available from the East FC to the Southern Distribution Center?",
]

ANALYTICS_QUERIES = [
    "Show me inventory turnover rates across all products for Q1 2025.",
    "What are the demand trends for prod-001 over the past two months?",
    "Which carrier has the best on-time delivery performance?",
    "Are there any products with decreasing demand trends?",
    "Compare shipment performance across all carriers - who is most reliable?",
]

ALL_QUERIES = {
    "Optimization": OPTIMIZATION_QUERIES,
    "Distribution": DISTRIBUTION_QUERIES,
    "Routing": ROUTING_QUERIES,
    "Analytics": ANALYTICS_QUERIES,
}


def invoke_agent(client, agent_arn: str, prompt: str, session_id: str) -> str:
    """Send a single prompt to the supply chain agent and return its text response."""
    resp = client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        qualifier="DEFAULT",
        runtimeSessionId=session_id,
        payload=json.dumps({"prompt": prompt}).encode("utf-8"),
    )
    raw = resp["response"].read().decode("utf-8")

    # Try SSE format first (streaming entrypoint with yield)
    text_parts = []
    for line in raw.splitlines():
        if not line.startswith("data: "):
            continue
        chunk_str = line[len("data: "):]
        try:
            chunk = json.loads(chunk_str)
        except Exception:
            continue
        if isinstance(chunk, dict):
            event = chunk.get("event", chunk)
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"].get("delta", {})
                text = delta.get("text", "")
                if text:
                    text_parts.append(text)

    if text_parts:
        return "".join(text_parts)

    # Non-streaming format (return response entrypoint)
    # Try parsing as JSON
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, str):
            return parsed
        if isinstance(parsed, dict):
            for key in ("response", "output", "text", "result", "body"):
                if key in parsed:
                    val = parsed[key]
                    return val if isinstance(val, str) else json.dumps(val, indent=2)
            return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        pass

    # Raw text fallback
    return raw.strip() if raw.strip() else "(no text in response)"


def run_session(client, agent_arn: str, turns: list, session_prefix: str) -> str:
    """Invoke a multi-turn session and return its session ID."""
    session_id = f"{session_prefix}-{uuid.uuid4()}"
    print(f"\n  Session: {session_id}")
    for turn_input in turns:
        print(f"    > {turn_input}")
        response = invoke_agent(client, agent_arn, turn_input, session_id)
        print(f"    < {response}")
        print()
    return session_id


def main():
    parser = argparse.ArgumentParser(description="Test the Supply Chain agent with sample queries")
    parser.add_argument("--runtime-arn", required=True, help="AgentCore runtime ARN for the supply chain agent")
    parser.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")
    parser.add_argument(
        "--category",
        nargs="*",
        choices=["optimization", "distribution", "routing", "analytics"],
        help="Run only specific categories (default: all)",
    )
    args = parser.parse_args()

    client = boto3.client("bedrock-agentcore", region_name=args.region)

    queries_to_run = ALL_QUERIES
    if args.category:
        queries_to_run = {k: v for k, v in ALL_QUERIES.items() if k.lower() in [c.lower() for c in args.category]}

    print(f"\n{'='*70}")
    print(f"  Supply Chain Agent Test Client")
    print(f"  Runtime ARN: {args.runtime_arn}")
    print(f"  Region:      {args.region}")
    print(f"  Categories:  {list(queries_to_run.keys())}")
    print(f"{'='*70}")

    session_ids = []

    for category, queries in queries_to_run.items():
        print(f"\n--- {category} Agent ({len(queries)} queries) ---")
        session_id = run_session(
            client,
            args.runtime_arn,
            queries,
            session_prefix=f"test-{category.lower()}",
        )
        session_ids.append({"category": category, "session_id": session_id})

    print(f"\n{'='*70}")
    print(f"  SESSIONS CREATED")
    print(f"{'='*70}")
    for s in session_ids:
        print(f"  {s['category']}: {s['session_id']}")
    print(f"\n  Use these session IDs with the evaluators API to assess response quality.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
