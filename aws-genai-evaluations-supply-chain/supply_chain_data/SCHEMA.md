# Supply Chain Mock Data Schema

## Overview

The mock data layer provides canned API responses for four supply chain endpoints. Data is stored as Python dictionaries keyed by product_id or location pairs. This document describes the structure as if it were a relational schema.

---

## Entity Models (Shared Reference Data)

### Locations — 9 records

| location_id | name | location_type | region |
|---|---|---|---|
| loc-fc-east | East Fulfillment Center | fulfillment_center | us-east-1 |
| loc-fc-west | West Fulfillment Center | fulfillment_center | us-west-2 |
| loc-fc-central | Central Fulfillment Center | fulfillment_center | us-central-1 |
| loc-dc-south | Southern Distribution Center | fulfillment_center | us-south-1 |
| loc-store-nyc | NYC Flagship Store | store | us-east-1 |
| loc-store-la | Los Angeles Store | store | us-west-2 |
| loc-store-chi | Chicago Store | store | us-central-1 |
| loc-digital-main | Main Digital Channel | digital_channel | us-east-1 |
| loc-digital-intl | International Digital Channel | digital_channel | eu-west-1 |

Location types: `fulfillment_center`, `store`, `digital_channel`

### Products — 8 records

| product_id |
|---|
| prod-001 |
| prod-002 |
| prod-003 |
| prod-004 |
| prod-005 |
| prod-006 |
| prod-007 |
| prod-008 |

### Carriers — 3 records

| carrier_name |
|---|
| FastShip Express |
| EcoFreight |
| CrossCountry Logistics |

---

## API Response Data

### 1. Optimization Responses — 8 records

Keyed by: `product_id`

| Column | Type | Description |
|---|---|---|
| product_id | str | Product identifier |
| location | Location | Location where the product is stocked |
| time_horizon | str | Forecasting period (e.g. "30d") |
| demand_forecast | int | Projected units needed in time horizon |
| recommended_inventory_level | int | Optimal stock level to hold |
| confidence | float | Model confidence (0.0–1.0) |
| constraints.budget_limit | Decimal | Maximum budget available |
| constraints.budget_used | Decimal | Budget already consumed |
| constraints.warehouse_capacity | int | Maximum units the warehouse can hold |
| constraints.warehouse_utilization | int | Current units stored |
| constraints.inventory_holding_cost | Decimal | Cost per unit per period |

Sample data:

| product_id | location | demand_forecast | recommended_level | confidence | budget_limit | budget_used | capacity | utilization | holding_cost |
|---|---|---|---|---|---|---|---|---|---|
| prod-001 | East FC | 1200 | 1500 | 0.87 | $50,000 | $32,500 | 5000 | 3200 | $2.50 |
| prod-002 | West FC | 800 | 1000 | 0.92 | $30,000 | $21,000 | 3000 | 2100 | $1.80 |
| prod-003 | East FC | 3500 | 4000 | 0.79 | $100,000 | $78,000 | 10000 | 8500 | $3.20 |
| prod-004 | Central FC | 2200 | 2600 | 0.84 | $75,000 | $45,000 | 7000 | 4800 | $2.10 |
| prod-005 | Southern DC | 450 | 600 | 0.91 | $20,000 | $12,000 | 2000 | 1100 | $4.50 |
| prod-006 | West FC | 5000 | 5800 | 0.76 | $150,000 | $120,000 | 12000 | 10200 | $1.50 |
| prod-007 | East FC | 1800 | 2100 | 0.88 | $60,000 | $38,000 | 6000 | 3900 | $2.80 |
| prod-008 | Central FC | 950 | 1200 | 0.93 | $35,000 | $18,000 | 4000 | 2200 | $3.00 |

---

### 2. Distribution Responses — 8 records (18 suggestions total)

Keyed by: `product_id`

Each record contains 1–3 rebalancing suggestions.

| Column | Type | Description |
|---|---|---|
| product_id | str | Product to rebalance |
| source_location | Location | Where to take inventory from |
| destination_location | Location | Where to send inventory to |
| transfer_quantity | int | Number of units to move |

Sample data:

| product_id | source | destination | quantity |
|---|---|---|---|
| prod-001 | East FC | NYC Store | 200 |
| prod-001 | East FC | Digital Channel | 100 |
| prod-002 | West FC | East FC | 350 |
| prod-003 | East FC | West FC | 500 |
| prod-003 | West FC | NYC Store | 150 |
| prod-004 | Central FC | Chicago Store | 400 |
| prod-004 | Central FC | LA Store | 250 |
| prod-005 | Southern DC | East FC | 180 |
| prod-006 | West FC | LA Store | 600 |
| prod-006 | East FC | Intl Digital | 300 |
| prod-006 | Central FC | Southern DC | 450 |
| prod-007 | Southern DC | NYC Store | 220 |
| prod-007 | East FC | Chicago Store | 180 |
| prod-008 | Central FC | West FC | 320 |

---

### 3. Routing Responses — 10 records (22 route options total)

Keyed by: `(origin_location_id, destination_location_id)` tuple

Each record contains 1–3 route options.

