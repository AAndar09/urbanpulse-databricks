# UrbanPulse

## London Urban Mobility Intelligence Platform

UrbanPulse is an automated lakehouse and analytics platform for London Underground operational data.

It ingests public transport, weather, and calendar APIs into Databricks, transforms them through a Bronze, Silver, and Gold medallion architecture, validates the resulting analytical model, and serves the data through an interactive Dash application.

The project demonstrates an end-to-end data product covering:

- API ingestion
- Delta Lake
- Unity Catalog
- PySpark
- Dimensional modeling
- SCD Type 2
- Data quality
- Lakeflow Jobs
- Databricks SQL
- Dash
- Bootstrap
- Plotly
- Databricks Apps
- Public cloud deployment

 

## Architecture

```text
TfL Unified API       Open-Meteo       GOV.UK
       |                   |              |
       +-------------------+--------------+
                           |
                           v
                  Raw JSON Landing
                 Unity Catalog Volume
                           |
                           v
                        Bronze
                           |
                           v
                        Silver
                           |
                  +--------+--------+
                  |                 |
                  v                 v
             Dimensions           Facts
                  |                 |
                  +--------+--------+
                           |
                           v
                    Gold Serving
                           |
                           v
                    Databricks SQL
                           |
              +------------+------------+
              |                         |
              v                         v
       Databricks Apps              Plotly Cloud
       Native deployment            Public dashboard
````

Detailed architecture documentation is available in [docs/architecture.md](docs/architecture.md).

 

## Data Sources

UrbanPulse currently uses:

| Source                           | Data                            |
| -------------------------------- | ------------------------------- |
| Transport for London Unified API | Tube line status                |
| Transport for London Unified API | Tube stop points                |
| Transport for London Unified API | Arrival predictions             |
| Open-Meteo                       | London weather                  |
| GOV.UK                           | England and Wales bank holidays |

Monitored arrivals currently cover ten major London Underground stations.

See [docs/data_sources.md](docs/data_sources.md).

 

## Medallion Architecture

### Bronze

Preserves API responses together with ingestion metadata.

Raw JSON is also retained in a Unity Catalog Volume for traceability and replay.

### Silver

Parses and conforms source payloads into typed operational datasets.

Responsibilities include:

* schema enforcement
* identifier normalization
* timestamp handling
* quality validation
* deterministic keys
* source-specific transformation

### Gold

Provides the business-facing analytical model.

Current Gold objects:

```text
dim_date
dim_line
dim_station
bridge_station_line

fact_line_status
fact_arrival_observation
fact_weather

current_line_status
station_arrival_summary
daily_network_kpis
```

See [docs/data_model.md](docs/data_model.md).

 

## Gold Serving Layer

The dashboard reads consumer-ready Gold tables rather than Bronze or raw Silver data.

### `current_line_status`

One current row per Tube line.

Used for:

* network health
* line status
* disruptions
* service-state classification

### `station_arrival_summary`

One row per station and Tube-line combination for the latest arrival date.

Used for:

* arrival observations
* vehicle counts
* ETA metrics
* next expected arrival

### `daily_network_kpis`

One row per analytical date.

Used for:

* disruption trends
* arrival trends
* weather comparisons
* future analytical and ML workloads

 

## Automated Pipelines

UrbanPulse runs automatically using Databricks Lakeflow Jobs.

### Operational Refresh

```text
urbanpulse_operational_refresh
```

Runs every 15 minutes.

Processes:

```text
TfL line status
    ↓
Bronze
    ↓
Silver
    ↓
fact_line_status
    ↓
current_line_status
```

and:

```text
TfL arrivals
    ↓
Bronze
    ↓
Silver
    ↓
fact_arrival_observation
    ↓
station_arrival_summary
```

Both branches feed:

```text
daily_network_kpis
    ↓
Gold validation
```

### Weather Refresh

```text
urbanpulse_weather_refresh
```

Runs hourly at five minutes past the hour.

```text
Open-Meteo
    ↓
Bronze
    ↓
Silver
    ↓
