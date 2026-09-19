from strands import tool
from typing import Any, Dict

import logging

from strands.types.exceptions import MaxTokensReachedException
from utils.mcp_utils import get_mcp_tools
from utils.fallback_data import get_optimization_fallback
from utils.agent_utils import (
    create_agent,
    get_response_text
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _make_fallback_tools():
    """Create a local tool that serves canned optimization data."""
    @tool
    def get_optimization_data(product_id: str, time_horizon: str) -> str:
        """Get demand forecast and inventory optimization recommendations for a product.

        Args:
            product_id: The product identifier to get optimization data for.
            time_horizon: The forecasting time horizon (e.g. "30d", "90d").

        Returns:
            JSON string with demand forecast, recommended inventory levels, and constraints.
        """
        return get_optimization_fallback(f"{product_id} {time_horizon}")

    return [get_optimization_data]


SYSTEM_PROMPT = """You are a supply chain optimization specialist for Northstar Retail Group.
You call the optimization MCP tool to retrieve demand forecasts, recommended inventory levels,
and constraint analysis for specific products.

The optimization API (get_optimization_data) accepts:
- product_id: e.g. "prod-001" through "prod-008"
- time_horizon: e.g. "30d", "90d"

It returns an OptimizationResponse with:
- product_id, time_horizon
- demand_forecast: projected units needed in the time horizon
- recommended_inventory_level: optimal stock level to hold
- confidence: model confidence (0.0 to 1.0)
- constraints:
  - budget_limit / budget_used: remaining budget = budget_limit - budget_used
  - warehouse_capacity / warehouse_utilization: remaining capacity = capacity - utilization
  - inventory_holding_cost: cost per unit per period

Your job is to:
1. Call get_optimization_data with the product_id and time_horizon from the user's query.
2. Analyze whether the recommendation satisfies all three constraints:
   - Budget: incremental cost (additional units × holding_cost) fits within remaining budget
   - Inventory: recommended level ≥ demand_forecast (avoids stockout) and ≤ 2× demand (avoids excess)
   - Capacity: recommended level fits within warehouse_capacity - warehouse_utilization + current stock
3. Present a clear recommendation with the constraint analysis and confidence level.

IMPORTANT constraints:
- Use at most 3 tool calls to gather data, then synthesize your answer.
- Return your analysis as text. Keep responses under 500 words.
- Always state the confidence level and whether each constraint is satisfied.
- NEVER invent or estimate data. You MUST call get_optimization_data to get real numbers.
  If the tool call fails, say so — do not fabricate a response.
"""


@tool
def optimization_agent(query: str) -> Dict[str, Any]:
    """
    Analyzes supply chain constraints and recommends optimal inventory levels.
    Evaluates budget, demand forecast, and warehouse capacity to produce feasible recommendations.

    Args:
    - query: The optimization query (e.g., "What is the optimal inventory level for SKU-1234 given current demand and budget?")

    Returns:
    {
        "status": "success" | "error",
        "optimization_recommendation": str,
        "error": str  # Only present if status is "error"
    }
    """
    try:
        logger.info(f"Optimization Agent received query ({len(query)} chars): {query[:500]}")
        tools = get_mcp_tools()

        if not tools:
            logger.warning("MCP unavailable — using fallback canned data for optimization")
            tools = _make_fallback_tools()

        agent = create_agent(SYSTEM_PROMPT, tools)
        response = agent(query)
        response_text = get_response_text(response)

        logger.info(f"Successful optimization ({len(response_text)} chars): {response_text[:100]}")
        return {
            "status": "success",
            "optimization_recommendation": response_text
        }

    except MaxTokensReachedException as e:
        logger.warning("Optimization Agent hit token limit, returning partial response")
        return {
            "status": "success",
            "optimization_recommendation": get_response_text(e, agent=agent)
        }

    except Exception as e:
        error_msg = f"Error in Optimization Agent: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "optimization_recommendation": "Error: unavailable.",
            "error": error_msg
        }
