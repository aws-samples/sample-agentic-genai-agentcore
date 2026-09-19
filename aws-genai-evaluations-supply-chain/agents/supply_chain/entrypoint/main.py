"""
BedrockAgentCoreApp entrypoint for the Supply Chain runtime.

Architecture:
  AgentCore Runtime ──▶ THIS MODULE ──▶ orchestrator_agent ──▶ tools/*
                        (BedrockAgentCoreApp)   (Strands+Claude)

Payload format:
  {"prompt": "What is the optimal inventory level for SKU-1234?"}

The orchestrator agent handles memory via AgentCoreMemorySessionManager.
This entrypoint only needs to extract IDs and pass them through.
"""

import json
import logging
import re

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from orchestrator_agent import orchestrator_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload, context):
    """Handler for agent invocation.

    Args:
        payload: Dict with at least {"prompt": "..."}.
        context: AgentCore runtime context (session_id, etc.).
    """
    prompt = payload.get(
        "prompt",
        "No prompt provided. Please send a JSON payload with a 'prompt' key.",
    )

    session_id = context.session_id
    actor_id = getattr(context, "user_id", None) or "unknown"

    logger.info(
        f"Invocation: actor={actor_id}, session={session_id}, "
        f"prompt=({len(prompt)} chars)"
    )

    try:
        agent = orchestrator_agent(actor_id=actor_id, session_id=session_id)
    except Exception as e:
        logger.error(f"Agent initialization failed: {e}")
        return json.dumps({"error": str(e)})

    # Collect streaming response and return as a single string
    parts = []
    async for event in agent.stream_async(prompt):
        if "data" in event:
            parts.append(str(event["data"]))
    response = "".join(parts)

    # Strip inline <thinking>...</thinking> blocks
    response = re.sub(
        r"<thinking>.*?</thinking>", "", response, flags=re.DOTALL
    ).strip()

    return response


if __name__ == "__main__":
    app.run()
