from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

from  dash_bootstrap_components import Row as R, Col as C

import geopandas as gpd
from urllib.request import urlopen
import json
import shapely.geometry
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import pandas as pd
pio.renderers.default="chrome"

def topRowElements():
    title_elem = html.Div(
        "EV Charging Station Optimization",
        style={"width": "100%", "height": "100%", "font-weight": "bold", "font-size": "48px"}
    )
    extra_elem = html.Div(
        "Unused Element",
        style={"width": "100%", "height": "100%", "font-weight": "bold", "font-size": "48px"}
    )
    return [
        C(title_elem),
        C(extra_elem)
    ]
    #, id="title",style={'display': 'inline-block'}

def rightInfoPlots():
    top_plot = html.Div(
        "Top Plot",
        style={"width": "440", "height": "440","font-weight": "bold", "font-size": "48px"}
    )

    bot_plot = html.Div(
        "Bot Plot",
        style={"width": "440", "height": "440","font-weight": "bold", "font-size": "48px"}
    )

    return [
        R(top_plot),
        R(bot_plot)
    ]

def bottomRowElements():
    left_col = html.Div(
        "Legend and Filters",
        style = {"width": "240", "height": "880", "font-weight": "bold", "font-size": "48px"}
    )
    main_map = dcc.Graph(id="graph", figure=displayRoads())
    right_plots = rightInfoPlots()
    return [ C(left_col),
        C(main_map),
        C(right_plots)
    ]#, id="bottom_row_elements",style={'display': 'inline-block'}

def main():
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = html.Div([
        R(topRowElements()),
        R(bottomRowElements())
    ], style={"width": "100%", "height": "100%"})

    app.run_server(debug=True)

def loadRoads():
    return(pd.read_hdf("geojsons/maps.h5","roads"))

def loadChargingStationData():
    return(pd.read_csv('data/EV_data_capacity.csv'))


def getColorForVolume(volume):
    colors = px.colors.sequential.YlOrBr
    volume = volume.fillna(volume.median())
    volume = volume.round(0).astype(int)
    lz = 5
    lc = len(colors)
    colors = [colors[int(i * lc / lz)] for i in range(0,lz)]
    return volume,pd.qcut(volume, lz, labels=colors, duplicates="drop"), colors

def getRoadGO(roads, color):
    rdf = roads[roads.vol_color == color]
    colmap = {v:k for k,v in enumerate(rdf.columns)}
    rpt = [[i]*v.flatten().shape[0] for i,v in enumerate(rdf.lat.values)]
    rpt = np.array([i for row in rpt for i in row])
    cd = rdf.iloc[rpt,:]
    return go.Scattergeo(
        locationmode='USA-states',
        lat=np.concatenate([i.flatten() for i in rdf.lat.values]),
        lon=np.concatenate([i.flatten() for i in rdf.lon.values]),
        mode="lines",
        line=dict(width=1, color=rdf.vol_color.iloc[0]),
        hovertemplate= '<b>Traffic Volume: '+ cd["volume"].astype(str) +
        '<br>Highway Num: '+ cd["name"] +
        '<br>Road Length: ' + cd["length_km"].astype(str) +
        '<extra></extra>',
        name=f">{rdf.volume.astype(int).min():,} to <{rdf.volume.astype(int).max():,}",
        hoverinfo="none",
    )

def displayRoads():
    roads = loadRoads()
    roads["volume"],roads["vol_color"], colors = getColorForVolume(roads.volume)
    fig = go.Figure()
    for c in colors:
        fig.add_trace( getRoadGO(roads, c) )
    fig = displayChargingSt(fig)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=20), width=1400, height=800)
    fig.update_geos(visible=True, scope="usa")
    return fig

def displayChargingSt(fig):

    stats = loadChargingStationData()
    fig.add_trace(
    go.Scattergeo(
        locationmode='USA-states',
        lat=np.concatenate([i.flatten() for i in stats.Latitude.values]),
        lon=np.concatenate([i.flatten() for i in stats.Longitude.values]),
        mode="markers",
        marker = dict(symbol = 'circle', size = 5, color = '#1f66e5', line = dict(width = 0.5, color = '#1347a4')),
        opacity = 0.7 ,
        #text = stats['Station Name'],
        #text = "Hey",
        hovertemplate = stats['Station Name']+'<br>'+stats['City']+'<br>'+stats['Access Days Time']+'<br>'+
        'Capacity: '+stats['b'] +'<br>'+ 'Ports : ' + stats['EV Connector Types'] + '<extra></extra>',
        #marker_color = '#55aaaa',
        #name=f">{stats.volume.astype(int).min():,} to <{stats.volume.astype(int).max():,}",
        hoverinfo="none"

    )
    )
    return fig





main()
