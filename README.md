# UrbanPulse

UrbanPulse is an end-to-end Databricks lakehouse project for analysing London Underground operations, service reliability, arrival activity, weather conditions, and calendar effects.

The project is built on Databricks Free Edition and applies production-oriented data engineering practices where supported.

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

The platform is being developed to support analytics, dashboards, machine learning, and downstream application consumption.

## Architecture

UrbanPulse follows the Databricks Medallion Architecture.

```text
Public APIs
    |
    v
Raw JSON Landing
    |
    v
Bronze Delta Tables
    |
    v
Silver
Validated and Conformed Data
    |
    v
Gold
Dimensions, Facts and Serving Models
    |
    +----> Databricks SQL
    +----> Databricks Apps Dashboard
    +----> Machine Learning
    +----> Future PHP Web Application
```

### Bronze

Bronze preserves source responses with minimal transformation.

Each ingestion records metadata such as:

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

Original API responses are also retained as JSON in a Unity Catalog Volume where appropriate.

### Silver

Silver contains structured, validated, and conformed operational data.

Responsibilities include:

* explicit schema parsing
* nested JSON processing
* timestamp normalization
* deduplication
* deterministic keys
* data quality validation
* incremental Delta processing
* preservation of historical observations
* normalization of source relationships

### Gold

Gold contains business-facing dimensions, fact tables, aggregates, and serving datasets.

The Gold layer is designed to support:

* Databricks SQL analytics
* Databricks Apps
* operational dashboards
* dimensional analysis
* machine learning features
* downstream application APIs and services

## Data Sources

| Source          | Dataset          | Purpose                                |
| --------------- | ---------------- | -------------------------------------- |
| TfL Unified API | Tube line status | Service health and disruption analysis |
| TfL Unified API | Tube stop points | Station reference data                 |
| TfL Unified API | Station arrivals | Operational arrival observations       |
| Open-Meteo      | London weather   | Weather enrichment                     |
| GOV.UK          | Bank holidays    | Calendar enrichment                    |

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

Raw landed API responses are stored under:

```text
/Volumes/workspace/urbanpulse_meta/landing/
```

## Bronze Layer

Implemented Bronze tables:

```text
workspace.urbanpulse_bronze.tfl_line_status
workspace.urbanpulse_bronze.tfl_stop_points
workspace.urbanpulse_bronze.tfl_arrivals
workspace.urbanpulse_bronze.weather
workspace.urbanpulse_bronze.bank_holidays
```

Bronze ingestion is append-oriented.

Repeated API executions create new source snapshots rather than overwriting historical records.

This provides:

* source traceability
* replay capability
* audit history
* separation between extraction and transformation

## Silver Layer

Implemented Silver tables:

```text
workspace.urbanpulse_silver.tfl_line_status
workspace.urbanpulse_silver.tfl_stop_points
workspace.urbanpulse_silver.tfl_stop_point_lines
workspace.urbanpulse_silver.tfl_arrivals
workspace.urbanpulse_silver.weather
workspace.urbanpulse_silver.bank_holidays
```

### TfL Line Status

Contains structured Tube line-status observations.

Key fields include:

```text
line_id
line_name
status_severity
status_description
status_reason
snapshot_at
```

Repeated snapshots are retained because service state is time-dependent.

### TfL Stop Points

Contains validated Tube station reference data.

The canonical TfL station NAPTAN identifier is used as the downstream station identity.

Station names are treated as descriptive attributes and are not used as keys.

### TfL Station-Line Relationships

Station and line relationships are normalized into:

```text
workspace.urbanpulse_silver.tfl_stop_point_lines
```

TfL StopPoint data may include relationships to bus routes and other services.

These relationships remain available in Silver.

The current Gold model restricts station-line relationships to London Underground lines represented by `dim_line`.

### TfL Arrivals

Contains individual arrival predictions observed during TfL polling requests.

Repeated observations of the same vehicle are intentionally retained.

For example:

```text
10:00 | Train A | ETA 300 seconds
10:05 | Train A | ETA 60 seconds
```

These are two valid operational observations rather than duplicates.

The observation grain is represented by:

```text
arrival_observation_key
```

### Weather

Open-Meteo responses are normalized into structured observations with explicit measurement units and UTC analytical timestamps.

Current measurements include:

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

GOV.UK holiday data is transformed into structured calendar events for England and Wales.

Repeated source snapshots are collapsed deterministically in Silver.

## Gold Layer

The Gold layer uses a dimensional model with supporting bridge and serving tables.

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

Example:

```text
2026-08-23 -> 20260823
```

Day-of-week numbering follows:

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

Each historical version receives its own:

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

The initial version begins from the earliest available Silver observation for the line so historical fact records can resolve correctly.

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

Each historical station version receives a separate `station_key`.

The initial dimension version is aligned with the earliest available Silver station observation.

### `bridge_station_line`

Implemented:

```text
workspace.urbanpulse_gold.bridge_station_line
```

Grain:

> One current canonical Tube station to Tube line relationship.

The bridge contains:

