import dash_bootstrap_components as dbc
from dash import Dash
from dash import html

row =  dbc.Container(
    [
        dbc.Row(dbc.Col(html.Div("A single column"))),
        dbc.Row(
            [
                dbc.Col(html.Div("One of three columns")),
                dbc.Col(html.Div("One of three columns")),
                dbc.Col(html.Div("One of three columns")),
            ]
        ),
    ]
)

app = Dash(__name__)#, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app.layout = html.Div([dbc.Card(dbc.CardBody([
#     topRowElements(),
#     #bottomRowElements()
# ]))], style={"width": "100%", "height": "100%"})
app.layout = row
app.run_server(debug=True)