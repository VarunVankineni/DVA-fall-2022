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


def main():
    app = Dash(__name__)
    app.layout = html.Div([
        html.Div([html.Center("EV Charging Station Optimization")],id="title",
                 style={"width": "100%", "height": "10%", "font-weight": "bold", "font-size": "48px"}),
        dcc.Graph(id="graph", figure=displayRoads())
    ], style={"width": "100%", "height": "90%"})
    app.run_server(debug=True)

def loadRoads():
    return(pd.read_hdf("maps.h5","roads"))

def loadChargingStationData():
    return(pd.read_csv('EV_data_capacity.csv'))
    

def getColorForVolume(volume):
    colors = px.colors.sequential.YlOrBr
    volume = volume.fillna(volume.median())
    #logVol = volume.fillna(roads.volume.median()).apply(np.log10)
    lz = 5
    lc = len(colors)
    colors = [colors[int(i * lc / lz)] for i in range(1,lz)]
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
        customdata=cd.values,
        hovertemplate='<b>Traffic Volume: %{customdata['+str(colmap["volume"])+']:,}' +
        '<br> Highway Num: %{customdata['+str(colmap["name"])+']:,}',
        name=f">{rdf.volume.astype(int).min():,} to <{rdf.volume.astype(int).max():,}",
        hoverinfo="none",
    )

def displayRoads():
    roads = loadRoads()
    roads["volume"],roads["vol_color"], colors = getColorForVolume(roads.volume)
    fig = go.Figure()
    for c in colors:
        fig.add_trace(getRoadGO(roads, c))
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
