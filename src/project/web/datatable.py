from dash import Dash, dash_table, dcc, html
from dash.dependencies import Input, Output
import pandas as pd

from models.Players import Players
from app import dash_app

# app = Dash(__name__, server=current_app, url_base_pathname="/web")

params = [
    "player_id",
    "player",
    "position",
    "team",
    "salary",
    "roster_id",
    "injured_reserve",
    "war",
    "value",
]

player_df = Players.get_all_players_df()
player_df = player_df.sort_values(by=["roster_id"], ascending=True)

dash_app.layout = html.Div(
    [
        dash_table.DataTable(
            id="table-editing-simple",
            columns=player_df.columns,
            data=player_df.to_dict(orient="records"),
            editable=False,
        ),
        dcc.Graph(id="table-editing-simple-output"),
    ]
)
