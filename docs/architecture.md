# UrbanPulse Architecture

## Overview

UrbanPulse is an automated lakehouse-backed analytics platform for London Underground operational data.

The platform separates ingestion, storage, transformation, business modeling, validation, serving, and presentation into distinct layers.

At a high level:

```text
Public APIs
    ↓
Raw JSON Landing
    ↓
Bronze
    ↓
Silver
    ↓
Gold Dimensions and Facts
    ↓
Gold Serving Tables
    ↓
Databricks SQL
    ↓
Applications
````

Automation is provided by Databricks Lakeflow Jobs.

 

# End-to-End Architecture

```text
                         PUBLIC DATA SOURCES
                                  |
              +-------------------+-------------------+
              |                   |                   |
              v                   v                   v
       TfL Unified API       Open-Meteo API      GOV.UK API
              |                   |                   |
              +-------------------+-------------------+
                                  |
                                  v
                    UNITY CATALOG VOLUME
                     Raw JSON Landing Zone
                                  |
                                  v
                           BRONZE DELTA
                                  |
                                  v
                    SILVER CONFORMED DATA
                                  |
                                  v
               +------------------+------------------+
               |                                     |
               v                                     v
       GOLD DIMENSIONS                         GOLD FACTS
               |                                     |
               +------------------+------------------+
                                  |
                                  v
                      GOLD SERVING TABLES
                                  |
                                  v
                       DATABRICKS SQL
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
             DATABRICKS APPS              PLOTLY CLOUD
             Native deployment            Public dashboard
```

 

# Architecture Principles

UrbanPulse follows several core principles.

## Clear Layer Responsibilities

Each layer has one primary responsibility.

```text
Landing
Preserve source payloads

Bronze
Store source responses with ingestion metadata

Silver
Parse, type, validate, and conform source data

Gold
Model business entities, facts, and relationships

Serving
Expose compact consumer-ready datasets

Application
Present information without recreating warehouse logic
```

This separation reduces duplication and makes the platform easier to maintain.

 

# Source Layer

UrbanPulse currently consumes three public providers.

## Transport for London

Used for:

* Tube line status
* Tube stop points
* Station arrival predictions

## Open-Meteo

Used for:

* London weather observations

## GOV.UK

Used for:

* England and Wales bank holidays

Source-specific configuration is maintained separately from transformation logic.

 

# Raw Landing Layer

Raw API responses are persisted before transformation.

Location:

```text
/Volumes/workspace/urbanpulse_meta/landing/
```

The landing hierarchy follows:

```text
source/
    dataset/
        YYYY/
            MM/
                DD/
                    HH/
                        request_id.json
