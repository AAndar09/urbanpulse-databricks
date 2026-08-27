import dash
import dash_bootstrap_components as dbc

from dash import (
    Input,
    Output,
    callback,
    dcc,
    html,
)

from components.disruptions import (
    build_reason_content,
)

from components.formatting import (
    format_timestamp,
)

from components.layout import (
    build_page_header,
    build_section_title,
)

from components.status import (
    get_service_style,
)

from services.queries import (
    get_current_line_status,
)


dash.register_page(
    __name__,
    path="/line-status",
    name="Line Status",
)


# =========================================================
# Page shell
# =========================================================

def build_layout():
    """
    Return a lightweight page shell immediately.

    Databricks SQL queries must not run inside this function,
    because Dash can evaluate page layouts while processing
    the initial application request.
    """

    return html.Main(
        [
            build_page_header(
                "Operations",
                "Line Status",
                (
                    "Current London Underground "
                    "service conditions and disruptions."
                ),
            ),

            dcc.Interval(
                id="line-status-loader",
                interval=500,
                n_intervals=0,
                max_intervals=1,
            ),

            dcc.Loading(
                type="circle",
                children=html.Div(
                    id="line-status-content",
                    children=dbc.Alert(
                        "Loading current line status...",
                        color="light",
                    ),
                ),
            ),
        ],
        className="page-container",
    )


layout = build_layout


# =========================================================
# Content builder
# =========================================================

def build_line_status_content():
    status_df = get_current_line_status()

    if status_df.empty:
        return html.Div(
            [
                build_section_title(
                    "Current Service",
                    (
                        "Latest operational state "
                        "across Tube lines."
                    ),
                ),

                dbc.Alert(
                    "No current line status data is available.",
                    color="warning",
                ),
            ]
        )

    status_df = status_df.sort_values(
        "line_name"
    )

    rows = []

    for _, row in status_df.iterrows():
        service = get_service_style(
            row["status_severity"],
            row["status_description"],
        )

        rows.append(
            html.Tr(
                [
                    html.Td(
                        html.Strong(
                            row["line_name"]
                        ),
                        className="disruption-line-cell",
                    ),

                    html.Td(
                        row["status_description"],
                        className="disruption-status-cell",
                    ),

                    html.Td(
                        dbc.Badge(
                            service["label"],
                            color=service["color"],
                            pill=True,
                            className="status-badge",
                        )
                    ),

                    html.Td(
                        build_reason_content(
                            row["status_reason"],
                            row["line_name"],
                            expandable=True,
                        ),
                        className="reason-cell",
                    ),

                    html.Td(
                        format_timestamp(
                            row[
                                "status_snapshot_at_local"
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
                        html.Th("Line"),
                        html.Th("Status"),
                        html.Th("Service State"),
                        html.Th("Reason"),
                        html.Th("Last Updated"),
                    ]
                )
            ),

            html.Tbody(rows),
        ],
        hover=True,
        responsive=True,
        borderless=True,
        className="mb-0 disruption-table",
    )

    return html.Div(
        [
            build_section_title(
                "Current Service",
                (
                    "Latest operational state "
                    "across Tube lines."
                ),
            ),

            dbc.Card(
                dbc.CardBody(table),
                className="content-card",
            ),
        ]
    )


# =========================================================
# Lazy data loading
# =========================================================

@callback(
    Output(
        "line-status-content",
        "children",
    ),
    Input(
        "line-status-loader",
        "n_intervals",
    ),
    prevent_initial_call=True,
)
def load_line_status(_):
    try:
        return build_line_status_content()

    except Exception as exc:
        return dbc.Alert(
            [
                html.H4(
                    "Unable to load Line Status",
                    className="alert-heading",
                ),

                html.P(
                    (
                        "UrbanPulse could not retrieve "
                        "the latest Databricks data."
                    )
                ),

                html.Hr(),

                html.Small(str(exc)),
            ],
            color="danger",
        )