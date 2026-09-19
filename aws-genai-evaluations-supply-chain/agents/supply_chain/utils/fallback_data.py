"""Fallback data access — serves canned responses when MCP tools are unavailable.

This provides the same data the Lambda handlers would return, enabling
the agent to produce evaluatable responses even without MCP connectivity.
"""

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# --- Inline canned data (mirrors supply_chain_data/canned_data.py) ---

OPTIMIZATION_DATA = {
    "prod-001": {"product_id": "prod-001", "location": {"location_id": "loc-fc-east", "name": "East Fulfillment Center", "location_type": "fulfillment_center", "region": "us-east-1"}, "time_horizon": "30d", "demand_forecast": 1200, "recommended_inventory_level": 1500, "confidence": 0.87, "constraints": {"budget_limit": "50000.00", "budget_used": "32500.00", "warehouse_capacity": 5000, "warehouse_utilization": 3200, "inventory_holding_cost": "2.50"}},
    "prod-002": {"product_id": "prod-002", "location": {"location_id": "loc-fc-west", "name": "West Fulfillment Center", "location_type": "fulfillment_center", "region": "us-west-2"}, "time_horizon": "30d", "demand_forecast": 800, "recommended_inventory_level": 1000, "confidence": 0.92, "constraints": {"budget_limit": "30000.00", "budget_used": "21000.00", "warehouse_capacity": 3000, "warehouse_utilization": 2100, "inventory_holding_cost": "1.80"}},
    "prod-003": {"product_id": "prod-003", "location": {"location_id": "loc-fc-east", "name": "East Fulfillment Center", "location_type": "fulfillment_center", "region": "us-east-1"}, "time_horizon": "30d", "demand_forecast": 3500, "recommended_inventory_level": 4000, "confidence": 0.79, "constraints": {"budget_limit": "100000.00", "budget_used": "78000.00", "warehouse_capacity": 10000, "warehouse_utilization": 8500, "inventory_holding_cost": "3.20"}},
    "prod-004": {"product_id": "prod-004", "location": {"location_id": "loc-fc-central", "name": "Central Fulfillment Center", "location_type": "fulfillment_center", "region": "us-central-1"}, "time_horizon": "30d", "demand_forecast": 2200, "recommended_inventory_level": 2600, "confidence": 0.84, "constraints": {"budget_limit": "75000.00", "budget_used": "45000.00", "warehouse_capacity": 7000, "warehouse_utilization": 4800, "inventory_holding_cost": "2.10"}},
    "prod-005": {"product_id": "prod-005", "location": {"location_id": "loc-dc-south", "name": "Southern Distribution Center", "location_type": "fulfillment_center", "region": "us-south-1"}, "time_horizon": "30d", "demand_forecast": 450, "recommended_inventory_level": 600, "confidence": 0.91, "constraints": {"budget_limit": "20000.00", "budget_used": "12000.00", "warehouse_capacity": 2000, "warehouse_utilization": 1100, "inventory_holding_cost": "4.50"}},
    "prod-006": {"product_id": "prod-006", "location": {"location_id": "loc-fc-west", "name": "West Fulfillment Center", "location_type": "fulfillment_center", "region": "us-west-2"}, "time_horizon": "30d", "demand_forecast": 5000, "recommended_inventory_level": 5800, "confidence": 0.76, "constraints": {"budget_limit": "150000.00", "budget_used": "120000.00", "warehouse_capacity": 12000, "warehouse_utilization": 10200, "inventory_holding_cost": "1.50"}},
    "prod-007": {"product_id": "prod-007", "location": {"location_id": "loc-fc-east", "name": "East Fulfillment Center", "location_type": "fulfillment_center", "region": "us-east-1"}, "time_horizon": "30d", "demand_forecast": 1800, "recommended_inventory_level": 2100, "confidence": 0.88, "constraints": {"budget_limit": "60000.00", "budget_used": "38000.00", "warehouse_capacity": 6000, "warehouse_utilization": 3900, "inventory_holding_cost": "2.80"}},
    "prod-008": {"product_id": "prod-008", "location": {"location_id": "loc-fc-central", "name": "Central Fulfillment Center", "location_type": "fulfillment_center", "region": "us-central-1"}, "time_horizon": "30d", "demand_forecast": 950, "recommended_inventory_level": 1200, "confidence": 0.93, "constraints": {"budget_limit": "35000.00", "budget_used": "18000.00", "warehouse_capacity": 4000, "warehouse_utilization": 2200, "inventory_holding_cost": "3.00"}},
}

