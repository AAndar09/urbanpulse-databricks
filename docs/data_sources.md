# UrbanPulse Data Sources

## Overview

UrbanPulse combines public transport, weather, and calendar data to support operational monitoring and historical analysis of the London Underground.

Current providers:

| Provider | Dataset | Purpose |
|---|---|---|
| Transport for London | Tube line status | Current and historical service conditions |
| Transport for London | Tube stop points | Station metadata and station-line relationships |
| Transport for London | Arrivals | Vehicle arrival predictions for monitored stations |
| Open-Meteo | Weather | London weather context |
| GOV.UK | Bank holidays | Calendar enrichment |

Source configuration is maintained in:

```text
conf/sources.yml
````

The monitored station list is maintained in:

```text
conf/monitored_stations.yml
```



# Transport for London

Transport for London provides the main operational datasets used by UrbanPulse.

Base API:

```text
https://api.tfl.gov.uk
```

UrbanPulse currently uses three TfL endpoint groups:

```text
Line status
Stop points
Arrivals
```



# TfL Line Status

## Endpoint

```text
/Line/Mode/tube/Status
```

## Purpose

This endpoint provides the current operational status of London Underground lines.

UrbanPulse uses it to capture:

* line identifiers
* line names
* mode
* status severity
* status descriptions
* disruption reasons
* status timestamps

The data supports both current-state reporting and historical status analysis.



## Example Analytical Use

A single API response may indicate:

```text
Central
Good Service

