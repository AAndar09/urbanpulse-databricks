import os

import dash_bootstrap_components as dbc

from dash import (
    Dash,
    html,
)

from services.queries import (
    get_current_line_status,
)


app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
    ],
)


def build_line_rows():

    line_status_df = (
        get_current_line_status()
    )

    rows = []

    for _, row in line_status_df.iterrows():

        disrupted = bool(
            row["is_disrupted"]
        )

        badge = dbc.Badge(
            (
                "Disrupted"
                if disrupted
                else "Good Service"
            ),
            color=(
                "danger"
                if disrupted
                else "success"
            ),
            pill=True,
        )

        rows.append(
            html.Tr(
                [
                    html.Td(
                        row["line_name"]
                    ),
                    html.Td(
                        row[
                            "status_description"
                        ]
                    ),
                    html.Td(
                        badge
                    ),
                ]
            )
        )

    return rows


app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.H1(
                        "UrbanPulse",
                        className=(
                            "display-4 fw-bold"
                        ),
                    ),

                    html.P(
                        (
                            "London Urban Mobility "
                            "Intelligence Platform"
                        ),
                        className=(
                            "lead text-secondary"
                        ),
                    ),
                ],
                className="py-4",
            )
        ),

        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H4(
                                "Current Tube Line Status",
                                className="mb-0",
                            )
                        ),

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
                                                    "Service State"
                                                ),
                                            ]
                                        )
                                    ),

                                    html.Tbody(
                                        build_line_rows()
                                    ),
                                ],
                                bordered=False,
                                hover=True,
                                responsive=True,
                            )
                        ),
                    ],
                    className="shadow-sm",
                )
            )
        ),
    ],
    fluid=True,
    className="px-4",
)


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                "8050",
            )
        ),
        debug=False,
    )