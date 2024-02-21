import numpy as np
import pandas as pd
import getdata as gd
import os
import glob
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


def speed_for_line(line, path='.', save=False):
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
        file = f"./DATA/LIVE/LINES/SPEED/{line}.csv"
        res_df = pd.read_csv(file)
    except:
        res_df = speed_for_line(line, save=True)
        
    return res_df[(res_df['speed'] >= limit) & 
                    (res_df['speed'] <= REASONABLE_SPEED_INFINITY) &
                    (res_df['dtime'] <= max_time)]
    

def sle_all(path="."):
    lines = glob.glob(f"{path}/DATA/LIVE/LINES/*.csv")
    ret_list = []
    
    for line in lines:
        print(line)
        
        ret_list.append(sle_line(line.removeprefix(f"{path}/DATA/LIVE/LINES/").removesuffix('.csv')))
        
    return pd.concat(ret_list, ignore_index=True)


@np.vectorize
def bus_status(lat, lon, line, brigade, time):
    found = all_positions.loc[(all_positions['Lines'] == line) &
                              (all_positions['Brigade'] == brigade)
                            ]

    
    found['dist'] = calc_dist(found['Lat'], 
                            found['Lon'],
                            found['Lat']-lat,
                            found['Lon']-lon
                        )
    
    found = found.sort_values(by=['dist'])
    return found['Time'].iloc[0]

def earliness():
    path = os.curdir
    df = pd.read_csv(f"{path}/DATA/TIMETABLES/timetable_all.csv")
    allstops = pd.read_csv(f"{path}/DATA/allstops.csv")
    for frame in (df, allstops):
        frame['zespol'] = frame['zespol'].astype(str)
        frame['slupek'] = frame['slupek'].astype(int)

    
    df = df.merge(allstops, on=['zespol', 'slupek'])
    
    gd.all_live()
    global all_positions 
    all_positions = pd.read_csv(f"{path}/DATA/LIVE/positions_all.csv")
    
    df = df.head(100)
    df['earliness'] = bus_status(df['szer_geo'], df['dlug_geo'], df['line'], df['brygada'], df['czas'])
    
    df.to_csv("earliness_test.csv")

earliness()