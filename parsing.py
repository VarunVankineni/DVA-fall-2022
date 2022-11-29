import pandas as pd
import re
import geopandas  as gpd
from shapely.geometry.linestring import LineString
from shapely.geometry.multilinestring import MultiLineString
import numpy as np
from scipy.spatial.distance import cdist

def roadsIntoFastJson():
    zipfile = "geojsons/ne_10m_roads.zip"
    roads = gpd.read_file(zipfile)
    volx = pd.read_csv("data/2020.csv")
    sel_columns = [
        "scalerank",
        "featurecla",
        "type",
        "name","namealt","namealtt",
        "length_km",
        "toll",
        "ne_part",
        "label", "label2",
        "expressway",
        "level",
        "min_zoom",
        "min_label",
        "geometry"
    ]

    roads = roads[roads["continent"]=="North America"]
    roads = roads[sel_columns]


    def getxy(x):
        if isinstance(x, LineString):
            linestrings = [x]
        elif isinstance(x, MultiLineString):
            linestrings = x.geoms
        out = {}
        out["lat"] = np.array([np.append(ls.xy[1],None) for ls in linestrings])
        #out["lat"] = out["lat"].flatten()
        out["lon"] = np.array([np.append(ls.xy[0],None) for ls in linestrings])
        #out["lon"] = out["lon"].flatten()
        return pd.Series(out)

    roads[["lat", "lon"]] = roads["geometry"].apply(getxy)
    roads.drop("geometry", axis=1, inplace=True)
    roads = pd.DataFrame(roads)

    vol = volx[volx["month"]==1]
    vol = vol[["lat", "long"]].values
    vol[:,1] = -vol[:,1]

    def distCross(x, p):
        lats = np.concatenate(x["lat"])
        lats = lats[lats != None]
        lons = np.concatenate(x["lon"])
        lons = lons[lons != None]

        v = np.vstack([lats,lons]).T
        try:
            if v.shape[0] == 0:
                d = np.full((p.shape[0],1),np.nan)
            else:
                d = cdist(v,p).min(axis=0)
        except:
            print("hehe")
        return d

    
    dists = roads.apply(lambda x: distCross(x, vol), axis=1)
    dists = np.vstack(dists)
    roads["arg_min"] = dists.argmin(axis=1)
    roads["arg_min"] = np.where(dists.min(axis=1)>2, np.nan, roads["arg_min"])
    roads["volume"] = roads["arg_min"].apply(lambda x: np.nan if np.isnan(x) else volx["dailytraffic"].loc[x])
    store = pd.HDFStore('geojsons/maps.h5')
    store['roads'] = roads  # save it
    
    return 0

def add_cap():
        stats = pd.read_csv('EVStations_data_cleaned.csv')
        stats["b"] = 0
        stats['b'] = np.where(~stats['EV Level1 EVSE Num'].isna(), 1.2 * stats['EV Level1 EVSE Num'], stats['b']) 
        stats['b'] = np.where(~stats['EV Level2 EVSE Num'].isna(),  7.6* stats['EV Level2 EVSE Num'] + stats['b'], stats['b']) 
        stats['b'] = np.where(~stats['EV DC Fast Count'].isna(),  50* stats['EV DC Fast Count'] + stats['b'], stats['b']) 
        stats['b'] = ((stats['b'].astype(int)).astype(str)) + 'kW'
        stats['EV Connector Types'] = stats['EV Connector Types'].str.replace(' ', ', ')
        stats.to_csv('EV_data_capacity.csv', index = False)


add_cap()
#roadsIntoFastJson()






