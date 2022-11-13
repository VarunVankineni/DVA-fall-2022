from dash import Dash, dcc, html, Input, Output
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

#with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    #counties = json.load(response)

#zipfile = "geojsons/ne_10m_roads.zip"
#roads = gpd.read_file(zipfile)

def loadRoads():
    return(pd.read_hdf("geojsons/maps.h5","roads"))

def getColorForVolume(volume):
    colors = px.colors.sequential.YlOrBr
    volume = volume.fillna(volume.median())
    #logVol = volume.fillna(roads.volume.median()).apply(np.log10)
    lz = 5
    lc = len(colors)
    colors = [colors[int(i * lc / lz)] for i in range(1,lz)]
    return pd.qcut(volume, lz, labels=colors, duplicates="drop")

def getRoadGO(rdf):
    return go.Scattergeo(
        locationmode='USA-states',
        lat=np.concatenate([i.flatten() for i in rdf.lat.values]),
        lon=np.concatenate([i.flatten() for i in rdf.lon.values]),
        mode="lines",
        line=dict(width=1, color=rdf.vol_color.iloc[0]),
    )

def display_roads():
    roads = loadRoads()
    roads["vol_color"] = getColorForVolume(roads.volume)

    fig = go.Figure()
    colors = roads.vol_color.value_counts().index.tolist()
    for c in colors:
        rdf = roads[roads.vol_color == c]
        fig.add_trace(getRoadGO(rdf))

    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), width=1400, height=800)

    fig.update_geos(visible=True, scope="usa")
    return fig

app = Dash(__name__)
app.layout = html.Div([
    dcc.Graph(id="graph", figure=display_roads())
], style = {"width" : "100%", "height" : "100%"})
app.run_server(debug=True)