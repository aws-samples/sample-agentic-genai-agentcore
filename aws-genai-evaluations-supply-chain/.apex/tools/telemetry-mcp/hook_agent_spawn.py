#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
APEX Telemetry agentSpawn hook.

Reads the hook event JSON from stdin, extracts session_id, and invokes
the telemetry MCP script in CLI mode to send a workflow_started event.

Runs with zero dependencies (stdlib only) — the telemetry_mcp.py script
handles auth and network.
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def main():
    # Parse hook event from stdin
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        event = {}

    session_id = event.get("session_id", "")
    cwd = event.get("cwd", os.getcwd())

    # Resolve user alias
    alias = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))

    # Resolve telemetry script path (sibling file)
    script_dir = Path(__file__).resolve().parent
    telemetry_script = script_dir / "telemetry_mcp.py"

    # Read version from build stamp
    version = "unknown"
    # version.txt is at context/ level; script is at context/tools/telemetry-mcp/
    version_file = script_dir.parent.parent / "version.txt"
    if version_file.exists():
        raw = version_file.read_text().strip()
        # Extract semver (e.g. "2.1.0-rc6" from "apex-extension v2.1.0-rc6 (sha)")
        import re
        m = re.search(r"v?(\d+\.\d+\.\d+[^\s]*)", raw)
        version = m.group(1) if m else raw

    # Determine workflow_id from agent name (passed via --agent-name or env fallback)
    agent_name = "apex-design-agent"
    if "--agent-name" in sys.argv:
        idx = sys.argv.index("--agent-name")
        if idx + 1 < len(sys.argv):
            agent_name = sys.argv[idx + 1]
    else:
        agent_name = os.environ.get("APEX_AGENT_NAME", agent_name)
    workflow_id = "spec-generation" if "design" in agent_name else "build"

    # Set telemetry environment if specified (injected by assembler for experimental builds)
    if "--telemetry-env" in sys.argv:
        idx = sys.argv.index("--telemetry-env")
        if idx + 1 < len(sys.argv):
            os.environ["APEX_TELEMETRY_ENV"] = sys.argv[idx + 1]

    # Detect caller context (Amazon Quick via ACP vs standalone kiro-cli)
    caller = os.environ.get("APEX_CALLER", "")
    ide_type = "amazon-quick-acp-kiro-cli" if "quick" in caller else "kiro-cli"

    # Read engagement tracking from .apex/workspace-config.json (same format as IDE)
    project_id = ""
    opportunity_id = ""
    workspace_config = Path(cwd) / ".apex" / "workspace-config.json"
    if workspace_config.exists():
        try:
            cfg = json.loads(workspace_config.read_text())
            tracking = cfg.get("engagementTracking", {})
            project_id = tracking.get("projectId", "")
            opportunity_id = tracking.get("opportunityId", "")
        except (json.JSONDecodeError, OSError):
            pass

    # Build metadata
    metadata = json.dumps({
        "extension_version": version,
        "ide_type": ide_type,
        "os_platform": platform.system().lower(),
        "agent_name": agent_name,
        "workflow_id": workflow_id,
    })

    # Invoke telemetry script in CLI mode
    cmd = ["uv", "run", "--script", str(telemetry_script), "workflow_started", alias]
    if session_id:
        cmd.extend(["--session-id", session_id])
    if project_id:
        cmd.extend(["--project-id", project_id])
    if opportunity_id:
        cmd.extend(["--opportunity-id", opportunity_id])
    cmd.extend(["--metadata", metadata])

    try:
        result = subprocess.run(cmd, timeout=14, capture_output=True, text=True)
        if result.returncode == 0 and "success" in result.stdout:
            print("✓ Telemetry: session started")
    except (subprocess.TimeoutExpired, OSError):
        pass  # Fire-and-forget — never block the agent


if __name__ == "__main__":
    main()
