"""Canned response data for mock supply chain API endpoints."""

from decimal import Decimal

from supply_chain_mock.schema import (
    AnalyticsResponse,
    DistributionResponse,
    Location,
    LocationType,
    OptimizationConstraints,
    OptimizationResponse,
    RebalancingSuggestion,
    RouteOption,
    RoutingResponse,
)

# --- Shared location fixtures (9 locations) ---

LOCATION_FC_EAST = Location(
    location_id="loc-fc-east",
    name="East Fulfillment Center",
    location_type=LocationType.FULFILLMENT_CENTER,
    region="us-east-1",
)

LOCATION_FC_WEST = Location(
    location_id="loc-fc-west",
    name="West Fulfillment Center",
    location_type=LocationType.FULFILLMENT_CENTER,
    region="us-west-2",
)

LOCATION_STORE_NYC = Location(
    location_id="loc-store-nyc",
    name="NYC Flagship Store",
    location_type=LocationType.STORE,
    region="us-east-1",
)

LOCATION_DIGITAL = Location(
    location_id="loc-digital-main",
    name="Main Digital Channel",
    location_type=LocationType.DIGITAL_CHANNEL,
    region="us-east-1",
)

LOCATION_FC_CENTRAL = Location(
    location_id="loc-fc-central",
    name="Central Fulfillment Center",
    location_type=LocationType.FULFILLMENT_CENTER,
    region="us-central-1",
)

LOCATION_STORE_LA = Location(
    location_id="loc-store-la",
    name="Los Angeles Store",
    location_type=LocationType.STORE,
    region="us-west-2",
)

LOCATION_STORE_CHI = Location(
    location_id="loc-store-chi",
    name="Chicago Store",
    location_type=LocationType.STORE,
    region="us-central-1",
)

LOCATION_DC_SOUTH = Location(
    location_id="loc-dc-south",
    name="Southern Distribution Center",
    location_type=LocationType.FULFILLMENT_CENTER,
    region="us-south-1",
)

LOCATION_DIGITAL_INTL = Location(
    location_id="loc-digital-intl",
    name="International Digital Channel",
    location_type=LocationType.DIGITAL_CHANNEL,
    region="eu-west-1",
)


# --- Optimization canned responses keyed by product_id (10 records) ---

