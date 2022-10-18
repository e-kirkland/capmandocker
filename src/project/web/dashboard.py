from dash import Dash, dash_table, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import current_app as app
import pandas as pd

from models.Players import Players
from views.players import upsert_player


def diff_dashtable(data, data_previous, row_id_name="player_id"):

    """Generate a diff of Dash DataTable data.

    Parameters
    ----------
    data: DataTable property (https://dash.plot.ly/datatable/reference)
        The contents of the table (list of dicts)
    data_previous: DataTable property
        The previous state of `data` (list of dicts).

    Returns
    -------
    A list of dictionaries in form of [{row_id_name:, column_name:, current_value:,
        previous_value:}]
    """

    df, df_previous = pd.DataFrame(data=data), pd.DataFrame(data_previous)

    df.set_index("player_id", inplace=True)
    df_previous.set_index("player_id", inplace=True)

    mask = df.ne(df_previous)

    df_diff = df[mask].dropna(how="all", axis="columns").dropna(how="all", axis="rows")

    changes = []

    for idx, row in df_diff.iterrows():

        row_id = row.name

        row.dropna(inplace=True)

        for change in row.iteritems():

            changes.append(
                {
                    row_id_name: row_id,
                    "column_name": change[0],
                    "current_value": change[1],
                    "previous_value": df_previous.at[row_id, change[0]],
                }
            )

    return changes


def get_player_data():

    player_df = Players.get_all_players_df()
    player_df = player_df.sort_values(by=["roster_id", "war"], ascending=[True, False])

    dt_col_param = []
    for col in player_df.columns:
        dt_col_param.append({"name": str(col), "id": str(col)})
    player_dict = player_df.to_dict(orient="records")

    return player_dict, player_df, dt_col_param


def get_layout():

    layout_list = []

    layout_div = html.Div([])
    layout_list.append(dcc.Store(id="diff-store"))
    layout_list.append(html.P("Changes to DataTable"))
    layout_list.append(html.Div(id="data-diff"))
    layout_list.append(html.Button("Save Changes", id="button"))
    layout_list.append(dcc.Interval(id="interval_component", interval=2000))

    # Full data table
    player_dict, player_df, dt_col_param = get_player_data()
    print("PLAYER DATA RETRIEVED: ", player_df.head(), flush=True)
    data_table = dash_table.DataTable(
        id="table-data-diff",
        # columns=dt_col_param,
        # data=player_df.to_dict("records"),
        columns=[],
        data=[],
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
    )
    layout_list.append(data_table)

    return html.Div(layout_list)


def get_dash_app(app, pathname="/web/"):

    # Bootstrap theme
    external_stylesheets = [dbc.themes.SOLAR]

    dash_app = Dash(
        __name__,
        external_stylesheets=external_stylesheets,
        server=app,
        url_base_pathname=pathname,
    )

    @dash_app.callback(
        [Output("table-data-diff", "data"), Output("table-data-diff", "columns")],
        [Input("button", "n_clicks")],
    )
    def get_player_data_callback(n_clicks):
        print("UPDATE_OUTPUT TRIGGERED: ", flush=True)

        player_df = Players.get_all_players_df()
        player_df = player_df.sort_values(
            by=["roster_id", "war"], ascending=[True, False]
        )

        dt_col_param = []
        for col in player_df.columns:
            dt_col_param.append({"name": str(col), "id": str(col)})
        player_dict = player_df.to_dict(orient="records")

        return player_dict, dt_col_param

    @dash_app.callback(
        Output("diff-store", "data"),
        [Input("table-data-diff", "data_timestamp")],
        [
            State("table-data-diff", "data"),
            State("table-data-diff", "data_previous"),
            State("diff-store", "data"),
        ],
    )
    def capture_diffs(ts, data, data_previous, diff_store_data):
        print("CAPTURE DIFFS TRIGGERED: ", flush=True)
        if ts is None:
            raise PreventUpdate

        diff_store_data = diff_store_data or {}

        diff_store_data[ts] = diff_dashtable(data, data_previous)

        print("DIFF: ", diff_store_data[ts])

        return diff_store_data

    @dash_app.callback(
        Output("data-diff", "children"),
        [Input("button", "n_clicks")],
        [State("diff-store", "data")],
    )
    def update_output(n_clicks, diff_store_data):

        print("UPDATE_OUTPUT TRIGGERED: ", flush=True)
        print("N_CLICKS: ", n_clicks, flush=True)
        print("DIFF STORE DATA: ", diff_store_data, flush=True)

        if n_clicks is None:

            raise PreventUpdate

        if diff_store_data:

            dt_changes = []
            pg_updates = []

            for v in diff_store_data.values():
                dt_changes.append(f"* {v}")
                for c in v:
                    pg_updates.append(c)

            print("CHANGES DETECTED: ", flush=True)

            # Update postgres using changes in data table
            for change in pg_updates:
                print("CHANGE: ", change, flush=True)
                player_id = change["player_id"]
                update_col = change["column_name"]
                update_value = change["current_value"]

                data = {}
                if str(update_col) in ["salary"]:
                    data[str(update_col)] = int(update_value)

                elif str(update_col) in ["war", "value"]:
                    data[str(update_col)] = float(update_value)

                elif str(update_col) in ["injured_reserve"]:
                    data[str(update_col)] = bool(update_value)

                else:
                    data[str(update_col)] = str(update_value)

                print(f"UPDATING PLAYER {player_id}: ", data, flush=True)

                _player = upsert_player(player_id, data)

                print("UPDATED PLAYER: ", _player)

            return [dcc.Markdown(change) for change in dt_changes]

        else:

            return "No Changes to DataTable"

    dash_app.layout = get_layout()

    return dash_app
