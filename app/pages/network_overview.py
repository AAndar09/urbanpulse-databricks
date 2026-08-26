import pandas as pd
import plotly.express as px

import dash
import dash_bootstrap_components as dbc

from dash import (
    dcc,
    html,
)

from components.disruptions import (
    build_reason_content,
)

from components.formatting import (
    format_date,
    format_eta,
    format_timestamp,
)

from components.layout import (
    build_kpi_card,
    build_page_header,
    build_section_title,
)

from components.status import (
    get_service_style,
)

from services.queries import (
    get_current_line_status,
    get_latest_arrival_kpis,
    get_latest_weather_kpis,
    get_network_summary,
    get_recent_network_trends,
)


dash.register_page(
    __name__,
    path="/",
    name="Network Overview",
)


# =========================================================
# Helpers
# =========================================================

def get_value(
    dataframe,
    column,
    default=None,
):
    if dataframe.empty:
        return default

    value = dataframe.iloc[0][
        column
    ]

    if pd.isna(value):
        return default

    return value


def style_figure(
    figure,
    y_title,
):
    figure.update_layout(
        template="plotly_white",
        height=300,
        autosize=False,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
        showlegend=False,
        hovermode="x unified",
        xaxis_title=None,
        yaxis_title=y_title,
    )

    return figure


# =========================================================
# Page
# =========================================================

