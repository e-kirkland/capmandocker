import os

from dash import Dash, dash_table, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import current_app as app
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from models.Players import Players
from models.Rosters import Rosters
from models.Settings import Settings
from models.Rosters import Rosters
from views.players import upsert_player
from scripts import war
from web import all_players, dashboard, rosters, tradeview
from dotenv import load_dotenv


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


def get_dash_app(app, pathname="/web/"):

    load_dotenv()

    # Bootstrap theme
    external_stylesheets = [dbc.themes.DARKLY]

    dash_app = Dash(
        __name__,
        external_stylesheets=external_stylesheets,
        server=app,
        url_base_pathname=pathname,
    )

    dash_app.title = "CapMan"

    # building the navigation bar
    # https://github.com/facultyai/dash-bootstrap-components/blob/master/examples/advanced-component-usage/Navbars.py
    dropdown = dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem("Dashboard", href="/dashboard"),
            dbc.DropdownMenuItem("Rosters", href="/rosters"),
            dbc.DropdownMenuItem("Trade View", href="/tradeview"),
            dbc.DropdownMenuItem("All Players", href="/allplayers"),
        ],
        nav=True,
        in_navbar=True,
        label="Explore",
    )

    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(
                                html.A(
                                    href="https://capman.fly.dev/",
                                    children=[
                                        html.Img(
                                            src=dash_app.get_asset_url("logo.png"),
                                            height="40px",
                                        )
                                    ],
                                )
                            ),
                        ],
                        align="left",
                    ),
                    href="/dashboard",
                    style={"marginRight": "20px"},
                ),
                dbc.NavbarBrand("CAPMAN - ATL Dynasty League", className="ml-2"),
                dbc.NavbarToggler(id="navbar-toggler2"),
                dbc.Collapse(
                    dbc.Nav(
                        # right align dropdown menu with ml-auto className
                        [dropdown],
                        className="ml-auto",
                        navbar=True,
                    ),
                    id="navbar-collapse2",
                    navbar=True,
                ),
            ]
        ),
        color="dark",
        dark=True,
        className="mb-4",
    )

    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open

        for i in [2]:
            app.callback(
                Output(f"navbar-collapse{i}", "is_open"),
                [Input(f"navbar-toggler{i}", "n_clicks")],
                [State(f"navbar-collapse{i}", "is_open")],
            )(toggle_navbar_collapse)

        # embedding the navigation bar
        app.layout = html.Div(
            [dcc.Location(id="url", refresh=False), navbar, html.Div(id="page-content")]
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
            dt_col_param.append(
                {
                    "name": str(col).upper().replace("INJURED_RESERVE", "IR"),
                    "id": str(col),
                }
            )
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

                    if "t" in update_value.lower():
                        update_value = bool(True)
                    else:
                        update_value = bool(False)

                    data[str(update_col)] = update_value

                else:
                    data[str(update_col)] = str(update_value)

                print(f"UPDATING PLAYER {player_id}: ", data, flush=True)

                _player = upsert_player(player_id, data)

            return [dcc.Markdown(change) for change in dt_changes]

        else:

            return "No Changes to DataTable"

    # embedding the navigation bar
    dash_app.layout = html.Div(
        [dcc.Location(id="url", refresh=False), navbar, html.Div(id="page-content")]
    )

    @dash_app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def display_page(pathname):
        if pathname == "/dashboard":
            return dashboard.layout
        elif pathname == "/rosters":
            return rosters.layout
        elif pathname == "/tradeview":
            return tradeview.layout
        elif pathname == "/allplayers":
            return all_players.layout
        else:
            return dashboard.layout

    @dash_app.callback(Output("bar-roster", "figure"), [Input("url", "pathname")])
    def roster_bar_chart(n):
        player_dict, player_df, dt_col_param = get_player_data()
        claimed_players = player_df[player_df["roster_id"] != 999]
        active_players = claimed_players[
            claimed_players["injured_reserve"] == bool(False)
        ]
        roster_count_df = active_players.groupby("roster_id")["player"].count()
        roster_count_df = roster_count_df.reset_index()
        roster_count_df["roster_id"] = roster_count_df["roster_id"].astype(str)

        # Get roster min/max
        league_id = app.config["ROSTER_DATA"]["league_id"]
        _settings = Settings.get_by_league_id(league_id)
        roster_min = _settings.roster_min
        roster_max = _settings.roster_max

        # Get display name
        roster_df = Rosters.get_all_rosters_df()
        merged = roster_count_df.merge(
            roster_df, left_on="roster_id", right_on="roster_id"
        )

        fig = px.bar(
            merged,
            x="display_name",
            y="player",
            labels={"player": "Number of Players", "display_name": "Team"},
            title="Roster Size (Not Including Injured Reserve)",
        )

        fig.add_hrect(
            y0=roster_min, y1=roster_max, line_width=0, fillcolor="teal", opacity=0.4
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )

        return fig

    @dash_app.callback(Output("bar-salary", "figure"), [Input("url", "pathname")])
    def salary_bar_chart(n):
        player_dict, player_df, dt_col_param = get_player_data()
        active_players = player_df[player_df["roster_id"] != 999]
        # active_players = claimed_players[claimed_players["injured_reserve"] != True]
        active_players["salary"] = active_players["salary"].astype(int)
        roster_count_df = active_players.groupby("roster_id")["salary"].sum()
        roster_count_df = roster_count_df.reset_index()
        roster_count_df["roster_id"] = roster_count_df["roster_id"].astype(str)

        # Get salary cap
        league_id = app.config["ROSTER_DATA"]["league_id"]
        _settings = Settings.get_by_league_id(league_id)
        salary_cap = _settings.salary_cap

        # Get display name
        roster_df = Rosters.get_all_rosters_df()
        merged = roster_count_df.merge(
            roster_df, left_on="roster_id", right_on="roster_id"
        )

        fig = px.bar(
            merged,
            x="display_name",
            y="salary",
            labels={"salary": "Total Cap Spend", "display_name": "Team"},
            title="Salary Cap Spend",
        )
        fig.add_hline(y=salary_cap, line_color="red", line_width=3)

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )

        return fig

    @dash_app.callback(Output("bar-starter-war", "figure"), [Input("url", "pathname")])
    def starter_war_bar_chart(n):
        player_dict, player_df, dt_col_param = get_player_data()
        active_players = player_df[player_df["roster_id"] != 999]

        starter_war_df = war.calculate_league_starter_war(active_players)
        starter_war_df["roster_id"] = starter_war_df["roster_id"].astype(str)

        # Get display name
        roster_df = Rosters.get_all_rosters_df()
        roster_df["roster_id"] = roster_df["roster_id"].astype(str)
        merged = starter_war_df.merge(
            roster_df, left_on="roster_id", right_on="roster_id"
        )

        # Get mean war
        mean_starter_war = merged["starter_war"].mean()

        fig = px.bar(
            merged,
            x="display_name",
            y="starter_war",
            labels={"starter_war": "Starters WAR", "display_name": "Team"},
            title="Starters WAR (1 QB, 1 TE, 4 RB, 4 WR)",
        )
        fig.add_hline(y=mean_starter_war, line_color="green", line_width=3)

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )

        return fig

    @dash_app.callback(
        Output("indicator-settings", "figure"), [Input("url", "pathname")]
    )
    def settings_indicators(n):
        league_id = app.config["ROSTER_DATA"]["league_id"]
        _settings = Settings.get_by_league_id(league_id)

        fig = go.Figure()

        fig.add_trace(
            go.Indicator(
                mode="number",
                value=_settings.salary_cap,
                number={"prefix": "$"},
                title={"text": "Salary Cap"},
                domain={"row": 0, "column": 0},
            )
        )

        fig.add_trace(
            go.Indicator(
                mode="number",
                value=_settings.roster_min,
                # number={"prefix": "$"},
                title={"text": "Roster Min"},
                domain={"row": 0, "column": 1},
            )
        )

        fig.add_trace(
            go.Indicator(
                mode="number",
                value=_settings.roster_max,
                # number={"prefix": "$"},
                title={"text": "Roster Max"},
                domain={"row": 0, "column": 2},
            )
        )

        fig.update_layout(
            grid={"rows": 1, "columns": 3, "pattern": "independent"},
            margin=dict(l=20, r=20, t=0, b=0),
            height=150,
            width=700,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )

        return fig

    @dash_app.callback(
        [
            Output("roster-dynamic-dropdown", "options"),
            Output("roster-dynamic-dropdown", "value"),
        ],
        Input("roster-dynamic-dropdown", "search_value"),
    )
    def update_options(search_value):

        roster_df = Rosters.get_all_rosters_df()
        roster_df = roster_df.sort_values(by=["display_name"], ascending=True)
        roster_options = []
        for index, row in roster_df.iterrows():
            roster_options.append(
                {"label": row["display_name"], "value": row["roster_id"]}
            )

        return roster_options, roster_options[0]["value"]

    @dash_app.callback(
        [Output("single-roster-data", "data"), Output("single-roster-data", "columns")],
        [Input("roster-dynamic-dropdown", "value")],
    )
    def get_single_roster_data_callback(value):
        if value:
            print("TRIGGERED: ", value, flush=True)
            player_df = Players.get_all_players_df()
            player_df = player_df[player_df["roster_id"] == int(value)]
            player_df = player_df.sort_values(
                by=["roster_id", "position", "war"], ascending=[True, True, False]
            )
            keepcols = [
                "player",
                "position",
                "team",
                "salary",
                "war",
                "value",
                "injured_reserve",
            ]
            player_df = player_df[keepcols]

            dt_col_param = []
            for col in player_df.columns:
                dt_col_param.append(
                    {
                        "name": str(col).upper().replace("INJURED_RESERVE", "IR"),
                        "id": str(col),
                    }
                )
            player_dict = player_df.to_dict(orient="records")

            return player_dict, dt_col_param

        else:
            return None, None

    @dash_app.callback(
        Output("indicator-rosters", "figure"),
        [Input("roster-dynamic-dropdown", "value")],
    )
    def roster_indicators(value):
        player_df = Players.get_all_players_df()
        player_df = player_df[player_df["roster_id"] == int(value)]
        player_df["salary"] = player_df["salary"].astype(int)
        salary_total = player_df["salary"].sum()

        active_df = player_df[player_df["injured_reserve"] != True]
        active_roster = len(active_df)

        # Get total WAR for top 10 players
        team_top_war = war.calculate_starter_war(player_df)

        fig = go.Figure()

        fig.add_trace(
            go.Indicator(
                mode="number",
                value=salary_total,
                number={"prefix": "$"},
                title={"text": "Salary Spend"},
                domain={"row": 0, "column": 0},
            )
        )

        fig.add_trace(
            go.Indicator(
                mode="number",
                value=active_roster,
                # number={"prefix": "$"},
                title={"text": "Roster Size"},
                domain={"row": 0, "column": 1},
            )
        )

        fig.add_trace(
            go.Indicator(
                mode="number",
                value=team_top_war,
                # number={"prefix": "$"},
                title={"text": "Top 10 WAR"},
                domain={"row": 0, "column": 2},
            )
        )

        fig.update_layout(
            grid={"rows": 1, "columns": 3, "pattern": "independent"},
            margin=dict(l=20, r=20, t=0, b=0),
            height=150,
            width=700,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )

        return fig

    @dash_app.callback(
        Output("left-dynamic-dropdown", "options"),
        Input("left-dynamic-dropdown", "search_value"),
    )
    def left_update_options(search_value):

        roster_df = Rosters.get_all_rosters_df()
        roster_df = roster_df.sort_values(by=["display_name"], ascending=True)
        roster_options = []
        for index, row in roster_df.iterrows():
            roster_options.append(
                {"label": row["display_name"], "value": row["roster_id"]}
            )

        return roster_options

    @dash_app.callback(
        [Output("left-roster-data", "data"), Output("left-roster-data", "columns")],
        [Input("left-dynamic-dropdown", "value")],
    )
    def get_left_roster_data_callback(value):
        if value:
            print("TRIGGERED: ", value, flush=True)
            player_df = Players.get_all_players_df()
            player_df = player_df[player_df["roster_id"] == int(value)]
            player_df = player_df.sort_values(
                by=["roster_id", "position", "war"], ascending=[True, True, False]
            )
            keepcols = [
                "player",
                "position",
                "team",
                "salary",
                "war",
                "value",
                "injured_reserve",
            ]
            player_df = player_df[keepcols]

            dt_col_param = []
            for col in player_df.columns:
                dt_col_param.append(
                    {
                        "name": str(col).upper().replace("INJURED_RESERVE", "IR"),
                        "id": str(col),
                    }
                )
            player_dict = player_df.to_dict(orient="records")

            return player_dict, dt_col_param

        else:
            return None, None

    @dash_app.callback(
        Output("right-dynamic-dropdown", "options"),
        Input("right-dynamic-dropdown", "search_value"),
    )
    def right_options(search_value):

        roster_df = Rosters.get_all_rosters_df()
        roster_df = roster_df.sort_values(by=["display_name"], ascending=True)
        roster_options = []
        for index, row in roster_df.iterrows():
            roster_options.append(
                {"label": row["display_name"], "value": row["roster_id"]}
            )

        return roster_options

    @dash_app.callback(
        [Output("right-roster-data", "data"), Output("right-roster-data", "columns")],
        [Input("right-dynamic-dropdown", "value")],
    )
    def get_right_roster_data_callback(value):
        if value:
            print("TRIGGERED: ", value, flush=True)
            player_df = Players.get_all_players_df()
            player_df = player_df[player_df["roster_id"] == int(value)]
            player_df = player_df.sort_values(
                by=["roster_id", "position", "war"], ascending=[True, True, False]
            )
            keepcols = [
                "player",
                "position",
                "team",
                "salary",
                "war",
                "value",
                "injured_reserve",
            ]
            player_df = player_df[keepcols]

            dt_col_param = []
            for col in player_df.columns:
                dt_col_param.append(
                    {
                        "name": str(col).upper().replace("INJURED_RESERVE", "IR"),
                        "id": str(col),
                    }
                )
            player_dict = player_df.to_dict(orient="records")

            return player_dict, dt_col_param

        else:
            return None, None

    return dash_app
