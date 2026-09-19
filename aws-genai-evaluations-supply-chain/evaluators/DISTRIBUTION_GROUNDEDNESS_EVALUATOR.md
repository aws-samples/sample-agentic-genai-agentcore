# Distribution Groundedness Evaluator

## Overview

The Distribution Groundedness Evaluator is a custom LLM-as-judge evaluator that assesses whether an agent's distribution rebalancing recommendation is grounded in actual inventory and demand data, and whether it improves stockout and overstock risk. It uses Claude Sonnet 4.5 at temperature 0.0 for deterministic scoring.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `{assistant_turn}` | Agent response | The distribution recommendation text produced by the agent |
| `{context}` | Tool output / trace | The inventory and demand data from the distribution API (locations, quantities, suggestions) |

## Evaluation Dimensions

The judge evaluates the agent's response across two primary dimensions:

### 1. Groundedness

| Check | Question |
|-------|----------|
| Source availability | Does the source location have sufficient available inventory (on_hand - reserved) to fulfill the transfer quantity? |
| Demand proportionality | Is the transfer quantity proportional to the demand forecast at the destination? |
| Capacity respect | Does the recommendation respect warehouse capacity constraints (destination utilization + transfer ≤ capacity)? |
| Budget adherence | Does the recommendation stay within budget constraints for transfer costs? |

### 2. Stockout/Overstock Risk Impact

| Check | Question |
|-------|----------|
| Stockout reduction | Does the transfer reduce stockout risk at the destination (moving inventory toward locations with high demand or low stock)? |
| Overstock reduction | Does the transfer reduce overstock risk at the source (moving inventory away from locations with excess stock)? |
| Level convergence | After the transfer, are inventory levels at both source and destination closer to the recommended level? |
| Source safety | Does the transfer avoid creating a new stockout risk at the source location? |

## Rating Scale

| Score | Label | Definition |
|-------|-------|------------|
| 1.0 | Very Good | Recommendation is fully grounded in inventory and demand data. All transfers are supported by sufficient source inventory, proportional to demand, and clearly reduce both stockout and overstock risk at all locations. |
| 0.75 | Good | Recommendation is grounded in data and reduces risk on at least one dimension (stockout or overstock) without worsening the other. Minor improvements possible but overall sound. |
| 0.50 | OK | Recommendation is partially grounded with minor data gaps or the risk impact is neutral. The transfer is feasible but may not optimally address the inventory imbalance. |
| 0.25 | Poor | Recommendation has significant grounding issues (e.g. source may not have enough inventory) or increases risk on one dimension. Should be revised. |
| 0.0 | Very Poor | Recommendation contradicts available inventory data (e.g. transferring more than available) or increases both stockout and overstock risk. Not feasible. |

## Scoring Examples

### Example 1: prod-001 transfers (Very Good)

Data:
- Transfer 1: East FC → NYC Store, 200 units
- Transfer 2: East FC → Digital Channel, 100 units
- East FC has high inventory (overstock risk)
- NYC Store and Digital Channel have high demand (stockout risk)

Analysis:
- Groundedness: East FC is a fulfillment center with large inventory → source has sufficient stock ✅
- Proportionality: 200 units to a flagship store, 100 to digital → proportional to channel demand ✅
- Risk impact: Reduces overstock at East FC, reduces stockout at NYC Store and Digital ✅
- Source safety: 300 total units from a large FC → doesn't create stockout at source ✅

**Score: 1.0 (Very Good)** — fully grounded, clearly reduces risk on both dimensions.

### Example 2: prod-006 transfers (Good)

Data:
- Transfer 1: West FC → LA Store, 600 units
- Transfer 2: East FC → Intl Digital, 300 units
- Transfer 3: Central FC → Southern DC, 450 units

Analysis:
- Groundedness: All sources are fulfillment centers with large capacity ✅
- Proportionality: 600 units to LA Store is a large transfer — may be aggressive ⚠️
- Risk impact: Reduces overstock at FCs, addresses stockout at stores ✅
- Source safety: 600 from West FC is significant — need to verify remaining stock ⚠️

**Score: 0.75 (Good)** — grounded and reduces risk, but one transfer is aggressive.

### Example 3: Hypothetical bad recommendation (Very Poor)

Scenario: Agent recommends transferring 5,000 units from a store (which only has 200 on hand) to a fulfillment center that's already at 95% capacity.

Analysis:
- Groundedness: Source doesn't have enough inventory → contradicts data ❌
- Capacity: Destination is near full → violates capacity constraint ❌
- Risk impact: Would create stockout at source AND overstock at destination ❌

**Score: 0.0 (Very Poor)** — contradicts available data and worsens risk on both dimensions.

## What Makes a Good Agent Response

The evaluator rewards agent responses that:

1. **Reference specific data** — cite actual inventory quantities, location names, and transfer amounts from the tool output
2. **Explain the rationale** — state why inventory should move (e.g., "East FC has excess stock while NYC Store faces stockout risk during the upcoming promotion")
3. **Assess feasibility** — confirm the source can afford to give up the units without creating a new problem
4. **Quantify risk impact** — state how much stockout/overstock risk is reduced (e.g., "This transfer brings NYC Store from 60% to 85% of target inventory level")
5. **Acknowledge limitations** — if data is incomplete or a transfer is borderline, say so

## Key Insight

The evaluator checks two things simultaneously: (1) is the recommendation factually supported by the data, and (2) does it actually improve the situation. An agent can be perfectly grounded in data but still make a bad recommendation (e.g., moving inventory from a location that's already low). Both dimensions must score well for a high rating.
