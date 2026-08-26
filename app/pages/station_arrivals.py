import pandas as pd
import plotly.express as px

import dash
import dash_bootstrap_components as dbc

from dash import (
    Input,
    Output,
    callback,
    dcc,
    html,
)

from components.formatting import (
    format_eta,
    format_timestamp,
)

from components.layout import (
    build_kpi_card,
    build_page_header,
    build_section_title,
)

from services.queries import (
    get_station_arrival_summary,
)


dash.register_page(
    __name__,
    path="/station-arrivals",
    name="Station Arrivals",
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def serialise_dataframe(dataframe):
    result = dataframe.copy()

    timestamp_columns = [
        "next_expected_arrival_utc",
        "next_expected_arrival_local",
        "latest_prediction_timestamp_utc",
        "latest_prediction_timestamp_local",
        "serving_updated_at",
    ]

    for column in timestamp_columns:
        if column not in result.columns:
            continue

        result[column] = result[column].apply(
            lambda value: (
                None
                if pd.isna(value)
                else pd.to_datetime(value).isoformat()
            )
        )

    return result.to_dict(
        orient="records"
    )


def weighted_average_eta(dataframe):
    if dataframe.empty:
        return None

    valid_df = dataframe[
        dataframe[
            "avg_eta_seconds"
        ].notna()
        &
        (
            dataframe[
                "arrival_observations"
            ] > 0
        )
    ]

    if valid_df.empty:
        return None

    weight_total = valid_df[
        "arrival_observations"
    ].sum()

    if weight_total == 0:
        return None

    weighted_total = (
        valid_df[
            "avg_eta_seconds"
        ]
        *
        valid_df[
            "arrival_observations"
        ]
    ).sum()

    return (
        weighted_total
        / weight_total
    )


def get_next_arrival(dataframe):
    if dataframe.empty:
        return None

    timestamps = pd.to_datetime(
        dataframe[
            "next_expected_arrival_local"
        ],
        errors="coerce",
    )

    timestamps = timestamps.dropna()

    if timestamps.empty:
        return None

    return timestamps.min()


def get_latest_prediction(dataframe):
    if dataframe.empty:
        return None

    timestamps = pd.to_datetime(
        dataframe[
            "latest_prediction_timestamp_local"
        ],
        errors="coerce",
    )

    timestamps = timestamps.dropna()

    if timestamps.empty:
        return None

    return timestamps.max()


def style_figure(figure):
    figure.update_layout(
        template="plotly_white",
        height=320,
        autosize=False,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
        xaxis_title=None,
        yaxis_title="Arrival Observations",
        legend_title_text="Line",
        hovermode="x unified",
    )

    return figure


# ---------------------------------------------------------
# Initial data
# ---------------------------------------------------------

def build_layout():
    try:
        arrivals_df = (
            get_station_arrival_summary()
        )

        if arrivals_df.empty:
            return html.Main(
                [
                    build_page_header(
                        "Operations",
                        "Station Arrivals",
                        (
                            "Arrival activity and ETA "
                            "intelligence across monitored "
                            "Tube stations."
                        ),
                    ),

                    dbc.Alert(
                        "No station arrival data is available.",
                        color="warning",
                    ),
                ],
                className="page-container",
            )


        station_options = [
            {
                "label": name,
                "value": station_id,
            }
            for station_id, name in (
                arrivals_df[
                    [
                        "station_id",
                        "station_name",
                    ]
                ]
                .drop_duplicates()
                .sort_values(
                    "station_name"
                )
                .itertuples(
                    index=False,
                    name=None,
                )
            )
        ]


        line_options = [
            {
                "label": name,
                "value": line_id,
            }
            for line_id, name in (
                arrivals_df[
                    [
                        "line_id",
                        "line_name",
                    ]
                ]
                .drop_duplicates()
                .sort_values(
                    "line_name"
                )
                .itertuples(
                    index=False,
                    name=None,
                )
            )
        ]


        return html.Main(
            [
                dcc.Store(
                    id="station-arrivals-data",
                    data=serialise_dataframe(
                        arrivals_df
                    ),
                ),


                build_page_header(
                    "Operations",
                    "Station Arrivals",
                    (
                        "Arrival activity and ETA "
                        "intelligence across monitored "
                        "London Underground stations."
                    ),
                ),


                # -----------------------------------------
                # Filters
                # -----------------------------------------

                build_section_title(
                    "Explore Arrivals",
                    (
                        "Filter the latest serving data "
                        "by station or Tube line."
                    ),
                ),


                dbc.Card(
                    dbc.CardBody(
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Station",
                                            html_for=(
                                                "arrival-station-filter"
                                            ),
                                        ),

                                        dcc.Dropdown(
                                            id=(
                                                "arrival-station-filter"
                                            ),
                                            options=(
                                                station_options
                                            ),
                                            value=None,
                                            placeholder=(
                                                "All stations"
                                            ),
                                            clearable=True,
                                            persistence=True,
                                            persistence_type=(
                                                "session"
                                            ),
                                        ),
                                    ],
                                    lg=6,
                                ),

                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Tube Line",
                                            html_for=(
                                                "arrival-line-filter"
                                            ),
                                        ),

                                        dcc.Dropdown(
                                            id=(
                                                "arrival-line-filter"
                                            ),
                                            options=(
                                                line_options
                                            ),
                                            value=None,
                                            placeholder=(
                                                "All lines"
                                            ),
                                            clearable=True,
                                            persistence=True,
                                            persistence_type=(
                                                "session"
                                            ),
                                        ),
                                    ],
                                    lg=6,
                                ),
                            ],
                            className="g-3",
                        )
                    ),
                    className=(
                        "content-card filter-card"
                    ),
                ),


                # -----------------------------------------
                # Dynamic page content
                # -----------------------------------------

                dcc.Loading(
                    id="station-arrivals-loading",
                    type="circle",
                    children=html.Div(
                        id="station-arrivals-content"
                    ),
                ),
            ],
            className="page-container",
        )


    except Exception as exc:
        return dbc.Container(
            dbc.Alert(
                [
                    html.H4(
                        "Unable to load Station Arrivals",
                        className="alert-heading",
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


# ---------------------------------------------------------
# Interactive filtering
# ---------------------------------------------------------

@callback(
    Output(
        "station-arrivals-content",
        "children",
    ),
    Input(
        "arrival-station-filter",
        "value",
    ),
    Input(
        "arrival-line-filter",
        "value",
    ),
    Input(
        "station-arrivals-data",
        "data",
    ),
)
def update_station_arrivals(
    selected_station,
    selected_line,
    stored_data,
):
    if not stored_data:
        return dbc.Alert(
            "No station arrival data is available.",
            color="warning",
        )


    dataframe = pd.DataFrame(
        stored_data
    )


    # -----------------------------------------------------
    # Apply filters
    # -----------------------------------------------------

    if selected_station:
        dataframe = dataframe[
            dataframe[
                "station_id"
            ] == selected_station
        ]


    if selected_line:
        dataframe = dataframe[
            dataframe[
                "line_id"
            ] == selected_line
        ]


    if dataframe.empty:
        return html.Div(
            [
                build_section_title(
                    "Arrival Summary"
                ),

                html.Div(
                    [
                        html.Div(
                            "No matching arrivals",
                            className=(
                                "empty-state-title"
                            ),
                        ),

                        html.P(
                            (
                                "No station-line services "
                                "match the selected filters."
                            ),
                            className=(
                                "empty-state-text"
                            ),
                        ),
                    ],
                    className="empty-state",
                ),
            ]
        )


    # -----------------------------------------------------
    # KPI calculations
    # -----------------------------------------------------

    service_count = len(
        dataframe
    )

    arrival_observations = int(
        dataframe[
            "arrival_observations"
        ]
        .fillna(0)
        .sum()
    )

    average_eta = (
        weighted_average_eta(
            dataframe
        )
    )

    next_arrival = (
        get_next_arrival(
            dataframe
        )
    )

    latest_prediction = (
        get_latest_prediction(
            dataframe
        )
    )


    # -----------------------------------------------------
    # Activity chart
    # -----------------------------------------------------

    chart_df = (
        dataframe[
            [
                "station_name",
                "line_name",
                "arrival_observations",
            ]
        ]
        .copy()
        .sort_values(
            [
                "station_name",
                "line_name",
            ]
        )
    )


    figure = px.bar(
        chart_df,
        x="station_name",
        y="arrival_observations",
        color="line_name",
        barmode="group",
        labels={
            "station_name": "Station",
            "arrival_observations":
                "Arrival Observations",
            "line_name": "Line",
        },
    )

    style_figure(
        figure
    )


    # -----------------------------------------------------
    # Table
    # -----------------------------------------------------

    table_rows = []

    table_df = (
        dataframe
        .sort_values(
            [
                "station_name",
                "line_name",
            ]
        )
    )


    for _, row in (
        table_df.iterrows()
    ):

        table_rows.append(
            html.Tr(
                [
                    html.Td(
                        html.Strong(
                            row[
                                "station_name"
                            ]
                        )
                    ),

                    html.Td(
                        row[
                            "line_name"
                        ]
                    ),

                    html.Td(
                        f"{int(row['arrival_observations']):,}"
                    ),

                    html.Td(
                        int(
                            row[
                                "distinct_vehicles"
                            ]
                        )
                        if pd.notna(
                            row[
                                "distinct_vehicles"
                            ]
                        )
                        else "—"
                    ),

                    html.Td(
                        format_eta(
                            row[
                                "avg_eta_seconds"
                            ]
                        )
                    ),

                    html.Td(
                        format_eta(
                            row[
                                "min_eta_seconds"
                            ]
                        )
                    ),

                    html.Td(
                        format_eta(
                            row[
                                "max_eta_seconds"
                            ]
                        )
                    ),

                    html.Td(
                        format_timestamp(
                            row[
                                "next_expected_arrival_local"
                            ]
                        )
                    ),

                    html.Td(
                        format_timestamp(
                            row[
                                "latest_prediction_timestamp_local"
                            ]
                        )
                    ),
                ]
            )
        )


    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th(
                            "Station"
                        ),

                        html.Th(
                            "Line"
                        ),

                        html.Th(
                            "Observations"
                        ),

                        html.Th(
                            "Vehicles"
                        ),

                        html.Th(
                            "Avg ETA"
                        ),

                        html.Th(
                            "Min ETA"
                        ),

                        html.Th(
                            "Max ETA"
                        ),

                        html.Th(
                            "Next Expected"
                        ),

                        html.Th(
                            "Latest Prediction"
                        ),
                    ]
                )
            ),

            html.Tbody(
                table_rows
            ),
        ],
        hover=True,
        responsive=True,
        borderless=True,
        className=(
            "arrival-table mb-0"
        ),
    )


    # -----------------------------------------------------
    # Page result
    # -----------------------------------------------------

    return html.Div(
        [
            build_section_title(
                "Arrival Summary",
                (
                    "Metrics reflect the current "
                    "station and line selection."
                ),
            ),


            dbc.Row(
                [
                    dbc.Col(
                        build_kpi_card(
                            "Station-Line Services",
                            service_count,
                            "Services represented",
                            "primary",
                        ),
                        lg=3,
                        md=6,
                    ),

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
                            "Average ETA",
                            format_eta(
                                average_eta
                            ),
                            "Observation weighted",
                            "warning",
                        ),
                        lg=3,
                        md=6,
                    ),

                    dbc.Col(
                        build_kpi_card(
                            "Next Expected Arrival",
                            format_timestamp(
                                next_arrival
                            ),
                            "Local London time",
                            "success",
                        ),
                        lg=3,
                        md=6,
                    ),
                ],
                className="g-3",
            ),


            html.Div(
                [
                    html.Span(
                        "Latest prediction represented: ",
                        className=(
                            "text-secondary"
                        ),
                    ),

                    html.Strong(
                        format_timestamp(
                            latest_prediction
                        )
                    ),
                ],
                className=(
                    "arrival-freshness mt-3"
                ),
            ),


            # ---------------------------------------------
            # Chart
            # ---------------------------------------------

            build_section_title(
                "Arrival Activity",
                (
                    "Observed arrival predictions "
                    "by station and Tube line."
                ),
            ),


            dbc.Card(
                dbc.CardBody(
                    dcc.Graph(
                        figure=figure,
                        config={
                            "displayModeBar":
                                False,
                            "responsive":
                                False,
                        },
                        responsive=False,
                        style={
                            "height": "320px",
                            "width": "100%",
                        },
                    )
                ),
                className="content-card",
            ),


            # ---------------------------------------------
            # Detail table
            # ---------------------------------------------

            build_section_title(
                "Station and Line Detail",
                (
                    "Latest ETA metrics from the "
                    "Gold station arrival serving table."
                ),
            ),


            dbc.Card(
                dbc.CardBody(
                    table
                ),
                className="content-card",
            ),
        ]
    )