DISTRIBUTION_DATA = {
    "prod-001": {"product_id": "prod-001", "suggestions": [{"source_location": {"location_id": "loc-fc-east", "name": "East Fulfillment Center", "location_type": "fulfillment_center", "region": "us-east-1"}, "destination_location": {"location_id": "loc-store-nyc", "name": "NYC Flagship Store", "location_type": "store", "region": "us-east-1"}, "product_id": "prod-001", "transfer_quantity": 200}, {"source_location": {"location_id": "loc-fc-east", "name": "East Fulfillment Center", "location_type": "fulfillment_center", "region": "us-east-1"}, "destination_location": {"location_id": "loc-digital-main", "name": "Main Digital Channel", "location_type": "digital_channel", "region": "us-east-1"}, "product_id": "prod-001", "transfer_quantity": 100}]},
    "prod-003": {"product_id": "prod-003", "suggestions": [{"source_location": {"location_id": "loc-fc-east", "name": "East Fulfillment Center", "location_type": "fulfillment_center", "region": "us-east-1"}, "destination_location": {"location_id": "loc-fc-west", "name": "West Fulfillment Center", "location_type": "fulfillment_center", "region": "us-west-2"}, "product_id": "prod-003", "transfer_quantity": 500}, {"source_location": {"location_id": "loc-fc-west", "name": "West Fulfillment Center", "location_type": "fulfillment_center", "region": "us-west-2"}, "destination_location": {"location_id": "loc-store-nyc", "name": "NYC Flagship Store", "location_type": "store", "region": "us-east-1"}, "product_id": "prod-003", "transfer_quantity": 150}]},
    "prod-004": {"product_id": "prod-004", "suggestions": [{"source_location": {"location_id": "loc-fc-central", "name": "Central Fulfillment Center", "location_type": "fulfillment_center", "region": "us-central-1"}, "destination_location": {"location_id": "loc-store-chi", "name": "Chicago Store", "location_type": "store", "region": "us-central-1"}, "product_id": "prod-004", "transfer_quantity": 400}, {"source_location": {"location_id": "loc-fc-central", "name": "Central Fulfillment Center", "location_type": "fulfillment_center", "region": "us-central-1"}, "destination_location": {"location_id": "loc-store-la", "name": "Los Angeles Store", "location_type": "store", "region": "us-west-2"}, "product_id": "prod-004", "transfer_quantity": 250}]},
    "prod-006": {"product_id": "prod-006", "suggestions": [{"source_location": {"location_id": "loc-fc-west", "name": "West Fulfillment Center", "location_type": "fulfillment_center", "region": "us-west-2"}, "destination_location": {"location_id": "loc-store-la", "name": "Los Angeles Store", "location_type": "store", "region": "us-west-2"}, "product_id": "prod-006", "transfer_quantity": 600}, {"source_location": {"location_id": "loc-fc-east", "name": "East Fulfillment Center", "location_type": "fulfillment_center", "region": "us-east-1"}, "destination_location": {"location_id": "loc-digital-intl", "name": "International Digital Channel", "location_type": "digital_channel", "region": "eu-west-1"}, "product_id": "prod-006", "transfer_quantity": 300}, {"source_location": {"location_id": "loc-fc-central", "name": "Central Fulfillment Center", "location_type": "fulfillment_center", "region": "us-central-1"}, "destination_location": {"location_id": "loc-dc-south", "name": "Southern Distribution Center", "location_type": "fulfillment_center", "region": "us-south-1"}, "product_id": "prod-006", "transfer_quantity": 450}]},
    "prod-007": {"product_id": "prod-007", "suggestions": [{"source_location": {"location_id": "loc-dc-south", "name": "Southern Distribution Center", "location_type": "fulfillment_center", "region": "us-south-1"}, "destination_location": {"location_id": "loc-store-nyc", "name": "NYC Flagship Store", "location_type": "store", "region": "us-east-1"}, "product_id": "prod-007", "transfer_quantity": 220}, {"source_location": {"location_id": "loc-fc-east", "name": "East Fulfillment Center", "location_type": "fulfillment_center", "region": "us-east-1"}, "destination_location": {"location_id": "loc-store-chi", "name": "Chicago Store", "location_type": "store", "region": "us-central-1"}, "product_id": "prod-007", "transfer_quantity": 180}]},
}