| Column | Type | Description |
|---|---|---|
| origin | str | Origin location_id |
| destination | str | Destination location_id |
| carrier_name | str | Logistics carrier |
| estimated_transit_days | int | Days in transit |
| estimated_cost | Decimal | Cost in USD |

Sample data:

| origin | destination | carrier | transit_days | cost |
|---|---|---|---|---|
| loc-fc-east | loc-store-nyc | FastShip Express | 1 | $45.00 |
| loc-fc-east | loc-store-nyc | EcoFreight | 3 | $22.50 |
| loc-fc-east | loc-fc-west | CrossCountry Logistics | 5 | $120.00 |
| loc-fc-east | loc-fc-west | FastShip Express | 2 | $210.00 |
| loc-fc-west | loc-store-nyc | CrossCountry Logistics | 6 | $135.00 |
| loc-fc-central | loc-store-chi | FastShip Express | 1 | $35.00 |
| loc-fc-central | loc-store-chi | EcoFreight | 2 | $18.00 |
| loc-fc-central | loc-store-la | CrossCountry Logistics | 4 | $95.00 |
| loc-fc-central | loc-store-la | FastShip Express | 2 | $175.00 |
| loc-dc-south | loc-fc-east | EcoFreight | 3 | $55.00 |
| loc-dc-south | loc-fc-east | CrossCountry Logistics | 4 | $42.00 |
| loc-fc-west | loc-store-la | FastShip Express | 1 | $28.00 |
| loc-fc-west | loc-store-la | EcoFreight | 2 | $15.00 |
| loc-fc-east | loc-dc-south | CrossCountry Logistics | 3 | $78.00 |
| loc-fc-east | loc-dc-south | FastShip Express | 1 | $145.00 |
| loc-dc-south | loc-store-nyc | FastShip Express | 2 | $88.00 |
| loc-dc-south | loc-store-nyc | EcoFreight | 4 | $48.00 |
| loc-fc-central | loc-fc-east | CrossCountry Logistics | 3 | $85.00 |
| loc-fc-central | loc-fc-east | FastShip Express | 1 | $160.00 |
| loc-fc-central | loc-fc-east | EcoFreight | 4 | $62.00 |

---

### 4. Analytics Responses — 3 query types

Keyed by: `query_type`

Each record is a tabular result with columns and rows.

**inventory_turnover** — 8 rows

| product_id | location_id | turnover_rate | period |
|---|---|---|---|
| prod-001 | loc-fc-east | 4.2 | 2025-Q1 |
| prod-002 | loc-fc-west | 3.8 | 2025-Q1 |
| prod-003 | loc-fc-east | 5.1 | 2025-Q1 |
| prod-004 | loc-fc-central | 3.5 | 2025-Q1 |
| prod-005 | loc-dc-south | 6.2 | 2025-Q1 |
| prod-006 | loc-fc-west | 2.9 | 2025-Q1 |
| prod-007 | loc-fc-east | 4.8 | 2025-Q1 |
| prod-008 | loc-fc-central | 3.1 | 2025-Q1 |

**demand_trends** — 10 rows

| product_id | month | units_sold | trend |
|---|---|---|---|
| prod-001 | 2025-01 | 1100 | increasing |
| prod-001 | 2025-02 | 1250 | increasing |
| prod-002 | 2025-01 | 780 | stable |
| prod-003 | 2025-01 | 3200 | increasing |
| prod-003 | 2025-02 | 3450 | increasing |
| prod-004 | 2025-01 | 2050 | stable |
| prod-005 | 2025-01 | 420 | decreasing |
| prod-006 | 2025-01 | 4800 | increasing |
| prod-007 | 2025-01 | 1750 | stable |
| prod-008 | 2025-01 | 900 | increasing |

**shipment_performance** — 3 rows

| carrier | on_time_pct | avg_transit_days | total_shipments |
|---|---|---|---|
| FastShip Express | 96.5 | 1.8 | 342 |
| EcoFreight | 89.2 | 3.2 | 215 |
| CrossCountry Logistics | 91.0 | 5.4 | 128 |

---

## Relationships

```
Product (prod-001 through prod-008)
  ├── Optimization: 1 product → 1 optimization response (with constraints)
  ├── Distribution: 1 product → N rebalancing suggestions (1–3 per product)
  │     └── each suggestion references 2 Locations (source → destination)
  └── Analytics: products appear in inventory_turnover and demand_trends rows

Location (9 locations)
  ├── Distribution: appears as source/destination in suggestions
  └── Routing: (origin, destination) pair → N route options (1–3 per pair)
        └── each option references a Carrier

Carrier (3 carriers)
  └── Routing: appears in route options with cost and transit time
  └── Analytics: appears in shipment_performance rows with reliability metrics
```

---

## Summary

| Endpoint | Records | Sub-records | Key |
|---|---|---|---|
| Optimization | 8 | — | product_id |
| Distribution | 8 | 18 suggestions | product_id |
| Routing | 10 | 22 route options | (origin, destination) |
| Analytics | 3 query types | 21 data rows | query_type |

Total: 29 top-level response objects, ~61 nested sub-records, linked through `product_id` and `location_id` as foreign keys.
