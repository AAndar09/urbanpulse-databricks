import pandas as pd
import plotly.express as px

import dash
import dash_bootstrap_components as dbc

from dash import (
    dcc,
    html,
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
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
        height=300,
        showlegend=False,
        hovermode="x unified",
        xaxis_title=None,
        yaxis_title=y_title,
    )

    return figure


def build_layout():
    try:
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


        # ---------------------------------
        # KPIs
        # ---------------------------------

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


        # ---------------------------------
        # Current disruptions
        # ---------------------------------

        disruption_cards = []

        if not status_df.empty:
            disrupted_df = status_df[
                status_df[
                    "is_disrupted"
                ] == True
            ]

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

                reason = (
                    row["status_reason"]
                )

                if pd.isna(reason):
                    reason = (
                        "No additional "
                        "information provided."
                    )

                disruption_cards.append(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Strong(
                                            row[
                                                "line_name"
                                            ],
                                            className=(
                                                "me-2"
                                            ),
                                        ),

                                        dbc.Badge(
                                            service[
                                                "label"
                                            ],
                                            color=service[
                                                "color"
                                            ],
                                            pill=True,
                                        ),
                                    ],
                                    className=(
                                        "d-flex "
                                        "justify-content-"
                                        "between "
                                        "align-items-center"
                                    ),
                                ),

                                html.Div(
                                    row[
                                        "status_description"
                                    ],
                                    className=(
                                        "fw-semibold mt-3"
                                    ),
                                ),

                                html.Div(
                                    reason,
                                    className=(
                                        "text-secondary "
                                        "small mt-1"
                                    ),
                                ),
                            ]
                        ),
                        className=(
                            "content-card mb-3"
                        ),
                    )
                )

        if not disruption_cards:
            disruption_cards = [
                dbc.Alert(
                    "All monitored Tube lines "
                    "are currently healthy.",
                    color="success",
                    className="mb-0",
                )
            ]


        # ---------------------------------
        # Trend charts
        # ---------------------------------

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

            trends_df = trends_df.sort_values(
                "calendar_date"
            )


            disruption_chart_df = (
                trends_df[
                    [
                        "calendar_date",
                        "disruption_rate_pct",
                    ]
                ]
                .dropna()
            )

            arrival_chart_df = (
                trends_df[
                    [
                        "calendar_date",
                        "arrival_observations",
                    ]
                ]
                .dropna()
            )


            disruption_figure = px.line(
                disruption_chart_df,
                x="calendar_date",
                y="disruption_rate_pct",
                markers=True,
            )

            style_figure(
                disruption_figure,
                "Disruption %",
            )


            arrival_figure = px.bar(
                arrival_chart_df,
                x="calendar_date",
                y="arrival_observations",
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
                                        "Disruption Rate",
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
                                                False
                                        },
                                    ),
                                ]
                            ),
                            className=(
                                "content-card h-100"
                            ),
                        ),
                        lg=6,
                    ),

                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        "Arrival Activity",
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
                                                False
                                        },
                                    ),
                                ]
                            ),
                            className=(
                                "content-card h-100"
                            ),
                        ),
                        lg=6,
                    ),
                ],
                className="g-3",
            )


        # ---------------------------------
        # Freshness
        # ---------------------------------

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


        return html.Main(
            [
                build_page_header(
                    "Live Network",
                    "Network Overview",
                    (
                        "Operational intelligence "
                        "for the London Underground "
                        "network."
                    ),
                ),


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
                            lg=3,
                            md=6,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Good Service",
                                good_lines,
                                "Operating normally",
                                "success",
                            ),
                            lg=3,
                            md=6,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Disrupted",
                                disrupted_lines,
                                "Require attention",
                                "danger",
                            ),
                            lg=3,
                            md=6,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Network Health",
                                f"{good_pct:.1f}%",
                                "Good service",
                                "info",
                            ),
                            lg=3,
                            md=6,
                        ),
                    ],
                    className="g-3",
                ),


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
                                "Arrival Observations",
                                (
                                    f"{arrival_observations:,}"
                                ),
                                "Predictions captured",
                                "primary",
                            ),
                            lg=3,
                            md=6,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Stations Observed",
                                stations_observed,
                                "Stations represented",
                                "primary",
                            ),
                            lg=3,
                            md=6,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Average ETA",
                                format_eta(
                                    avg_eta
                                ),
                                "Predicted wait",
                                "warning",
                            ),
                            lg=3,
                            md=6,
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
                                "Weather context",
                                "info",
                            ),
                            lg=3,
                            md=6,
                        ),
                    ],
                    className="g-3",
                ),


                build_section_title(
                    "Current Disruptions",
                    (
                        "Lines currently requiring "
                        "operational attention."
                    ),
                ),

                html.Div(
                    disruption_cards
                ),


                build_section_title(
                    "Recent Trends",
                    (
                        "Recent disruption and "
                        "arrival activity."
                    ),
                ),

                chart_content,


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
                            lg=4,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Arrival Data",
                                format_date(
                                    arrival_date
                                ),
                                "Latest arrival date",
                                "primary",
                            ),
                            lg=4,
                        ),

                        dbc.Col(
                            build_kpi_card(
                                "Weather Data",
                                format_date(
                                    weather_date
                                ),
                                "Latest weather date",
                                "primary",
                            ),
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
                        "Unable to load "
                        "Network Overview",
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