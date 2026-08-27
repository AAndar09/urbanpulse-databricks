# UrbanPulse Data Model

## Overview

UrbanPulse uses a dimensional Gold model designed for analytics, dashboards, and future downstream applications.

The Gold layer contains:

```text
Dimensions
Facts
Relationship tables
Serving tables
````

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

The model is designed around several principles:

* clear table grain
* stable business identifiers
* surrogate keys where historical versioning is required
* SCD Type 2 for changing dimensions
* explicit UTC and Europe/London timestamps
* deterministic fact keys
* consumer-ready serving tables
* minimal business logic in the frontend


# Model Overview

```text
                    dim_date
                       |
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
fact_line_status  fact_arrival   fact_weather
        |          observation
        |              |
        v              v
     dim_line       dim_station
        |              |
        +-------> bridge_station_line
                       |
                       v
                station-line
                relationships
```

The fact tables retain historical observations.

Serving tables provide simplified application-facing views.

# Dimension Tables

## `dim_date`

Table:

```text
workspace.urbanpulse_gold.dim_date
```

### Grain

```text
one row per calendar date
```

### Date Range

```text
2019-01-01
to
2035-12-31
```

### Primary Key

```text
date_key
```

The key uses:

```text
YYYYMMDD
```

Example:

```text
20260827
```

### Purpose

`dim_date` provides reusable calendar attributes for all analytical facts.

It supports:

* year analysis
* quarter analysis
* month analysis
* weekday analysis
* weekend analysis
* bank-holiday analysis
* date-based joins across fact domains

### Representative Fields

```text
date_key
calendar_date
year
quarter
month
month_name
day_of_month
day_of_week
day_name
is_weekend
is_bank_holiday
holiday_name
```

### Weekday Convention

UrbanPulse uses ISO-style weekday numbering:

```text
Monday = 1
Tuesday = 2
Wednesday = 3
Thursday = 4
Friday = 5
Saturday = 6
Sunday = 7
```

### Bank Holiday Enrichment

Bank holiday information is sourced from the GOV.UK England and Wales bank holiday dataset.


# `dim_line`

Table:

```text
workspace.urbanpulse_gold.dim_line
```

### Grain

```text
one row per historical version of a Tube line
```

### Business Key

```text
line_id
```

### Surrogate Key

```text
line_key
```

### Dimension Type

```text
SCD Type 2
```

### Purpose

`dim_line` provides historically correct Tube line attributes.

Typical attributes include:

```text
line_id
line_name
mode_name
is_active
```

### SCD Fields

```text
attribute_hash
effective_from
effective_to
is_current
created_at
updated_at
```

### Temporal Validity

A fact resolves a dimension row using:

```text
effective_from <= event_timestamp
AND
(
    event_timestamp < effective_to
    OR effective_to IS NULL
)
```

### Initial Effective Date

The first version of a line begins at the earliest observed Silver line-status timestamp.

This allows historical fact rows to resolve correctly.


# `dim_station`

Table:

```text
workspace.urbanpulse_gold.dim_station
```

### Grain

```text
one row per historical version of a canonical Tube station
```

### Business Key

```text
station_id
```

UrbanPulse defines:

```text
station_id = station_naptan
```

### Surrogate Key

```text
station_key
```

### Dimension Type

```text
SCD Type 2
```

### Representative Fields

```text
station_key
station_id
representative_stop_point_id
station_name
latitude
longitude
stop_type
modes
is_active
attribute_hash
effective_from
effective_to
is_current
created_at
updated_at
```

### Canonical Station Resolution

TfL may expose several stop-point records associated with one station.

UrbanPulse prefers:

```text
stop_point_id == station_naptan
```

where available.

If a direct canonical row is not available, a deterministic representative stop point is selected.

### Initial Effective Date

The initial station version begins at the earliest observed Silver stop-point timestamp.


# Relationship Table

## `bridge_station_line`

Table:

```text
workspace.urbanpulse_gold.bridge_station_line
```

### Grain

```text
one current Tube station-to-line relationship
```

### Purpose

This table represents the many-to-many relationship between:

```text
stations
and
Tube lines
```

A station can serve multiple lines.

A line can serve multiple stations.

### Representative Fields

```text
station_line_key
station_key
line_key
station_id
line_id
source_snapshot_at
created_at
```

### Tube Scope

TfL stop-point relationships can contain:

* Tube routes
* bus routes
* night-bus routes
* other transport relationships

Silver preserves the broader source relationships.

Gold restricts the bridge to line identifiers represented in the current Tube-focused `dim_line`.

This keeps the Gold analytical model aligned with the application's London Underground scope.


# Fact Tables

## `fact_line_status`

Table:

```text
workspace.urbanpulse_gold.fact_line_status
```

### Grain

```text
one Tube line status observation per TfL polling snapshot
```

### Primary Observation Key

```text
line_status_key
```

### Foreign Keys

```text
line_key
snapshot_date_key
```

### Representative Fields

```text
line_status_key
line_key
line_id
snapshot_date_key
request_id
snapshot_at
status_id
status_severity
status_description
status_reason
status_created_at
is_good_service
is_disrupted
source
created_at
```

### Historical Behavior

Each polling observation is retained.

Example:

```text
14:00
Piccadilly
Good Service

