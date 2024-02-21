import genericpath
from pickletools import long1
from re import L, S
from sqlite3 import Time
from tempfile import TemporaryFile
import numpy as np
import pandas as pd
import os
import glob
from datetime import datetime
from getdata import MAXTIMEDIFF 
from ztmclasses import Position
from geopy import distance
from haversine import haversine


REASONABLE_SPEED_INFINITY = 130
SPEED_LIMIT = 50
MAX_TIME_ELAPSED = 60.0


@np.vectorize
def calc_dist(lon, lat, dlon, dlat):
    lon2 = lon + dlon
    lat2 = lat + dlat
    
    return haversine((lat, lon), (lat2, lon2))*1000.0


def calc_speed(dist, time):
    return dist/time * 3.6


def speed_line(line, path='.', save=False):
    path = f"{path}/DATA/LIVE/LINES/{line}.csv"
    
    df = pd.read_csv(path).drop_duplicates(subset=['VehicleNumber', 'Time'])
    
    vehicles = df['VehicleNumber'].unique().tolist()
    
    frames = []
    
    for vehicle in vehicles:
        cur_df = df[df['VehicleNumber'] == vehicle].copy()
        
        cur_df['Time'] = pd.to_datetime(cur_df['Time'])

        lon, lat, time = (cur_df[key].to_numpy() for key in ('Lon', 'Lat', 'Time'))        
        dlon, dlat, dtime = np.diff(lon), np.diff(lat), (np.diff(time) / 1e9).astype(float)
        
        time, lon, lat = (array[:-1] for array in (time, lon, lat))

        if len(dtime) > 0:
            speed = calc_speed(calc_dist(lon, lat, dlon, dlat), dtime).astype(float)
            dist = calc_dist(lon, lat, dlon, dlat).astype(float)
            
            frame = pd.DataFrame({
                'line' : line,
                'start_lat' : lat,
                'start_lon' : lon,
                'end_lat' : lat+dlat,
                'end_lon' : lon+dlon,
                'speed' : speed,
                'distance' : dist,
                'dtime' : dtime,
                'time' : time
                
            })
            frames.append(frame)
            
    res_df = pd.concat(frames)

    if save:
        path = path.removesuffix(f"{line}.csv")
        os.makedirs(f"{path}/SPEED/", exist_ok=True)
        path = path + f"/SPEED/{line}.csv"
        res_df.to_csv(path, index=False)
    
    return res_df
    
    
def sle_line(line, limit=50, max_time=60):
    try:
        raise ValueError
        file = f"./DATA/LIVE/LINES/SPEED/{line}.csv"
        res_df = pd.read_csv(file)
    except:
        res_df = speed_line(line, save=True)
        
    return res_df[(res_df['speed'] >= limit) & 
                    (res_df['speed'] <= REASONABLE_SPEED_INFINITY) &
                    (res_df['dtime'] <= max_time)]
    

def sle(path="."):
    lines = glob.glob(f"{path}/DATA/LIVE/LINES/*.csv")
    ret_list = []
    
    for line in lines:
        print(line)
        
        ret_list.append(sle_line(line.removeprefix(f"{path}/DATA/LIVE/LINES/").removesuffix('.csv')))
        
    return pd.concat(ret_list, ignore_index=True)