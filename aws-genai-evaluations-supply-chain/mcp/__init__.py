"""
mcp — Standalone MCP tools server runtime deployed on AgentCore.

Exposes document-authoring tools (research_topic, generate_outline,
update_document, publish_document) over the MCP streamable-HTTP
transport. The AGUI agent runtime connects here as a client to
invoke these tools during orchestration.

mcp_tools_server : FastMCP application defining the tool endpoints
                   and running in stateless-HTTP mode for AgentCore.
"""
