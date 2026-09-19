"""
MCP Tools Server — Exposes supply chain data tools as an MCP server on AgentCore.

This is a SEPARATE AgentCore runtime that exposes tools via MCP protocol.
The Supply Chain orchestrator agent connects to this MCP server to use these tools.

Architecture:
  ┌──────────────────────────┐         ┌──────────────────────────┐         ┌──────────────────────────┐
  │  Supply Chain Orchestrator│──MCP──▶│  MCP Tools Server         │──HTTP──▶│  Northstar Retail API     │
  │  Runtime (Strands+Claude) │        │  Runtime (this file)      │        │  (Lambda + API Gateway)   │
  └──────────────────────────┘         └──────────────────────────┘         └──────────────────────────┘

Tools: get_optimization_data, get_distribution_data, get_routing_data, get_analytics_data

Each tool calls the corresponding Northstar Retail API Gateway endpoint using
the SUPPLY_CHAIN_API_URL environment variable.

Deploy: agentcore configure -e mcp_tools_server.py -p MCP && agentcore deploy
"""

import json
import os
import urllib.request
import urllib.error
import urllib.parse

from mcp.server.fastmcp import FastMCP

# stateless_http=True is required for AgentCore (each request is independent)
mcp = FastMCP(host="0.0.0.0", stateless_http=True)

SUPPLY_CHAIN_API_URL = os.environ.get("SUPPLY_CHAIN_API_URL", "")


def _call_api(endpoint: str, params: dict) -> str:
    """Call a Northstar Retail API endpoint and return the response body."""
    query_string = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    url = f"{SUPPLY_CHAIN_API_URL}/{endpoint}"
    if query_string:
        url = f"{url}?{query_string}"

    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return json.dumps({"error": f"HTTP {e.code}", "details": error_body})
    except urllib.error.URLError as e:
        return json.dumps({"error": "Connection failed", "details": str(e.reason)})


@mcp.tool()
def get_optimization_data(product_id: str, time_horizon: str) -> str:
    """Get demand forecast and inventory optimization recommendations for a product.

    Args:
        product_id: The product identifier to get optimization data for.
        time_horizon: The forecasting time horizon (e.g. "30d", "90d").

    Returns:
        JSON string with demand forecast, recommended inventory levels, and constraints.
    """
    return _call_api("optimization", {
        "product_id": product_id,
        "time_horizon": time_horizon,
    })


@mcp.tool()
def get_distribution_data(product_id: str) -> str:
    """Get inventory rebalancing suggestions across distribution locations.

    Args:
        product_id: The product identifier to get distribution suggestions for.

    Returns:
        JSON string with rebalancing suggestions between locations.
    """
    return _call_api("distribution", {"product_id": product_id})


@mcp.tool()
def get_routing_data(origin: str, destination: str) -> str:
    """Get shipping route options between two locations.

    Args:
        origin: The origin location identifier.
        destination: The destination location identifier.

    Returns:
        JSON string with available route options including carrier, transit time, and cost.
    """
    return _call_api("routing", {
        "origin": origin,
        "destination": destination,
    })


@mcp.tool()
def get_analytics_data(query_type: str) -> str:
    """Get supply chain analytics data for a specific query type.

    Args:
        query_type: The type of analytics query to run (e.g. "inventory_turnover", "demand_trends").

    Returns:
        JSON string with analytics results including columns and data rows.
    """
    return _call_api("analytics", {"query_type": query_type})


if __name__ == "__main__":
    # streamable-http transport — required for AgentCore MCP protocol
    mcp.run(transport="streamable-http")
