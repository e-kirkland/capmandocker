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
                                    children="Trade View",
                                ),
                                html.P(
                                    children="Select two rosters to compare and explore trade options"
                                ),
                            ],
                            align="start",
                            style={"marginLeft": "20px", "marginTop": "20px"},
                        ),
                    ],
                    align="start",
                    style={"height": "20vh"},
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dcc.Dropdown(
                                    id="left-dynamic-dropdown",
                                    placeholder="Select a team",
                                    className="DropdownSelector",
                                ),
                                dash_table.DataTable(
                                    id="left-roster-data",
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
                            style={"marginLeft": "20px"},
                        ),
                        dbc.Col(
                            [
                                dcc.Dropdown(
                                    id="right-dynamic-dropdown",
                                    placeholder="Select a team",
                                    className="DropdownSelector",
                                ),
                                dash_table.DataTable(
                                    id="right-roster-data",
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
                            style={"marginRight": "20px"},
                        ),
                    ]
                ),
            ]
        )
    ]
)
