import pandas as pd
import plotly.express as px

import dash
import dash_bootstrap_components as dbc

from dash import (
    Input,
    Output,
    State,
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


# =========================================================
# Constants
# =========================================================

ALL_STATIONS = "__ALL_STATIONS__"
ALL_LINES = "__ALL_LINES__"


# =========================================================
# Helpers
# =========================================================

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
        dataframe[
            "arrival_observations"
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

    weights = valid_df[
        "arrival_observations"
    ].astype(float)

    weight_total = weights.sum()

    if weight_total == 0:
        return None

    weighted_total = (
        valid_df[
            "avg_eta_seconds"
        ].astype(float)
        *
        weights
    ).sum()

    return weighted_total / weight_total


def get_next_arrival(dataframe):
    if dataframe.empty:
        return None

    timestamps = pd.to_datetime(
        dataframe[
            "next_expected_arrival_local"
        ],
        errors="coerce",
    ).dropna()

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
    ).dropna()

    if timestamps.empty:
        return None

    return timestamps.max()


def shorten_station_name(value):
    return (
        str(value)
        .replace(
            " Underground Station",
            "",
        )
        .replace(
            " Underground",
            "",
        )
    )


def style_figure(
    figure,
    row_count,
):
    chart_height = max(
        320,
        min(
            650,
            90 + (row_count * 45),
        ),
    )

    figure.update_layout(
        template="plotly_white",
        height=chart_height,
        autosize=False,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
        xaxis_title=(
            "Arrival Observations"
        ),
        yaxis_title=None,
        legend_title_text=(
            "Tube Line"
        ),
        hovermode="closest",
        bargap=0.25,
    )

    figure.update_yaxes(
        automargin=True,
    )

    figure.update_xaxes(
        rangemode="tozero",
        gridcolor="#e2e8f0",
    )

    return figure


def build_station_options(
    dataframe,
):
    station_records = (
        dataframe[
            [
                "station_id",
                "station_name",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "station_name"
        )
    )

    options = [
        {
            "label": "All stations",
            "value": ALL_STATIONS,
        }
    ]

    for (
        station_id,
        station_name,
    ) in station_records.itertuples(
        index=False,
        name=None,
    ):
        options.append(
            {
                "label": station_name,
                "value": station_id,
            }
        )

    return options


def build_line_options(
    dataframe,
    selected_station=None,
):
    filtered_df = dataframe.copy()

    if (
        selected_station
        and selected_station
        != ALL_STATIONS
    ):
        filtered_df = filtered_df[
            filtered_df[
                "station_id"
            ] == selected_station
        ]

    line_records = (
        filtered_df[
            [
                "line_id",
                "line_name",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "line_name"
        )
    )

    options = [
        {
            "label": "All lines",
            "value": ALL_LINES,
        }
    ]

    for (
        line_id,
        line_name,
    ) in line_records.itertuples(
        index=False,
        name=None,
    ):
        options.append(
            {
                "label": line_name,
                "value": line_id,
            }
        )

    return options


# =========================================================
# Dashboard content
# =========================================================

def build_arrival_content(
    dataframe,
):
    if dataframe.empty:
        return html.Div(
            [
                build_section_title(
                    "Arrival Summary",
                    (
                        "Metrics reflect the "
                        "current station and "
                        "line selection."
                    ),
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
                                "No station-line "
                                "services match the "
                                "selected filters."
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
    # KPIs
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
    # Chart
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
            "arrival_observations",
            ascending=True,
        )
    )

    chart_df[
        "station_display_name"
    ] = chart_df[
        "station_name"
    ].apply(
        shorten_station_name
    )

    figure = px.bar(
        chart_df,
        x="arrival_observations",
        y="station_display_name",
        color="line_name",
        orientation="h",
        barmode="group",
        labels={
            "station_display_name":
                "Station",

            "arrival_observations":
                "Arrival Observations",

            "line_name":
                "Tube Line",
        },
        hover_data={
            "station_name": True,
            "line_name": True,
            "arrival_observations": True,
        },
    )

    style_figure(
        figure,
        len(chart_df),
    )


    # -----------------------------------------------------
    # Detail table
    # -----------------------------------------------------

    table_rows = []

    table_df = dataframe.sort_values(
        [
            "station_name",
            "line_name",
        ]
    )

    for _, row in table_df.iterrows():

        arrival_count = (
            int(
                row[
                    "arrival_observations"
                ]
            )
            if pd.notna(
                row[
                    "arrival_observations"
                ]
            )
            else 0
        )

        vehicle_count = (
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
        )

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
                        f"{arrival_count:,}"
                    ),

                    html.Td(
                        vehicle_count
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
                        html.Th("Station"),
                        html.Th("Line"),
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
    # Result
    # -----------------------------------------------------

    return html.Div(
        [
            build_section_title(
                "Arrival Summary",
                (
                    "Metrics reflect the "
                    "current station and "
                    "line selection."
                ),
            ),

            dbc.Row(
                [
                    dbc.Col(
                        build_kpi_card(
                            "Station-Line Services",
                            service_count,
                            (
                                "Services represented"
                            ),
                            "primary",
                        ),
                        xs=12,
                        sm=6,
                        lg=3,
                    ),

                    dbc.Col(
                        build_kpi_card(
                            "Arrival Observations",
                            (
                                f"{arrival_observations:,}"
                            ),
                            (
                                "Predictions captured"
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
                                average_eta
                            ),
                            (
                                "Observation weighted"
                            ),
                            "warning",
                        ),
                        xs=12,
                        sm=6,
                        lg=3,
                    ),

                    dbc.Col(
                        build_kpi_card(
                            "Next Expected Arrival",
                            format_timestamp(
                                next_arrival
                            ),
                            (
                                "Local London time"
                            ),
                            "success",
                        ),
                        xs=12,
                        sm=6,
                        lg=3,
                    ),
                ],
                className="g-3",
            ),

            html.Div(
                [
                    html.Span(
                        (
                            "Latest prediction "
                            "represented:"
                        ),
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
                            "width": "100%",
                        },
                    )
                ),
                className="content-card",
            ),


            build_section_title(
                "Station and Line Detail",
                (
                    "Latest ETA metrics from the "
                    "Gold station arrival "
                    "serving table."
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


# =========================================================
# Page layout
# =========================================================

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
                            "Arrival activity and "
                            "ETA intelligence across "
                            "monitored London "
                            "Underground stations."
                        ),
                    ),

                    dbc.Alert(
                        (
                            "No station arrival "
                            "data is available."
                        ),
                        color="warning",
                    ),
                ],
                className="page-container",
            )


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


                build_section_title(
                    "Explore Arrivals",
                    (
                        "Choose a station first to "
                        "limit Tube Line options to "
                        "valid station-line combinations."
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
                                        ),

                                        dcc.Dropdown(
                                            id=(
                                                "arrival-"
                                                "station-filter"
                                            ),
                                            options=(
                                                build_station_options(
                                                    arrivals_df
                                                )
                                            ),
                                            value=(
                                                ALL_STATIONS
                                            ),
                                            clearable=False,
                                            searchable=True,
                                        ),
                                    ],
                                    xs=12,
                                    lg=6,
                                ),

                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Tube Line",
                                        ),

                                        dcc.Dropdown(
                                            id=(
                                                "arrival-"
                                                "line-filter"
                                            ),
                                            options=(
                                                build_line_options(
                                                    arrivals_df
                                                )
                                            ),
                                            value=(
                                                ALL_LINES
                                            ),
                                            clearable=False,
                                            searchable=True,
                                        ),
                                    ],
                                    xs=12,
                                    lg=6,
                                ),
                            ],
                            className="g-3",
                        )
                    ),
                    className=(
                        "content-card "
                        "filter-card"
                    ),
                ),


                dcc.Loading(
                    type="circle",
                    children=html.Div(
                        id=(
                            "station-arrivals-content"
                        )
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
                        (
                            "Unable to load "
                            "Station Arrivals"
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


# =========================================================
# Station -> Line options
# =========================================================

@callback(
    Output(
        "arrival-line-filter",
        "options",
    ),

    Output(
        "arrival-line-filter",
        "value",
    ),

    Input(
        "arrival-station-filter",
        "value",
    ),

    State(
        "arrival-line-filter",
        "value",
    ),

    State(
        "station-arrivals-data",
        "data",
    ),
)
def update_line_options(
    selected_station,
    current_line,
    stored_data,
):
    if not stored_data:
        return (
            [
                {
                    "label": "All lines",
                    "value": ALL_LINES,
                }
            ],
            ALL_LINES,
        )


    dataframe = pd.DataFrame(
        stored_data
    )

    options = build_line_options(
        dataframe,
        selected_station,
    )

    valid_values = {
        option["value"]
        for option in options
    }

    if current_line not in valid_values:
        current_line = ALL_LINES

    return (
        options,
        current_line,
    )


# =========================================================
# Dashboard filtering
# =========================================================

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
            (
                "No station arrival "
                "data is available."
            ),
            color="warning",
        )


    dataframe = pd.DataFrame(
        stored_data
    )


    if (
        selected_station
        and selected_station
        != ALL_STATIONS
    ):
        dataframe = dataframe[
            dataframe[
                "station_id"
            ] == selected_station
        ]


    if (
        selected_line
        and selected_line
        != ALL_LINES
    ):
        dataframe = dataframe[
            dataframe[
                "line_id"
            ] == selected_line
        ]


    return build_arrival_content(
        dataframe
    )