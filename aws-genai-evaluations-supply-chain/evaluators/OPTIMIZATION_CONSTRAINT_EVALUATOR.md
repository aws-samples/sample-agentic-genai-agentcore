# Optimization Constraint Evaluator

## Overview

The Optimization Constraint Evaluator is a custom LLM-as-judge evaluator that assesses whether an agent's optimization recommendation correctly satisfies budget, inventory, and warehouse capacity constraints. It uses Claude Sonnet 4.5 at temperature 0.0 for deterministic scoring.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `{assistant_turn}` | Agent response | The optimization recommendation text produced by the agent |
| `{context}` | Tool output / trace | The constraint data from the optimization API (budget, capacity, demand) |

## Evaluation Dimensions

The judge evaluates the agent's response across three constraint dimensions:

### 1. Budget Constraint

| Check | Question |
|-------|----------|
| Affordability | Does the cost of reaching the recommended inventory level fit within remaining budget (budget_limit - budget_used)? |
| Incremental cost | Is the incremental holding cost (additional units × holding_cost per unit) affordable? |
| Limit adherence | Does the recommendation avoid exceeding the budget_limit? |

### 2. Inventory Constraint

| Check | Question |
|-------|----------|
| Stockout avoidance | Is the recommended inventory level ≥ demand_forecast? |
| Overstock avoidance | Is the recommended level reasonable relative to demand (not more than 2× demand)? |
| Confidence threshold | Is the confidence level sufficient (≥ 0.75)? |

### 3. Warehouse Capacity Constraint

| Check | Question |
|-------|----------|
| Physical fit | Does the recommended inventory level fit within warehouse_capacity? |
| Buffer margin | Does the recommendation leave a reasonable buffer (at least 10% capacity remaining)? |
| High utilization acknowledgment | If warehouse is near capacity (>85% utilized), does the recommendation acknowledge this? |

## Rating Scale

| Score | Label | Definition |
|-------|-------|------------|
| 1.0 | Very Good | All three constraints (budget, inventory, capacity) are satisfied with comfortable margins exceeding 20% headroom. The recommendation is safe and well within operational limits. |
| 0.75 | Good | All constraints are satisfied but at least one has less than 20% margin. The recommendation is acceptable but approaching a limit. |
| 0.50 | OK | One constraint is at risk with less than 15% margin but none are violated. The recommendation requires monitoring and may need adjustment. |
| 0.25 | Poor | One constraint is technically violated or two constraints are at risk. The recommendation should be revised before implementation. |
| 0.0 | Very Poor | Multiple constraints are violated or a single critical violation exists (e.g. recommended level exceeds warehouse capacity, cost exceeds budget). The recommendation is not feasible. |

## Scoring Examples

### Example 1: prod-001 (Very Good)

Data:
- Budget: $50,000 limit, $32,500 used → $17,500 remaining
- Demand: 1,200 units, Recommended: 1,500 units
- Capacity: 5,000 total, 3,200 utilized → 1,800 remaining
- Holding cost: $2.50/unit
- Confidence: 0.87

Analysis:
- Budget headroom: $17,500 / ($2.50 × 1,500) = ~467% → well above 20% ✅
- Inventory ratio: 1,500 / 1,200 = 1.25× demand → healthy buffer, under 2× ✅
- Capacity headroom: 1,800 remaining for 1,500 → 36% of capacity free ✅
- Confidence: 0.87 ≥ 0.75 ✅

**Score: 1.0 (Very Good)** — all constraints satisfied with comfortable margins.

### Example 2: prod-003 (Poor/Very Poor)

Data:
- Budget: $100,000 limit, $78,000 used → $22,000 remaining
- Demand: 3,500 units, Recommended: 4,000 units
- Capacity: 10,000 total, 8,500 utilized → 1,500 remaining
- Holding cost: $3.20/unit
- Confidence: 0.79

Analysis:
- Budget: $22,000 / ($3.20 × 4,000) = ~172% → OK
- Inventory ratio: 4,000 / 3,500 = 1.14× → tight but valid
- Capacity: 1,500 remaining, utilization at 85% → at risk, only 15% free ⚠️
- If agent recommends stocking 4,000 without acknowledging capacity risk → constraint at risk

**Score: 0.25–0.50** depending on whether the agent acknowledges the capacity constraint.

### Example 3: prod-006 (Critical)

Data:
- Budget: $150,000 limit, $120,000 used → $30,000 remaining
- Demand: 5,000 units, Recommended: 5,800 units
- Capacity: 12,000 total, 10,200 utilized → 1,800 remaining
- Holding cost: $1.50/unit
- Confidence: 0.76

Analysis:
- Budget: $30,000 / ($1.50 × 5,800) = ~345% → OK
- Inventory ratio: 5,800 / 5,000 = 1.16× → valid
- Capacity: 10,200 + 5,800 = 16,000 > 12,000 → **VIOLATED** ❌
- Utilization already at 85% → high risk

**Score: 0.0 (Very Poor)** if agent doesn't flag the capacity violation.

## Key Insight

The evaluator doesn't just check if the agent provided a number. It assesses whether the agent:
1. Correctly calculated constraint margins
2. Identified which constraints are satisfied vs. at risk
3. Flagged violations or near-violations explicitly
4. Provided actionable guidance when constraints conflict
