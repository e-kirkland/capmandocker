from dash import Dash, dash_table, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from flask import current_app as app
import pandas as pd

from models.Players import Players
from views.players import players_upsert_df


def get_player_data():

    player_df = Players.get_all_players_df()
    player_df = player_df.sort_values(by=["roster_id", "war"], ascending=[True, False])

    dt_col_param = []
    for col in player_df.columns:
        dt_col_param.append({"name": str(col), "id": str(col)})
    print("PLAYER DF: ", player_df.head(), flush=True)
    player_dict = player_df.to_dict(orient="records")
    print("PLAYER DICT: ", player_dict)

    return player_dict, player_df, dt_col_param


def get_layout():

    layout_list = []

    # Full data table
    player_dict, player_df, dt_col_param = get_player_data()
    data_table = dash_table.DataTable(
        id="all_players_datatable",
        columns=dt_col_param,
        data=player_df.to_dict("records"),
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
    )
    layout_list.append(data_table)

    return html.Div(layout_list)


def app_layout():
    layout = html.Div(
        [
            dcc.Interval(id="interval_update", interval=30000, n_intervals=0),
            html.Div(id="all_players_datatable"),
            # Create notification when saving to excel
            html.Div(id="placeholder", children=[]),
            # dcc.Store(id="store", data=0),
            # dcc.Interval(id="interval", interval=1000),
        ]
    )

    return layout


def get_dash_app(app, pathname="/web/"):
    dash_app = Dash(__name__, server=app, url_base_pathname=pathname)

    dash_app.layout = get_layout()

    # dash_app.layout = app_layout()

    # # Callback to populate all player table
    # @dash_app.callback(
    #     Output("all_players_datatable", "children"),
    #     [Input("interval_update", "n_intervals")],
    # )
    def populate_all_player_datatable(n_intervals):
        # Full data table
        player_dict, player_df, dt_col_param = get_player_data()
        data_table = dash_table.DataTable(
            id="all_player_datatable",
            columns=dt_col_param,
            data=player_df.to_dict("records"),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
        )

        return [data_table]

    @dash_app.callback(
        Output("a_text_area", "value"), [Input("all_player_datatable", "data")]
    )
    def loading_data(data):
        print("TESTING DATA CHANGE: ", flush=True)
        # D=pd.DataFrame(data)
        # D.to_sql('test_backend',if_exists='replace')

        return "updated"

    # # Callback to update table
    # @dash_app.callback(
    #     [Output("placeholder", "children"), Output("store", "data")],
    #     [Input("save_to_postgres", "n_clicks"), Input("interval", "n_intervals")],
    #     [State("all_players_datatable", "data"), State("store", "data")],
    #     prevent_initial_call=True,
    # )
    # def update_postgres_db(n_clicks, n_intervals, dataset, s):
    #     print("UPDATE TRIGGERED, ", flush=True)
    #     output = html.Plaintext(
    #         "The data has been saved to your PostgreSQL database.",
    #         style={"color": "green", "font-weight": "bold", "font-size": "large"},
    #     )
    #     no_output = html.Plaintext("", style={"margin": "0px"})

    #     input_triggered = callback_context.triggered[0]["prop_id"].split(".")[0]

    #     if input_triggered == "save_to_postgres":
    #         s = 6
    #         updated_player_df = pd.DataFrame(dataset)
    #         msg = players_upsert_df(updated_player_df)
    #         return output, s
    #     elif input_triggered == "interval" and s > 0:
    #         s = s - 1
    #         if s > 0:
    #             return output, s
    #         else:
    #             return no_output, s
    #     elif s == 0:
    #         return no_output, s

    return dash_app