14:15
Piccadilly
Minor Delays
```

These remain separate fact observations.

### Dimension Resolution

`line_key` is resolved using the line dimension version valid at the fact event timestamp.

### Date Resolution

`snapshot_date_key` is based on the Europe/London calendar date of the status snapshot.


# `fact_arrival_observation`

Table:

```text
workspace.urbanpulse_gold.fact_arrival_observation
```

### Grain

```text
one observed arrival prediction
```

### Primary Key

```text
arrival_observation_key
```

This key is deterministic.

### Foreign Keys

```text
station_key
line_key
prediction_date_key
```

### Representative Fields

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
naptan_id
station_name
line_name
platform_name
direction
destination_naptan_id
destination_name
prediction_timestamp
expected_arrival
time_to_station_seconds
current_location
towards
mode_name
snapshot_at
source
created_at
```

### Observation Preservation

Repeated predictions are intentionally retained.

Example:

```text
14:00
vehicle 123
ETA = 420 seconds

14:05
vehicle 123
ETA = 120 seconds
```

These represent two separate observations of the prediction process.

### Dimension Resolution

`station_key` and `line_key` are resolved using the dimension versions valid at:

```text
prediction_timestamp
```

### Date Resolution

`prediction_date_key` is derived using Europe/London calendar semantics.


# `fact_weather`

Table:

```text
workspace.urbanpulse_gold.fact_weather
```

### Grain

```text
one London weather observation
```

### Primary Key

```text
weather_observation_key
```

### Foreign Key

```text
observation_date_key
```

### Representative Fields

```text
weather_observation_key
observation_date_key
weather_observed_at
weather_observed_at_local
latitude
longitude
weather_timezone
utc_offset_seconds
temperature_c
relative_humidity_pct
precipitation_mm
rain_mm
weather_code
weather_description
cloud_cover_pct
wind_speed_kmh
wind_gusts_kmh
measurement_interval_seconds
snapshot_at
source
created_at
```

### Date Resolution

`observation_date_key` uses the Europe/London calendar date.

### Purpose

The fact supports contextual analysis of network conditions alongside:

* temperature
* humidity
* rainfall
* wind
* cloud conditions

Weather data is not treated as a direct causal explanation for transport disruption.

---

# Serving Tables

Serving tables provide stable contracts for applications.

They deliberately reduce the amount of SQL and business logic required by consumers.


# `current_line_status`

Table:

```text
workspace.urbanpulse_gold.current_line_status
```

### Grain

```text
one current row per Tube line
```

### Purpose

Provides the latest known operational state for each Tube line.

Used by:

* Network Overview
* Line Status
* Current Disruptions

### Representative Fields

```text
line_key
line_id
line_name
mode_name
status_severity
status_description
status_reason
is_good_service
is_disrupted
status_record_count
status_snapshot_at_utc
status_snapshot_at_local
request_id
serving_updated_at
```

### Latest-State Logic

The serving table selects the latest available line-status snapshot for each line.

Where multiple status records exist for the same latest snapshot, they are aggregated into one application-facing row.


# `station_arrival_summary`

Table:

```text
workspace.urbanpulse_gold.station_arrival_summary
```

### Grain

```text
one station and line combination
for the latest available London arrival date
```

### Purpose

Provides compact arrival metrics for the frontend.

Used by:

* Station Arrivals
* Network Overview arrival KPIs

### Representative Fields

```text
station_key
station_id
station_name
latitude
longitude

line_key
line_id
line_name

arrival_observations
distinct_vehicles

avg_eta_seconds
min_eta_seconds
max_eta_seconds

next_expected_arrival_utc
next_expected_arrival_local

latest_prediction_timestamp_utc
latest_prediction_timestamp_local

serving_updated_at
```

### Metrics

#### Arrival Observations

Number of arrival predictions represented by the station-line combination.

#### Distinct Vehicles

Number of unique vehicles represented.

#### Average ETA

Average value of:

```text
time_to_station_seconds
```

#### Minimum ETA

Shortest observed ETA.

#### Maximum ETA

Longest observed ETA.

#### Next Expected Arrival

