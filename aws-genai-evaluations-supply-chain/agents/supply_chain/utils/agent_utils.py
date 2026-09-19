import os
import logging

from typing import Any, Dict, Optional, Union

from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.types.exceptions import MaxTokensReachedException

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def create_agent(
    system_prompt: str,
    tools: list[Any],
    temperature: float = 0.7,
    max_tokens: int = 4096,
    model_id: str = DEFAULT_MODEL_ID,
    region: str = AWS_REGION,
    **kwargs: Any
) -> Agent:
    """
    Creates Strands agent with custom model parameters, system prompt, and tools.

    Arguments
    - system_prompt: The system prompt to use when defining the agent
    - tools: A list of tools to provide the agent
    - temperature: The temperature to use for the model (default 0.7)
    - max_tokens: The maximum number of tokens to generate (default 4096)
    - model_id: The model ID to use for the agent
    - region: The AWS region to use for the agent
    - **kwargs: Additional arguments passed directly to Agent()
      (e.g. session_manager, callback_handler)

    Returns
    - agent: a custom Strands agent
    """
    try:
        agent = Agent(
            model=BedrockModel(
                model_id=model_id,
                region_name=region,
                temperature=temperature,
                max_tokens=max_tokens
            ),
            system_prompt=system_prompt,
            tools=tools,
            **kwargs
        )

        # Compatibility shim: ag_ui_strands 0.1.3 expects agent.state._state
        # but strands-agents 1.34+ uses _data instead
        if hasattr(agent, "state") and agent.state is not None:
            state_obj = agent.state
            if not hasattr(state_obj, "_state") and hasattr(state_obj, "_data"):
                state_obj._state = state_obj._data

        return agent
    except Exception as e:
        logger.info(f"Error creating Strands agent: {str(e)}")
        raise e


def _extract_partial_text(agent: Agent) -> str:
    """Extract any assistant text from agent.messages after a token-limit error."""
    try:
        for msg in reversed(agent.messages):
            if msg.get("role") != "assistant":
                continue
            parts = [
                block["text"]
                for block in (msg.get("content") or [])
                if isinstance(block, dict) and block.get("text")
            ]
            if parts:
                return "\n".join(parts)
    except Exception as e:
        logger.warning(f"Could not extract partial response: {str(e)}")
    return ""


def get_response_text(
    agent_response: Union[Dict[str, Any], Any],
    agent: Optional[Agent] = None,
) -> str:
    """
    Parse agent response to retrieve string response text.

    Arguments
    - agent_response: The agent's raw output (or a MaxTokensReachedException)
    - agent: Optional Agent instance; when provided and agent_response is a
      MaxTokensReachedException, the partial text is extracted from agent.messages.

    Returns
    - response_text: The agent's output as a string
    """
    try:
        # Handle token-limit exceptions — return partial agent response
        if isinstance(agent_response, MaxTokensReachedException):
            logger.warning("MaxTokensReachedException — extracting partial response")
            partial = _extract_partial_text(agent) if agent else ""
            return partial or "[Response truncated — token limit reached]"

        if hasattr(agent_response, 'content'):
            response_text = agent_response.content
        elif hasattr(agent_response, 'message'):
            response_text = agent_response.message.get('content', [{}])[0].get('text', str(agent_response.message))
        else:
            response_text = str(agent_response)

        return response_text
    except Exception as e:
        logger.error(f"Failed to parse agent response: {str(e)}")
        return ""
