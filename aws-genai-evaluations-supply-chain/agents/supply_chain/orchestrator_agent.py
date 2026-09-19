"""
Orchestrator Agent — Multi-agent coordinator for the Supply Chain runtime.

Delegates user requests to domain-specific sub-agent tools:
  - optimization_agent       (inventory optimization under constraints)
  - distribution_agent       (inventory rebalancing across locations)
  - routing_agent            (logistics route optimization)
  - analytics_agent          (supply chain KPIs and insights)

Maintains conversational memory through AgentCore Memory.

Architecture:
  entrypoint/main.py ──▶ THIS MODULE ──▶ tools/*
                                            (Strands+Claude)
"""

import logging
import os

from tools.optimization_agent import optimization_agent
from tools.distribution_agent import distribution_agent
from tools.routing_agent import routing_agent
from tools.analytics_agent import analytics_agent

from utils.agent_utils import create_agent

from strands import Agent
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


MEMORY_ID = os.environ.get("MEMORY_ID", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

SYSTEM_PROMPT = """You are the supply chain orchestration assistant for Northstar Retail Group,
a multinational retailer operating e-commerce channels, regional fulfillment centers,
distribution centers, and thousands of physical stores.

Northstar planners come to you with questions about inventory allocation, distribution
adjustments, shipping logistics, and supply chain diagnostics. You delegate work to
specialized sub-agents:

- optimization_agent: Calls the optimization API to get demand forecasts, recommended
  inventory levels, and constraint analysis (budget, warehouse capacity, holding cost)
  for a given product and time horizon.
- distribution_agent: Calls the distribution API to get inventory rebalancing suggestions
  between fulfillment centers, stores, and digital channels for a given product.
- routing_agent: Calls the routing API to get carrier options with estimated transit days
  and cost between two locations (e.g., loc-fc-east, loc-fc-west, loc-store-nyc).
- analytics_agent: Queries structured supply chain data to answer diagnostics questions
  about inventory turnover, demand trends, and shipment performance.

CRITICAL: Select exactly ONE sub-agent per user query — the single most relevant one.
Do NOT call multiple sub-agents. If the query spans domains, pick the primary one
and note what other agents could provide if the user wants more detail.

Known locations in the system:
- loc-fc-east: East Fulfillment Center (us-east-1)
- loc-fc-west: West Fulfillment Center (us-west-2)
- loc-fc-central: Central Fulfillment Center (us-central-1)
- loc-dc-south: Southern Distribution Center (us-south-1)
- loc-store-nyc: NYC Flagship Store (us-east-1)
- loc-store-la: Los Angeles Store (us-west-2)
- loc-store-chi: Chicago Store (us-central-1)
- loc-digital-main: Main Digital Channel (us-east-1)
- loc-digital-intl: International Digital Channel (eu-west-1)

Known products: prod-001, prod-002, prod-003, prod-004, prod-005, prod-006, prod-007, prod-008

Your workflow:
1. Identify the planner's intent and select the appropriate sub-agent.
2. Formulate a clear query for the sub-agent including relevant parameters.
3. Present the sub-agent's findings in a clear, actionable format for the planner.
"""


def _create_session_manager(actor_id: str, session_id: str) -> AgentCoreMemorySessionManager:
    """
    Creates an AgentCoreMemorySessionManager for the given actor and session IDs.
    """
    config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        actor_id=actor_id,
        session_id=session_id,
        retrieval_config={
            f"/knowledge/{actor_id}/": RetrievalConfig(
                top_k=10,
                relevance_score=0.3
            )
        }
    )

    return AgentCoreMemorySessionManager(config, AWS_REGION)


def orchestrator_agent(actor_id: str, session_id: str) -> Agent:
    """
    Orchestrator Agent. Integrates with AgentCore Memory for
    conversational memory.

    Implements the agents-as-tools framework with four sub-agents
    1. optimization agent
    2. distribution agent
    3. routing agent
    4. analytics agent
    """

    session_manager = None
    if MEMORY_ID:
        try:
            session_manager = _create_session_manager(actor_id, session_id)
            logger.info(f"Session manager created. Memory enabled for actor={actor_id}, session={session_id}")
        except Exception as e:
            logger.warning(f"Memory unavailable, continuing without memory: {str(e)}")

    try:
        agent = create_agent(
            SYSTEM_PROMPT,
            tools=[
                optimization_agent,
                distribution_agent,
                routing_agent,
                analytics_agent
            ],
            session_manager=session_manager
        )
        logger.info("Orchestrator agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Failed to create orchestrator agent: {str(e)}")
        raise RuntimeError(f"Orchestrator agent initialization failed: {str(e)}") from e
