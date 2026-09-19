import logging
import os

from strands.tools.mcp import MCPClient

# Optional import — package may not be available in all environments
try:
    from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
    _HAS_MCP_PROXY = True
except ImportError:
    _HAS_MCP_PROXY = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Module-level MCP client (kept alive for the runtime lifetime)
_mcp_client: MCPClient | None = None
_mcp_tools: list = []

# ---------------------------------------------------------------------------
# MCP Server Configuration — points to the SEPARATE tools runtime
# ---------------------------------------------------------------------------

MCP_SERVER_ARN = os.environ.get("MCP_SERVER_ARN", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# ---------------------------------------------------------------------------
# MCP Tools — loaded from the remote MCP server runtime
# ---------------------------------------------------------------------------


def build_mcp_url() -> str:
    """Build the MCP invocations URL from the server ARN."""
    encoded_arn = MCP_SERVER_ARN.replace(":", "%3A").replace("/", "%2F")
    return (
        f"https://bedrock-agentcore.{AWS_REGION}.amazonaws.com"
        f"/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    )


def create_mcp_client() -> MCPClient:
    """Create a Strands MCPClient connected to the remote MCP tools runtime."""
    if not _HAS_MCP_PROXY:
        raise ImportError("mcp-proxy-for-aws not installed — MCP unavailable")

    mcp_url = build_mcp_url()
    logger.info(f"Connecting to MCP tools server: {MCP_SERVER_ARN}")
    logger.info(f"MCP URL: {mcp_url}")

    client = MCPClient(lambda: aws_iam_streamablehttp_client(
        endpoint=mcp_url,
        aws_region=AWS_REGION,
        aws_service="bedrock-agentcore",
    ))
    return client


def init_mcp_client():
    """Start the MCP client with retry for cold-start latency."""
    global _mcp_client
    if _mcp_client is not None:
        return

    if not _HAS_MCP_PROXY:
        logger.warning("mcp-proxy-for-aws not available — skipping MCP init")
        return

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            _mcp_client = create_mcp_client()
            _mcp_client.start()
            logger.info(f"MCP client started successfully (attempt {attempt}).")
            return
        except Exception as e:
            logger.warning(
                f"MCP client init attempt {attempt}/{max_retries} failed: {str(e)}"
            )
            _mcp_client = None
            if attempt < max_retries:
                import time
                time.sleep(2 * attempt)

    logger.error("All MCP client initialization attempts failed.")


def get_mcp_tools() -> list:
    """Loads tools from MCP server or returns cached tools."""
    global _mcp_client, _mcp_tools
    if _mcp_tools:
        return _mcp_tools

    if _mcp_client is None:
        init_mcp_client()

    if _mcp_client is None:
        logger.warning("MCP client is None — fallback tools will be used")
        return []

    try:
        logger.info("Listing MCP tools...")
        _mcp_tools = _mcp_client.list_tools_sync()
        logger.info(
            f"Loaded {len(_mcp_tools)} tools from MCP server: "
            f"{[t.tool_name for t in _mcp_tools]}"
        )
    except Exception as e:
        _mcp_tools = []
        logger.error(f"Failed to load MCP tools: {str(e)}")

    return _mcp_tools