fact_weather
```

### Reference Refresh

```text
urbanpulse_reference_refresh
```

Runs daily.

Maintains:

* TfL stop points
* bank holidays
* `dim_date`
* `dim_line`
* `dim_station`
* `bridge_station_line`

The jobs use:

* serverless compute
* dependency DAGs
* retries for API ingestion
* timeouts
* queueing
* maximum concurrent runs of one
* failure notifications

Scheduled unattended refresh has been successfully verified.

See [docs/automation.md](docs/automation.md).

 

## Data Quality

UrbanPulse performs validation throughout the pipeline.

Checks include:

* required identifiers
* schema validation
* duplicate keys
* source coverage
* Silver-to-Gold reconciliation
* Gold foreign keys
* SCD integrity
* overlapping SCD versions
* bridge uniqueness
* serving-table grain
* KPI arithmetic

Gold validation results are persisted to:

```text
workspace.urbanpulse_meta.gold_validation_results
```

See [docs/data_quality.md](docs/data_quality.md).

 

## Application

UrbanPulse uses:

```text
Dash
Dash Bootstrap Components
Plotly
Databricks SQL Connector
```

Current pages:

* Network Overview
* Line Status
* Station Arrivals

Planned pages:

* Network Trends
* Data Freshness

The interface includes:

* responsive Bootstrap layouts
* KPI cards
* service-health pills
* structured disruption information
* Plotly charts
* interactive filters
* linked station and Tube-line selection
* responsive mobile behavior

A dark-mode theme system is also prepared for a future night-mode toggle.

See [docs/dashboard.md](docs/dashboard.md).

 

## Deployment

UrbanPulse supports two application deployments.

### Databricks Apps

Demonstrates native integration with:

* Databricks SQL
* Unity Catalog
* app service-principal authentication
* managed Databricks resources

### Plotly Cloud

Provides a publicly accessible portfolio deployment using the same Dash application and Gold serving layer.

The external deployment uses environment variables for Databricks SQL authentication.

Credentials are never committed to Git.

See [docs/deployment.md](docs/deployment.md).

 

## Repository Structure

```text
urbanpulse-databricks/
├── README.md
├── conf/
├── src/
│   └── urbanpulse/
│       ├── ingestion/
│       ├── transformations/
│       ├── quality/
│       ├── models/
│       └── utils/
│
├── notebooks/
│   ├── 00_setup/
│   ├── 01_bronze/
│   ├── 02_silver/
│   ├── 03_gold/
│   ├── 04_analytics/
│   └── 05_ml/
│
├── app/
│   ├── assets/
│   ├── components/
│   ├── pages/
│   └── services/
│
├── sql/
├── tests/
└── docs/
```

 

## Documentation

Detailed technical documentation is maintained separately from this README.

```text
docs/
├── architecture.md
├── data_model.md
├── data_sources.md
├── pipeline.md
├── automation.md
├── data_quality.md
├── dashboard.md
├── deployment.md
├── runbook.md
└── decisions/
```

This keeps the README focused while allowing detailed engineering decisions to be documented properly.

 

## Engineering Principles

UrbanPulse follows several core principles:

* explicit schemas
* snake_case naming
* configuration separate from logic
* no secrets in Git
* idempotent processing
* deterministic identifiers
* reusable Python modules
* notebooks used primarily for orchestration
* UTC analytical timestamps
* Europe/London business-calendar semantics
* business logic in Gold
* consumer-ready serving tables
* automated validation

 

## Current Status

```text
Bronze pipelines             Complete
Silver pipelines             Complete
Gold dimensions              Complete
Gold facts                   Complete
Gold serving layer           Complete
Gold validation              Complete
Pipeline automation          Complete
Databricks Apps deployment   Complete
Plotly Cloud deployment      Complete

Network Overview             Complete
Line Status                  Complete
Station Arrivals             Complete

Responsive design            In progress
Network Trends               Planned
Data Freshness               Planned
Machine learning             Planned
```

 

## Roadmap

### Next

1. Complete mobile responsiveness.
2. Build Network Trends.
3. Build Data Freshness and platform-health page.
4. Add night-mode toggle.
5. Complete dashboard hardening.
6. Add automated tests.
7. Add final application screenshots.

### Later

* exploratory analytics
* disruption prediction
* feature engineering
* MLflow integration
* CI/CD
* Databricks Asset Bundles
* additional consumer applications
* future PHP frontend

 

## Free Edition

UrbanPulse is intentionally built using Databricks Free Edition.

The implementation therefore favors:

* serverless compute
* conservative refresh schedules
* small serving tables
* controlled concurrency
* efficient incremental processing

A production enterprise deployment could extend the same architecture with dedicated environments, service principals, CI/CD, monitoring integrations, and larger compute resources.

 

## Project Purpose

UrbanPulse is designed to demonstrate how raw public APIs can become a complete operational data product:

```text
API
↓
Lakehouse
↓
Data model
↓
Validation
↓
Automation
↓
Serving layer
↓
Application
```

The emphasis is not only on producing a dashboard.

The project focuses on building the reliable engineering platform that makes the dashboard meaningful.