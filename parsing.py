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
    stats.to_csv('data/EV_data_capacity.csv', index = False)

def get_roads():
    df = pd.read_hdf("geojsons/maps.h5", "roads")
    x = 0
    rpt = [[i]*v.flatten().shape[0] for i,v in enumerate(df.lat.values)]
    rpt = np.array([i for row in rpt for i in row])
    lat=[i.flatten() for i in df.lat.values]
    lon=[i.flatten() for i in df.lon.values]
    c = np.concatenate(lat)
    d = np.concatenate(lon)
    #a = [i for x in range(len(lat)) for i in lat[x]]
    #b = [i for x in range(len(lon)) for i in lon[x]]
    #lat_lon = [[i,j] for i in c for j in d ]
    #cd['lat'] = cd['lat'].apply(lambda x : x.flatten())
    my_df=pd.DataFrame(data=c,columns=['LAT'])
    my_df['LON'] = d.tolist()

    my_df = my_df.sort_values(['LAT', 'LON'], ascending=[True, False])
    my_df.to_csv('data/sorted_roads.csv', index = False)

add_cap()
roadsIntoFastJson()

get_roads()






