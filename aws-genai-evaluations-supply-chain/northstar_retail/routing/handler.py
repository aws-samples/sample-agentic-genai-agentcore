"""Lambda handler for the Routing API endpoint."""

import json
from typing import Any

from supply_chain_mock.canned_data import ROUTING_RESPONSES
from supply_chain_mock.schema import ErrorResponse


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle GET /routing requests.

    Expected query string parameters:
        - origin: origin location identifier
        - destination: destination location identifier

    Returns:
        API Gateway proxy response with RoutingResponse or ErrorResponse.
    """
    params = event.get("queryStringParameters") or {}
    required = ["origin", "destination"]
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

    origin = params["origin"]
    destination = params["destination"]
    response = ROUTING_RESPONSES.get((origin, destination))

    if response is None:
        response = next(iter(ROUTING_RESPONSES.values()))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": response.model_dump_json(),
    }
