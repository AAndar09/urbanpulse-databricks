# ADR 004: Use Dedicated Gold Serving Tables

## Status

Accepted

## Decision

UrbanPulse exposes dedicated Gold serving tables for application consumption.

Current serving tables:

```text
current_line_status
station_arrival_summary
daily_network_kpis
````

 

## Rationale

The frontend should not reproduce complex joins, SCD logic, or KPI calculations.

Serving tables provide stable, consumer-ready contracts.

 

## Benefits

This approach provides:

* simpler application queries
* predictable table grains
* lower query complexity
* reusable outputs for multiple consumers
* easier frontend development
* clearer separation between analytics and presentation

 

## Consumer Model

```text
Gold facts and dimensions
        ↓
Gold serving tables
        ↓
Databricks SQL
        ↓
Applications
```

Applications should prefer serving tables over direct Bronze, Silver, or raw fact access.

 

## Consequences

Serving tables introduce an additional transformation layer and must be refreshed when upstream data changes.

UrbanPulse handles this through scheduled Lakeflow Jobs.

 

## Guiding Rule

Business logic belongs in Gold.

Applications should focus on filtering, formatting, interaction, and presentation.
