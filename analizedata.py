from codecs import ascii_decode
from importlib import simple
from markupsafe import _simple_escaping_wrapper
import numpy as np
import pandas as pd
import getdata as gd
import os
import glob

REASONABLE_SPEED_INFINITY = 130
SPEED_LIMIT = 50
MAX_TIME_ELAPSED = 60.0
MAX_LATE_ALLOWED = 60.0*30.0


def calc_speed(dist, time):
    return dist/time * 3.6


def speed_for_line(line, path='.', save=False):
    path = f"{path}/DATA/LIVE/LINES/{line}.csv"
    
    try:
        df = pd.read_csv(path).drop_duplicates(subset=['VehicleNumber', 'Time'])
    except FileNotFoundError:
        return pd.DataFrame()
    
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


    try:
        return res_df[(res_df['speed'] >= limit) & 
                        (res_df['speed'] <= REASONABLE_SPEED_INFINITY) &
                        (res_df['dtime'] <= max_time)]
    except KeyError:
        return pd.DataFrame()
        
    

def sle_all(path="."):
    lines = glob.glob(f"{path}/DATA/ROUTES/*")
    ret_list = []
    
    for line in lines:
        print(line)
        
        ret_list.append(sle_line(line.removeprefix(f"{path}/DATA/ROUTES/").removesuffix("/")))
        
    return pd.concat(ret_list, ignore_index=True)


@np.vectorize
def calc_dist(lon, lat, dlon, dlat):
    a = np.sin(dlat/2)**2 + np.cos(lat) * np.cos(lat+dlat) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0
    return c*r


@np.vectorize
def bus_status(lat, lon, line, brigade, time):
    found = all_positions.loc[(all_positions['Lines'] == line) &
                              (all_positions['Brigade'] == brigade)
                            ]

    if found.size == 0:
        return np.NaN
    
    found['timediff'] = time - found['Time']
    found['timediff'] = found['timediff'].dt.seconds
    
    found = found.loc[np.abs(found['timediff']) <= MAX_LATE_ALLOWED]
    
    if found.size == 0:
        return np.NaN    
    
    
    found['dist'] = calc_dist(found['Lat'], 
                            found['Lon'],
                            found['Lat']-lat,
                            found['Lon']-lon
                        )

    found = found[found['dist'] <= 50]
    
    if found.size == 0:
        return np.NaN
    
    found = found.sort_values(by='timediff', key = lambda x: np.abs(x))
    
    return found['timediff'].iloc[0]


@np.vectorize
def correct_hours(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    if hours >= 24:
        hours -= 24
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def earliness():
    pd.options.mode.chained_assignment = None 
    
    path = os.curdir
    df = pd.read_csv(f"{path}/DATA/timetable_all.csv")
    allstops = pd.read_csv(f"{path}/DATA/allstops.csv")
    df['line'] = df['line'].astype(str)
    
    for frame in (df, allstops):
        frame['zespol'] = frame['zespol'].astype(str)
        frame['slupek'] = frame['slupek'].astype(str)

    
    df['czas'] = pd.to_datetime(correct_hours(df['czas']))
    
    df = df.merge(allstops, on=['zespol', 'slupek'])
    
    df = df.drop(labels=['trasa', 'id_ulicy', 'kierunek_x', 'obowiazuje_od', 'kierunek_y', 'nazwa_zespolu'], axis=1)
    
    global all_positions
    all_positions = pd.read_csv(f"{path}/DATA/LIVE/positions_all.csv")
    
    all_positions['Time'] = pd.to_datetime(all_positions['Time'])
    all_positions['Brigade'] = all_positions['Brigade'].apply(hash)
    all_positions['Lines'] = all_positions['Lines'].apply(hash) 
       
    df['brygadaH'] = df['brygada'].apply(hash)
    df['lineH'] = df['line'].apply(hash)
    df = df.head(1000)
    
    df['earliness'] = bus_status(df['szer_geo'], 
                                 df['dlug_geo'], 
                                 df['lineH'], 
                                 df['brygadaH'], 
                                 df['czas']
                            )
    
    df.to_csv("earliness_test.csv")
    fd = df['earliness'].count()
    return fd/df.size