OPTIMIZATION_RESPONSES: dict[str, OptimizationResponse] = {
    "prod-001": OptimizationResponse(
        product_id="prod-001",
        location=LOCATION_FC_EAST,
        time_horizon="30d",
        demand_forecast=1200,
        recommended_inventory_level=1500,
        confidence=0.87,
        constraints=OptimizationConstraints(
            budget_limit=Decimal("50000.00"),
            budget_used=Decimal("32500.00"),
            warehouse_capacity=5000,
            warehouse_utilization=3200,
            inventory_holding_cost=Decimal("2.50"),
        ),
    ),
    "prod-002": OptimizationResponse(
        product_id="prod-002",
        location=LOCATION_FC_WEST,
        time_horizon="30d",
        demand_forecast=800,
        recommended_inventory_level=1000,
        confidence=0.92,
        constraints=OptimizationConstraints(
            budget_limit=Decimal("30000.00"),
            budget_used=Decimal("21000.00"),
            warehouse_capacity=3000,
            warehouse_utilization=2100,
            inventory_holding_cost=Decimal("1.80"),
        ),
    ),
    "prod-003": OptimizationResponse(
        product_id="prod-003",
        location=LOCATION_FC_EAST,
        time_horizon="30d",
        demand_forecast=3500,
        recommended_inventory_level=4000,
        confidence=0.79,
        constraints=OptimizationConstraints(
            budget_limit=Decimal("100000.00"),
            budget_used=Decimal("78000.00"),
            warehouse_capacity=10000,
            warehouse_utilization=8500,
            inventory_holding_cost=Decimal("3.20"),
        ),
    ),
    "prod-004": OptimizationResponse(
        product_id="prod-004",
        location=LOCATION_FC_CENTRAL,
        time_horizon="30d",
        demand_forecast=2200,
        recommended_inventory_level=2600,
        confidence=0.84,
        constraints=OptimizationConstraints(
            budget_limit=Decimal("75000.00"),
            budget_used=Decimal("45000.00"),
            warehouse_capacity=7000,
            warehouse_utilization=4800,
            inventory_holding_cost=Decimal("2.10"),
        ),
    ),
    "prod-005": OptimizationResponse(
        product_id="prod-005",
        location=LOCATION_DC_SOUTH,
        time_horizon="30d",
        demand_forecast=450,
        recommended_inventory_level=600,
        confidence=0.91,
        constraints=OptimizationConstraints(
            budget_limit=Decimal("20000.00"),
            budget_used=Decimal("12000.00"),
            warehouse_capacity=2000,
            warehouse_utilization=1100,
            inventory_holding_cost=Decimal("4.50"),
        ),
    ),
    "prod-006": OptimizationResponse(
        product_id="prod-006",
        location=LOCATION_FC_WEST,
        time_horizon="30d",
        demand_forecast=5000,
        recommended_inventory_level=5800,
        confidence=0.76,
        constraints=OptimizationConstraints(
            budget_limit=Decimal("150000.00"),
            budget_used=Decimal("120000.00"),
            warehouse_capacity=12000,
            warehouse_utilization=10200,
            inventory_holding_cost=Decimal("1.50"),
        ),
    ),
    "prod-007": OptimizationResponse(
        product_id="prod-007",
        location=LOCATION_FC_EAST,
        time_horizon="30d",
        demand_forecast=1800,
        recommended_inventory_level=2100,
        confidence=0.88,
        constraints=OptimizationConstraints(
            budget_limit=Decimal("60000.00"),
            budget_used=Decimal("38000.00"),
            warehouse_capacity=6000,
            warehouse_utilization=3900,
            inventory_holding_cost=Decimal("2.80"),
        ),
    ),
    "prod-008": OptimizationResponse(
        product_id="prod-008",
        location=LOCATION_FC_CENTRAL,
        time_horizon="30d",
        demand_forecast=950,
        recommended_inventory_level=1200,
        confidence=0.93,
        constraints=OptimizationConstraints(
            budget_limit=Decimal("35000.00"),
            budget_used=Decimal("18000.00"),
            warehouse_capacity=4000,
            warehouse_utilization=2200,
            inventory_holding_cost=Decimal("3.00"),
        ),
    ),
}


# --- Distribution canned responses keyed by product_id (10 records) ---

DISTRIBUTION_RESPONSES: dict[str, DistributionResponse] = {
    "prod-001": DistributionResponse(
        product_id="prod-001",
        suggestions=[
            RebalancingSuggestion(
                source_location=LOCATION_FC_EAST,
                destination_location=LOCATION_STORE_NYC,
                product_id="prod-001",
                transfer_quantity=200,
            ),
            RebalancingSuggestion(
                source_location=LOCATION_FC_EAST,
                destination_location=LOCATION_DIGITAL,
                product_id="prod-001",
                transfer_quantity=100,
            ),
        ],
    ),
    "prod-002": DistributionResponse(
        product_id="prod-002",
        suggestions=[
            RebalancingSuggestion(
                source_location=LOCATION_FC_WEST,
                destination_location=LOCATION_FC_EAST,
                product_id="prod-002",
                transfer_quantity=350,
            ),
        ],
    ),
    "prod-003": DistributionResponse(
        product_id="prod-003",
        suggestions=[
            RebalancingSuggestion(
                source_location=LOCATION_FC_EAST,
                destination_location=LOCATION_FC_WEST,
                product_id="prod-003",
                transfer_quantity=500,
            ),
            RebalancingSuggestion(
                source_location=LOCATION_FC_WEST,
                destination_location=LOCATION_STORE_NYC,
                product_id="prod-003",
                transfer_quantity=150,
            ),
        ],
    ),
    "prod-004": DistributionResponse(
        product_id="prod-004",
        suggestions=[
            RebalancingSuggestion(
                source_location=LOCATION_FC_CENTRAL,
                destination_location=LOCATION_STORE_CHI,
                product_id="prod-004",
                transfer_quantity=400,
            ),
            RebalancingSuggestion(
                source_location=LOCATION_FC_CENTRAL,
                destination_location=LOCATION_STORE_LA,
                product_id="prod-004",
                transfer_quantity=250,
            ),
        ],
    ),
    "prod-005": DistributionResponse(
        product_id="prod-005",
        suggestions=[
            RebalancingSuggestion(
                source_location=LOCATION_DC_SOUTH,
                destination_location=LOCATION_FC_EAST,
                product_id="prod-005",
                transfer_quantity=180,
            ),
        ],
    ),
    "prod-006": DistributionResponse(
        product_id="prod-006",
        suggestions=[
            RebalancingSuggestion(
                source_location=LOCATION_FC_WEST,
                destination_location=LOCATION_STORE_LA,
                product_id="prod-006",
                transfer_quantity=600,
            ),
            RebalancingSuggestion(
                source_location=LOCATION_FC_EAST,
                destination_location=LOCATION_DIGITAL_INTL,
                product_id="prod-006",
                transfer_quantity=300,
            ),
            RebalancingSuggestion(
                source_location=LOCATION_FC_CENTRAL,
                destination_location=LOCATION_DC_SOUTH,
                product_id="prod-006",
                transfer_quantity=450,
            ),
        ],
    ),
    "prod-007": DistributionResponse(
        product_id="prod-007",
        suggestions=[
            RebalancingSuggestion(
                source_location=LOCATION_DC_SOUTH,
                destination_location=LOCATION_STORE_NYC,
                product_id="prod-007",
                transfer_quantity=220,
            ),
            RebalancingSuggestion(
                source_location=LOCATION_FC_EAST,
                destination_location=LOCATION_STORE_CHI,
                product_id="prod-007",
                transfer_quantity=180,
            ),
        ],
    ),
    "prod-008": DistributionResponse(
        product_id="prod-008",
        suggestions=[
            RebalancingSuggestion(
                source_location=LOCATION_FC_CENTRAL,
                destination_location=LOCATION_FC_WEST,
                product_id="prod-008",
                transfer_quantity=320,
            ),
        ],
    ),
}


