# UrbanPulse

UrbanPulse is an end-to-end Databricks lakehouse project for analysing London Underground operations, service reliability, arrival activity, weather conditions, and calendar effects.

The project is built on Databricks Free Edition and follows production-oriented data engineering practices where supported.

## Project Objectives

UrbanPulse is designed to answer questions such as:

* Which Underground lines experience the most disruption?
* How frequently do service conditions change?
* Which stations have the highest arrival activity?
* How do arrival predictions change over time?
* Are disruptions associated with weather conditions?
* Do weekends and bank holidays affect transport behaviour?
* Which lines or stations currently require operational attention?
* Can historical operational data be used to predict elevated disruption risk?

The final platform will support analytics, dashboard consumption, and machine learning.

## Architecture

UrbanPulse follows the Databricks Medallion Architecture.

```text
Public APIs
    |
    v
Ingestion
    |
    +----> Raw JSON Landing
    |
    v
Bronze Delta Tables
    |
    v
Silver
Validated and Structured Data
    |
    v
Gold
Business and Analytical Models
    |
    +----> SQL Analytics
    +----> Dashboard Serving Tables
    +----> Machine Learning
```

### Bronze

Bronze preserves source responses with minimal transformation.

Each ingestion records metadata including:

```text
request_id
source
dataset
source_endpoint
ingested_at
ingestion_date
http_status
payload
```

The original API response is also retained in a Unity Catalog Volume where appropriate.

### Silver

Silver contains structured and validated operational data.

Responsibilities include:

* explicit schema parsing
* nested JSON processing
* timestamp normalization
* deduplication
* data quality validation
* deterministic business keys
* Delta MERGE processing
* preservation of historical observations

### Gold

Gold provides business-facing dimensional models, facts, aggregates, and serving datasets.

The Gold layer is designed for:

* Databricks SQL
* reporting
* operational dashboards
* downstream application consumption
* machine learning feature development

## Data Sources

| Source          | Dataset          | Purpose                                |
| --------------- | ---------------- | -------------------------------------- |
| TfL Unified API | Tube line status | Service health and disruption analysis |
| TfL Unified API | Tube stop points | Station reference data                 |
| TfL Unified API | Station arrivals | Live operational arrival observations  |
| Open-Meteo      | London weather   | Weather enrichment                     |
| GOV.UK          | Bank holidays    | Calendar enrichment                    |

## Current Pipeline

```text
TfL Line Status
    |
    +----> Bronze
    |        |
    |        v
    |      Silver
    |
TfL Stop Points
    |
    +----> Bronze
    |        |
    |        +----> Silver Stop Points
    |        |
    |        +----> Silver Station-Line Relationships
    |
TfL Arrivals
    |
    +----> Bronze
             |
             v
           Silver Arrival Observations


Open-Meteo Weather
    |
    +----> Bronze
             |
             v
           Silver Weather


GOV.UK Bank Holidays
    |
    +----> Bronze
             |
             v
           Silver Bank Holidays
```

The first Gold model has also been implemented:

```text
Silver Bank Holidays
        +
Generated Calendar
        |
        v
Gold dim_date
```

## Repository Structure

```text
urbanpulse-databricks/
|
├── conf/
│   ├── sources.yml
│   ├── monitored_stations.yml
│   └── project.yml
|
├── notebooks/
│   ├── 00_setup/
│   ├── 01_bronze/
│   ├── 02_silver/
│   ├── 03_gold/
│   ├── 04_analytics/
│   └── 05_ml/
|
├── src/
│   └── urbanpulse/
│       ├── ingestion/
│       ├── transformations/
│       ├── quality/
│       ├── models/
│       └── utils/
|
├── sql/
│   ├── ddl/
│   ├── gold/
│   └── analytics/
|
├── tests/
│   ├── unit/
│   └── integration/
|
├── resources/
├── docs/
├── pyproject.toml
├── databricks.yml
└── README.md
```

## Databricks Structure

The project currently uses the `workspace` catalog.

```text
workspace
|
├── urbanpulse_bronze
├── urbanpulse_silver
├── urbanpulse_gold
└── urbanpulse_meta
```

Raw landed files are stored under:

```text
/Volumes/workspace/urbanpulse_meta/landing/
```

## Implemented Bronze Tables

```text
workspace.urbanpulse_bronze.tfl_line_status
workspace.urbanpulse_bronze.tfl_stop_points
workspace.urbanpulse_bronze.tfl_arrivals
workspace.urbanpulse_bronze.weather
workspace.urbanpulse_bronze.bank_holidays
```

Each execution creates a new source snapshot rather than overwriting historical ingestion records.

## Implemented Silver Tables

```text
workspace.urbanpulse_silver.tfl_line_status
workspace.urbanpulse_silver.tfl_stop_points
workspace.urbanpulse_silver.tfl_stop_point_lines
workspace.urbanpulse_silver.tfl_arrivals
workspace.urbanpulse_silver.weather
workspace.urbanpulse_silver.bank_holidays
```

### TfL Line Status

Contains one structured line-status observation per TfL snapshot.

Key fields include:

```text
line_id
line_name
status_severity
status_description
status_reason
snapshot_at
```

### TfL Stop Points

Contains validated Tube station reference data.

The canonical TfL station NAPTAN identifier is used for downstream station identity rather than station name alone.

This avoids ambiguity where multiple TfL records share the same display name.

### TfL Station-Line Relationships

Tube station and line relationships are normalized into a separate Silver table.

This supports the many-to-many relationship between stations and Underground lines.

### TfL Arrivals

Contains individual arrival predictions observed during each polling request.

Repeated observations of the same train are preserved because they represent changes in operational state over time.

Example:

```text
10:00 | Train A | ETA 300 seconds
10:05 | Train A | ETA 60 seconds
```

These are treated as two valid observations.

### Weather

Open-Meteo responses are normalized into structured weather observations with explicit units and UTC timestamps.

Measurements currently include:

```text
temperature
relative humidity
precipitation
rain
weather code
cloud cover
wind speed
wind gusts
```

### Bank Holidays

GOV.UK holiday snapshots are converted into structured calendar events for England and Wales.

Repeated identical source snapshots are collapsed in Silver.

## Gold Layer

The planned Gold model follows a dimensional design.

```text
urbanpulse_gold
|
├── dim_date
├── dim_line
├── dim_station
├── bridge_station_line
├── fact_line_status
├── fact_arrival_observation
├── fact_weather
├── current_line_status
├── station_arrival_summary
└── daily_network_kpis
```

### `dim_date`

The first Gold dimension is implemented.

```text
workspace.urbanpulse_gold.dim_date
```

Grain:

> One row per calendar date.

Current date range:

```text
2019-01-01 to 2035-12-31
```

The range covers all currently available bank-holiday records in the source data.

Key attributes include:

```text
date_key
calendar_date
year
quarter
month
month_name
week_of_year
day_of_month
day_of_week
day_name
is_weekend
is_bank_holiday
holiday_name
```

`date_key` uses the `YYYYMMDD` integer convention.

Example:

```text
2026-08-23 -> 20260823
```

Day-of-week numbering uses:

```text
1 Monday
2 Tuesday
3 Wednesday
4 Thursday
5 Friday
6 Saturday
7 Sunday
```

## Data Quality

Data quality checks are applied before records enter Silver or Gold.

Current checks include:

* required identifiers
* required timestamps
* valid latitude and longitude ranges
* non-negative arrival times
* humidity between 0 and 100 percent
* cloud cover between 0 and 100 percent
* non-negative precipitation
* non-negative wind measurements
* valid date parsing
* duplicate key detection
* dimensional uniqueness checks
* calendar coverage checks

Unexpected invalid records cause the relevant transformation to fail rather than silently entering downstream datasets.

## Idempotency

Silver pipelines use Delta MERGE patterns to prevent duplicate records when transformations are rerun.

Examples include:

```text
request_id + line_id + status_id
arrival_observation_key
weather_observation_key
holiday_key
```

Gold dimensions are rebuilt or merged based on the behaviour of the dataset.

`dim_date` is deterministic and inexpensive to regenerate, so it is rebuilt atomically.

## Engineering Principles

The project follows these conventions:

* `snake_case` naming
* notebooks focused on orchestration
* reusable processing logic under `src/`
* configuration separated from transformation logic
* explicit Spark schemas
* no secrets committed to Git
* raw source preservation
* stable business identifiers
* deterministic analytical keys
* idempotent processing
* Delta Lake for persisted tables
* UTC timestamps for analytical data
* data quality validation before promotion
* normalized relational structures where appropriate
* Git-based version control
* reusable Delta utilities
* testing of reusable logic as the project develops

## Timestamp Strategy

Operational datasets contain several different timestamp concepts.

UrbanPulse keeps them separate rather than treating them as interchangeable.

Examples include:

```text
prediction_timestamp
expected_arrival
weather_observed_at
snapshot_at
processed_at
```

Analytical timestamps are standardized to UTC where appropriate.

Local London timestamps may also be retained when useful for readability or debugging.

## Downstream Application Support

The Gold layer is being designed as a stable interface for downstream consumers.

A separate PHP-based web application will eventually use dashboard-oriented serving datasets such as:

```text
current_line_status
station_arrival_summary
daily_network_kpis
```

The frontend will not be responsible for rebuilding complex analytical logic from raw transport data.

Serving datasets will provide:

* stable identifiers
* predictable schemas
* precomputed metrics
* clear timestamp semantics
* consumer-friendly row grains

## Planned Gold Model

### Dimensions

```text
dim_date
dim_line
dim_station
```

### Relationship Tables

```text
bridge_station_line
```

### Facts

```text
fact_line_status
fact_arrival_observation
fact_weather
```

### Serving Tables

```text
current_line_status
station_arrival_summary
daily_network_kpis
```

## Planned Analytics

The Gold layer will support analysis such as:

* disruption frequency by line
* service reliability by weekday
* bank holiday behaviour
* station arrival activity
* average predicted waiting time
* repeated vehicle observations
* weather and disruption relationships
* daily network health
* operational trend analysis

## Planned Machine Learning

Once sufficient historical data has accumulated, UrbanPulse will create ML-ready feature datasets using:

```text
line status
arrival observations
weather
calendar attributes
recent operational history
```

Potential features include:

```text
hour of day
day of week
bank holiday status
temperature
rainfall
wind
line
station
recent arrival frequency
recent disruption rate
```

A later phase will evaluate whether these features provide enough signal to model elevated disruption risk.

## Databricks Features Covered

The project currently demonstrates or is designed to cover:

* Databricks notebooks
* PySpark DataFrames
* Spark SQL
* Unity Catalog
* Unity Catalog Volumes
* Delta Lake
* Delta MERGE
* Bronze, Silver, and Gold architecture
* nested JSON parsing
* explicit Spark schemas
* incremental ingestion
* REST API integration
* dimensional modelling
* slowly changing dimensions
* fact modelling
* data quality
* deterministic keys
* window functions
* orchestration
* Databricks SQL
* dashboards
* MLflow
* machine learning
* testing
* CI/CD concepts
* monitoring and observability
* performance analysis

## Databricks Free Edition

The implementation targets Databricks Free Edition.

Where Free Edition differs from a typical production Databricks environment, the project separates:

```text
Free Edition implementation
+
Enterprise production approach
```

This keeps the project executable while preserving production-oriented design principles.

## Project Status

Current phase:

```text
Gold dimensional modelling
```

Completed:

```text
[✓] Databricks project setup
[✓] Unity Catalog schemas and landing Volume
[✓] Reusable API ingestion framework
[✓] TfL line-status Bronze ingestion
[✓] TfL line-status Silver transformation
[✓] TfL StopPoint Bronze ingestion
[✓] TfL StopPoint Silver transformation
[✓] Station-line normalization
[✓] TfL arrivals Bronze ingestion
[✓] TfL arrivals Silver transformation
[✓] Open-Meteo Bronze ingestion
[✓] Open-Meteo Silver transformation
[✓] GOV.UK bank-holiday Bronze ingestion
[✓] GOV.UK bank-holiday Silver transformation
[✓] Gold data-model design
[✓] Gold dim_date
```

Next:

```text
Gold dim_line with Slowly Changing Dimension Type 2 handling
```