ROUTING_DATA = {
    ("loc-fc-east", "loc-store-nyc"): {"origin": "loc-fc-east", "destination": "loc-store-nyc", "options": [{"carrier_name": "FastShip Express", "estimated_transit_days": 1, "estimated_cost": "45.00"}, {"carrier_name": "EcoFreight", "estimated_transit_days": 3, "estimated_cost": "22.50"}]},
    ("loc-fc-central", "loc-store-chi"): {"origin": "loc-fc-central", "destination": "loc-store-chi", "options": [{"carrier_name": "FastShip Express", "estimated_transit_days": 1, "estimated_cost": "35.00"}, {"carrier_name": "EcoFreight", "estimated_transit_days": 2, "estimated_cost": "18.00"}]},
    ("loc-dc-south", "loc-fc-east"): {"origin": "loc-dc-south", "destination": "loc-fc-east", "options": [{"carrier_name": "EcoFreight", "estimated_transit_days": 3, "estimated_cost": "55.00"}, {"carrier_name": "CrossCountry Logistics", "estimated_transit_days": 4, "estimated_cost": "42.00"}]},
    ("loc-fc-west", "loc-store-la"): {"origin": "loc-fc-west", "destination": "loc-store-la", "options": [{"carrier_name": "FastShip Express", "estimated_transit_days": 1, "estimated_cost": "28.00"}, {"carrier_name": "EcoFreight", "estimated_transit_days": 2, "estimated_cost": "15.00"}]},
    ("loc-fc-east", "loc-dc-south"): {"origin": "loc-fc-east", "destination": "loc-dc-south", "options": [{"carrier_name": "CrossCountry Logistics", "estimated_transit_days": 3, "estimated_cost": "78.00"}, {"carrier_name": "FastShip Express", "estimated_transit_days": 1, "estimated_cost": "145.00"}]},
}

ANALYTICS_DATA = {
    "inventory_turnover": {"query_type": "inventory_turnover", "columns": ["product_id", "location_id", "turnover_rate", "period"], "rows": [["prod-001", "loc-fc-east", "4.2", "2025-Q1"], ["prod-002", "loc-fc-west", "3.8", "2025-Q1"], ["prod-003", "loc-fc-east", "5.1", "2025-Q1"], ["prod-004", "loc-fc-central", "3.5", "2025-Q1"], ["prod-005", "loc-dc-south", "6.2", "2025-Q1"], ["prod-006", "loc-fc-west", "2.9", "2025-Q1"], ["prod-007", "loc-fc-east", "4.8", "2025-Q1"], ["prod-008", "loc-fc-central", "3.1", "2025-Q1"]]},
    "demand_trends": {"query_type": "demand_trends", "columns": ["product_id", "month", "units_sold", "trend"], "rows": [["prod-001", "2025-01", "1100", "increasing"], ["prod-001", "2025-02", "1250", "increasing"], ["prod-002", "2025-01", "780", "stable"], ["prod-003", "2025-01", "3200", "increasing"], ["prod-003", "2025-02", "3450", "increasing"], ["prod-004", "2025-01", "2050", "stable"], ["prod-005", "2025-01", "420", "decreasing"], ["prod-006", "2025-01", "4800", "increasing"], ["prod-007", "2025-01", "1750", "stable"], ["prod-008", "2025-01", "900", "increasing"]]},
    "shipment_performance": {"query_type": "shipment_performance", "columns": ["carrier", "on_time_pct", "avg_transit_days", "total_shipments"], "rows": [["FastShip Express", "96.5", "1.8", "342"], ["EcoFreight", "89.2", "3.2", "215"], ["CrossCountry Logistics", "91.0", "5.4", "128"]]},
}


