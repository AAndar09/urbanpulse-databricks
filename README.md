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

The final platform will support analytics, dashboards, machine learning, and downstream application consumption.

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
    +----> Databricks SQL
    +----> Databricks Apps Dashboard
    +----> Dashboard Serving Tables
    +----> Machine Learning
    +----> Future PHP Web Application
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

Original API responses are also retained in a Unity Catalog Volume where appropriate.

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

Gold provides business-facing dimensional models, fact tables, aggregates, and serving datasets.

The Gold layer is designed for:

* Databricks SQL
* Databricks Apps
* operational dashboards
* analytical reporting
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

Current Gold processing:

```text
Silver Bank Holidays
        +
Generated Calendar
        |
        v
dim_date


Silver Line Status
        |
        v
dim_line
SCD Type 2


Silver Stop Points
        |
        v
dim_station
SCD Type 2


dim_station
     |
     +---- bridge_station_line ----+
                                   |
                                dim_line
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

## Bronze Tables

```text
workspace.urbanpulse_bronze.tfl_line_status
workspace.urbanpulse_bronze.tfl_stop_points
workspace.urbanpulse_bronze.tfl_arrivals
workspace.urbanpulse_bronze.weather
workspace.urbanpulse_bronze.bank_holidays
```

Each ingestion execution creates a new source snapshot rather than overwriting historical records.

## Silver Tables

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

The canonical TfL station NAPTAN identifier is used for downstream station identity rather than station name.

### TfL Station-Line Relationships

Station and line relationships are normalized into a separate Silver table.

The source can contain relationships to other TfL services such as bus routes. Gold models currently restrict these relationships to London Underground lines represented in `dim_line`.

### TfL Arrivals

Contains individual arrival predictions observed during each polling request.

Repeated observations of the same train are preserved because they represent changes in operational state over time.

```text
10:00 | Train A | ETA 300 seconds
10:05 | Train A | ETA 60 seconds
```

These are two separate observations.

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

The Gold layer follows a dimensional model designed for analytics and downstream consumption.

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

Implemented:

```text
workspace.urbanpulse_gold.dim_date
```

Grain:

> One row per calendar date.

Current range:

```text
2019-01-01 to 2035-12-31
```

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

### `dim_line`

Implemented using Slowly Changing Dimension Type 2.

```text
workspace.urbanpulse_gold.dim_line
```

Business key:

```text
line_id
```

Each historical version receives a separate:

```text
line_key
```

Tracked attributes include:

```text
line_name
mode_name
is_active
```

Historical validity is represented by:

```text
effective_from
effective_to
is_current
```

### `dim_station`

Implemented using Slowly Changing Dimension Type 2.

```text
workspace.urbanpulse_gold.dim_station
```

Business key:

```text
station_id
```

where:

```text
station_id = station_naptan
```

Tracked attributes include:

```text
station_name
latitude
longitude
stop_type
modes
is_active
```

Station names are treated as descriptive values rather than identifiers.

### `bridge_station_line`

Implemented:

```text
workspace.urbanpulse_gold.bridge_station_line
```

Grain:

> One current canonical Tube station to Tube line relationship.

The bridge resolves:

```text
station_key
line_key
station_id
line_id
```

TfL StopPoint data can include bus and other interchange relationships. These remain available in Silver but are excluded from the current Tube-specific Gold bridge.

## Data Quality

Data quality checks are applied before records are promoted between layers.

Current checks include:

* required identifiers
* required timestamps
* valid latitude and longitude
* non-negative arrival times
* humidity between 0 and 100 percent
* cloud cover between 0 and 100 percent
* non-negative precipitation
* non-negative wind measurements
* valid date parsing
* duplicate key detection
* dimensional uniqueness
* referential integrity
* calendar coverage
* SCD effective-date integrity
* source coverage validation
* Gold relationship coverage

Unexpected invalid records cause the relevant transformation to fail rather than silently entering downstream datasets.

## Idempotency

Silver and Gold pipelines are designed to be safely rerunnable.

Current patterns include:

```text
request_id + line_id + status_id
arrival_observation_key
weather_observation_key
holiday_key
station_line_key
```

Delta MERGE is used where incremental insert or update behaviour is appropriate.

Deterministic Gold structures such as `dim_date` and `bridge_station_line` are rebuilt when a full reconstruction is simpler and safer.

## Slowly Changing Dimensions

UrbanPulse uses SCD Type 2 for line and station reference data.

Changes follow the pattern:

```text
unchanged
    -> no write

