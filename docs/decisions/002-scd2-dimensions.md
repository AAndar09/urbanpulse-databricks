# ADR 002: Use SCD Type 2 for Line and Station Dimensions

## Status

Accepted

## Decision

UrbanPulse uses SCD Type 2 for:

```text
dim_line
dim_station
````

Historical versions are preserved using:

```text
effective_from
effective_to
is_current
attribute_hash
```

 

## Rationale

Line and station attributes can change over time.

Overwriting dimension rows would cause historical facts to be interpreted using only the latest metadata.

SCD Type 2 preserves the state that was valid when an event occurred.

 

## Temporal Join Rule

Facts resolve the dimension version where:

```text
effective_from <= event_timestamp
AND
(
    event_timestamp < effective_to
    OR effective_to IS NULL
)
```

 

## Benefits

This provides:

* historically correct joins
* reproducible analysis
* explicit version history
* stable surrogate keys
* support for future attribute changes

 

## Consequences

The model is more complex than a Type 1 dimension.

Pipelines must enforce:

* one current row per business key
* valid effective ranges
* no overlapping versions
* correct temporal fact joins

These conditions are covered by Gold validation.

 

## Guiding Rule

Use stable source identifiers such as `line_id` and `station_id` as business keys, and surrogate keys such as `line_key` and `station_key` for historical dimension versions.

