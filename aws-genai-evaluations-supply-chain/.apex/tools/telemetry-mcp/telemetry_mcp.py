#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp>=2.0.0", "boto3>=1.34.0"]
# ///
"""
APEX Telemetry MCP Server (kiro-cli)

Single-file MCP server that emits telemetry events to the APEX telemetry
backend. Auth flow: mcscli (MCS) → Federate OIDC id_token → Cognito
Identity Pool → SigV4-signed POST to API Gateway.

No dependency on mwinit or ~/.midway/cookie — uses mcscli for auth.

Invoked by kiro-cli via: uv run --script telemetry_mcp.py
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import string
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qs

# Prevent ambient AWS credentials from interfering with Cognito auth flow.
# Must run before importing boto3 (which caches credential providers at import).
for _var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
             "AWS_PROFILE", "AWS_SHARED_CREDENTIALS_FILE", "AWS_CONFIG_FILE"):
    os.environ.pop(_var, None)

import boto3
from botocore.config import Config
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_ENV_CONFIG = {
    "prod": {
        "api_url": "https://telemetry-api.apex.aws.dev/telemetry",
        "identity_pool_id": "us-east-1:9c9481f0-6ae4-488c-85d7-f3cc7ed32cc8",
        "client_id": "apex-telemetry-mcp",
    },
    "beta": {
        "api_url": "https://4ojst1huuc.execute-api.us-east-1.amazonaws.com/prod/telemetry",
        "identity_pool_id": "us-east-1:a7ec038e-8309-460b-9ca3-e9033b320cb6",
        "client_id": "apex-telemetry-mcp-beta",
    },
}
_ENV = os.environ.get("APEX_TELEMETRY_ENV", "prod")
_CFG = _ENV_CONFIG.get(_ENV, _ENV_CONFIG["prod"])

API_URL = os.environ.get("APEX_TELEMETRY_API_URL", _CFG["api_url"])
REGION = "us-east-1"
IDENTITY_POOL_ID = _CFG["identity_pool_id"]
CLIENT_ID = _CFG["client_id"]
FEDERATE_PROVIDER = "idp.federate.amazon.com"
FEDERATE_AUTH_ENDPOINT = "https://idp.federate.amazon.com/api/oauth2/v1/authorize"

LOG_FILE = os.environ.get(
    "APEX_TELEMETRY_LOG_FILE",
    str(Path.home() / ".apex" / "telemetry.log"),
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("apex-telemetry")

# ---------------------------------------------------------------------------
# Auth: mcscli → Federate OIDC → Cognito → SigV4
# ---------------------------------------------------------------------------


def _random_string(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _get_federate_token() -> str:
    """Get OIDC id_token from Federate via mcscli curl (MCS keys process).

    mcscli follows the Federate redirect chain using the MCS keys process
    (no mwinit/cookie dependency) but fails on the final localhost redirect
    (connection refused). The token is parsed from verbose output.
    """
    import re

    params = {
        "response_type": "id_token",
        "client_id": CLIENT_ID,
        "redirect_uri": "http://localhost/callback",
        "scope": "openid",
        "state": _random_string(),
        "nonce": _random_string(),
    }
    url = f"{FEDERATE_AUTH_ENDPOINT}?{urlencode(params)}"

    cookie_path = str(Path.home() / ".midway" / "cookie")
    Path(cookie_path).parent.mkdir(parents=True, exist_ok=True)
    Path(cookie_path).touch(exist_ok=True)

    result = subprocess.run(
        [
            "mcscli", "curl",
            "-c", cookie_path, "-b", cookie_path,
            "-L", "-v", "-s", "-o", os.devnull, url,
        ],
        capture_output=True, text=True, timeout=15,
    )

    # mcscli logs the callback URL (with token) in verbose output before
    # failing to connect to localhost. Parse from combined output.
    output = result.stdout + result.stderr
    match = re.search(r"localhost/callback#id_token=([^&\"\s]+)", output)
    if match:
        return match.group(1)

    raise RuntimeError(
        "Failed to get Federate token via mcscli. "
        "Ensure MCS session is valid: mcscli is-valid session"
    )


def _get_cognito_credentials(id_token: str) -> dict[str, str]:
    """Exchange Federate id_token for temporary AWS credentials via Cognito."""
    client = boto3.client(
        "cognito-identity", region_name=REGION,
        aws_access_key_id="", aws_secret_access_key="",
        config=Config(signature_version="UNSIGNED"),
    )
    identity = client.get_id(
        IdentityPoolId=IDENTITY_POOL_ID,
        Logins={FEDERATE_PROVIDER: id_token},
    )
    creds = client.get_credentials_for_identity(
        IdentityId=identity["IdentityId"],
        Logins={FEDERATE_PROVIDER: id_token},
    )["Credentials"]
    return {
        "access_key": creds["AccessKeyId"],
        "secret_key": creds["SecretKey"],
        "session_token": creds["SessionToken"],
    }


def _sign_v4(method: str, url: str, body: str, creds: dict[str, str]) -> dict[str, str]:
    """Produce SigV4 headers for execute-api."""
    parsed = urlparse(url)
    host = parsed.hostname
    now = datetime.now(timezone.utc)
    datestamp = now.strftime("%Y%m%d")
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")

    canonical_uri = parsed.path or "/"
    canonical_querystring = parsed.query or ""
    payload_hash = hashlib.sha256(body.encode()).hexdigest()

    headers_to_sign = {
        "content-type": "application/json",
        "host": host,
        "x-amz-date": amz_date,
        "x-amz-security-token": creds["session_token"],
    }
    signed_headers = ";".join(sorted(headers_to_sign.keys()))
    canonical_headers = "".join(
        f"{k}:{v}\n" for k, v in sorted(headers_to_sign.items())
    )
    canonical_request = "\n".join([
        method, canonical_uri, canonical_querystring,
        canonical_headers, signed_headers, payload_hash,
    ])

    credential_scope = f"{datestamp}/{REGION}/execute-api/aws4_request"
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", amz_date, credential_scope,
        hashlib.sha256(canonical_request.encode()).hexdigest(),
    ])

    def _h(key: bytes, msg: str) -> bytes:
        return hmac.digest(key, msg.encode(), "sha256")

    signing_key = _h(_h(_h(_h(
        f"AWS4{creds['secret_key']}".encode(), datestamp),
        REGION), "execute-api"), "aws4_request")
    signature = hmac.digest(
        signing_key, string_to_sign.encode(), "sha256"
    ).hex()

    return {
        "Content-Type": "application/json",
        "X-Amz-Date": amz_date,
        "X-Amz-Security-Token": creds["session_token"],
        "Authorization": (
            f"AWS4-HMAC-SHA256 Credential={creds['access_key']}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        ),
    }


# Cache credentials across tool calls within a session
_cached_creds: dict[str, str] | None = None


def _get_credentials() -> dict[str, str]:
    global _cached_creds
    if _cached_creds is None:
        id_token = _get_federate_token()
        _cached_creds = _get_cognito_credentials(id_token)
    return _cached_creds


def _post_telemetry(payload: dict[str, Any]) -> dict[str, Any]:
    """Sign and POST a payload to the telemetry API."""
    body = json.dumps(payload)

    if LOG_FILE:
        Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(body + "\n")

    creds = _get_credentials()
    headers = _sign_v4("POST", API_URL, body, creds)

    # Use urllib to avoid requests dependency
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()
    req = urllib.request.Request(API_URL, data=body.encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP("apex-telemetry")


def _default_alias() -> str:
    """Get alias from OS username (matches Amazon login on corp machines)."""
    import getpass
    return os.environ.get("USER") or getpass.getuser() or ""


@mcp.tool()
def send_telemetry(
    action: str,
    alias: str = "",
    session_id: str = "",
    project_id: str = "",
    salesforce_opportunity_id: str = "",
    metadata: str = "",
) -> str:
    """Send a telemetry event to the APEX telemetry backend.

    Args:
        action: Action name (e.g. "session_start", "stage_complete")
        alias: User alias (Amazon login). Defaults to OS username if omitted.
        session_id: Optional session correlation ID
        project_id: Optional ProServe project ID (e.g. "PR-123456")
        salesforce_opportunity_id: Optional SFDC opportunity ID (006...)
        metadata: Optional JSON string with extra key-value pairs
    """
    resolved_alias = alias or _default_alias()
    if not resolved_alias:
        return json.dumps({"error": "alias could not be determined"})
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "action": action,
        "alias": resolved_alias,
    }
    if session_id:
        payload["session_id"] = session_id
    if project_id:
        payload["project_id"] = project_id
    if salesforce_opportunity_id:
        payload["salesforce_opportunity_id"] = salesforce_opportunity_id
    # Auto-inject default metadata, merge with caller-provided values
    import platform as _platform
    caller = os.environ.get("APEX_CALLER", "")
    ide_type = "amazon-quick-acp-kiro-cli" if "quick" in caller else "kiro-cli"
    agent_name = os.environ.get("APEX_AGENT_NAME", "")
    default_metadata: dict[str, Any] = {
        "os_platform": _platform.system().lower(),
        "ide_type": ide_type,
    }
    if agent_name:
        default_metadata["agent_name"] = agent_name
    # Read extension version from version.txt if available
    _version_file = Path(__file__).resolve().parent.parent.parent / "version.txt"
    if _version_file.exists():
        import re as _re
        _raw = _version_file.read_text().strip()
        _m = _re.search(r"v?(\d+\.\d+\.\d+[^\s]*)", _raw)
        if _m:
            default_metadata["extension_version"] = _m.group(1)

    if metadata:
        try:
            caller_metadata = json.loads(metadata)
            default_metadata.update(caller_metadata)
        except json.JSONDecodeError:
            return json.dumps({"error": "metadata must be valid JSON"})

    payload["metadata"] = default_metadata

    try:
        result = _post_telemetry(payload)
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Telemetry send failed: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def check_telemetry_status(days: int = 30) -> str:
    """Check if telemetry events have been recorded for the current user.

    Returns the most recent event, first event, and total count within the
    specified time window. Use this to verify that telemetry is working or
    to answer questions like "when was my last telemetry event?"

    Args:
        days: Number of days to look back (default 30, max 90)
    """
    try:
        alias = _default_alias()
        if not alias:
            return json.dumps({"error": "alias could not be determined"})
        days = max(1, min(days, 90))

        # Build the status URL with query params
        status_url = API_URL + "/status"
        params = urlencode({"alias": alias, "days": str(days)})
        full_url = f"{status_url}?{params}"

        creds = _get_credentials()
        headers = _sign_v4("GET", full_url, "", creds)

        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        req = urllib.request.Request(full_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=35, context=ctx) as resp:
            return resp.read().decode()
    except Exception as e:
        logger.error(f"Telemetry status check failed: {e}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            # CLI mode: uv run --script telemetry_mcp.py status [--days 30]
            import argparse
            p = argparse.ArgumentParser(description="APEX Telemetry Status")
            p.add_argument("_cmd", help=argparse.SUPPRESS)
            p.add_argument("--days", type=int, default=30)
            args = p.parse_args()
            print(check_telemetry_status(args.days))
        else:
            # CLI mode: uv run --script telemetry_mcp.py <action> <alias> [--session-id X] [--project-id X] [--opportunity-id X]
            import argparse
            p = argparse.ArgumentParser(description="APEX Telemetry CLI")
            p.add_argument("action", help="Event action name")
            p.add_argument("alias", help="User alias")
            p.add_argument("--session-id", default="")
            p.add_argument("--project-id", default="")
            p.add_argument("--opportunity-id", default="")
            p.add_argument("--metadata", default="")
            args = p.parse_args()
            print(send_telemetry(args.action, args.alias, args.session_id,
                                 args.project_id, args.opportunity_id, args.metadata))
    else:
        mcp.run()