```

This provides:

* replay capability
* traceability
* debugging support
* preservation of source responses
* separation between ingestion and transformation

The landing layer is not intended for direct analytical consumption.

 

# Bronze Layer

Schema:

```text
workspace.urbanpulse_bronze
```

Bronze stores API payloads together with ingestion metadata.

Typical metadata includes:

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

Current Bronze tables:

```text
tfl_line_status
tfl_stop_points
tfl_arrivals
weather
bank_holidays
```

Bronze remains intentionally close to the original source.

 

# Silver Layer

Schema:

```text
workspace.urbanpulse_silver
```

Silver converts raw payloads into structured operational datasets.

Responsibilities include:

* JSON parsing
* explicit typing
* timestamp normalization
* source-specific validation
* identifier normalization
* deterministic keys
* relationship extraction
* duplicate handling
* preservation of analytically meaningful repeated observations

Current Silver tables:

```text
tfl_line_status
tfl_stop_points
tfl_stop_point_lines
tfl_arrivals
weather
bank_holidays
```

Silver is designed to represent source data faithfully.

 

# Gold Layer

Schema:

```text
workspace.urbanpulse_gold
```

Gold contains business-oriented analytical models.

The Gold layer is divided into:

```text
Dimensions
Facts
Relationships
Serving tables
```

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

Detailed grains and fields are documented in:

```text
docs/data_model.md
```

 

# Dimensional Architecture

UrbanPulse uses a dimensional model for analytical consistency.

## Dimensions

```text
dim_date
dim_line
dim_station
```

## Relationship Table

```text
bridge_station_line
```

## Facts

```text
fact_line_status
fact_arrival_observation
fact_weather
```

This supports historical analysis while keeping dashboard-facing data separate from raw operational records.

 

# Slowly Changing Dimensions

`dim_line` and `dim_station` use SCD Type 2.

This preserves historical versions when descriptive attributes change.

Typical SCD fields include:

```text
effective_from
effective_to
is_current
attribute_hash
```

Facts resolve the appropriate historical dimension row using the event timestamp.

Conceptually:

```text
effective_from <= event_timestamp
AND
(
    event_timestamp < effective_to
    OR effective_to IS NULL
)
```

This prevents historical facts from being interpreted using only the latest dimension state.

 

# Station Identity Model

TfL exposes multiple stop-related identifiers.

UrbanPulse standardizes station identity around:

```text
station_naptan
```

This becomes the Gold business identifier:

```text
station_id
```

Arrival ingestion first resolves configured station names to canonical station identifiers before requesting predictions.

This avoids building Gold models around platform-level or child stop-point IDs.

 

# Station-Line Relationships

Silver preserves the broader relationships exposed by TfL.

These may include non-Tube routes.

The Gold bridge intentionally restricts station-line relationships to lines represented in the current Tube-focused line dimension.

This produces:

```text
Silver
Source-faithful relationships

Gold
Tube-focused analytical relationships
```

 

# Fact Architecture

## Line Status

```text
TfL Line Status
    ↓
Silver line observations
    ↓
fact_line_status
```

Grain:

```text
one line-status observation per polling snapshot
```

Repeated snapshots are preserved to support historical analysis.

 

## Arrivals

```text
TfL Arrival Predictions
    ↓
Silver arrival observations
    ↓
fact_arrival_observation
```

Grain:

```text
one observed arrival prediction
```

Repeated predictions for the same vehicle are intentionally retained because they represent distinct observations over time.

 

## Weather

```text
Open-Meteo
    ↓
Silver weather observations
    ↓
fact_weather
```

Grain:

```text
one weather observation
```

Weather is modeled separately from transport facts.

Cross-domain analysis happens after each domain is aggregated to a compatible analytical grain.

 

# Serving Layer Architecture

The frontend does not query large fact tables for common views.

Instead, dedicated Gold serving tables expose compact application contracts.

## Current Line Status

```text
current_line_status
```

Provides one current row per Tube line.

Used by:

* Network Overview
* Line Status
* Current Disruptions

 

## Station Arrival Summary

```text
station_arrival_summary
```

Provides one station and line summary for the latest available arrival date.

Used by:

* Station Arrivals
* Network Overview arrival KPIs

 

## Daily Network KPIs

```text
daily_network_kpis
```

Provides one analytical row per date.

Used by:

* Recent Trends
* Future Network Trends
* Weather comparison analysis
* Future feature engineering

 

# Cross-Domain Aggregation

A key design principle is:

> Aggregate each fact domain independently before joining across domains.

Incorrect pattern:

```text
line facts
    ×
arrival facts
    ×
weather facts
```

This can create many-to-many multiplication and inflated metrics.

UrbanPulse instead uses:

```text
line facts
    ↓
daily line aggregate

arrival facts
    ↓
daily arrival aggregate

weather facts
    ↓
daily weather aggregate
```

Then:

```text
daily line aggregate
        +
daily arrival aggregate
        +
daily weather aggregate
        ↓
daily_network_kpis
```

This preserves metric correctness.

 

# Time Architecture

UrbanPulse uses two explicit time concepts.

## UTC

Used for:

* analytical timestamps
* event ordering
* cross-source alignment
* technical auditing

## Europe/London

Used for:

* dashboard display
* calendar dates
* weekday calculations
* weekend classification
* bank holiday joins

This distinction is necessary because London changes between GMT and BST.

Examples of explicit serving fields include:

```text
status_snapshot_at_utc
status_snapshot_at_local

