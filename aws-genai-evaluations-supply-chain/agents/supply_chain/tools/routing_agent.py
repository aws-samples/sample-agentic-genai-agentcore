from strands import tool
from typing import Any, Dict

import logging

from strands.types.exceptions import MaxTokensReachedException
from utils.mcp_utils import get_mcp_tools
from utils.fallback_data import get_routing_fallback
from utils.agent_utils import (
    create_agent,
    get_response_text
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _make_fallback_tools():
    """Create a local tool that serves canned routing data."""
    @tool
    def get_routing_data(origin: str, destination: str) -> str:
        """Get shipping route options between two locations.

        Args:
            origin: The origin location identifier.
            destination: The destination location identifier.

        Returns:
            JSON string with available route options including carrier, transit time, and cost.
        """
        return get_routing_fallback(f"{origin} {destination}")

    return [get_routing_data]


SYSTEM_PROMPT = """You are a supply chain routing and logistics specialist for Northstar Retail Group.
You call the routing MCP tool to retrieve carrier options and shipping routes between locations.

The routing API (get_routing_data) accepts:
- origin: location identifier (e.g. "loc-fc-east", "loc-fc-west")
- destination: location identifier (e.g. "loc-store-nyc", "loc-fc-west")

It returns a RoutingResponse with:
- origin, destination
- options: a list of RouteOption objects, each containing:
  - carrier_name: name of the logistics carrier (e.g. "FastShip Express", "EcoFreight", "CrossCountry Logistics")
  - estimated_transit_days: integer days in transit
  - estimated_cost: decimal cost in USD

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
1. Call get_routing_data with the origin and destination from the user's query.
2. Compare the route options by cost, transit time, and service level.
3. Recommend the best option based on the user's priorities (speed vs. cost).
4. If the user has a delivery deadline, identify which carriers can meet it.

IMPORTANT constraints:
- Use at most 3 tool calls to gather data, then synthesize your answer.
- Return your analysis as text. Keep responses under 500 words.
- Always include estimated cost and transit time for each recommended route.
- Always state a clear recommendation: which carrier to use and why.
- Always explain the cost vs. speed tradeoff between available options.
- NEVER invent or estimate data. You MUST call get_routing_data to get real numbers.
  If the tool call fails, say so — do not fabricate a response.
"""


@tool
def routing_agent(query: str) -> Dict[str, Any]:
    """
    Analyzes logistics routes and recommends optimal shipping strategies
    considering cost, transit time, and reliability.

    Args:
    - query: The routing query (e.g., "What is the most cost-effective route to ship 500 units from Chicago to Miami by Friday?")

    Returns:
    {
        "status": "success" | "error",
        "routing_recommendation": str,
        "error": str  # Only present if status is "error"
    }
    """
    try:
        logger.info(f"Routing Agent received query ({len(query)} chars): {query[:500]}")
        tools = get_mcp_tools()

        if not tools:
            logger.warning("MCP unavailable — using fallback canned data for routing")
            tools = _make_fallback_tools()

        agent = create_agent(SYSTEM_PROMPT, tools)
        response = agent(query)
        response_text = get_response_text(response)

        logger.info(f"Successful routing analysis ({len(response_text)} chars): {response_text[:100]}")
        return {
            "status": "success",
            "routing_recommendation": response_text
        }

    except MaxTokensReachedException as e:
        logger.warning("Routing Agent hit token limit, returning partial response")
        return {
            "status": "success",
            "routing_recommendation": get_response_text(e, agent=agent)
        }

    except Exception as e:
        error_msg = f"Error in Routing Agent: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "routing_recommendation": "Error: unavailable.",
            "error": error_msg
        }
