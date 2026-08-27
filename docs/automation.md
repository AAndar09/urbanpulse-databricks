# UrbanPulse Automation

## Overview

UrbanPulse uses Databricks Lakeflow Jobs to refresh source data and rebuild analytical tables automatically.

Current jobs:

| Job | Schedule | Purpose |
|---|---|---|
| `urbanpulse_operational_refresh` | Every 15 minutes | TfL line status, arrivals, serving tables |
| `urbanpulse_weather_refresh` | Hourly at `:05` | Weather ingestion and fact refresh |
| `urbanpulse_reference_refresh` | Daily at 03:16 Europe/London | Stop points, holidays, dimensions |

 

## Operational Refresh

Job:

```text
urbanpulse_operational_refresh
````

### Line Status Branch

```text
ingest_tfl_line_status
        ↓
transform_tfl_line_status
        ↓
build_fact_line_status
        ↓
build_current_line_status
```

### Arrivals Branch

```text
ingest_tfl_arrivals
        ↓
transform_tfl_arrivals
        ↓
build_fact_arrival_observation
        ↓
build_station_arrival_summary
```

Both fact branches feed:

```text
build_daily_network_kpis
        ↓
validate_gold_layer
```

This job provides the primary data used by the dashboard.

 

## Weather Refresh

Job:

```text
urbanpulse_weather_refresh
```

Pipeline:

```text
ingest_weather
    ↓
transform_weather
    ↓
build_fact_weather
```

Weather runs hourly at five minutes past the hour.

`daily_network_kpis` is not rebuilt here. The next operational refresh incorporates the latest weather data.

 

## Reference Refresh

Job:

```text
urbanpulse_reference_refresh
```

### Stop Points

```text
ingest_tfl_stop_points
        ↓
transform_tfl_stop_points
        ↓
build_dim_station
```

### Lines and Station Relationships

```text
build_dim_line
        ↓
build_bridge_station_line
        ↑
build_dim_station
```

### Bank Holidays

```text
ingest_bank_holidays
        ↓
transform_bank_holidays
        ↓
build_dim_date
```

 

## Reliability Settings

Each job uses:

```text
Maximum concurrent runs: 1
Queueing: Enabled
Compute: Serverless
```

API ingestion tasks use retry protection for transient failures.

Typical settings:

```text
Retries: 2
Retry interval: 60 seconds
Timeout: 5 minutes
```

Transformation and Gold tasks use conservative timeouts and generally avoid automatic retries for deterministic failures.

Failure notifications are enabled.

 

## Source Control

Scheduled jobs execute code from:

```text
GitHub
Branch: main
```

Only tested and committed changes should therefore reach automated runs.

 

## Validation

The operational pipeline ends with:

```text
validate_gold_layer
```

Validation results are persisted to:

```text
workspace.urbanpulse_meta.gold_validation_results
```

A failed validation causes the job run to fail visibly rather than silently serving invalid data.

 

## Verified Unattended Operation

Automation has been tested without manually running notebooks.

Verified flow:

```text
Scheduled Job
    ↓
API ingestion
    ↓
Bronze
    ↓
Silver
    ↓
Gold
    ↓
Serving tables
    ↓
Databricks SQL
    ↓
Dashboard
```

Gold timestamps and public dashboard data were confirmed to update following scheduled runs.

 

## Design Principle

Jobs are separated by data volatility:

```text
Fast-changing operational data → every 15 minutes
Weather                      → hourly
Slow-changing reference data → daily
```

This keeps the dashboard useful while limiting unnecessary compute and avoiding competing writes to the same serving tables.
