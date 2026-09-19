from strands import tool
from typing import Any, Dict

import logging

from strands.types.exceptions import MaxTokensReachedException
from utils.mcp_utils import get_mcp_tools
from utils.fallback_data import get_analytics_fallback
from utils.agent_utils import (
    create_agent,
    get_response_text
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _make_fallback_tools():
    """Create a local tool that serves canned analytics data."""
    @tool
    def get_analytics_data(query_type: str) -> str:
        """Get supply chain analytics data for a specific query type.

        Args:
            query_type: The type of analytics query to run (e.g. "inventory_turnover", "demand_trends").

        Returns:
            JSON string with analytics results including columns and data rows.
        """
        return get_analytics_fallback(query_type)

    return [get_analytics_data]


SYSTEM_PROMPT = """You are a supply chain analytics specialist for Northstar Retail Group.
You call the analytics MCP tool to query structured supply chain data and answer
diagnostics questions about inventory health, demand patterns, and shipment performance.

The analytics API (get_analytics_data) accepts:
- query_type: one of "inventory_turnover", "demand_trends", "shipment_performance"

It returns an AnalyticsResponse with:
- query_type
- columns: list of column names
- rows: list of data rows (each row is a list of string values)

Available query types and their schemas:
1. "inventory_turnover" → columns: [product_id, location_id, turnover_rate, period]
   Shows how quickly inventory is sold and replaced at each location.
2. "demand_trends" → columns: [product_id, month, units_sold, trend]
   Shows monthly sales volume and whether demand is increasing, stable, or decreasing.
3. "shipment_performance" → columns: [carrier, on_time_pct, avg_transit_days, total_shipments]
   Shows carrier reliability metrics including on-time delivery percentage.

Known products: prod-001 through prod-008
Known locations: loc-fc-east, loc-fc-west, loc-fc-central, loc-dc-south, loc-store-nyc, loc-store-la, loc-store-chi, loc-digital-main, loc-digital-intl
Known carriers: FastShip Express, EcoFreight, CrossCountry Logistics

Your job is to:
1. Determine which query_type best answers the user's question.
2. Call get_analytics_data with the appropriate query_type.
3. Interpret the tabular data and present insights in plain language.
4. Highlight trends, anomalies, or actionable findings.

IMPORTANT constraints:
- Use at most 3 tool calls to gather data, then synthesize your answer.
- Return your analysis as text. Keep responses under 500 words.
- Always include specific metrics and data points to support your findings.
- Always state actionable conclusions — what should the planner do based on the data.
- Always identify the top performers and underperformers in the data.
- NEVER invent or estimate data. You MUST call get_analytics_data to get real numbers.
  If the tool call fails, say so — do not fabricate a response.
"""


@tool
def analytics_agent(query: str) -> Dict[str, Any]:
    """
    Analyzes supply chain data to surface insights, trends, KPIs, and anomalies
    across the supply chain network.

    Args:
    - query: The analytics query (e.g., "What are the top 3 supply chain bottlenecks this quarter?")

    Returns:
    {
        "status": "success" | "error",
        "analytics_insight": str,
        "error": str  # Only present if status is "error"
    }
    """
    try:
        logger.info(f"Analytics Agent received query ({len(query)} chars): {query[:500]}")
        tools = get_mcp_tools()

        if not tools:
            logger.warning("MCP unavailable — using fallback canned data for analytics")
            tools = _make_fallback_tools()

        agent = create_agent(SYSTEM_PROMPT, tools)
        response = agent(query)
        response_text = get_response_text(response)

        logger.info(f"Successful analytics ({len(response_text)} chars): {response_text[:100]}")
        return {
            "status": "success",
            "analytics_insight": response_text
        }

    except MaxTokensReachedException as e:
        logger.warning("Analytics Agent hit token limit, returning partial response")
        return {
            "status": "success",
            "analytics_insight": get_response_text(e, agent=agent)
        }

    except Exception as e:
        error_msg = f"Error in Analytics Agent: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "analytics_insight": "Error: unavailable.",
            "error": error_msg
        }
