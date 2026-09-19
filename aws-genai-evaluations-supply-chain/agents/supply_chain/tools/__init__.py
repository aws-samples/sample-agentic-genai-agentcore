"""
tools — Domain-specific sub-agent tools exposed to the orchestrator.

Each module defines a @tool-decorated function that spins up a
Strands agent backed by the remote MCP tool set and returns a
structured result dict.

optimization_agent    : Recommends optimal inventory levels under
                        budget, demand, and capacity constraints.
distribution_agent    : Recommends inventory rebalancing transfers
                        across warehouse locations to reduce risk.
routing_agent         : Optimizes logistics routes considering cost,
                        transit time, and carrier reliability.
analytics_agent       : Surfaces supply chain KPIs, trends, anomalies,
                        and performance insights.
"""