```text
station_line_key
station_key
line_key
station_id
line_id
```

The bridge is restricted to lines represented in the Tube-specific `dim_line`.

Bus and other non-Tube relationships remain available in Silver but are deliberately excluded from the current Gold bridge.

### `fact_line_status`

Implemented:

```text
workspace.urbanpulse_gold.fact_line_status
```

Grain:

> One Tube line-status observation per TfL polling snapshot.

Key fields include:

```text
line_status_key
line_key
line_id
snapshot_date_key
snapshot_at
status_severity
status_description
status_reason
is_good_service
is_disrupted
```

Historical facts are joined to the `dim_line` version that was valid at the observation timestamp.

Calendar enrichment uses the London-local date while analytical timestamps remain UTC.

The fact supports analysis such as:

* disruption counts
* disruption rates by line
* service-state history
* weekday analysis
* bank holiday analysis

### `fact_arrival_observation`

Implemented:

```text
workspace.urbanpulse_gold.fact_arrival_observation
```

Grain:

> One arrival prediction observed during one TfL polling request.

Key fields include:

```text
arrival_observation_key
station_key
line_key
requested_station_id
line_id
prediction_date_key
request_id
arrival_id
vehicle_id
prediction_timestamp
expected_arrival
time_to_station_seconds
platform_name
direction
destination_name
snapshot_at
```

Each observation resolves to:

```text
dim_station
dim_line
dim_date
```

Station and line dimensions are resolved using their SCD Type 2 validity intervals.

This preserves correct historical relationships when descriptive dimension attributes change.

The fact supports analysis such as:

* arrival observation volume
* average predicted waiting time
* distinct observed vehicles
* station activity
* line activity
* platform and destination patterns

### `fact_weather`

Planned next:

```text
workspace.urbanpulse_gold.fact_weather
```

Grain:

> One weather observation for one location and observation timestamp.

It will connect Silver weather observations to `dim_date` and provide environmental context for transport analysis.

## Current Gold Model

```text
                         dim_date
                            |
                 +----------+----------+
                 |                     |
                 v                     v
        fact_line_status     fact_arrival_observation
                 |                  /       \
                 v                 v         v
             dim_line         dim_line   dim_station
                 \                         /
                  \                       /
                   bridge_station_line


Planned:

dim_date
    |
    v
fact_weather
```

## Slowly Changing Dimensions

UrbanPulse uses SCD Type 2 for reference entities where descriptive attributes can change.

Current SCD dimensions:

```text
dim_line
dim_station
```

The processing pattern is:

```text
unchanged
    -> no write

new
    -> insert current version

changed
    -> expire previous version
    -> insert new current version
```

Validity follows:

```text
effective_from <= observation_timestamp < effective_to
```

For the current version:

```text
effective_to = NULL
is_current = TRUE
```

This allows historical fact records to resolve the dimension state that was valid when an operational event occurred.

## Data Quality

Data quality validation is applied throughout the pipeline.

Current checks include:

* required identifiers
* required timestamps
* explicit source schemas
* valid latitude and longitude ranges
* non-negative arrival times
* humidity between 0 and 100 percent
* cloud cover between 0 and 100 percent
* non-negative precipitation
* non-negative wind measurements
* duplicate key detection
* dimensional uniqueness
* canonical station identity validation
* source coverage validation
* referential integrity
* SCD effective-date integrity
* fact grain validation
* calendar coverage
* deterministic key uniqueness

Invalid records cause the relevant transformation to fail rather than silently entering downstream datasets.

## Idempotency

Pipelines are designed to be safely rerunnable.

Current deterministic keys include:

```text
arrival_observation_key
weather_observation_key
holiday_key
station_line_key
line_status_key
station_key
line_key
```

Processing strategies include:

* insert-only Delta MERGE
* SCD-aware updates
* deterministic table rebuilds
* source-level deduplication
* business-key validation

Unchanged reruns should not create duplicate records.

## Timestamp Strategy

UrbanPulse keeps different timestamp concepts separate.

Examples include:

```text
snapshot_at
prediction_timestamp
expected_arrival
weather_observed_at
status_created_at
processed_at
effective_from
effective_to
```

Analytical timestamps are stored in UTC where appropriate.

London-local time is applied explicitly when determining calendar attributes such as:

```text
calendar date
weekday
weekend
bank holiday
```

This prevents ambiguous timezone behaviour in downstream analytics.

## Engineering Principles

The project follows these conventions:

* `snake_case` naming
* explicit Spark schemas
* notebooks focused on orchestration
* reusable logic under `src/`
* configuration separated from processing logic
* raw source preservation
* stable business identifiers
* deterministic analytical keys
* idempotent processing
* Delta Lake persistence
* SCD Type 2 for changing reference data
* UTC analytical timestamps
* explicit local-time conversion
* quality validation before promotion
* referential integrity between Gold models
* Git-based version control
* reusable Delta utilities
* testing of reusable processing logic
* consumer-friendly Gold interfaces

## Dashboard and Application Strategy

UrbanPulse will provide two application experiences.

### Databricks Apps Dashboard

