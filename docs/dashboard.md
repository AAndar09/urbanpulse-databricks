# UrbanPulse Dashboard

## Overview

UrbanPulse uses Dash, Dash Bootstrap Components, Plotly, and Databricks SQL.

The frontend reads only from Gold serving tables.

```text
Dash
↓
Query Service
↓
Databricks SQL
↓
Gold Serving Tables
````

 

## Current Pages

### Network Overview

Provides:

* network health KPIs
* operational activity KPIs
* current disruptions
* recent trend charts
* data freshness indicators

Primary source:

```text
workspace.urbanpulse_gold.current_line_status
workspace.urbanpulse_gold.daily_network_kpis
```

 

### Line Status

Displays:

* Tube line
* TfL status
* normalized service state
* disruption reason
* latest update time

Service states are simplified into:

```text
Healthy
Degraded
Disrupted
Unknown
```

 

### Station Arrivals

Provides:

* station filter
* Tube line filter
* arrival observation count
* distinct vehicles
* average ETA
* next expected arrival
* arrival activity chart
* detailed station-line metrics

Primary source:

```text
workspace.urbanpulse_gold.station_arrival_summary
```

 

## Application Structure

```text
app/
├── app.py
├── assets/
│   └── urbanpulse.css
├── components/
├── pages/
└── services/
```

Responsibilities:

```text
pages/
Page-specific layouts and callbacks

components/
Reusable UI and formatting

services/
SQL connectivity and queries

assets/
Application styling
```

 

## Responsive Design

The dashboard uses Bootstrap breakpoints.

Typical KPI layout:

```text
Phone     1 card per row
Tablet    2 cards per row
Desktop   4 cards per row
```

Large tables remain horizontally scrollable on small screens rather than compressing columns into unreadable layouts.

 

## Plotly Charts

Charts use explicit heights to avoid resize loops observed during development.

The application therefore avoids relying on uncontrolled Plotly auto-resizing.

 

## Presentation Principles

UrbanPulse keeps analytical and presentation logic separate.

```text
Gold
Business logic and metrics

Dash
Filtering, formatting, interaction and presentation
```

Raw TfL disruption descriptions are formatted for readability without altering their operational meaning.

 

## Planned Pages

### Network Trends

Planned features:

* date filtering
* disruption trends
* arrival trends
* ETA trends
* weather comparisons
* weekday and bank-holiday analysis

### Data Freshness

Planned features:

* latest source timestamps
* serving refresh status
* Gold validation results
* platform health indicators

 

## Future UI Work

Planned improvements include:

* complete mobile optimization
* night-mode toggle
* Plotly dark-theme support
* accessibility review
* loading and error-state refinement
* lightweight caching

 

## Design Principle

The dashboard should remain a thin consumer of the data platform.

It should not recreate transformations already implemented in Gold.
