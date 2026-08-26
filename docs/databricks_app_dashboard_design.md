# UrbanPulse Databricks Apps Dashboard

## Purpose

Provide an operational and analytical dashboard for London Underground data using the UrbanPulse Gold serving layer.

## Technology

- Databricks Apps
- Streamlit
- Databricks SQL
- Unity Catalog Gold tables

## Pages

### Network Overview

Shows:

- total Tube lines
- good service lines
- disrupted lines
- network good service percentage
- arrival activity
- average ETA
- weather summary
- recent trends

### Line Status

Source:

`workspace.urbanpulse_gold.current_line_status`

Shows the current operational status of every Tube line.

Filters:

- line
- service state

### Station Arrivals

Source:

`workspace.urbanpulse_gold.station_arrival_summary`

Shows:

- arrival observations
- distinct vehicles
- average ETA
- minimum ETA
- maximum ETA
- next expected arrival

Filters:

- station
- line

### Network Trends

Source:

`workspace.urbanpulse_gold.daily_network_kpis`

Shows historical:

- disruption rate
- arrival activity
- average ETA
- temperature
- precipitation

Filters:

- date range
- day of week
- weekend
- bank holiday

### Data Freshness

Shows:

- latest line-status data
- latest arrival data
- latest weather data
- serving-table refresh times
- latest Gold validation result

## Data Sources

The application primarily reads:

- `workspace.urbanpulse_gold.current_line_status`
- `workspace.urbanpulse_gold.station_arrival_summary`
- `workspace.urbanpulse_gold.daily_network_kpis`

Validation information reads:

- `workspace.urbanpulse_meta.gold_validation_results`

The application does not use Bronze or raw source data.

## Security

The application is read-only.

It requires:

- SELECT access to serving tables
- SELECT access to Gold validation results
- permission to use its SQL warehouse

No credentials are stored in Git.

## Timestamp Rules

UTC timestamps are retained for technical and freshness checks.

Europe/London timestamps are used for dashboard display.

## Application Identifiers

Line:

`line_id`

Station:

`station_id`

Date:

`date_key`

## Architecture

```text
Gold Serving Tables
        |
        v
Databricks SQL
        |
        v
Databricks App
        |
        v
Streamlit Dashboard