Earliest current expected arrival represented by the dataset.


# `daily_network_kpis`

Table:

```text
workspace.urbanpulse_gold.daily_network_kpis
```

### Grain

```text
one analytical calendar date represented by fact data
```

### Purpose

Provides a compact daily analytical dataset across:

* line status
* arrivals
* weather

Used by:

* Network Overview trend charts
* future Network Trends page
* exploratory analytics
* future machine learning feature engineering

### Date Attributes

Representative date fields include:

```text
date_key
calendar_date
year
quarter
month
month_name
day_of_week
day_name
is_weekend
is_bank_holiday
holiday_name
```

### Line Metrics

```text
line_snapshots
distinct_lines_observed
disrupted_line_snapshots
good_service_line_snapshots
disruption_rate_pct
```

### Arrival Metrics

```text
arrival_observations
distinct_vehicles
stations_observed
avg_eta_seconds
```

### Weather Metrics

```text
weather_observations
avg_temperature_c
min_temperature_c
max_temperature_c
avg_relative_humidity_pct
total_precipitation_mm
max_wind_gust_kmh
```

### Audit Field

```text
serving_updated_at
```


# Daily KPI Join Strategy

Fact domains are never joined directly at their raw observation grains.

For example, UrbanPulse avoids:

```text
fact_line_status
    ×
fact_arrival_observation
    ×
fact_weather
```

This could create many-to-many row multiplication.

Instead:

```text
fact_line_status
    ↓
daily line aggregate
```

```text
fact_arrival_observation
    ↓
daily arrival aggregate
```

```text
fact_weather
    ↓
daily weather aggregate
```

The three daily aggregates are then joined by date.

This preserves metric correctness.


# Key Strategy

UrbanPulse uses two key categories.

## Business Keys

Stable identifiers originating from the business or source domain.

Examples:

```text
line_id
station_id
arrival_id
vehicle_id
request_id
```

These are useful for:

* filtering
* application controls
* source traceability
* integration

## Surrogate Keys

Warehouse-generated identifiers for dimensional versions.

Examples:

```text
line_key
station_key
```

These allow facts to reference a specific historical dimension version.


# Application Filter Strategy

Application filters should use stable identifiers as values.

Example:

```text
Displayed label:
Baker Street Underground Station

Filter value:
station_id
```

Similarly:

```text
Displayed label:
Piccadilly

Filter value:
line_id
```

This prevents display-name changes from breaking application behavior.


# Timezone Strategy

UrbanPulse explicitly distinguishes UTC and London-local time.

## UTC

Used for:

* analytical timestamps
* ordering
* cross-source comparison
* audit operations

## Europe/London

Used for:

* dashboard timestamps
* local calendar dates
* weekdays
* weekends
* bank holidays

Examples:

```text
status_snapshot_at_utc
status_snapshot_at_local

next_expected_arrival_utc
next_expected_arrival_local

latest_prediction_timestamp_utc
latest_prediction_timestamp_local
```


# Model Validation

Gold model validation includes:

* dimension key uniqueness
* one current SCD row per business key
* valid SCD effective date ranges
* no overlapping SCD versions
* fact key uniqueness
* fact foreign-key integrity
* bridge uniqueness
* bridge foreign-key integrity
* Silver-to-Gold reconciliation
* serving-table grain validation
* KPI arithmetic validation

Validation results are stored in:

```text
workspace.urbanpulse_meta.gold_validation_results
```

Detailed validation documentation is available in:

```text
docs/data_quality.md
```


# Consumer Contract

Consumers should primarily query:

```text
current_line_status
station_arrival_summary
daily_network_kpis
```

Consumers should generally avoid rebuilding application views directly from:

```text
Bronze
raw Silver tables
raw fact tables
```

The serving layer exists to provide stable, compact, reusable contracts.


# Future Model Extensions

The current model can support future objects such as:

```text
line_hourly_kpis
station_hourly_kpis
line_daily_kpis
station_daily_kpis
disruption_events
weather_network_features
ml_disruption_features
```

Possible future ML features include:

```text
line_id
hour
day_of_week
is_weekend
is_bank_holiday
recent_disruption_rate
temperature_c
precipitation_mm
relative_humidity_pct
wind_speed_kmh
wind_gusts_kmh
```

Any future tables should continue to define an explicit grain before implementation.


# Summary

The UrbanPulse Gold model separates:

```text
Historical analytical records
from
current application-serving datasets
```

The dimensional layer provides historical correctness.

The fact layer preserves operational observations.

The serving layer provides compact consumer contracts.

This structure allows the same platform to support:

* current operational dashboards
* historical analysis
* external applications
* future machine learning
* future reporting tools

