"""Lambda handler for the Optimization API endpoint."""

import json
from typing import Any

from supply_chain_mock.canned_data import OPTIMIZATION_RESPONSES
from supply_chain_mock.schema import ErrorResponse


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle GET /optimization requests.

    Expected query string parameters:
        - product_id: identifier for the product
        - time_horizon: forecasting time horizon

    Returns:
        API Gateway proxy response with OptimizationResponse or ErrorResponse.
    """
    params = event.get("queryStringParameters") or {}
    required = ["product_id", "time_horizon"]
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
    response = OPTIMIZATION_RESPONSES.get(product_id)

    if response is None:
        # Return first available canned response as fallback for unknown product_ids
        response = next(iter(OPTIMIZATION_RESPONSES.values()))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": response.model_dump_json(),
    }
