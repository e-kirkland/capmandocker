from dash import html, dcc, dash_table


layout = html.Div(
    [
        dcc.Store(id="diff-store"),
        html.H1("All Players"),
        html.P(
            "Make changes and save below. NOTE: Saved changes are stored in database."
        ),
        html.Div(id="data-diff"),
        html.Button("Save Changes", id="button"),
        dcc.Interval(id="interval_component", interval=2000),
        dash_table.DataTable(
            id="table-data-diff",
            columns=[],
            data=[],
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            style_header={"backgroundColor": "rgb(30, 30, 30)", "color": "white"},
            style_data={"backgroundColor": "rgb(50, 50, 50)", "color": "white"},
        ),
    ],
    style={"marginLeft": "20px", "marginRight": "20px"},
)