Once the Gold dimensions, facts, and serving tables are fully implemented, a dashboard-style application will be developed using **Databricks Apps**.

This will be the first application layer built directly on top of the lakehouse.

The application is expected to cover:

* current Tube network status
* disrupted lines
* line reliability
* station arrival activity
* predicted waiting times
* recent operational trends
* weather conditions
* daily network KPIs

The application will primarily consume Gold serving tables rather than rebuilding analytical logic in the user interface.

Planned serving datasets include:

```text
current_line_status
station_arrival_summary
daily_network_kpis
```

This provides a clear separation between:

```text
data engineering
business logic
application presentation
```

### Future PHP Web Application

A separate PHP-based web application is planned for a later phase.

The PHP application will consume stable, dashboard-oriented Gold outputs.

It will not be responsible for reproducing Spark transformation logic.

The Gold serving layer will provide:

* stable identifiers
* predictable schemas
* precomputed business metrics
* explicit timestamp semantics
* small consumer-friendly datasets
* current-state datasets
* historical analytical datasets

The Databricks Apps implementation will therefore demonstrate native Databricks application development, while the later PHP frontend will demonstrate consumption of the platform from an external application architecture.

## Planned Serving Layer

After the core Gold facts are complete, UrbanPulse will build dashboard-oriented serving models.

### `current_line_status`

Grain:

> One row per Tube line containing its latest known operational state.

Expected use cases:

* network status dashboard
* disruption indicators
* line health cards
* downstream API consumption

### `station_arrival_summary`

Grain:

> One station and line summary for a defined observation period.

Expected metrics include:

```text
arrival observations
distinct vehicles
average ETA
minimum ETA
maximum ETA
next expected arrival
```

### `daily_network_kpis`

Grain:

> One row per calendar date.

Expected metrics include:

```text
line-status observations
disrupted observations
disruption rate
arrival observations
distinct vehicles
average ETA
average temperature
rainfall
maximum wind gust
bank holiday indicator
```

These serving tables will be the preferred data interface for:

```text
Databricks Apps
Databricks SQL
future PHP frontend
```

## Planned Analytics

Gold models will support analysis including:

* disruption frequency by line
* disruption rate by weekday
* bank holiday effects
* station arrival activity
* average predicted waiting time
* distinct vehicle observations
* repeated train observations
* service reliability trends
* weather and disruption relationships
* daily network health
* operational trend analysis

## Planned Machine Learning

Once sufficient historical observations have accumulated, UrbanPulse will create ML-ready datasets using:

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
weekend indicator
bank holiday indicator
temperature
rainfall
wind
line
station
recent arrival activity
recent disruption rate
```

A later phase will assess whether these features provide sufficient predictive signal to model elevated disruption risk.

MLflow will be used where supported for experiment tracking and model lifecycle management.

## Databricks Features Covered

The project currently demonstrates or is designed to demonstrate:

* Databricks notebooks
* PySpark DataFrames
* Spark SQL
* Unity Catalog
* Unity Catalog Volumes
* Delta Lake
* Delta MERGE
* Medallion Architecture
* REST API ingestion
* nested JSON parsing
* explicit Spark schemas
* incremental processing
* dimensional modelling
* fact modelling
* SCD Type 2
* bridge tables
* deterministic keys
* referential integrity
* data quality
* window functions
* historical temporal joins
* Databricks SQL
* Databricks Apps
* dashboard serving models
* workflow orchestration
* MLflow
* machine learning
* automated testing
* CI/CD concepts
* monitoring
* observability
* performance analysis

## Databricks Free Edition

The implementation targets Databricks Free Edition.

Where functionality differs from a typical production Databricks environment, the project distinguishes between:

```text
Free Edition implementation
+
Enterprise production approach
```

This keeps the repository executable while still demonstrating production-oriented architecture and engineering decisions.

## Project Status

Current phase:

```text
Gold fact modelling
```

Completed:

```text
[✓] Databricks project setup
[✓] Unity Catalog schemas
[✓] Raw landing Volume
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
[✓] Gold fact_line_status
[✓] Gold fact_arrival_observation
```

Current implementation:

```text
[ ] Gold fact_weather
```

Next phase:

```text
[ ] Gold current_line_status
[ ] Gold station_arrival_summary
[ ] Gold daily_network_kpis
```

Later phases:

```text
[ ] Databricks Apps dashboard
[ ] Databricks SQL analytics
[ ] Workflow orchestration
[ ] Monitoring and observability
[ ] Automated testing
[ ] CI/CD
[ ] Machine learning and MLflow
[ ] Future PHP web application
```

## Roadmap

```text
Bronze ingestion
       ✓
       |
Silver transformation
       ✓
       |
Gold dimensions
       ✓
       |
Gold historical facts
       |
       +---- fact_line_status ✓
       +---- fact_arrival_observation ✓
       +---- fact_weather
       |
       v
Gold serving tables
       |
       v
Databricks Apps Dashboard
       |
       v
Analytics and Machine Learning
       |
       v
Future PHP Web Application
```
