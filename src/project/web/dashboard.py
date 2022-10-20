from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

layout = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            children="League Dashboard",
                        ),
                        html.P(
                            children="Checking roster size/salary spend of all teams"
                        ),
                    ],
                    align="start",
                    style={"marginLeft": "20px", "marginTop": "20px"},
                ),
                dbc.Col(
                    [dcc.Graph(id="indicator-settings")],
                    align="start",
                ),
            ],
            align="start",
            style={"height": "20vh"},
        ),
        dcc.Graph(id="bar-roster"),
        dcc.Graph(id="bar-salary"),
        dcc.Graph(id="bar-starter-war"),
    ]
)