def build_layout():
    try:
        # -------------------------------------------------
        # Load Gold serving data
        # -------------------------------------------------

        network_df = (
            get_network_summary()
        )

        arrival_df = (
            get_latest_arrival_kpis()
        )

        weather_df = (
            get_latest_weather_kpis()
        )

        status_df = (
            get_current_line_status()
        )

        trends_df = (
            get_recent_network_trends()
        )


        # =================================================
        # Network KPI values
        # =================================================

        total_lines = int(
            get_value(
                network_df,
                "total_lines",
                0,
            )
        )

        good_lines = int(
            get_value(
                network_df,
                "good_service_lines",
                0,
            )
        )

        disrupted_lines = int(
            get_value(
                network_df,
                "disrupted_lines",
                0,
            )
        )

        good_pct = float(
            get_value(
                network_df,
                "good_service_pct",
                0,
            )
        )


        # =================================================
        # Operational activity values
        # =================================================

        arrival_observations = int(
            get_value(
                arrival_df,
                "arrival_observations",
                0,
            )
        )

        stations_observed = int(
            get_value(
                arrival_df,
                "stations_observed",
                0,
            )
        )

        avg_eta = get_value(
            arrival_df,
            "avg_eta_seconds",
        )

        temperature = get_value(
            weather_df,
            "avg_temperature_c",
        )


        # =================================================
        # Current disruptions
        # =================================================

        disruption_rows = []

        if not status_df.empty:
            disrupted_df = (
                status_df[
                    status_df[
                        "is_disrupted"
                    ] == True
                ]
                .sort_values(
                    "line_name"
                )
            )

            for _, row in (
                disrupted_df.iterrows()
            ):
                service = (
                    get_service_style(
                        row[
                            "status_severity"
                        ],
                        row[
                            "status_description"
                        ],
                    )
                )

                disruption_rows.append(
                    html.Tr(
                        [
                            html.Td(
                                html.Strong(
                                    row[
                                        "line_name"
                                    ]
                                ),
                                className=(
                                    "disruption-line-cell"
                                ),
                            ),

                            html.Td(
                                row[
                                    "status_description"
                                ],
                                className=(
                                    "disruption-status-cell"
                                ),
                            ),

                            html.Td(
                                dbc.Badge(
                                    service[
                                        "label"
                                    ],
                                    color=service[
                                        "color"
                                    ],
                                    pill=True,
                                    className=(
                                        "status-badge"
                                    ),
                                )
                            ),

                            html.Td(
                                build_reason_content(
                                    row[
                                        "status_reason"
                                    ],
                                    row[
                                        "line_name"
                                    ],
                                    expandable=True,
                                ),
                                className=(
                                    "reason-cell"
                                ),
                            ),
                        ]
                    )
                )


        # =================================================
        # Recent trend charts
        # =================================================

        chart_content = dbc.Alert(
            "No recent trend data available.",
            color="secondary",
        )

        if not trends_df.empty:
            trends_df = (
                trends_df.copy()
            )

            trends_df[
                "calendar_date"
            ] = pd.to_datetime(
                trends_df[
                    "calendar_date"
                ]
            )

            trends_df = (
                trends_df.sort_values(
                    "calendar_date"
                )
            )


            # ---------------------------------------------
            # Disruption rate
            # ---------------------------------------------

            disruption_chart_df = (
                trends_df[
                    [
                        "calendar_date",
                        "disruption_rate_pct",
                    ]
                ]
                .dropna()
            )

            disruption_figure = (
                px.line(
                    disruption_chart_df,
                    x="calendar_date",
                    y=(
                        "disruption_rate_pct"
                    ),
                    markers=True,
                )
            )

            style_figure(
                disruption_figure,
                "Disruption %",
            )


            # ---------------------------------------------
            # Arrival activity
            # ---------------------------------------------

            arrival_chart_df = (
                trends_df[
                    [
                        "calendar_date",
                        "arrival_observations",
                    ]
                ]
                .dropna()
            )

            arrival_figure = (
                px.bar(
                    arrival_chart_df,
                    x="calendar_date",
                    y=(
                        "arrival_observations"
                    ),
                )
            )

            style_figure(
                arrival_figure,
                "Observations",
            )


            chart_content = dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        (
                                            "Disruption "
                                            "Rate"
                                        ),
                                        className=(
                                            "card-title"
                                        ),
                                    ),

                                    dcc.Graph(
                                        figure=(
                                            disruption_figure
                                        ),
                                        config={
                                            "displayModeBar":
                                                False,
                                            "responsive":
                                                False,
                                        },
                                        responsive=False,
                                        style={
                                            "height":
                                                "300px",
                                            "width":
                                                "100%",
                                        },
                                    ),
                                ]
                            ),
                            className=(
                                "content-card "
                                "h-100"
                            ),
                        ),
                        xs=12,
                        lg=6,
                    ),

                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        (
                                            "Arrival "
                                            "Activity"
                                        ),
                                        className=(
                                            "card-title"
                                        ),
                                    ),

                                    dcc.Graph(
                                        figure=(
                                            arrival_figure
                                        ),
                                        config={
                                            "displayModeBar":
                                                False,
                                            "responsive":
                                                False,
                                        },
                                        responsive=False,
                                        style={
                                            "height":
                                                "300px",
                                            "width":
                                                "100%",
                                        },
                                    ),
                                ]
                            ),
                            className=(
                                "content-card "
                                "h-100"
                            ),
                        ),
                        xs=12,
                        lg=6,
                    ),
                ],
                className="g-3",
            )


        # =================================================
        # Data freshness
        # =================================================

        latest_line_update = (
            status_df[
                "status_snapshot_at_local"
            ].max()
            if not status_df.empty
            else None
        )

        arrival_date = get_value(
            arrival_df,
            "calendar_date",
        )

        weather_date = get_value(
            weather_df,
            "calendar_date",
        )


        # =================================================
        # Final layout
        # =================================================

        return html.Main(
            [
                # -----------------------------------------
                # Header
                # -----------------------------------------

                build_page_header(
                    "Live Network",
                    "Network Overview",
                    (
                        "Operational intelligence "
                        "for the London Underground "
                        "network."
                    ),
                ),


                # =========================================
                # Network Health
                # =========================================

                build_section_title(
                    "Network Health",
                    (
                        "Latest operational state "
                        "across monitored Tube lines."
                    ),
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            build_kpi_card(
                                "Tube Lines",
                                total_lines,
                                "Lines monitored",
                                "primary",
                            ),
                            xs=12,
                            sm=6,
                            lg=3,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Good Service",
                                good_lines,
                                (
                                    "Operating "
                                    "normally"
                                ),
                                "success",
                            ),
                            xs=12,
                            sm=6,
                            lg=3,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Disrupted",
                                disrupted_lines,
                                (
                                    "Require "
                                    "attention"
                                ),
                                "danger",
                            ),
                            xs=12,
                            sm=6,
                            lg=3,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Network Health",
                                (
                                    f"{good_pct:.1f}%"
                                ),
                                "Good service",
                                "info",
                            ),
                            xs=12,
                            sm=6,
                            lg=3,
                        ),
                    ],
                    className="g-3",
                ),


                # =========================================
                # Operational Activity
                # =========================================

                build_section_title(
                    "Operational Activity",
                    (
                        "Latest monitored arrivals "
                        "and weather context."
                    ),
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            build_kpi_card(
                                (
                                    "Arrival "
                                    "Observations"
                                ),
                                (
                                    f"{arrival_observations:,}"
                                ),
                                (
                                    "Predictions "
                                    "captured"
                                ),
                                "primary",
                            ),
                            xs=12,
                            sm=6,
                            lg=3,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                (
                                    "Stations "
                                    "Observed"
                                ),
                                stations_observed,
                                (
                                    "Stations "
                                    "represented"
                                ),
                                "primary",
                            ),
                            xs=12,
                            sm=6,
                            lg=3,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Average ETA",
                                format_eta(
                                    avg_eta
                                ),
                                (
                                    "Predicted "
                                    "wait"
                                ),
                                "warning",
                            ),
                            xs=12,
                            sm=6,
                            lg=3,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Temperature",
                                (
                                    f"{float(temperature):.1f} °C"
                                    if temperature
                                    is not None
                                    else "No data"
                                ),
                                (
                                    "Weather "
                                    "context"
                                ),
                                "info",
                            ),
                            xs=12,
                            sm=6,
                            lg=3,
                        ),
                    ],
                    className="g-3",
                ),


                # =========================================
                # Current Disruptions
                # =========================================

                build_section_title(
                    "Current Disruptions",
                    (
                        "Lines currently requiring "
                        "operational attention."
                    ),
                ),

                (
                    dbc.Card(
                        dbc.CardBody(
                            dbc.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th(
                                                    "Line"
                                                ),

                                                html.Th(
                                                    "Status"
                                                ),

                                                html.Th(
                                                    (
                                                        "Service "
                                                        "State"
                                                    )
                                                ),

                                                html.Th(
                                                    (
                                                        "Service "
                                                        "Impact"
                                                    )
                                                ),
                                            ]
                                        )
                                    ),

                                    html.Tbody(
                                        disruption_rows
                                    ),
                                ],
                                hover=True,
                                responsive=True,
                                borderless=True,
                                className=(
                                    "mb-0 "
                                    "disruption-table"
                                ),
                            )
                        ),
                        className=(
                            "content-card"
                        ),
                    )

                    if disruption_rows

                    else dbc.Alert(
                        (
                            "All monitored Tube "
                            "lines are currently "
                            "healthy."
                        ),
                        color="success",
                        className="mb-0",
                    )
                ),


                # =========================================
                # Recent Trends
                # =========================================

                build_section_title(
                    "Recent Trends",
                    (
                        "Recent disruption and "
                        "arrival activity."
                    ),
                ),

                chart_content,


                # =========================================
                # Data Freshness
                # =========================================

                build_section_title(
                    "Data Freshness",
                    (
                        "Latest data represented "
                        "by the dashboard."
                    ),
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            build_kpi_card(
                                "Line Status",
                                format_timestamp(
                                    latest_line_update
                                ),
                                "Latest snapshot",
                                "primary",
                            ),
                            xs=12,
                            md=6,
                            lg=4,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Arrival Data",
                                format_date(
                                    arrival_date
                                ),
                                (
                                    "Latest "
                                    "arrival date"
                                ),
                                "primary",
                            ),
                            xs=12,
                            md=6,
                            lg=4,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Weather Data",
                                format_date(
                                    weather_date
                                ),
                                (
                                    "Latest "
                                    "weather date"
                                ),
                                "primary",
                            ),
                            xs=12,
                            md=6,
                            lg=4,
                        ),
                    ],
                    className="g-3",
                ),
            ],
            className="page-container",
        )


    except Exception as exc:
        return dbc.Container(
            dbc.Alert(
                [
                    html.H4(
                        (
                            "Unable to load "
                            "Network Overview"
                        ),
                        className=(
                            "alert-heading"
                        ),
                    ),

                    html.P(
                        str(exc)
                    ),
                ],
                color="danger",
            ),
            className="py-5",
        )


layout = build_layout