from strands import tool
from typing import Any, Dict

import logging

from strands.types.exceptions import MaxTokensReachedException
from utils.mcp_utils import get_mcp_tools
from utils.fallback_data import get_distribution_fallback
from utils.agent_utils import (
    create_agent,
    get_response_text
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _make_fallback_tools():
    """Create a local tool that serves canned distribution data."""
    @tool
    def get_distribution_data(product_id: str) -> str:
        """Get inventory rebalancing suggestions across distribution locations.

        Args:
            product_id: The product identifier to get distribution suggestions for.

        Returns:
            JSON string with rebalancing suggestions between locations.
        """
        return get_distribution_fallback(product_id)

    return [get_distribution_data]


SYSTEM_PROMPT = """You are a supply chain distribution specialist for Northstar Retail Group.
You call the distribution MCP tool to retrieve inventory rebalancing suggestions across
fulfillment centers, stores, and digital channels.

The distribution API (get_distribution_data) accepts:
- product_id: e.g. "prod-001" through "prod-008"

It returns a DistributionResponse with:
- product_id
- suggestions: a list of RebalancingSuggestion objects, each containing:
  - source_location: {location_id, name, location_type, region}
  - destination_location: {location_id, name, location_type, region}
  - product_id
  - transfer_quantity: number of units to move

Location types: fulfillment_center, store, digital_channel
Known locations:
- loc-fc-east: East Fulfillment Center (us-east-1)
- loc-fc-west: West Fulfillment Center (us-west-2)
- loc-fc-central: Central Fulfillment Center (us-central-1)
- loc-dc-south: Southern Distribution Center (us-south-1)
- loc-store-nyc: NYC Flagship Store (us-east-1)
- loc-store-la: Los Angeles Store (us-west-2)
- loc-store-chi: Chicago Store (us-central-1)
- loc-digital-main: Main Digital Channel (us-east-1)
- loc-digital-intl: International Digital Channel (eu-west-1)

Your job is to:
1. Call get_distribution_data with the product_id from the user's query.
2. Analyze the rebalancing suggestions and explain:
   - Why inventory should move from source to destination (stockout risk at destination, overstock at source)
   - Whether the transfer quantities are reasonable given the locations involved
   - The expected impact on stockout and overstock risk
3. Present clear, actionable transfer recommendations.

IMPORTANT constraints:
- Use at most 3 tool calls to gather data, then synthesize your answer.
- Return your analysis as text. Keep responses under 500 words.
- Always specify transfer quantities, source location, and destination location.
- Always state whether each transfer reduces stockout risk, overstock risk, or both.
- Always conclude with a summary of the net risk impact across all suggested transfers.
- NEVER invent or estimate data. You MUST call get_distribution_data to get real numbers.
  If the tool call fails, say so — do not fabricate a response.
"""


@tool
def distribution_agent(query: str) -> Dict[str, Any]:
    """
    Analyzes inventory distribution across locations and recommends rebalancing transfers
    to reduce stockout and overstock risk.

    Args:
    - query: The distribution query (e.g., "Recommend inventory transfers to balance stock across East Coast warehouses")

    Returns:
    {
        "status": "success" | "error",
        "distribution_recommendation": str,
        "error": str  # Only present if status is "error"
    }
    """
    try:
        logger.info(f"Distribution Agent received query ({len(query)} chars): {query[:500]}")
        tools = get_mcp_tools()

        if not tools:
            logger.warning("MCP unavailable — using fallback canned data for distribution")
            tools = _make_fallback_tools()

        agent = create_agent(SYSTEM_PROMPT, tools)
        response = agent(query)
        response_text = get_response_text(response)

        logger.info(f"Successful distribution analysis ({len(response_text)} chars): {response_text[:100]}")
        return {
            "status": "success",
            "distribution_recommendation": response_text
        }

    except MaxTokensReachedException as e:
        logger.warning("Distribution Agent hit token limit, returning partial response")
        return {
            "status": "success",
            "distribution_recommendation": get_response_text(e, agent=agent)
        }

    except Exception as e:
        error_msg = f"Error in Distribution Agent: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "distribution_recommendation": "Error: unavailable.",
            "error": error_msg
        }
