# UrbanPulse Deployment

## Overview

UrbanPulse supports two Dash deployment targets:

```text
Databricks Apps
Plotly Cloud
````

Both use the same application code and Gold serving tables.

 

## Databricks Apps

The native deployment uses:

* Databricks Apps
* Databricks SQL
* Unity Catalog
* managed app identity
* resource bindings

Required resources include:

```text
SQL warehouse
current_line_status
station_arrival_summary
daily_network_kpis
gold_validation_results
```

The app runs from:

```text
app/
```

with:

```text
app/app.py
app/app.yaml
app/requirements.txt
```

No Databricks token is stored in the repository.

 

## Plotly Cloud

Plotly Cloud provides the public portfolio deployment.

It connects externally to Databricks SQL using environment variables.

Required variables:

```text
DATABRICKS_SERVER_HOSTNAME
DATABRICKS_HTTP_PATH
DATABRICKS_TOKEN

CURRENT_LINE_STATUS_TABLE
STATION_ARRIVAL_SUMMARY_TABLE
DAILY_NETWORK_KPIS_TABLE
GOLD_VALIDATION_RESULTS_TABLE
```

Secrets must be configured in the hosting environment and never committed to Git.

 

## SQL Connectivity

`app/services/databricks_sql.py` supports both environments.

Conceptually:

```text
External Databricks credentials available?
    |
    +-- Yes → external SQL connection
    |
    +-- No  → Databricks Apps managed authentication
```

This keeps the application portable.

 

## Application Dependencies

The Dash runtime includes:

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

Dependencies are maintained in:

```text
app/requirements.txt
```

 

## Deployment Workflow

Recommended workflow:

```text
Develop
↓
Test locally / in Databricks
↓
Commit
↓
Push to main
↓
Redeploy application
↓
Verify SQL connectivity
↓
Verify dashboard freshness
```

Scheduled Lakeflow Jobs continue refreshing the underlying Gold data independently of application deployment.

 

## Security

Deployment follows these principles:

* no secrets in Git
* read-only application access
* environment-based credentials
* least-privilege table access
* Gold serving tables exposed instead of Bronze or Silver

 

## Verification

After deployment, confirm:

```text
Application loads
Navigation works
Gold queries succeed
Current line status appears
Station arrivals appear
Freshness timestamps are current
No credentials appear in logs or source
```

 

## Design Principle

The application deployment is separate from the data pipeline.

```text
Lakeflow Jobs
    ↓
Gold data refresh

Application deployment
    ↓
UI code refresh
```

This allows data to continue updating without redeploying the frontend.