Piccadilly
Minor Delays
```

UrbanPulse stores each polling snapshot.

This means a later snapshot such as:

```text
Piccadilly
Good Service
```

does not overwrite the earlier disruption observation.

Both remain available for historical analysis.

 

## Bronze Destination

```text
workspace.urbanpulse_bronze.tfl_line_status
```

## Silver Destination

```text
workspace.urbanpulse_silver.tfl_line_status
```

## Gold Consumers

```text
workspace.urbanpulse_gold.dim_line
workspace.urbanpulse_gold.fact_line_status
workspace.urbanpulse_gold.current_line_status
workspace.urbanpulse_gold.daily_network_kpis
```

 

# TfL Stop Points

## Endpoint

```text
/StopPoint/Mode/tube
```

## Purpose

The stop-point dataset provides:

* station identifiers
* stop-point identifiers
* station names
* coordinates
* transport modes
* line relationships
* station hierarchy information

It is used primarily to build station reference data.

 

# TfL Station Identity

TfL exposes several identifiers associated with stations and stop areas.

UrbanPulse standardizes Gold station identity using:

```text
station_naptan
```

This becomes:

```text
station_id
```

in the Gold model.

The station dimension therefore avoids relying on temporary display labels or platform-level identifiers as the main business key.

 

# Canonical Station Resolution

Configured station names are resolved against TfL stop-point data before arrivals are requested.

The preferred station record is one where:

```text
stop_point_id == station_naptan
```

where available.

If a direct canonical record is not available, UrbanPulse uses a deterministic representative stop point.

This ensures downstream arrival ingestion uses consistent station identifiers.

 

# Stop-Point Relationships

TfL stop-point data contains relationships between stations and transport lines.

These relationships can include:

* Underground lines
* buses
* night buses
* other route types

UrbanPulse therefore uses two stages.

## Silver

Silver preserves the broader source relationships.

Table:

```text
workspace.urbanpulse_silver.tfl_stop_point_lines
```

## Gold

Gold restricts the station-line bridge to Tube lines represented in the current line dimension.

Table:

```text
workspace.urbanpulse_gold.bridge_station_line
```

This keeps Silver source-faithful while keeping Gold aligned with the project's analytical scope.

 

## Bronze Destination

```text
workspace.urbanpulse_bronze.tfl_stop_points
```

## Silver Destinations

```text
workspace.urbanpulse_silver.tfl_stop_points
workspace.urbanpulse_silver.tfl_stop_point_lines
```

## Gold Consumers

```text
workspace.urbanpulse_gold.dim_station
workspace.urbanpulse_gold.bridge_station_line
```

 

# TfL Arrivals

## Endpoint

```text
/StopPoint/{station_id}/Arrivals
```

The `{station_id}` placeholder is replaced with the canonical TfL station identifier resolved from stop-point data.

 

## Purpose

The arrivals endpoint provides operational vehicle prediction data.

Representative fields include:

```text
arrival ID
vehicle ID
station
line
platform
direction
destination
prediction timestamp
expected arrival
time to station
current location
towards
```

This source supports station-level operational analysis.

 

# Monitored Stations

UrbanPulse currently monitors ten major London Underground stations.

```text
Baker Street
Bank
Green Park
King's Cross St. Pancras
Liverpool Street
London Bridge
Oxford Circus
Paddington
Victoria
Waterloo
```

The monitored list is configuration-driven.

File:

```text
conf/monitored_stations.yml
```

The application is therefore not dependent on these stations being hardcoded throughout the transformation logic.

 

# Arrival API Pattern

UrbanPulse resolves each configured station to a canonical TfL identifier.

It then makes one arrivals request per monitored station.

With ten monitored stations, a complete operational arrivals ingestion run currently makes:

```text
10 TfL arrival API requests
```

Each request receives its own ingestion metadata and request identifier.

 

# Valid Empty Responses

A TfL arrival request can successfully return:

```json
[]
```

This is a valid source response.

It means:

```text
No arrival predictions are currently available
```

It does not necessarily mean:

```text
The API request failed
```

UrbanPulse therefore treats an empty list as a successful response with zero observations.

 

# Silver Explosion Behavior

Arrival payloads contain arrays of prediction records.

Silver uses:

```text
explode
```

rather than:

```text
explode_outer
```

for these arrays.

This matters because an empty array should produce:

```text
0 arrival rows
```

not:

```text
1 synthetic row containing null arrival fields
```

 

# Repeated Arrival Predictions

UrbanPulse deliberately preserves repeated observations.

Example:

```text
14:00
Vehicle A
ETA = 360 seconds
```

Later:

```text
14:05
Vehicle A
ETA = 60 seconds
```

These are not duplicates.

They represent two observations of the same vehicle prediction at different times.

This history can later support:

* ETA reliability analysis
* prediction stability analysis
* station activity analysis
* machine learning features

 

# Arrival Observation Key

Silver and Gold use a deterministic observation key.

The key is generated using SHA256 and combines source-level identifying information so repeated pipeline execution does not duplicate the same observation.

This supports idempotent processing.

 

## Bronze Destination

```text
workspace.urbanpulse_bronze.tfl_arrivals
```

## Silver Destination

```text
workspace.urbanpulse_silver.tfl_arrivals
```

## Gold Consumers

```text
workspace.urbanpulse_gold.fact_arrival_observation
workspace.urbanpulse_gold.station_arrival_summary
workspace.urbanpulse_gold.daily_network_kpis
```

 

# Open-Meteo

UrbanPulse uses Open-Meteo for London weather data.

Base API:

```text
https://api.open-meteo.com/v1
```

Current source configuration uses London coordinates:

```text
Latitude: 51.5074
Longitude: -0.1278
Timezone: Europe/London
```

 

# Weather Purpose

Weather data provides context for transport operations.

Current fields include:

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

These fields can later support analysis such as:

```text
disruption activity by rainfall
disruption activity by temperature
ETA patterns by weather conditions
wind conditions versus operational performance
```

These relationships should be interpreted descriptively unless a formal causal methodology is introduced.

 

# Weather Variables

Configured current variables include:

```text
temperature_2m
relative_humidity_2m
precipitation
rain
weather_code
cloud_cover
wind_speed_10m
wind_gusts_10m
```

Units are configured as:

```text
temperature: Celsius
wind speed: km/h
precipitation: mm
```

 

# Weather Time Handling

Open-Meteo provides local weather timestamps according to the configured timezone.

UrbanPulse retains both:

```text
weather_observed_at
weather_observed_at_local
```

UTC is used for analytical consistency.

Europe/London is used for display and calendar analysis.

 

# Weather Observation Key

Each weather observation receives a deterministic observation key.

This allows repeated pipeline execution without creating duplicate analytical observations.

 

## Bronze Destination

```text
workspace.urbanpulse_bronze.weather
```

## Silver Destination

```text
workspace.urbanpulse_silver.weather
```

## Gold Consumers

```text
workspace.urbanpulse_gold.fact_weather
workspace.urbanpulse_gold.daily_network_kpis
```

 

# GOV.UK Bank Holidays

UrbanPulse uses the GOV.UK bank holiday dataset.

Endpoint:

```text
https://www.gov.uk/bank-holidays.json
```

Region:

```text
england-and-wales
```

 

# Bank Holiday Purpose

The source enriches the date dimension.

This allows analysis by:

```text
ordinary weekday
weekend
bank holiday
```

Representative fields include:

```text
holiday name
holiday date
notes
bunting indicator
division
```

 

# Date Range Impact

During implementation, the source data revealed bank holiday records beginning in 2019.

The original UrbanPulse date dimension started in 2020.

Gold validation correctly identified that some valid source holiday dates fell outside the configured date range.

The date dimension was therefore changed to:

```text
2019-01-01
to
2035-12-31
```

This is an example of data-quality checks influencing model design.

 

## Bronze Destination

```text
workspace.urbanpulse_bronze.bank_holidays
```

## Silver Destination

```text
workspace.urbanpulse_silver.bank_holidays
```

## Gold Consumer

```text
workspace.urbanpulse_gold.dim_date
```

 

# Source Configuration

Source configuration is stored in:

```text
conf/sources.yml
```

This separates:

```text
URLs
parameters
locations
source settings
```

from Python transformation logic.

Representative structure:

```yaml
tfl:
  base_url: "https://api.tfl.gov.uk"

  line_status:
    endpoint: "/Line/Mode/tube/Status"

  stop_points:
    endpoint: "/StopPoint/Mode/tube"

  arrivals:
    endpoint: "/StopPoint/{station_id}/Arrivals"

