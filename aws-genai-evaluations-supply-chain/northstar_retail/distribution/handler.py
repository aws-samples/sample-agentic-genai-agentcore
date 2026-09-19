"""Lambda handler for the Distribution API endpoint."""

import json
from typing import Any

from supply_chain_mock.canned_data import DISTRIBUTION_RESPONSES
from supply_chain_mock.schema import ErrorResponse


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle GET /distribution requests.

    Expected query string parameters:
        - product_id: identifier for the product

    Returns:
        API Gateway proxy response with DistributionResponse or ErrorResponse.
    """
    params = event.get("queryStringParameters") or {}
    required = ["product_id"]
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

    product_id = params["product_id"]
    response = DISTRIBUTION_RESPONSES.get(product_id)

    if response is None:
        response = next(iter(DISTRIBUTION_RESPONSES.values()))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": response.model_dump_json(),
    }
