from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

from dash_bootstrap_components import Row as R, Col as C

import geopandas as gpd
from urllib.request import urlopen
import json
import shapely.geometry
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import pandas as pd
import bisect

pio.renderers.default="chrome"
mapbox_access_token = "pk.eyJ1IjoidmFydW52YW5raW5lbmkiLCJhIjoiY2xiMnFtYmphMDcwcTNvcWVxYjA0aTZvOSJ9.-olc2j26zfM8Z51fjKpqzw"

TRAFFIC_BINS = [0,1000,5000,10000, np.inf]

def getColorForVolume(volume):
    colors = px.colors.sequential.YlOrBr[-7:]
    volume = volume.fillna(volume.median())
    volume = volume.round(0).astype(int)
    bins = TRAFFIC_BINS.copy()
    lz = len(bins)- 1
    lc = len(colors)
    colors = [colors[int(i * lc / lz)] for i in range(0,lz)]
    return volume, pd.cut(volume, bins, labels=colors), colors

def loadBaseRoads():
    #roads = pd.read_hdf("geojsons/maps.h5", "roads")
    roads = pd.read_csv("data/sorted_roads.csv")
    roads["volume"], roads["vol_color"], colors = getColorForVolume(roads.volume)
    return(roads, colors)

def loadChargingStationData():
    return(pd.read_csv('data/EV_data_capacity.csv'))

GLOBAL_ROADS_DB_BASE, GLOBAL_ROADS_COLORS = loadBaseRoads()
GLOBAL_ROADS_DB = GLOBAL_ROADS_DB_BASE.copy()

def trafficVolumeStrings():
    while(1):
        strings = []
        for i,v in enumerate(TRAFFIC_BINS[:-2]):
            strings.append(f">={v} to <{TRAFFIC_BINS[i+1]}")
        strings.append(f">={TRAFFIC_BINS[-2]}")
        for s in strings:
            yield s

trafficVolumeGen = trafficVolumeStrings()

def topRowElements():
    title_elem = html.Div(
        "EV Charging Station Optimization",
        style={"width": "100%", "height": "100%", "font-weight": "bold", "font-size": "48px"}
    )

    highways = dbc.Checklist(
        options=[
            {"label": "Primary HW", "value": "primary"},
            {"label": "Secondary HW", "value": "secondary"},
            {"label": "Others", "value": "others"},
        ],
        value=["primary","secondary", "others"],
        id="checklist-highways",
    )

    extra_elem = C([
        highways
    ])

    return [C(title_elem),C(extra_elem)]
#


def rightInfoPlots():
    top_plot = html.Div(
        "Top Plot",
        style={"width": "440", "height": "440","font-weight": "bold", "font-size": "48px"}
    )
    bot_plot = html.Div(
        "Bot Plot",
        style={"width": "440", "height": "440","font-weight": "bold", "font-size": "48px"},
        id = "bot-plot"
    )
    return [R(top_plot),R(bot_plot)]

def bottomRowElements():
    left_col = html.Div(
        "Legend and Filters",
        style = {"width": "240", "height": "880", "font-weight": "bold", "font-size": "48px"}
    )
    main_map = dcc.Graph(id="graph", figure=mainGraph())
    right_plots = rightInfoPlots()
    return [C(main_map),C(right_plots)]#C(left_col)


def getRoadGO(roads, color):
    rdf = roads[roads.vol_color == color]
    #rpt = [[i]*v.flatten().shape[0] for i,v in enumerate(rdf.lat.values)]
    #rpt = np.array([i for row in rpt for i in row])
    #cd = rdf.iloc[rpt,:]
    rdf = rdf.sort_values(["road num","index"])
    return go.Scattermapbox(
        lat=rdf.lat,
        lon=rdf.lon,
        mode="lines",
        line=dict(width=1, color=rdf.vol_color.iloc[0]),
        hovertemplate= '<b>Traffic Volume: '+ rdf["volume"].astype(str) +
        '<br>Highway Num: '+ rdf["name"] +
        '<br>Road Length: ' + rdf["length_km"].astype(str) +
        '<extra></extra>',
        name=next(trafficVolumeGen),
        hoverinfo="none",
        legendgroup = "Roads",
        legendgrouptitle = {"text": "Traffic Volume"},
    )

def mainGraph():
    fig = createBaseFig()
    fig = displayRoads(fig)
    fig = displayChargingSt(fig)
    return fig

def createBaseFig():
    fig = go.Figure()
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0), width=1400, height=800,
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(lat=37.8283, lon=-99.5795),
            pitch=0,
            zoom=3.9
        ),
        legend_x=0
    )
    return fig

def displayRoads(fig):
    global GLOBAL_ROADS_DB
    roads = GLOBAL_ROADS_DB
    for c in GLOBAL_ROADS_COLORS:
        fig.add_trace(getRoadGO(roads, c))
    return fig

def displayChargingSt(fig):
    stats = loadChargingStationData()
    fig.add_trace(
        go.Scattermapbox(
            lat=np.concatenate([i.flatten() for i in stats.Latitude.values]),
            lon=np.concatenate([i.flatten() for i in stats.Longitude.values]),
            mode="markers",
            marker = dict(symbol = 'circle', size = 5, color = '#1f66e5'),
            opacity = 0.7 ,
            hovertemplate = stats['Station Name']+'<br>'+ 'Capacity: '+stats['capacity'] +'<br>'+
                            'Port Types: ' + stats['EV Connector Types'] + '<br>' +
                            'Number of Ports: ' + stats['ports'].astype(int).astype(str) +
                            '<extra></extra>',
            hoverinfo="none",
            name="EV Station",
            legendgroup="Stations",
            legendgrouptitle={"text": "EV Stations"},
        )
    )
    return fig


def mainChildren():
    return [
        R(topRowElements(), id = "top_row"),
        R(bottomRowElements(), id = "bot_row")
    ]

def mainLayout():
    return html.Div(mainChildren(), id="main", style={"width": "100%", "height": "100%"})

app = Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
app.layout = mainLayout()

@app.callback(
    Output("graph", "figure"),
    Input("checklist-highways", "value"),
)
def filterPrimaryHighways(values):
    global GLOBAL_ROADS_DB
    roads = GLOBAL_ROADS_DB_BASE.copy()
    if "primary" not in values:
        roads = roads[roads["type"]!="Major Highway"]
    if "secondary" not in values:
        roads = roads[roads["type"] != "Secondary Highway"]
    if "others" not in values:
        roads = roads[(roads["type"] == "Major Highway") | (roads["type"] == "Secondary Highway")]
    GLOBAL_ROADS_DB = roads.copy()
    return mainGraph()

@app.callback(
    Output("bot-plot", "children"),
    Input("graph", "hoverData"),
)
def display_hover(hoverData):
    print(hoverData)
    return "Bar Plot"

app.run_server(debug=True)
