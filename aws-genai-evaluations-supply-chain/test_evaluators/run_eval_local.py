"""
Run evaluations locally using the bedrock_agentcore_starter_toolkit directly.
Bypasses the Lambda/API Gateway (which has a 30s timeout limit).

Usage:
    python run_eval_local.py --agent-id <runtime-name> --session-id <session-id>
    python run_eval_local.py --agent-id <runtime-name> --session-id <session-id> --evaluators optimization
"""

import argparse
import json
import sys

from bedrock_agentcore_starter_toolkit import Evaluation
from boto3.session import Session


def main():
    parser = argparse.ArgumentParser(description="Run evaluations locally")
    parser.add_argument("--agent-id", required=True, help="Agent runtime name (e.g. supply_chain_orchestrator_agent-YK657xBNWi)")
    parser.add_argument("--session-id", required=True, help="Session ID to evaluate")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--evaluators", default="both", choices=["optimization", "distribution", "both", "builtin"],
                        help="Which evaluators to run")
    parser.add_argument("--optimization-evaluator-id", help="Custom optimization evaluator ID")
    parser.add_argument("--distribution-evaluator-id", help="Custom distribution evaluator ID")
    parser.add_argument("--output", help="Output file path for results JSON")
    args = parser.parse_args()

    eval_client = Evaluation(region=args.region)

    # Build evaluator list
    evaluator_ids = []

    if args.evaluators == "builtin":
        evaluator_ids = ["Builtin.Correctness", "Builtin.GoalSuccessRate"]
    else:
        evaluator_ids.extend(["Builtin.Correctness", "Builtin.GoalSuccessRate"])
        if args.evaluators in ("optimization", "both") and args.optimization_evaluator_id:
            evaluator_ids.append(args.optimization_evaluator_id)
        if args.evaluators in ("distribution", "both") and args.distribution_evaluator_id:
            evaluator_ids.append(args.distribution_evaluator_id)

    print(f"\n{'='*60}")
    print(f"  Running Evaluations (local)")
    print(f"  Agent ID:    {args.agent_id}")
    print(f"  Session ID:  {args.session_id}")
    print(f"  Evaluators:  {evaluator_ids}")
    print(f"{'='*60}\n")

    try:
        results = eval_client.run(
            agent_id=args.agent_id,
            session_id=args.session_id,
            evaluators=evaluator_ids,
            **({"output": args.output} if args.output else {}),
        )

        print(f"  Results:")
        print(f"  {'-'*60}")
        for result in results.results:
            print(f"\n  Evaluator:   {result.evaluator_name}")
            print(f"  Verdict:     {result.label} ({result.value})")
            print(f"  Explanation: {result.explanation[:300]}")
            if hasattr(result, "token_usage"):
                print(f"  Tokens:      {result.token_usage}")
            print(f"  {'-'*60}")

        if args.output:
            print(f"\n  Results saved to: {args.output}")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