new
    -> insert current version

changed
    -> expire existing version
    -> insert new current version
```

Historical facts can therefore resolve the dimension record that was valid at the time of the observation.

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
* explicit timezone semantics
* data quality validation before promotion
* normalized relational structures where appropriate
* Git-based version control
* reusable Delta utilities
* SCD Type 2 for changing reference data
* referential integrity checks between Gold models
* automated testing as reusable logic grows

## Timestamp Strategy

Operational datasets contain several different timestamp concepts.

UrbanPulse keeps these meanings separate:

```text
prediction_timestamp
expected_arrival
weather_observed_at
snapshot_at
processed_at
effective_from
effective_to
```

Analytical timestamps are standardized to UTC where appropriate.

London-local calendar logic is applied explicitly when operational dates are required.

## Dashboard Strategy

UrbanPulse will provide two dashboard experiences.

### Databricks Apps Dashboard

Once the core Gold fact tables, dimensions, and serving tables are complete, a dashboard-style application will be built using **Databricks Apps**.

This will be the first application layer implemented directly on top of the lakehouse.

It will consume Gold datasets such as:

```text
current_line_status
station_arrival_summary
daily_network_kpis
```

The Databricks application will focus on:

* current network health
* line disruption status
* station activity
* arrival metrics
* historical operational trends
* weather context
* daily KPIs

The dashboard will also provide an opportunity to demonstrate application development directly within the Databricks platform.

### Future PHP Web Application

At a later stage, a separate PHP-based web application will consume stable Gold serving datasets.

The PHP application is intentionally separated from the Databricks data-engineering implementation.

Gold serving datasets will provide:

* stable identifiers
* predictable schemas
* precomputed metrics
* clear timestamp semantics
* small consumer-friendly datasets
* separation between current state and historical data

The PHP frontend will not be responsible for recreating complex Spark transformations or business logic.

## Planned Gold Facts

### `fact_line_status`

Grain:

> One Tube line-status observation per TfL polling snapshot.

Planned relationships:

```text
dim_line
dim_date
```

Primary analytical outputs include:

```text
service observations
disruption observations
disruption rates
historical line health
```

### `fact_arrival_observation`

Grain:

> One arrival prediction observed during one polling request.

Planned relationships:

```text
dim_station
dim_line
dim_date
```

### `fact_weather`

Grain:

> One London weather observation per observation timestamp.

It will support temporal enrichment of transport observations.

## Planned Serving Tables

### `current_line_status`

One row per Tube line containing its latest known operational state.

### `station_arrival_summary`

Aggregated station and line arrival metrics suitable for dashboards and application consumption.

### `daily_network_kpis`

Daily network-level operational and environmental metrics.

These serving tables will be the preferred interface for both Databricks Apps and the later PHP frontend.

## Planned Analytics

Gold models will support:

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

A later phase will evaluate whether these features provide enough predictive signal to model elevated disruption risk.

## Databricks Features Covered

The project currently demonstrates or is designed to cover:

* Databricks notebooks
* PySpark DataFrames
* Spark SQL
* Unity Catalog
* Unity Catalog Volumes
* Delta Lake
* Delta MERGE
* Medallion Architecture
* nested JSON parsing
* explicit Spark schemas
* incremental ingestion
* REST API integration
* dimensional modelling
* SCD Type 2
* bridge tables
* fact modelling
* data quality
* deterministic keys
* referential integrity
* window functions
* orchestration
* Databricks SQL
* Databricks Apps
* dashboards
* MLflow
* machine learning
* testing
* CI/CD concepts
* monitoring and observability
* performance analysis

## Databricks Free Edition

The implementation targets Databricks Free Edition.

Where Free Edition differs from a typical production Databricks environment, the project distinguishes between:

```text
Free Edition implementation
+
Enterprise production approach
```

This keeps the project executable while preserving production-oriented design principles.

## Project Status

Current phase:

```text
Gold fact modelling
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
[✓] Gold dim_line with SCD Type 2
[✓] Gold dim_station with SCD Type 2
[✓] Gold bridge_station_line
```

Next:

```text
Gold fact_line_status
```

Later stages:

```text
Gold fact_arrival_observation
Gold fact_weather
Gold serving tables
Databricks Apps dashboard
workflow orchestration
monitoring and observability
Databricks SQL analytics
machine learning and MLflow
automated testing
CI/CD
PHP dashboard application
```
