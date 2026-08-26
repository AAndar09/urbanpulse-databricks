import dash_bootstrap_components as dbc

from dash import html


def build_navbar():
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand(
                    "UrbanPulse",
                    href="/",
                    className=(
                        "brand-title "
                        "text-white fs-4"
                    ),
                ),

                dbc.Nav(
                    [
                        dbc.NavLink(
                            "Network Overview",
                            href="/",
                            active="exact",
                        ),

                        dbc.NavLink(
                            "Line Status",
                            href="/line-status",
                            active="exact",
                        ),

                        dbc.NavLink(
                            "Station Arrivals",
                            href="/station-arrivals",
                            active="exact",
                        ),
                        
                    ],
                    navbar=True,
                    className="ms-auto",
                ),
            ],
            fluid=True,
        ),
        className=(
            "urbanpulse-navbar "
            "navbar-dark"
        ),
    )


def build_page_header(
    kicker,
    title,
    description,
):
    return html.Div(
        [
            html.Div(
                kicker,
                className="page-kicker",
            ),

            html.H1(
                title,
                className="page-title",
            ),

            html.P(
                description,
                className="page-description",
            ),
        ]
    )


def build_section_title(
    title,
    description=None,
):
    children = [
        html.H2(
            title,
            className="section-title",
        )
    ]

    if description:
        children.append(
            html.P(
                description,
                className=(
                    "section-description"
                ),
            )
        )

    return html.Div(
        children,
        className="section-header",
    )


def build_kpi_card(
    label,
    value,
    helper=None,
    accent="primary",
):
    body = [
        html.Div(
            label,
            className="kpi-label",
        ),

        html.Div(
            value,
            className="kpi-value",
        ),
    ]

    if helper:
        body.append(
            html.Div(
                helper,
                className="kpi-helper",
            )
        )

    return dbc.Card(
        dbc.CardBody(body),
        className=(
            f"kpi-card "
            f"kpi-{accent}"
        ),
    )