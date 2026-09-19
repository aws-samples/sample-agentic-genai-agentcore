"""
utils — Shared helpers for agent creation and MCP connectivity.

agent_utils : Factory for Strands Agent instances (Bedrock model
              configuration, system prompt, tool wiring) and a
              response-text parser.
mcp_utils   : Manages the singleton MCPClient that connects to the
              remote MCP tools server runtime via Cognito-authenticated
              streamable HTTP transport. Provides get_mcp_tools() for
              lazy-loading the tool catalogue.
"""
