# ADR 001: Use a Medallion Architecture

## Status

Accepted

## Decision

UrbanPulse uses three analytical layers:

```text
Bronze
Silver
Gold
````

A raw JSON landing layer is also retained before Bronze processing.



## Rationale

The source APIs contain nested, changing, operational data that should not be exposed directly to analytics or applications.

The medallion model provides clear separation:

```text
Landing
Preserve original API responses

Bronze
Store source payloads with ingestion metadata

Silver
Parse, type, validate, and conform source data

Gold
Model business entities, facts, KPIs, and serving tables
```



## Benefits

This approach provides:

* source traceability
* replay capability
* cleaner transformations
* explicit data-quality boundaries
* reusable analytical models
* simpler application queries
* easier troubleshooting



## Consequences

The architecture introduces more tables and pipeline stages than a direct API-to-dashboard solution.

This additional structure is intentional because UrbanPulse is designed as an end-to-end data engineering project rather than a lightweight API application.



## Guiding Rule

Applications should consume Gold serving tables rather than reconstructing business logic from Bronze or Silver data.

