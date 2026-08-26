import pandas as pd

import dash
import dash_bootstrap_components as dbc

from dash import html

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


def build_layout():
    try:
        status_df = (
            get_current_line_status()
        )

        rows = []

        for _, row in (
            status_df.iterrows()
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
                reason = "No additional information"


            rows.append(
                html.Tr(
                    [
                        html.Td(
                            html.Strong(
                                row[
                                    "line_name"
                                ]
                            )
                        ),

                        html.Td(
                            row[
                                "status_description"
                            ]
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
                            reason
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
                            html.Th(
                                "Service State"
                            ),
                            html.Th("Reason"),
                            html.Th(
                                "Last Updated"
                            ),
                        ]
                    )
                ),

                html.Tbody(rows),
            ],
            hover=True,
            responsive=True,
            borderless=True,
            className="mb-0",
        )


        return html.Main(
            [
                build_page_header(
                    "Operations",
                    "Line Status",
                    (
                        "Current operational "
                        "status of London "
                        "Underground lines."
                    ),
                ),

                build_section_title(
                    "Current Service",
                    (
                        "Latest status from the "
                        "UrbanPulse Gold serving "
                        "layer."
                    ),
                ),

                dbc.Card(
                    dbc.CardBody(
                        table
                    ),
                    className="content-card",
                ),
            ],
            className="page-container",
        )


    except Exception as exc:
        return dbc.Container(
            dbc.Alert(
                str(exc),
                color="danger",
            ),
            className="py-5",
        )


layout = build_layout