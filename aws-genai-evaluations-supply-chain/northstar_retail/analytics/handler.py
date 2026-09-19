"""Lambda handler for the Analytics API endpoint."""

import json
from typing import Any

from supply_chain_mock.canned_data import (
    ANALYTICS_RESPONSES,
    SUPPORTED_QUERY_TYPES,
)
from supply_chain_mock.schema import ErrorResponse


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle GET /analytics requests.

    Expected query string parameters:
        - query_type: the type of analytics query to run

    Returns:
        API Gateway proxy response with AnalyticsResponse or ErrorResponse.
    """
    params = event.get("queryStringParameters") or {}
    required = ["query_type"]
    missing = [p for p in required if p not in params or not params[p]]

    if missing:
        error = ErrorResponse(
            error=f"Missing required parameters: {', '.join(missing)}",
            missing_parameters=missing,
        )
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": error.model_dump_json(),
        }

    query_type = params["query_type"]

    if query_type not in SUPPORTED_QUERY_TYPES:
        error = ErrorResponse(
            error=f"Unrecognized query_type '{query_type}'. Supported types: {', '.join(SUPPORTED_QUERY_TYPES)}",
        )
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": error.model_dump_json(),
        }

    response = ANALYTICS_RESPONSES[query_type]

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": response.model_dump_json(),
    }
