# UrbanPulse Runbook

## Purpose

This runbook provides quick operational guidance for checking, restarting, and troubleshooting UrbanPulse.

 

## Scheduled Jobs

UrbanPulse uses three Databricks Lakeflow Jobs:

```text
urbanpulse_operational_refresh
urbanpulse_weather_refresh
urbanpulse_reference_refresh
````

Schedules:

```text
Operational refresh
Every 15 minutes

Weather refresh
Hourly at :05

Reference refresh
Daily at 03:16 Europe/London
```

 

## Check Job Health

In Databricks:

```text
Jobs & Pipelines
→ select job
→ Runs
```

Confirm the latest run shows:

```text
Scheduled
Succeeded
```

If a run failed, open the failed task and inspect its error output.

 

## Operational Refresh Failure

Check which branch failed.

### Line Status

```text
ingest_tfl_line_status
transform_tfl_line_status
build_fact_line_status
build_current_line_status
```

### Arrivals

```text
ingest_tfl_arrivals
transform_tfl_arrivals
build_fact_arrival_observation
build_station_arrival_summary
```

### Final Tasks

```text
build_daily_network_kpis
validate_gold_layer
```

Fix the failing task first, then use:

```text
Repair run
```

or:

```text
Run now
```

after the issue is resolved.

 

## Weather Refresh Failure

Check:

```text
ingest_weather
transform_weather
build_fact_weather
```

Transient API failures may recover automatically through configured retries.

 

## Reference Refresh Failure

Check:

```text
ingest_tfl_stop_points
transform_tfl_stop_points
build_dim_station

build_dim_line
build_bridge_station_line

ingest_bank_holidays
transform_bank_holidays
build_dim_date
```

Reference failures are less urgent than operational failures, but should still be resolved before the next daily run.

 

## Verify Fresh Data

### Line Status

```sql
SELECT
    MAX(status_snapshot_at_local) AS latest_line_status
FROM workspace.urbanpulse_gold.current_line_status;
```

### Arrivals

```sql
SELECT
    MAX(latest_prediction_timestamp_local) AS latest_arrival_prediction
FROM workspace.urbanpulse_gold.station_arrival_summary;
```

### Weather

```sql
SELECT
    MAX(weather_observed_at_local) AS latest_weather
FROM workspace.urbanpulse_gold.fact_weather;
```

 

## Check Gold Validation

```sql
SELECT *
FROM workspace.urbanpulse_meta.gold_validation_results
ORDER BY checked_at DESC;
```

Look for:

```text
status = FAIL
```

The latest validation run should contain no critical failures.

 

## Dashboard Appears Stale

Check in this order:

```text
1. Did the scheduled job succeed?
2. Did Gold timestamps advance?
3. Is the SQL warehouse available?
4. Can the app query Databricks SQL?
5. Refresh the application.
```

If Gold is current but the dashboard is stale, the issue is likely in the application or SQL connectivity rather than the pipeline.

 

## Databricks App Failure

Check:

```text
Databricks Apps
→ urbanpulse-dashboard
→ deployment / logs
```

Verify:

* SQL warehouse resource is available
* required table resources have `SELECT`
* `DATABRICKS_WAREHOUSE_ID` is populated through the resource binding
* application dependencies install successfully

 

## Plotly Cloud Failure

Verify these environment variables:

```text
DATABRICKS_SERVER_HOSTNAME
DATABRICKS_HTTP_PATH
DATABRICKS_TOKEN
CURRENT_LINE_STATUS_TABLE
STATION_ARRIVAL_SUMMARY_TABLE
DAILY_NETWORK_KPIS_TABLE
GOLD_VALIDATION_RESULTS_TABLE
```

Do not print secret values into logs.

 

## Common Deployment Dependencies

`app/requirements.txt` should include the required Dash and Databricks SQL dependencies, including:

```text
dash
dash-bootstrap-components
plotly
pandas
pyarrow
pytz
tzdata
databricks-sql-connector
databricks-sdk
```

 

## Manual Recovery

If automation is temporarily disabled:

```text
1. Run the required Lakeflow Job manually.
2. Confirm all tasks succeed.
3. Verify Gold timestamps.
4. Verify validation.
5. Re-enable the schedule.
```

Avoid manually running individual downstream notebooks unless necessary, because task dependencies may be skipped.

 

## Incident Priority

Suggested priority:

```text
High
Operational job repeatedly failing
Gold validation failing
Dashboard cannot query data

Medium
Weather job failing
Reference job failing
One dashboard page broken

Low
Minor visual issue
Non-critical stale reference metadata
```

 

## Design Principle

Troubleshoot from the data source toward the frontend:

```text
API
↓
Job
↓
Bronze
↓
Silver
↓
Gold
↓
SQL
↓
Application
```

Find the first layer where expected data stops appearing, then investigate there.

