# UrbanPulse Pipeline

## Overview

UrbanPulse follows a repeatable medallion pipeline:

```text
API
↓
Raw JSON Landing
↓
Bronze
↓
Silver
↓
Gold
↓
Serving Tables
↓
Dashboard
````

Each layer has a clear responsibility.

 

## 1. API Ingestion

UrbanPulse retrieves data from:

* Transport for London
* Open-Meteo
* GOV.UK

A reusable HTTP client provides:

* connection reuse
* timeouts
* transient error retries
* HTTP status handling

Source configuration is stored in:

```text
conf/sources.yml
```

 

## 2. Raw Landing

Every API response is preserved in:

```text
/Volumes/workspace/urbanpulse_meta/landing/
```

Typical structure:

```text
source/
    dataset/
        YYYY/
            MM/
                DD/
                    HH/
                        request_id.json
```

This supports:

* traceability
* debugging
* replay
* auditability

 

## 3. Bronze

Schema:

```text
workspace.urbanpulse_bronze
```

Bronze stores the raw payload with ingestion metadata.

Typical fields:

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

Bronze stays close to the source and performs minimal transformation.

 

## 4. Silver

Schema:

```text
workspace.urbanpulse_silver
```

Silver converts raw payloads into typed operational datasets.

Typical responsibilities:

* parse JSON
* enforce schemas
* normalize identifiers
* parse timestamps
* create deterministic keys
* validate required fields
* handle duplicates
* preserve valid repeated observations

Current Silver tables:

```text
tfl_line_status
tfl_stop_points
tfl_stop_point_lines
tfl_arrivals
weather
bank_holidays
```

 

## 5. Gold

Schema:

```text
workspace.urbanpulse_gold
```

Gold provides the analytical model.

### Dimensions

```text
dim_date
dim_line
dim_station
```

### Relationship

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

See [data_model.md](data_model.md) for detailed grains and relationships.

 

## Idempotency

Pipeline stages are designed to be safely rerunnable.

UrbanPulse uses:

* deterministic observation keys
* Delta merges
* upsert logic
* insert-only logic where appropriate
* reproducible serving-table rebuilds

Repeated execution should not create duplicate analytical records.

 

## Arrival Handling

Repeated arrival predictions are intentionally preserved.

Example:

```text
14:00 → ETA 6 minutes
14:05 → ETA 2 minutes
```

These are two valid observations, not duplicates.

Empty arrival responses such as:

```json
[]
```

are also valid and produce zero Silver arrival rows.

 

## Slowly Changing Dimensions

`dim_line` and `dim_station` use SCD Type 2.

Facts resolve the dimension version valid at the event timestamp.

```text
effective_from <= event_timestamp
AND
(
    event_timestamp < effective_to
    OR effective_to IS NULL
)
```

This preserves historical correctness.

 

## Cross-Domain Aggregation

Fact tables are aggregated independently before being combined.

```text
fact_line_status
    ↓
daily line metrics

fact_arrival_observation
    ↓
daily arrival metrics

fact_weather
    ↓
daily weather metrics
```

The daily aggregates are then joined into:

```text
daily_network_kpis
```

This prevents many-to-many row multiplication.

 

## Time Handling

UrbanPulse uses:

```text
UTC
```

for analytical timestamps and:

```text
Europe/London
```

for:

* dashboard display
* calendar dates
* weekdays
* weekends
* bank holidays

Timezone semantics are explicit throughout Gold and serving tables.

 

## Validation

Validation runs throughout the pipeline.

Examples include:

* required identifiers
* duplicate keys
* schema integrity
* Silver-to-Gold reconciliation
* foreign-key integrity
* SCD overlap checks
* serving-table grain
* KPI arithmetic

Gold validation results are persisted to:

```text
workspace.urbanpulse_meta.gold_validation_results
```

 

## Orchestration

The pipeline is automated with Databricks Lakeflow Jobs.

```text
Operational refresh
Every 15 minutes

Weather refresh
Hourly

Reference refresh
Daily
```

See [automation.md](automation.md) for task dependencies and schedules.

 

## Design Principle

The pipeline follows one core rule:

> Source complexity is handled in the data platform, not in the frontend.

Applications consume compact Gold serving tables rather than rebuilding Bronze, Silver, or dimensional logic.
