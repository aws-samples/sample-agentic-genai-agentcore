"""
entrypoint — BedrockAgentCoreApp serving the Supply Chain runtime.

Exposes a single @app.entrypoint handler that receives
{"prompt": "..."} payloads, delegates to the orchestrator agent,
and streams responses back via AgentCore Runtime.
"""
