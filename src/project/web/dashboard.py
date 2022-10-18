from dash import html, dcc, dash_table
import plotly.graph_objects as go

layout = html.Div(
    children=[
        html.H1(
            children="League Dashboard",
        ),
        html.P(children="Checking roster size/salary spend of all teams"),
        dcc.Graph(id="bar-roster"),
        dcc.Graph(id="bar-salary"),
    ]
)