def _extract_product_id(query: str) -> str:
    """Extract product ID from a query string."""
    match = re.search(r"prod-\d+", query)
    return match.group(0) if match else "prod-001"


def _extract_locations(query: str) -> tuple:
    """Extract origin/destination location IDs from a query string."""
    location_map = {
        "east fulfillment": "loc-fc-east", "east fc": "loc-fc-east",
        "west fulfillment": "loc-fc-west", "west fc": "loc-fc-west",
        "central fulfillment": "loc-fc-central", "central fc": "loc-fc-central",
        "southern distribution": "loc-dc-south", "southern dc": "loc-dc-south",
        "nyc": "loc-store-nyc", "new york": "loc-store-nyc",
        "los angeles": "loc-store-la", "la store": "loc-store-la",
        "chicago": "loc-store-chi",
    }
    found = []
    query_lower = query.lower()
    for name, loc_id in location_map.items():
        if name in query_lower and loc_id not in found:
            found.append(loc_id)
    if len(found) >= 2:
        return (found[0], found[1])
    elif len(found) == 1:
        return (found[0], "loc-store-nyc")
    return ("loc-fc-east", "loc-store-nyc")


def _extract_query_type(query: str) -> str:
    """Extract analytics query type from a query string."""
    query_lower = query.lower()
    if "turnover" in query_lower:
        return "inventory_turnover"
    elif "demand" in query_lower or "trend" in query_lower:
        return "demand_trends"
    elif "shipment" in query_lower or "carrier" in query_lower or "delivery" in query_lower:
        return "shipment_performance"
    return "inventory_turnover"


def get_optimization_fallback(query: str) -> str:
    """Return canned optimization data as JSON string."""
    product_id = _extract_product_id(query)
    data = OPTIMIZATION_DATA.get(product_id, OPTIMIZATION_DATA["prod-001"])
    return json.dumps(data)


def get_distribution_fallback(query: str) -> str:
    """Return canned distribution data as JSON string."""
    product_id = _extract_product_id(query)
    data = DISTRIBUTION_DATA.get(product_id, DISTRIBUTION_DATA["prod-001"])
    return json.dumps(data)


def get_routing_fallback(query: str) -> str:
    """Return canned routing data as JSON string."""
    # First try direct ID lookup (when called with IDs like "loc-fc-east loc-store-nyc")
    parts = query.strip().split()
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            key = (parts[i], parts[j])
            if key in ROUTING_DATA:
                return json.dumps(ROUTING_DATA[key])
    # Fall back to name-based extraction
    origin, destination = _extract_locations(query)
    data = ROUTING_DATA.get((origin, destination))
    if data is None:
        data = next(iter(ROUTING_DATA.values()))
    return json.dumps(data)


def get_analytics_fallback(query: str) -> str:
    """Return canned analytics data as JSON string."""
    query_type = _extract_query_type(query)
    data = ANALYTICS_DATA.get(query_type, ANALYTICS_DATA["inventory_turnover"])
    return json.dumps(data)
