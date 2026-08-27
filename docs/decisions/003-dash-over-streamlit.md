# ADR 003: Use Dash Instead of Streamlit

## Status

Accepted

## Decision

UrbanPulse uses Dash with Dash Bootstrap Components and Plotly for the application frontend.

Streamlit was used initially, then replaced.

 

## Rationale

The project needed stronger control over:

- responsive layout
- navigation
- Bootstrap components
- reusable UI structure
- callbacks
- tables
- badges and status pills
- chart layout
- mobile behavior
- future dark mode

Dash provides more flexibility for this application design.

 

## Benefits

The change enables:

- multi-page navigation
- responsive Bootstrap grids
- reusable components
- richer callback logic
- greater CSS control
- consistent visual hierarchy
- easier future theming

 

## Consequences

Dash requires more explicit application code than Streamlit.

Layout, callbacks, state, and styling must be managed deliberately.

This additional complexity is acceptable because UrbanPulse is intended to demonstrate application engineering as well as data engineering.

 

## Deployment

The same Dash codebase is used for:

```text
Databricks Apps
Plotly Cloud
````

This also demonstrates portability across hosting environments.

 

## Guiding Rule

Use Dash for presentation and interaction only.

Business logic and analytical calculations should remain in the Gold data layer wherever practical.
