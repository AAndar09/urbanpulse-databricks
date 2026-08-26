import os

import dash
import dash_bootstrap_components as dbc

from dash import Dash, html

from components.layout import (
    build_navbar,
)


app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP,
    ],
)

app.title = "UrbanPulse"


app.layout = html.Div(
    [
        build_navbar(),

        dash.page_container,
    ]
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