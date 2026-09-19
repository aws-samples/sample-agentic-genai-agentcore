"""Mock schema models for supply chain domain entities."""

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class LocationType(str, Enum):
    """Type of supply chain location."""

    FULFILLMENT_CENTER = "fulfillment_center"
    STORE = "store"
    DIGITAL_CHANNEL = "digital_channel"


class Product(BaseModel):
    """A product in the supply chain."""

    product_id: str
    name: str
    sku: str
    category: str


class Location(BaseModel):
    """A supply chain location (fulfillment center, store, or digital channel)."""

    location_id: str
    name: str
    location_type: LocationType
    region: str


class Inventory(BaseModel):
    """Inventory record referencing a Product and a Location."""

    inventory_id: str
    product: Product
    location: Location
    quantity_on_hand: int
    quantity_reserved: int


class Carrier(BaseModel):
    """A logistics carrier."""

    carrier_id: str
    name: str
    service_level: str


class Route(BaseModel):
    """A route between two locations via a carrier."""

    route_id: str
    origin: Location
    destination: Location
    carrier: Carrier
    estimated_transit_days: int
    estimated_cost: Decimal


class Shipment(BaseModel):
    """A shipment referencing source, destination, carrier, and product quantities."""

    shipment_id: str
    origin: Location
    destination: Location
    carrier: Carrier
    items: List[dict]  # [{"product_id": str, "quantity": int}]


# --- Response Models ---


class OptimizationConstraints(BaseModel):
    """Constraints evaluated during optimization."""

    budget_limit: Decimal
    budget_used: Decimal
    warehouse_capacity: int
    warehouse_utilization: int
    inventory_holding_cost: Decimal


class OptimizationResponse(BaseModel):
    """Response from the optimization endpoint."""

    product_id: str
    location: Location
    time_horizon: str
    demand_forecast: int
    recommended_inventory_level: int
    confidence: float
    constraints: OptimizationConstraints


class RebalancingSuggestion(BaseModel):
    """A single rebalancing suggestion within a distribution response."""

    source_location: Location
    destination_location: Location
    product_id: str
    transfer_quantity: int


class DistributionResponse(BaseModel):
    """Response from the distribution endpoint."""

    product_id: str
    suggestions: List[RebalancingSuggestion]


class RouteOption(BaseModel):
    """A single route option within a routing response."""

    carrier_name: str
    estimated_transit_days: int
    estimated_cost: Decimal


class RoutingResponse(BaseModel):
    """Response from the routing endpoint."""

    origin: str
    destination: str
    options: List[RouteOption]


class AnalyticsResponse(BaseModel):
    """Response from the analytics endpoint."""

    query_type: str
    columns: List[str]
    rows: List[List[str]]


class ErrorResponse(BaseModel):
    """Error response returned on invalid requests."""

    error: str
    missing_parameters: Optional[List[str]] = None
