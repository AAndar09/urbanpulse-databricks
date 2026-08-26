import dash_bootstrap_components as dbc

from dash import html


def build_navbar():
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(
                dbc.NavLink(
                    "Network Overview",
                    href="/",
                    active="exact",
                )
            ),

            dbc.NavItem(
                dbc.NavLink(
                    "Line Status",
                    href="/line-status",
                    active="exact",
                )
            ),

            dbc.NavItem(
                dbc.NavLink(
                    "Station Arrivals",
                    href="/station-arrivals",
                    active="exact",
                )
            ),
        ],
        brand="UrbanPulse",
        brand_href="/",
        color="dark",
        dark=True,
        expand="lg",
        className="urbanpulse-navbar",
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