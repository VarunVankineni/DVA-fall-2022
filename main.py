from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from dash_bootstrap_components import Row as R, Col as C
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import pandas as pd

class TrafficData:
    def __init__(
            self,
            roads_data_path = "data/sorted_roads.csv",
            charging_station_data_path="data/EV_data_capacity.csv",
            new_station_data_path="data/new_cap.csv"
    ):
        self.roads_data_path = roads_data_path
        self.roads_data = pd.read_csv(roads_data_path)
        self.charging_station_data_path = charging_station_data_path
        self.new_station_data_path = new_station_data_path
        self.charging_station_data = pd.read_csv(charging_station_data_path)
        self.new_station_data = pd.read_csv(new_station_data_path)

        self.color_palette = px.colors.sequential.YlOrBr[-7:]
        self.traffic_bins = [0,1000,5000,10000, np.inf]
        self.roads_data["volume"], self.roads_data["vol_color"] = self._getColorForVolume()
        self.roads_data_modified = self.roads_data.copy()
        
    def _getColorForVolume(self):
        volume = self.roads_data.volume
        volume = volume.fillna(volume.median())
        volume = volume.round(0).astype(int)
        lz = len(self.traffic_bins)- 1
        lc = len(self.color_palette)
        self.colors = [self.color_palette[int(i * lc / lz)] for i in range(0,lz)]
        return volume, pd.cut(volume, self.traffic_bins, labels=self.colors)

    def trafficVolumeStrings(self):
        strings = []
        for i, v in enumerate(self.traffic_bins[:-2]):
            strings.append(f">={v} to <{self.traffic_bins[i + 1]}")
        strings.append(f">={self.traffic_bins[-2]}")
        return strings
    def __call__(self):
        return self.roads_data_modified, self.colors



class Figure:
    def __init__(self, traffic_data):
        self.traffic_data = traffic_data
        self.mapbox_access_token = "pk.eyJ1IjoidmFydW52YW5raW5lbmkiLCJhIjoiY2xiMnFtYmphMDcwcTNvcWVxYjA0aTZvOSJ9.-olc2j26zfM8Z51fjKpqzw"
    def createBaseFig(self):
        fig = go.Figure()
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),# width="100%", height="100%",
            mapbox=dict(
                accesstoken=self.mapbox_access_token,
                bearing=0,
                center=dict(lat=37.8283, lon=-99.5795),
                pitch=0,
                zoom=3.75
            ),
            legend_x=0
        )
        return fig
    def getRoadGO(self, roads, color, string):
        rdf = roads[roads.vol_color == color]
        rdf = rdf.sort_values(["road num","index"])
        rdf["hover_string"] = rdf.apply(lambda x: f"""<b>Traffic Volume: {x["volume"]}
<br>Gmap Link: https://maps.google.com/?q={x['lat']},{x['lon']}
<br>Highway Num: {x["name"]}
<br>Road Length: {x["length_km"]}<extra></extra>
"""
        , axis=1)
        return go.Scattermapbox(
            lat=rdf.lat,
            lon=rdf.lon,
            mode="lines",
            line=dict(width=1, color=rdf.vol_color.iloc[0]),
            hovertemplate= rdf["hover_string"],
            customdata=rdf,
            name=string,
            hoverinfo="none",
            legendgroup = "Roads",
            legendgrouptitle = {"text": "Traffic Volume"},
        )
    def trafficVolumes(self, fig):
        roads = self.traffic_data.roads_data_modified
        strings = self.traffic_data.trafficVolumeStrings()
        for si, c in enumerate(self.traffic_data.colors):
            fig.add_trace(self.getRoadGO(roads, c, strings[si]))
        return fig
    def currentStations(self, fig):
        def safeconvert(x):
            try:
                return x.astype(str)
            except:
                return x
        stats = self.traffic_data.charging_station_data
        stats = stats.apply(lambda x: safeconvert(x))

        fig.add_trace(
            go.Scattermapbox(
                lat=stats.Latitude,
                lon=stats.Longitude,
                mode="markers",
                marker=dict(symbol='circle', size=5, color='#0e9901'),
                opacity=0.7,
                hovertemplate=stats['Station Name'] + '<br>' +
                              'Address: ' + stats['Street Address'] + ", " +stats['City'] + ", " +stats['State']+ ", "+ stats['ZIP'] + '<br>' +
                              'Gmap Link: ' + 'https://maps.google.com/?q=' + stats['Latitude'] +","+ stats['Longitude']  + '<br>' +
                              'Capacity: '+stats['capacity'] +'<br>'+
                              'Open' + ' : ' + stats['Access Days Time'] + '<br>' +
                              'Port Types: ' + stats['EV Connector Types'] + '<br>' +
                              'Number of Ports: ' + stats['ports'] +
                              '<extra></extra>',
                hoverinfo="none",
                customdata=stats,
                name="Existing Station",
                legendgroup="Stations",
                legendgrouptitle={"text": "EV Stations"},
            )
        )
        return fig

    def newStations(self, fig):
        stats = traffic_data.new_station_data
        stats = stats[stats["capacity"] > 0]
        stats["hover_string"] = stats.apply(lambda x: f"""<br>Road Number for Proposed Station: {x["road num"]}
<br>Proposed Station Num: {x["candidate index"]}
<br>Capacity: {x["capacity"]}
<br>Gmap Link: https://maps.google.com/?q={x['lat']},{x['lon']}
<extra></extra>
"""
        , axis=1)

        fig.add_trace(
            go.Scattermapbox(
                lat=stats.lat,
                lon=stats.lon,
                mode="markers",
                marker=dict(symbol='circle', size=5, color='#FF0000'),
                opacity=0.7,
                hovertemplate=stats["hover_string"],
                hoverinfo="none",
                name="Proposed Station",
                customdata=stats,
                legendgroup="Stations",
                legendgrouptitle={"text": "EV Stations"},
            )
        )
        return fig
    def __call__(self):
        fig = self.createBaseFig()
        fig = self.trafficVolumes(fig)
        fig = self.currentStations(fig)
        fig = self.newStations(fig)
        return fig


class Layout:
    def __init__(self, traffic_data):
        self.traffic_data = traffic_data
        self.figure = Figure(traffic_data)
        self._mainLayout()

    def _mainLayout(self):
        self.main_layout = html.Div([
            dbc.Card(dbc.CardBody(
                self._mainChildren()
            ))],
            id="main",
            style={"width": "100vw", "height": "100vh", "border": "2vw solid white"}
        )

    def _mainChildren(self):
        return [
            R([dbc.Card(dbc.CardBody(self._topRowElements()))], id="top_row", align='center'),
            html.Br(),
            R([dbc.Card(dbc.CardBody(self._bottomRowElements()))], id="bot_row", align='center')
        ]

    def _topRowElements(self):
        title_elem = html.Div(
            "EV Charging Stations: Current Capacity, Proposed New Station and EV Traffic Flow (2022)",
            style={"font-weight": "bold", "font-size": "3vh", 'textAlign': 'center', "height": "4vh"}
        )
        return [C(title_elem)]

    def _bottomRowElements(self):
        main_map = dcc.Graph(id="graph", figure=self.figure(), style={"height": "70vh"})
        return [C(main_map)]

pio.renderers.default="chrome"
traffic_data = TrafficData()
app = Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
app.layout = Layout(traffic_data).main_layout
app.run_server(host='127.0.0.1', port=8000, debug=False)