open_meteo:
  base_url: "https://api.open-meteo.com/v1"

  weather:
    endpoint: "/forecast"
    latitude: 51.5074
    longitude: -0.1278
    timezone: "Europe/London"

gov_uk:
  bank_holidays:
    url: "https://www.gov.uk/bank-holidays.json"
    region: "england-and-wales"
```

The configuration file remains the implementation source of truth.

Documentation should not duplicate every individual setting unless it is important to understand the design.

 

# Source Refresh Cadence

The current automated source cadence is:

| Source               | Automated Cadence |
| -------------------- | ----------------- |
| TfL line status      | Every 15 minutes  |
| TfL arrivals         | Every 15 minutes  |
| Open-Meteo weather   | Hourly            |
| TfL stop points      | Daily             |
| GOV.UK bank holidays | Daily             |

The actual scheduling is managed through Databricks Lakeflow Jobs.

Detailed orchestration is documented in:

```text
docs/automation.md
```

 

# HTTP Reliability

UrbanPulse uses a reusable API client.

The client provides:

* persistent HTTP sessions
* connection reuse
* request timeouts
* retries
* handling for transient HTTP failures

Retryable response codes include:

```text
429
500
502
503
504
```

Lakeflow Jobs also provides task-level retry protection for ingestion tasks.

This creates two layers of resilience:

```text
HTTP client retry
        +
Lakeflow task retry
```

 

# Raw Source Preservation

Every ingestion flow preserves the original response before transformation.

This means UrbanPulse keeps both:

```text
raw JSON file
and
Bronze Delta record
```

The raw landing copy supports:

* debugging
* replay
* source comparison
* auditability

 

# Request Metadata

Each ingestion request receives metadata such as:

```text
request_id
source
dataset
endpoint
HTTP status
ingestion timestamp
ingestion date
```

This makes individual API interactions traceable through the pipeline.

 

# Source Scope

UrbanPulse deliberately does not attempt to model all TfL data.

Current analytical scope is:

```text
London Underground Tube operations
```

This is important because TfL contains substantially broader data covering:

* buses
* roads
* cycling
* river services
* other rail modes
* disruptions across many transport networks

UrbanPulse preserves relevant source richness where useful but applies a clear Tube-focused analytical boundary in Gold.

 

# Future Data Sources

Potential future additions include:

```text
TfL disruption history
TfL Journey Planner
TfL occupancy data
TfL accessibility data
London events
public footfall datasets
air-quality data
additional weather history
planned engineering works
```

Any new source should follow the same ingestion pattern:

```text
API
    ↓
Raw landing
    ↓
Bronze
    ↓
Silver
    ↓
Gold model
    ↓
Validation
```

 

# Source Selection Principles

New UrbanPulse sources should preferably be:

* publicly accessible
* free or suitable for portfolio use
* documented
* stable enough for scheduled ingestion
* analytically relevant
* legally appropriate to consume
* capable of being modeled with explicit timestamps and identifiers

Sources should not be added merely to increase dataset count.

Each source should support a clear analytical or operational question.



# Summary

UrbanPulse currently integrates:

```text
Transport for London
    ↓
network operations

Open-Meteo
    ↓
weather context

GOV.UK
    ↓
calendar context
```

Together, these sources support a broader model of London Underground operations while keeping the architecture modular.

The source layer is intentionally separated from downstream business modeling so additional datasets can be introduced without redesigning the entire platform.

