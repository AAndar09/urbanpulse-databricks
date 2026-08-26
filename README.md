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

The platform is designed to support analytics, dashboards, machine learning, and downstream application consumption.

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

Bronze preserves API responses with minimal transformation.

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

Original API responses are also retained as JSON in a Unity Catalog Volume.

### Silver

Silver contains structured, validated, and conformed operational data.

Responsibilities include:

* explicit schema parsing
* nested JSON processing
* timestamp normalization
* deterministic keys
* source deduplication
* data quality validation
* incremental Delta processing
* preservation of historical observations
* normalization of source relationships

### Gold

Gold provides business-facing dimensional models, historical facts, and consumer-ready serving datasets.

The Gold layer supports:

* Databricks SQL analytics
* Databricks Apps
* operational dashboards
* historical analysis
* machine learning features
* downstream application consumption

## Data Sources

| Source          | Dataset          | Purpose                                |
| --------------- | ---------------- | -------------------------------------- |
| TfL Unified API | Tube line status | Service health and disruption analysis |
| TfL Unified API | Tube stop points | Station reference data                 |
| TfL Unified API | Station arrivals | Operational arrival observations       |
| Open-Meteo      | London weather   | Environmental enrichment               |
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

Raw API responses are landed under:

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

Repeated API executions create new snapshots rather than replacing historical records.

This provides:

* source traceability
* replay capability
* ingestion history
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

Key attributes include:

```text
line_id
line_name
status_severity
status_description
status_reason
snapshot_at
```

Repeated observations are retained because service state changes over time.

### TfL Stop Points

Contains validated Tube station reference data.

The canonical TfL station NAPTAN identifier is used as the downstream station identity.

Station names are descriptive attributes and are not treated as identifiers.

### TfL Station-Line Relationships

Station and line relationships are normalized into a separate Silver table.

TfL StopPoint responses can contain relationships to services outside the London Underground, including bus routes.

These relationships remain available in Silver.

Gold restricts station-line relationships to Tube lines represented by `dim_line`.

### TfL Arrivals

Contains individual arrival predictions observed during TfL polling requests.

Repeated observations of the same vehicle are intentionally retained.

For example:

```text
10:00 | Train A | ETA 300 seconds
10:05 | Train A | ETA 60 seconds
```

These are two valid operational observations.

Each observation is identified by:

```text
arrival_observation_key
```

### Weather

Open-Meteo responses are normalized into structured London weather observations.

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

Weather timestamps are normalized for analytical use while preserving explicit London timezone semantics.

### Bank Holidays

GOV.UK holiday data is transformed into structured calendar events for England and Wales.

Repeated identical source snapshots are collapsed deterministically.

## Gold Layer

The Gold layer follows a dimensional model with historical fact tables and dashboard-oriented serving models.

```text
urbanpulse_gold
|
├── dim_date
├── dim_line
├── dim_station
├── bridge_station_line
|
├── fact_line_status
├── fact_arrival_observation
├── fact_weather
|
├── current_line_status
├── station_arrival_summary
└── daily_network_kpis
```

## Gold Dimensions

### `dim_date`

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

### `dim_line`

```text
workspace.urbanpulse_gold.dim_line
```

Implemented using Slowly Changing Dimension Type 2.

Business key:

```text
line_id
```

Historical version key:

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

```text
workspace.urbanpulse_gold.dim_station
```

Implemented using Slowly Changing Dimension Type 2.

Business key:

```text
station_id
```

where:

```text
station_id = station_naptan
```

Historical version key:

```text
station_key
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

## Gold Bridge

### `bridge_station_line`

```text
workspace.urbanpulse_gold.bridge_station_line
```

Grain:

> One current canonical Tube station to Tube line relationship.

Key fields include:

```text
station_line_key
station_key
line_key
station_id
line_id
```

Only Tube lines represented in `dim_line` are included.

Non-Tube relationships remain available in Silver.

## Gold Facts

### `fact_line_status`

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

Each historical observation resolves to the SCD line version valid at the observation timestamp.

### `fact_arrival_observation`

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

Station and line dimensions are joined using their SCD Type 2 validity periods.

### `fact_weather`

```text
workspace.urbanpulse_gold.fact_weather
```

Grain:

> One London weather observation per location and observation timestamp.

Key fields include:

```text
weather_observation_key
observation_date_key
weather_observed_at
weather_observed_at_local
temperature_c
relative_humidity_pct
precipitation_mm
rain_mm
weather_code
weather_description
cloud_cover_pct
wind_speed_kmh
wind_gusts_kmh
```

Weather observations are enriched with their London-local calendar date.

## Gold Serving Layer

Serving tables provide small, predictable, dashboard-friendly datasets.

They are designed to be consumed directly by Databricks Apps, SQL dashboards, and future external applications.

### `current_line_status`

```text
workspace.urbanpulse_gold.current_line_status
```

Grain:

> One row per current Tube line.

Provides the latest operational state for each line.

Key outputs include:

```text
line_id
line_name
status_severity
status_description
status_reason
is_good_service
is_disrupted
status_snapshot_at_utc
status_snapshot_at_local
serving_updated_at
```

Typical use cases:

* network status cards
* disruption indicators
* current line status views
* operational dashboard summaries

### `station_arrival_summary`

```text
workspace.urbanpulse_gold.station_arrival_summary
```

Grain:

> One station and line summary for the latest available arrival observation date.

Key metrics include:

```text
arrival_observations
distinct_vehicles
avg_eta_seconds
min_eta_seconds
max_eta_seconds
next_expected_arrival_utc
next_expected_arrival_local
latest_prediction_timestamp_utc
latest_prediction_timestamp_local
```

Typical use cases:

* station activity views
* line activity views
* arrival KPI cards
* next-arrival views
* station comparison

### `daily_network_kpis`

```text
workspace.urbanpulse_gold.daily_network_kpis
```

Grain:

> One row per calendar date represented by operational data.

The table combines separately aggregated line-status, arrival, weather, and calendar metrics.

Key metrics include:

```text
line_snapshots
distinct_lines_observed
disrupted_line_snapshots
good_service_line_snapshots
disruption_rate_pct

arrival_observations
distinct_vehicles
stations_observed
avg_eta_seconds

weather_observations
avg_temperature_c
min_temperature_c
max_temperature_c
avg_relative_humidity_pct
total_precipitation_mm
max_wind_gust_kmh

is_weekend
is_bank_holiday
holiday_name
```

Each fact domain is aggregated independently before being joined.

This avoids many-to-many metric inflation.

## Gold Model

```text
                          dim_date
                             |
             +---------------+---------------+
             |               |               |
             v               v               v
     fact_line_status  fact_arrival       fact_weather
             |         observation
             |            /    \
             v           v      v
         dim_line     dim_line  dim_station
             \                    /
              \                  /
               bridge_station_line


Historical Facts
        |
        v
Gold Serving Layer
        |
        +---- current_line_status
        +---- station_arrival_summary
        +---- daily_network_kpis