next_expected_arrival_utc
next_expected_arrival_local

latest_prediction_timestamp_utc
latest_prediction_timestamp_local
```

 

# Automation Architecture

UrbanPulse uses three Databricks Lakeflow Jobs.

## Operational Job

```text
urbanpulse_operational_refresh
```

Runs every 15 minutes.

Responsibilities:

* line-status ingestion
* arrival ingestion
* Silver processing
* operational facts
* current line status serving
* station arrival serving
* daily KPIs
* Gold validation

 

## Weather Job

```text
urbanpulse_weather_refresh
```

Runs hourly.

Responsibilities:

* weather ingestion
* weather Silver transformation
* weather fact refresh

 

## Reference Job

```text
urbanpulse_reference_refresh
```

Runs daily.

Responsibilities:

* stop-point refresh
* bank-holiday refresh
* dimension maintenance
* station-line bridge maintenance

Detailed scheduling and dependency information is documented in:

```text
docs/automation.md
```

 

# Application Architecture

UrbanPulse uses Dash with Dash Bootstrap Components and Plotly.

The frontend reads through Databricks SQL.

```text
Dash
    ↓
Query Service
    ↓
Databricks SQL Connector
    ↓
Gold Serving Tables
```

Application code is separated into:

```text
pages/
components/
services/
assets/
```

This keeps:

* page layout
* reusable presentation
* SQL access
* styling

independent from one another.

 

# Deployment Architecture

UrbanPulse supports two deployment environments.

## Databricks Apps

```text
Dash App
    ↓
Databricks-managed identity
    ↓
SQL Warehouse
    ↓
Unity Catalog Gold Tables
```

This demonstrates native platform integration.

## Plotly Cloud

```text
Public Dash App
    ↓
Databricks SQL Connector
    ↓
External authentication
    ↓
SQL Warehouse
    ↓
Unity Catalog Gold Tables
```

This provides public portfolio access while using the same serving layer.

 

# Authentication Architecture

The SQL connection service supports both application environments.

Conceptually:

```text
External Databricks credentials present?
    |
    +-- yes --> external SQL authentication
    |
    +-- no --> native Databricks Apps authentication
```

This allows one application codebase to run in both environments.

Credentials are never stored in source control.

 

# Data Quality Architecture

Validation exists throughout the platform.

```text
Source
    ↓
Bronze checks
    ↓
Silver checks
    ↓
Gold integrity checks
    ↓
Serving checks
    ↓
Audit table
```

Gold validation results are persisted to:

```text
workspace.urbanpulse_meta.gold_validation_results
```

This enables future platform-health reporting.

 

# Repository Architecture

The repository mirrors the platform layers.

```text
conf/
    source and project configuration

src/urbanpulse/
    reusable Python logic

notebooks/
    Databricks orchestration

app/
    Dash application

sql/
    SQL assets

tests/
    automated tests

docs/
    technical documentation
```

The preferred rule is:

> Logic belongs in reusable source modules. Notebooks primarily orchestrate that logic.

 

# Consumer Design Principle

UrbanPulse treats Gold serving tables as contracts.

Applications should prefer:

```text
current_line_status
station_arrival_summary
daily_network_kpis
```

Applications should avoid:

```text
raw JSON
Bronze payloads
large Silver joins
rebuilding warehouse business logic
```

This makes future consumers easier to support.

Possible consumers include:

* Dash
* Databricks Apps
* Plotly Cloud
* SQL reports
* machine learning pipelines
* future APIs
* future PHP frontend

 

# Architecture Summary

The project can be summarized as:

```text
Public APIs
    ↓
Reliable ingestion
    ↓
Raw preservation
    ↓
Bronze
    ↓
Silver conformance
    ↓
Gold dimensional model
    ↓
Validated serving layer
    ↓
Databricks SQL
    ↓
Multiple application consumers
```

The architecture is designed to remain:

* automated
* modular
* historically correct
* consumer-friendly
* observable
* testable
* portable
* extensible