# --- Routing canned responses keyed by (origin, destination) tuple (10 records) ---

ROUTING_RESPONSES: dict[tuple[str, str], RoutingResponse] = {
    ("loc-fc-east", "loc-store-nyc"): RoutingResponse(
        origin="loc-fc-east",
        destination="loc-store-nyc",
        options=[
            RouteOption(carrier_name="FastShip Express", estimated_transit_days=1, estimated_cost=Decimal("45.00")),
            RouteOption(carrier_name="EcoFreight", estimated_transit_days=3, estimated_cost=Decimal("22.50")),
        ],
    ),
    ("loc-fc-east", "loc-fc-west"): RoutingResponse(
        origin="loc-fc-east",
        destination="loc-fc-west",
        options=[
            RouteOption(carrier_name="CrossCountry Logistics", estimated_transit_days=5, estimated_cost=Decimal("120.00")),
            RouteOption(carrier_name="FastShip Express", estimated_transit_days=2, estimated_cost=Decimal("210.00")),
        ],
    ),
    ("loc-fc-west", "loc-store-nyc"): RoutingResponse(
        origin="loc-fc-west",
        destination="loc-store-nyc",
        options=[
            RouteOption(carrier_name="CrossCountry Logistics", estimated_transit_days=6, estimated_cost=Decimal("135.00")),
        ],
    ),
    ("loc-fc-central", "loc-store-chi"): RoutingResponse(
        origin="loc-fc-central",
        destination="loc-store-chi",
        options=[
            RouteOption(carrier_name="FastShip Express", estimated_transit_days=1, estimated_cost=Decimal("35.00")),
            RouteOption(carrier_name="EcoFreight", estimated_transit_days=2, estimated_cost=Decimal("18.00")),
        ],
    ),
    ("loc-fc-central", "loc-store-la"): RoutingResponse(
        origin="loc-fc-central",
        destination="loc-store-la",
        options=[
            RouteOption(carrier_name="CrossCountry Logistics", estimated_transit_days=4, estimated_cost=Decimal("95.00")),
            RouteOption(carrier_name="FastShip Express", estimated_transit_days=2, estimated_cost=Decimal("175.00")),
        ],
    ),
    ("loc-dc-south", "loc-fc-east"): RoutingResponse(
        origin="loc-dc-south",
        destination="loc-fc-east",
        options=[
            RouteOption(carrier_name="EcoFreight", estimated_transit_days=3, estimated_cost=Decimal("55.00")),
            RouteOption(carrier_name="CrossCountry Logistics", estimated_transit_days=4, estimated_cost=Decimal("42.00")),
        ],
    ),
    ("loc-fc-west", "loc-store-la"): RoutingResponse(
        origin="loc-fc-west",
        destination="loc-store-la",
        options=[
            RouteOption(carrier_name="FastShip Express", estimated_transit_days=1, estimated_cost=Decimal("28.00")),
            RouteOption(carrier_name="EcoFreight", estimated_transit_days=2, estimated_cost=Decimal("15.00")),
        ],
    ),
    ("loc-fc-east", "loc-dc-south"): RoutingResponse(
        origin="loc-fc-east",
        destination="loc-dc-south",
        options=[
            RouteOption(carrier_name="CrossCountry Logistics", estimated_transit_days=3, estimated_cost=Decimal("78.00")),
            RouteOption(carrier_name="FastShip Express", estimated_transit_days=1, estimated_cost=Decimal("145.00")),
        ],
    ),
    ("loc-dc-south", "loc-store-nyc"): RoutingResponse(
        origin="loc-dc-south",
        destination="loc-store-nyc",
        options=[
            RouteOption(carrier_name="FastShip Express", estimated_transit_days=2, estimated_cost=Decimal("88.00")),
            RouteOption(carrier_name="EcoFreight", estimated_transit_days=4, estimated_cost=Decimal("48.00")),
        ],
    ),
    ("loc-fc-central", "loc-fc-east"): RoutingResponse(
        origin="loc-fc-central",
        destination="loc-fc-east",
        options=[
            RouteOption(carrier_name="CrossCountry Logistics", estimated_transit_days=3, estimated_cost=Decimal("85.00")),
            RouteOption(carrier_name="FastShip Express", estimated_transit_days=1, estimated_cost=Decimal("160.00")),
            RouteOption(carrier_name="EcoFreight", estimated_transit_days=4, estimated_cost=Decimal("62.00")),
        ],
    ),
}


