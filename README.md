# UrbanPulse

UrbanPulse is an end-to-end Databricks lakehouse project for analysing London transport operations, disruptions, weather, and related city data.

The project is designed around **Databricks Free Edition** and follows production-style data engineering practices where supported.

## Project Goals

UrbanPulse will provide a platform for answering questions such as:

* Which London Underground lines experience the most disruption?
* When are disruptions most likely?
* How does weather affect transport reliability?
* Are there recurring patterns by time, weekday, season, or public holiday?
* Which parts of the network currently require attention?
* Can historical data be used to predict elevated disruption risk?

## Architecture

```text
Public APIs
    |
    v
API Ingestion
    |
    +----> Raw JSON Landing
    |
    v
Bronze Delta Tables
    |
    v
Silver
Cleaned + Validated + Conformed
    |
    v
Gold
Business-Ready Data Models
    |
    +----> SQL / Analytics
    +----> Dashboard Data
    +----> Machine Learning
```

The project follows the Databricks **Medallion Architecture**:

* **Bronze** — raw source data and ingestion metadata
* **Silver** — cleaned, validated, deduplicated, and conformed data
* **Gold** — business-ready facts, dimensions, KPIs, and serving datasets

## Data Sources

| Source          | Dataset                | Purpose                                |
| --------------- | ---------------------- | -------------------------------------- |
| TfL Unified API | Tube line status       | Network health and disruption analysis |
| TfL Unified API | Station arrivals       | Operational transport activity         |
| TfL Unified API | Station/reference data | Station and line enrichment            |
| Open-Meteo      | Weather                | Weather impact analysis                |
| GOV.UK          | Bank holidays          | Calendar enrichment                    |

Additional public datasets may be introduced where they provide useful analytical value.

## Current Implementation

The project currently includes:

* Databricks Free Edition workspace setup
* Unity Catalog schemas for Bronze, Silver, Gold, and metadata
* Unity Catalog landing Volume
* Git-based project structure
* Reusable Python source package
* YAML-based source configuration
* Reusable REST API client
* Retry and HTTP error handling
* Raw JSON landing
* Bronze Delta ingestion
* TfL Tube line-status ingestion
* Ingestion metadata and request traceability
* Historical snapshot accumulation

Current pipeline:

```text
TfL Unified API
      |
      v
Reusable API Client
      |
      +----> Raw JSON
      |      Unity Catalog Volume
      |
      v
workspace.urbanpulse_bronze.tfl_line_status
```

## Repository Structure

```text
urbanpulse-databricks/
|
├── conf/
│   └── sources.yml
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

Raw landing files are stored under:

```text
/Volumes/workspace/urbanpulse_meta/landing/
```

Example Bronze table:

```text
workspace.urbanpulse_bronze.tfl_line_status
```

## Engineering Principles

The project follows these conventions:

* `snake_case` naming
* reusable Python modules instead of large notebooks
* notebooks focused primarily on orchestration
* configuration separated from processing logic
* no secrets committed to Git
* explicit Spark schemas where appropriate
* idempotent processing where applicable
* incremental ingestion
* raw source preservation
* data-quality validation
* stable business keys
* audit and ingestion metadata
* Delta Lake for persisted lakehouse tables
* Git-based version control
* testing for reusable transformation logic

## Bronze Ingestion Metadata

Bronze records include metadata such as:

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

This provides traceability from a Delta record back to the API request and raw landed response.

## Planned Development

The project will progressively add:

* additional TfL datasets
* Open-Meteo ingestion
* UK bank-holiday ingestion
* explicit nested JSON schemas
* Silver transformations
* deduplication
* data-quality checks
* quarantine handling
* dimensional modelling
* Gold fact and dimension tables
* Slowly Changing Dimensions
* Spark window operations
* Delta `MERGE`
* incremental processing
* workflow orchestration
* monitoring and audit tables
* Databricks SQL analytics
* dashboard-ready Gold datasets
* feature engineering
* machine-learning models
* MLflow experiment tracking where supported
* automated tests
* CI/CD concepts
* performance and optimisation analysis

## Downstream Consumption

Gold datasets will be designed as stable serving interfaces for analytical consumers.

Examples may include:

```text
current_line_status
station_summary
disruption_summary
weather_impact
daily_network_kpis
disruption_predictions
```

These datasets will use predictable schemas, stable identifiers, and clearly defined timestamp semantics.

A separate web application may later consume these serving datasets to provide a dashboard-style user interface.

## Free Edition

The implementation targets **Databricks Free Edition**.

Where Free Edition differs from a typical enterprise Databricks environment, the project will distinguish between:

```text
Free Edition implementation
        +
Enterprise production equivalent
```

This allows the project to remain executable while still demonstrating production-oriented architectural decisions.

## Project Status

**Current phase:** Bronze ingestion

**Completed source:** TfL Tube line status

**Next phase:** Bronze to Silver transformation, schema parsing, validation, and data-quality handling.
