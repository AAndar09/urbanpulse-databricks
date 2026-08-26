import os

import dash_bootstrap_components as dbc

from dash import (
    Dash,
    html,
)

from components.status import (
    get_service_style,
)

from services.queries import (
    get_current_line_status,
    get_network_summary,
)


app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP,
    ],
)

app.title = "UrbanPulse"


def build_kpi_card(
    label,
    value,
):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    label,
                    className="kpi-label",
                ),
                html.Div(
                    value,
                    className="kpi-value",
                ),
            ]
        ),
        className="kpi-card",
    )


def build_status_table():

    status_df = (
        get_current_line_status()
    )

    rows = []

    for _, row in status_df.iterrows():

        style = get_service_style(
            row["status_description"]
        )

        rows.append(
            html.Tr(
                [
                    html.Td(
                        html.Strong(
                            row["line_name"]
                        )
                    ),

                    html.Td(
                        row[
                            "status_description"
                        ]
                    ),

                    html.Td(
                        dbc.Badge(
                            style["label"],
                            color=style[
                                "color"
                            ],
                            pill=True,
                            className=(
                                "status-badge"
                            ),
                        )
                    ),
                ]
            )
        )

    return dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Line"),
                        html.Th("Status"),
                        html.Th(
                            "Service State"
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


def build_page():

    network_df = (
        get_network_summary()
    )

    network = (
        network_df.iloc[0]
    )

    total_lines = int(
        network["total_lines"]
    )

    good_lines = int(
        network[
            "good_service_lines"
        ]
    )

    disrupted_lines = int(
        network[
            "disrupted_lines"
        ]
    )

    good_pct = float(
        network[
            "good_service_pct"
        ]
    )


    navbar = dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand(
                    [
                        html.Span(
                            "UrbanPulse",
                            className=(
                                "brand-title"
                            ),
                        ),
                    ],
                    className=(
                        "text-white fs-4"
                    ),
                ),

                html.Div(
                    "London Mobility Intelligence",
                    className=(
                        "text-white-50 "
                        "small"
                    ),
                ),
            ],
            fluid=True,
        ),
        className="urbanpulse-navbar",
    )


    content = html.Main(
        [
            html.Div(
                "Live Network",
                className="page-kicker",
            ),

            html.H1(
                "Network Overview",
                className="page-title",
            ),

            html.P(
                (
                    "Operational intelligence "
                    "for the London Underground "
                    "network."
                ),
                className="page-description",
            ),


            html.H2(
                "Network Health",
                className="section-title",
            ),


            dbc.Row(
                [
                    dbc.Col(
                        build_kpi_card(
                            "Tube Lines",
                            total_lines,
                        ),
                        lg=3,
                        md=6,
                    ),

                    dbc.Col(
                        build_kpi_card(
                            "Good Service",
                            good_lines,
                        ),
                        lg=3,
                        md=6,
                    ),

                    dbc.Col(
                        build_kpi_card(
                            "Disrupted",
                            disrupted_lines,
                        ),
                        lg=3,
                        md=6,
                    ),

                    dbc.Col(
                        build_kpi_card(
                            "Network Health",
                            f"{good_pct:.1f}%",
                        ),
                        lg=3,
                        md=6,
                    ),
                ],
                className="g-3",
            ),


            html.H2(
                "Current Tube Status",
                className="section-title",
            ),


            dbc.Card(
                dbc.CardBody(
                    build_status_table()
                ),
                className="content-card",
            ),
        ],
        className="page-container",
    )


    return html.Div(
        [
            navbar,
            content,
        ]
    )


try:
    app.layout = build_page()

except Exception as exc:

    app.layout = dbc.Container(
        dbc.Alert(
            [
                html.H4(
                    "Unable to load UrbanPulse",
                    className="alert-heading",
                ),
                html.P(str(exc)),
            ],
            color="danger",
        ),
        className="py-5",
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