```

## Slowly Changing Dimensions

UrbanPulse uses SCD Type 2 for line and station reference data.

Current SCD dimensions:

```text
dim_line
dim_station
```

Processing behaviour:

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

Current records use:

```text
effective_to = NULL
is_current = TRUE
```

This allows historical facts to resolve the descriptive dimension state that was valid when an observation occurred.

## Data Quality

Data quality checks are applied throughout Bronze, Silver, and Gold processing.

Current checks include:

* required identifiers
* required timestamps
* explicit source schemas
* valid latitude and longitude
* valid percentage ranges
* non-negative arrival times
* non-negative precipitation
* non-negative wind measurements
* deterministic key uniqueness
* business-key uniqueness
* source grain validation
* canonical station identity validation
* source coverage validation
* referential integrity
* SCD effective-date integrity
* SCD overlap detection
* fact-to-Silver reconciliation
* serving-table grain validation
* KPI arithmetic reconciliation
* calendar coverage validation

Unexpected invalid records cause the relevant transformation to fail instead of silently entering downstream datasets.

## Gold Validation and Reconciliation

The completed Gold model is validated end to end using:

```text
notebooks/03_gold/11_validate_gold_layer
```

Validation covers:

```text
table existence
table population
dimension key uniqueness
SCD current-version integrity
SCD validity periods
SCD overlap detection
bridge referential integrity
Silver-to-Gold fact reconciliation
fact key uniqueness
fact foreign-key integrity
serving-table grain
serving-table coverage
daily KPI reconciliation
```

Validation results are persisted to:

```text
workspace.urbanpulse_meta.gold_validation_results
```

Each validation execution receives a unique:

```text
validation_run_id
```

and records:

```text
check_name
status
actual_value
expected_value
details
checked_at
```

The validation notebook fails when one or more checks fail, while still retaining the validation results for audit purposes.

This provides an initial observability and reconciliation layer for the project.

## Idempotency

UrbanPulse pipelines are designed to be safely rerunnable.

Deterministic keys include:

```text
line_key
station_key
station_line_key
line_status_key
arrival_observation_key
weather_observation_key
holiday_key
```

Processing strategies include:

* insert-only Delta MERGE
* SCD-aware updates
* deterministic table rebuilds
* source-level deduplication
* business-key validation
* consumer-table overwrite where the dataset represents current state

Unchanged reruns do not create duplicate business records.

## Timestamp Strategy

UrbanPulse separates timestamp concepts rather than treating them as interchangeable.

Examples include:

```text
snapshot_at
prediction_timestamp
expected_arrival
weather_observed_at
status_created_at
effective_from
effective_to
serving_updated_at
```

Analytical timestamps are stored in UTC where appropriate.

Europe/London conversions are applied explicitly when determining:

```text
calendar date
weekday
weekend
bank holiday
dashboard display timestamps
```

This provides clear timezone semantics for analytical and application consumers.

## Engineering Principles

The project follows these conventions:

* `snake_case` naming
* explicit Spark schemas
* notebooks focused on orchestration
* reusable processing logic under `src/`
* configuration separated from transformation logic
* raw source preservation
* stable business identifiers
* deterministic analytical keys
* idempotent processing
* Delta Lake persistence
* SCD Type 2 for changing reference data
* explicit UTC and London-local timestamp semantics
* quality validation before promotion
* fact-to-source reconciliation
* referential integrity between Gold models
* Git-based version control
* reusable Delta utilities
* consumer-friendly serving interfaces
* audit-friendly validation outputs

## Dashboard and Application Strategy

UrbanPulse will provide two application experiences.

### Databricks Apps Dashboard

The next major implementation phase is a dashboard-style application using **Databricks Apps**.

The application will consume the completed Gold serving layer:

```text
current_line_status
station_arrival_summary
daily_network_kpis
```

Planned dashboard areas include:

* network overview
* current Tube line health
* disrupted lines
* disruption trends
* station arrival activity
* predicted waiting times
* transport and weather trends
* daily network KPIs
* data freshness indicators

The application layer will consume business-ready Gold outputs rather than reproducing Spark transformation logic.

This keeps responsibilities separated between:

```text
data engineering
business logic
serving layer
application presentation
```

### Future PHP Web Application

A separate PHP-based web application is planned for a later phase.

The PHP application will consume stable Gold serving datasets rather than raw or Silver data.

Gold provides:

* stable identifiers
* predictable schemas
* precomputed metrics
* explicit timestamp semantics
* small consumer-friendly datasets
* separation between current and historical state

The Databricks Apps implementation will demonstrate native Databricks application development.

The later PHP application will demonstrate external consumption of the platform through an independent application architecture.

## Planned Analytics

The completed Gold layer supports analysis such as:

* disruption frequency by line
* disruption rate by weekday
* bank holiday effects
* station arrival activity
* predicted waiting times
* distinct vehicle observations
* service reliability trends
* weather and disruption relationships
* wet versus dry day comparison
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

A later phase will assess whether these features provide enough predictive signal to model elevated disruption risk.

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
* serving-layer modelling
* reconciliation testing
* validation auditing
* Databricks SQL
* Databricks Apps
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

This keeps the repository executable while preserving production-oriented architecture and engineering decisions.

## Project Status

Current phase:

```text
Core Gold implementation and validation complete
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
[✓] Gold fact_weather

[✓] Gold current_line_status
[✓] Gold station_arrival_summary
[✓] Gold daily_network_kpis

[✓] End-to-end Gold validation
[✓] Silver-to-Gold reconciliation
[✓] Gold validation audit table
```

Next phase:

```text
[ ] Databricks Apps dashboard design
[ ] Databricks Apps dashboard implementation
```

Later phases:

```text
[ ] Databricks SQL analytics
[ ] Workflow orchestration
[ ] Monitoring and observability
[ ] Automated unit and integration testing
[ ] CI/CD
[ ] Machine learning feature engineering
[ ] MLflow experiments
[ ] Disruption-risk modelling
[ ] Future PHP web application
```

## Roadmap

```text
Public API Ingestion
        ✓
        |
        v
Bronze
        ✓
        |
        v
Silver
        ✓
        |
        v
Gold Dimensions
        ✓
        |
        v
Gold Historical Facts
        ✓
        |
        v
Gold Serving Layer
        ✓
        |
        v
Gold Validation and Reconciliation
        ✓
        |
        v
Databricks Apps Dashboard
        |
        v
Analytics and Orchestration
        |
        v
Machine Learning and MLflow
        |
        v
Future PHP Web Application
```
