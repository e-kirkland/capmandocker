from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


layout = html.Div(
    [
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1(
                                    children="Roster Status",
                                ),
                                html.P(children="Select a team to view current roster"),
                            ],
                            align="start",
                            style={"marginLeft": "20px", "marginTop": "20px"},
                        ),
                        dbc.Col(
                            [dcc.Graph(id="indicator-rosters")],
                            align="start",
                        ),
                    ],
                    align="start",
                    style={"height": "20vh"},
                ),
                dbc.Col(
                    [
                        dcc.Dropdown(
                            id="roster-dynamic-dropdown",
                            placeholder="Select a team",
                            className="DropdownSelector",
                        ),
                        dash_table.DataTable(
                            id="single-roster-data",
                            columns=[],
                            data=[],
                            editable=False,
                            sort_action="native",
                            sort_mode="multi",
                            style_header={
                                'backgroundColor': 'rgb(30, 30, 30)',
                                'color': 'white'
                            },
                            style_data={
                                'backgroundColor': 'rgb(50, 50, 50)',
                                'color': 'white'
                            },
                        ),
                    ],
                    style={"marginLeft": "20px", "marginRight": "20px"},
                ),
            ]
        )
    ]
)
