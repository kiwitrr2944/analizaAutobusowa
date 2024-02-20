from turtle import speed
from numpy import NAN, NaN
import pandas as pd
import os
import glob
from datetime import datetime
from getdata import MAXTIMEDIFF 
from ztmclasses import Position

REASONABLE_SPEED_INFINITY = 100
SPEED_LIMIT = 50


def calc_speed(row, prev) -> float:
    if prev['VehicleNumber'] != row['VehicleNumber']:
        return 0.0
    
    x_pos = Position(row['Lon'], row['Lat'])
    y_pos = Position(prev['Lon'], prev['Lat'])
    
    x_time = pd.to_datetime(prev['Time'])
    y_time = pd.to_datetime(row['Time'])
    
    dist = x_pos.distance(y_pos)
    time = (y_time - x_time).total_seconds()

    speed = dist / time * 3.6

    if speed <= REASONABLE_SPEED_INFINITY:
        return speed 
    
    return NaN


def sle_line(line, path='.', save=False):
    path = f"{path}/DATA/LIVE/LINES/{line}.csv"
    
    df = pd.read_csv(path).drop_duplicates(subset=['VehicleNumber', 'Time'])
    
    all = 0
    speeds = [NaN]
    
    for row in df.iterrows():
        if all > 0:                
            speeds.append(calc_speed(row[1], prev[1]))
        all += 1
        prev = row
        
    df['Speed'] = speeds
    df = df.loc[df['Speed'] >= 50.0]
    if save:
        path = path.removesuffix(f"{line}.csv")
        os.makedirs(f"{path}/SLE/", exist_ok=True)
        path = path + f"/SLE/{line}.csv"
        df.to_csv(path, index=False)
    
    return df
    

def sle(path="."):
    lines = glob.glob(f"{path}/DATA/LIVE/LINES/*.csv")
    ret_list = []
    
    for line in lines:
        ret_list.append(sle_line(line.removeprefix(f"{path}/DATA/LIVE/LINES/", path)))
        
    return pd.concat(ret_list, ignore_index=True)