from pickletools import long1
import numpy as np
import pandas as pd
import os
import glob
from datetime import datetime
from getdata import MAXTIMEDIFF 
from ztmclasses import Position
from geopy import distance

REASONABLE_SPEED_INFINITY = 100
SPEED_LIMIT = 50
MAX_TIME_ELAPSED = 60


@np.vectorize
def calc_dist(lon, lat, dlon, dlat):
    lon2 = lon + dlon
    lat2 = lat + dlat
    
    return distance.distance((lat, lon), (lat2, lon2)).m


def calc_speed(dist, time):
    return dist/time * 3.6


def sle_line(line, path='.', save=False):
    path = f"{path}/DATA/LIVE/LINES/{line}.csv"
    
    df = pd.read_csv(path).drop_duplicates(subset=['VehicleNumber', 'Time'])
    
    all = 0
    
    vehicles = df['VehicleNumber'].unique().tolist()
    lon1 = []
    lat1 = []
    lons = []
    lats = []
    speeds = []
    dists = []
    times = []
    
    for vehicle in vehicles:
        cur_df = df[df['VehicleNumber'] == vehicle].copy()
        
        cur_df['Time'] = pd.to_datetime(cur_df['Time'])
        
        lon = cur_df['Lon'].to_numpy()
        lat = cur_df['Lat'].to_numpy()
        time = cur_df['Time'].to_numpy()
        
        dlon = np.diff(lon)
        dlat = np.diff(lat)
        dtime = np.diff(time)
        
        dtime /= 1000000000.0
        dtime = dtime.astype(float)

        if len(dtime) > 0:
            speed = calc_speed(calc_dist(lon[:-1], lat[:-1], dlon, dlat), dtime)
            
            dist = calc_dist(lon[:-1], lat[:-1], dlon, dlat)
            times.append(pd.Series(dtime))
            times.append(pd.Series([np.NaN]))
            dists.append(pd.Series(dist))
            dists.append(pd.Series([np.NaN]))
            speeds.append(pd.Series(speed))
            speeds.append(pd.Series([np.NaN]))
            lons.append(pd.Series(lon))
            lons.append(pd.Series([np.NaN]))
            lon1.append(pd.Series(lon[:-1] + dlon))
            lon1.append(pd.Series([np.NaN]))
            lats.append(pd.Series(lat))
            lats.append(pd.Series([np.NaN]))
            lat1.append(pd.Series(lat[:-1] + dlat))
            lat1.append(pd.Series([np.NaN]))

    res_df = pd.DataFrame()            
    res_df['start_lat'] = pd.concat(lats, ignore_index=True)    
    res_df['start_lon'] = pd.concat(lons, ignore_index=True)
    res_df['end_lat'] = pd.concat(lat1, ignore_index=True)           
    res_df['end_lon'] = pd.concat(lon1, ignore_index=True)
    res_df['speed'] = pd.concat(speeds, ignore_index=True)
    res_df['dist'] = pd.concat(dists, ignore_index=True)
    res_df['time'] = pd.concat(times, ignore_index=True)
    
    res_df = res_df[(res_df['speed'] >= SPEED_LIMIT) & 
                    (res_df['speed'] <= REASONABLE_SPEED_INFINITY) &
                    (res_df['time'] <= MAX_TIME_ELAPSED)]
    
    if save:
        path = path.removesuffix(f"{line}.csv")
        os.makedirs(f"{path}/SLE/", exist_ok=True)
        path = path + f"/SLE/{line}.csv"
        res_df.to_csv(path, index=False)
    
    return res_df
    

def sle(path="."):
    lines = glob.glob(f"{path}/DATA/LIVE/LINES/*.csv")
    ret_list = []
    
    for line in lines:
        print(line)
        ret_list.append(sle_line(line.removeprefix(f"{path}/DATA/LIVE/LINES/").removesuffix('.csv'), save=True))
        
    return pd.concat(ret_list, ignore_index=True)