# --- Analytics canned responses keyed by query_type ---

SUPPORTED_QUERY_TYPES = ["inventory_turnover", "demand_trends", "shipment_performance"]

ANALYTICS_RESPONSES: dict[str, AnalyticsResponse] = {
    "inventory_turnover": AnalyticsResponse(
        query_type="inventory_turnover",
        columns=["product_id", "location_id", "turnover_rate", "period"],
        rows=[
            ["prod-001", "loc-fc-east", "4.2", "2025-Q1"],
            ["prod-002", "loc-fc-west", "3.8", "2025-Q1"],
            ["prod-003", "loc-fc-east", "5.1", "2025-Q1"],
            ["prod-004", "loc-fc-central", "3.5", "2025-Q1"],
            ["prod-005", "loc-dc-south", "6.2", "2025-Q1"],
            ["prod-006", "loc-fc-west", "2.9", "2025-Q1"],
            ["prod-007", "loc-fc-east", "4.8", "2025-Q1"],
            ["prod-008", "loc-fc-central", "3.1", "2025-Q1"],
        ],
    ),
    "demand_trends": AnalyticsResponse(
        query_type="demand_trends",
        columns=["product_id", "month", "units_sold", "trend"],
        rows=[
            ["prod-001", "2025-01", "1100", "increasing"],
            ["prod-001", "2025-02", "1250", "increasing"],
            ["prod-002", "2025-01", "780", "stable"],
            ["prod-003", "2025-01", "3200", "increasing"],
            ["prod-003", "2025-02", "3450", "increasing"],
            ["prod-004", "2025-01", "2050", "stable"],
            ["prod-005", "2025-01", "420", "decreasing"],
            ["prod-006", "2025-01", "4800", "increasing"],
            ["prod-007", "2025-01", "1750", "stable"],
            ["prod-008", "2025-01", "900", "increasing"],
        ],
    ),
    "shipment_performance": AnalyticsResponse(
        query_type="shipment_performance",
        columns=["carrier", "on_time_pct", "avg_transit_days", "total_shipments"],
        rows=[
            ["FastShip Express", "96.5", "1.8", "342"],
            ["EcoFreight", "89.2", "3.2", "215"],
            ["CrossCountry Logistics", "91.0", "5.4", "128"],
        ],
    ),
}
