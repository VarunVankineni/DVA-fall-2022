import pandas as pd
import re
import bisect
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
        "type",
        "name",
        "length_km",
        "toll",
        "geometry"
    ]

    roads = roads[
        (roads["continent"]=="North America") &
        (roads["sov_a3"]=="USA") &
        (roads["featurecla"]=="Road")
    ]
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
                d = cdist(v.astype(np.float64),p).min(axis=0)
        except:
            print("hehe")
        return d

    
    dists = roads.apply(lambda x: distCross(x, vol), axis=1)
    dists = np.vstack(dists)
    roads["arg_min"] = dists.argmin(axis=1)
    roads["arg_min"] = np.where(dists.min(axis=1)>2, np.nan, roads["arg_min"])
    roads["volume"] = roads["arg_min"].apply(lambda x: np.nan if np.isnan(x) else volx["dailytraffic"].loc[x])
    roads["lat"] = roads["lat"].apply(lambda x: np.concatenate(x).flatten())
    roads["lon"] = roads["lon"].apply(lambda x: np.concatenate(x).flatten())
    with pd.HDFStore('geojsons/maps.h5') as store:
        store['roads'] = roads  # save it

    return 0

def add_cap():
    stats = pd.read_csv('data/EVStations_data_cleaned.csv')
    stats["capacity"] = 0
    stats['capacity'] = np.where(~stats['EV Level1 EVSE Num'].isna(), 1.2 * stats['EV Level1 EVSE Num'], stats['capacity'])
    stats['capacity'] = np.where(~stats['EV Level2 EVSE Num'].isna(),  7.6* stats['EV Level2 EVSE Num'] + stats['capacity'], stats['capacity'])
    stats['capacity'] = np.where(~stats['EV DC Fast Count'].isna(),  50* stats['EV DC Fast Count'] + stats['capacity'], stats['capacity'])
    stats['capacity'] = ((stats['capacity'].astype(int)).astype(str)) + 'kW'
    stats['EV Connector Types'] = stats['EV Connector Types'].str.replace(' ', ', ')
    stats['ports'] = stats['EV Level1 EVSE Num'] + stats['EV Level2 EVSE Num'] + stats['EV DC Fast Count']
    stats['ports'] = np.where(stats['ports'].isna(), 0, stats['ports'])
    df = pd.read_csv('data/sorted_roads.csv')
    stats['distance'] = stats.apply(lambda x : dist(x, df), axis = 1)
    stats.to_csv('data/EV_data_capacity.csv', index = False)

def get_roads():
    df = pd.read_hdf("geojsons/maps.h5", "roads")
    df = pd.concat(df.apply(data_add, axis = 1).tolist())
    df = df.sort_values(['lat', 'lon'], ascending=[True, True])
    df.to_csv('data/sorted_roads.csv', index = False)

def data_add(r1):
    #print(r1.index)
    lat1 = r1['lat']
    lon1 = r1['lon']
    new_df = pd.DataFrame(data = lat1, columns = ['lat'] )
    new_df['lon'] = lon1.tolist()
    new_df['road num'] = r1.name
    for c in r1.index.tolist():
        if c not in ['lat', 'lon']:
            new_df[c] = r1[c]
    
    return new_df.reset_index()


def dist(r, df):
    
    a = bisect.bisect_left(df['lat'].tolist(), r['Latitude']) 
    b = df['lat'].iloc[a] + 0.02
    mx = bisect.bisect_left(df['lat'].tolist(), b) 
    c = df['lat'].iloc[a] - 0.02
    mn = bisect.bisect_left(df['lat'].tolist(), b) 
    df2 = df.iloc[mn:mx+1,:][['lat','lon']] 
    Y = cdist(r[['Latitude', 'Longitude']].values.reshape(1,-1).astype(np.float64), df2.values, 'euclidean')
    armin = Y.argmin(axis = 1)
    i = df2.iloc[armin,:]
    i["min dis"] = Y.min(axis = 1)
    return i


add_cap()
roadsIntoFastJson()

get_roads()






