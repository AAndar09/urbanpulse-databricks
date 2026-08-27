# UrbanPulse Data Quality

## Overview

UrbanPulse applies validation across Silver, Gold, and serving layers.

The goal is to detect bad data before it reaches the dashboard.

 

## Validation Areas

Checks include:

- required identifiers
- duplicate keys
- schema integrity
- timestamp validity
- source coverage
- foreign-key integrity
- SCD consistency
- serving-table grain
- KPI arithmetic
- Silver-to-Gold reconciliation

 

## SCD Validation

`dim_line` and `dim_station` are checked for:

```text
one current row per business key
valid effective date ranges
no overlapping versions
unique surrogate keys
````

 

## Fact Validation

Facts are checked for:

```text
unique observation keys
valid dimension references
valid date keys
expected row reconciliation
```

Current facts:

```text
fact_line_status
fact_arrival_observation
fact_weather
```

 

## Serving Table Validation

Serving tables are checked against their intended grain.

### `current_line_status`

Expected:

```text
one current row per Tube line
```

### `station_arrival_summary`

Expected:

```text
one row per station and line combination
for the latest available arrival date
```

### `daily_network_kpis`

Expected:

```text
one row per analytical date
```

KPI checks also verify that calculated totals and rates remain logically consistent.

 

## Gold Validation Notebook

Validation is orchestrated by:

```text
notebooks/03_gold/11_validate_gold_layer
```

The operational refresh job runs this after serving tables are rebuilt.

 

## Validation Audit Table

Results are persisted to:

```text
workspace.urbanpulse_meta.gold_validation_results
```

Typical fields include:

```text
validation_run_id
check_name
status
actual_value
expected_value
details
checked_at
```

This provides a durable history of pipeline quality.

 

## Failure Behaviour

If a critical Gold validation fails:

```text
validation result recorded
        ↓
notebook fails
        ↓
Lakeflow Job marked failed
        ↓
failure notification triggered
```

Invalid data therefore does not fail silently.

 

## Design Principle

UrbanPulse treats data quality as part of the pipeline itself:

```text
ingest
↓
transform
↓
validate
↓
serve
```

Validation is not a separate manual review step.
