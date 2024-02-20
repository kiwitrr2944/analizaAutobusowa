import pandas as pd
import os
import glob
from datetime import datetime
from getdata import MAXTIMEDIFF 
from ztmclasses import Position

def calc_speed(row, prev) -> float:
    if prev[3] != row[3]:
        return 0.0
    
    x_pos = Position(row[2], row[5])
    y_pos = Position(prev[2], prev[5])
    
    x_time = pd.to_datetime(prev[4])
    y_time = pd.to_datetime(row[4])
    
    dist = x_pos.distance(y_pos)
    time = (y_time - x_time).total_seconds()

    return dist / time * 3.6


def speed_limit(dirpath="."):
    lines = glob.glob(f"{dirpath}/DATA/LIVE/LINES/*.csv")
    exceeded = 0
    all = 0
    maxspeed = 0
    for line in lines:
        df = pd.read_csv(line).drop_duplicates(subset=['VehicleNumber', 'Time'])
        
        for row in df.itertuples():
            if all > 0:                
                speed = calc_speed(row, prev)
                
                if speed >= 50:
                    exceeded += 1

                if speed >= maxspeed:
                    print(line, speed)
                    maxspeed = speed

            all += 1
            prev = row  

    
    print(exceeded/all)
    return (exceeded, all)