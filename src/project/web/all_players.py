from dash import html, dcc, dash_table



layout = html.Div([
    dcc.Store(id="diff-store"),
    html.P("Changes to DataTable"),
    html.Div(id="data-diff"),
    html.Button("Save Changes", id="button"),
    dcc.Interval(id="interval_component", interval=2000),
    dash_table.DataTable(
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
])
