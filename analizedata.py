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
        df = pd.read_csv(path)
        df = df.drop_duplicates(subset=['VehicleNumber', 'Time'])
    except FileNotFoundError:
        return pd.DataFrame()

    vehicles = df['VehicleNumber'].unique().tolist()

    frames = []

    for vehicle in vehicles:
        veh = df[df['VehicleNumber'] == vehicle].copy()

        veh['Time'] = pd.to_datetime(veh['Time'])

        lon, lat, t = (veh[k].to_numpy() for k in ('Lon', 'Lat', 'Time'))

        dlon, dlat, dt = np.diff(lon), np.diff(lat), (np.diff(t)).astype(float)
        dt = dt / 1e9

        time, lon, lat = (series[:-1] for series in (t, lon, lat))

        if len(dt) > 0:
            dist = calc_dist(lon, lat, dlon, dlat).astype(float)
            speed = calc_speed(dist, dt)

            frame = pd.DataFrame({
                'line': line,
                'start_lat': lat,
                'start_lon': lon,
                'end_lat': lat+dlat,
                'end_lon': lon+dlon,
                'speed': speed,
                'distance': dist,
                'dtime': dt,
                'time': time
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
    except FileNotFoundError:
        res_df = speed_for_line(line, save=True)

    try:
        return res_df[(res_df['speed'] >= limit) &
                      (res_df['speed'] <= REASONABLE_SPEED_INFINITY) &
                      (res_df['dtime'] <= max_time)
                      ]
    except KeyError:
        return pd.DataFrame()


def sle_all(path="."):
    lines = glob.glob(f"{path}/DATA/ROUTES/*")
    ret_list = []

    for line in lines:
        line = line.removeprefix(f"{path}/DATA/ROUTES/").removesuffix("/")
        print(line)

        ret_list.append(sle_line(line))

    return pd.concat(ret_list, ignore_index=True)


@np.vectorize
def calc_dist(lon, lat, dlon, dlat):
    a = np.sin(dlat/2)**2 + np.cos(lat) * np.cos(lat+dlat) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0
    return c*r


@np.vectorize
def correct_hours(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    if hours >= 24:
        hours -= 24
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@np.vectorize
def timediff(time1, time2) -> float:
    hdiff = time1.hour - time2.hour
    mdiff = time1.minute - time2.minute
    sdiff = time1.second - time2.second
    return (hdiff if hdiff < 24 else hdiff-24) * 60 * 60 + mdiff * 60 + sdiff


@np.vectorize
def bus_status(lat, lon, line, brigade, time):
    found = all_positions.loc[(all_positions['Lines'] == line) &
                              (all_positions['Brigade'] == brigade)
                              ]

    if found.size == 0:
        return np.NaN

    found['timediff'] = timediff(time, found['Time'])

    found = found.loc[np.abs(found['timediff']) <= MAX_LATE_ALLOWED]

    if found.size == 0:
        return np.NaN

    found['dist'] = calc_dist(found['Lat'],
                              found['Lon'],
                              found['Lat']-lat,
                              found['Lon']-lon
                              )

    found = found[found['dist'] <= 100]

    if found.size == 0:
        return np.NaN

    found = found.sort_values(by='timediff', key=lambda x: np.abs(x))

    return found['timediff'].iloc[0]


def earliness():
    # pd.options.mode.chained_assignment = None

    path = os.curdir
    timetable = pd.read_csv(f"{path}/DATA/timetable_all.csv")
    allstops = pd.read_csv(f"{path}/DATA/allstops.csv")
    timetable['line'] = timetable['line'].astype(str)

    for frame in (timetable, allstops):
        frame['zespol'] = frame['zespol'].astype(str)
        frame['slupek'] = frame['slupek'].astype(str)

    timetable = timetable.merge(allstops, on=['zespol', 'slupek'])

    timetable = timetable.drop(axis=1,
                               columns=['trasa',
                                        'id_ulicy',
                                        'kierunek_x',
                                        'obowiazuje_od',
                                        'kierunek_y'],

                               )

    timetable['czas'] = pd.to_datetime(correct_hours(timetable['czas']))
    timetable['czas'] = timetable['czas'].dt.time
    timetable['brygadaH'] = timetable['brygada'].apply(hash)
    timetable['lineH'] = timetable['line'].apply(hash)

    global all_positions
    try:
        all_positions = pd.read_csv(f"{path}/DATA/LIVE/positions_all.csv")
    except FileNotFoundError:
        gd.all_live()
        all_positions = pd.read_csv(f"{path}/DATA/LIVE/positions_all.csv")

    all_positions['Time'] = pd.to_datetime(all_positions['Time']).dt.time
    all_positions['Brigade'] = all_positions['Brigade'].apply(hash)
    all_positions['Lines'] = all_positions['Lines'].apply(hash)

    timetable = timetable.head(1000)

    timetable['earliness'] = bus_status(timetable['szer_geo'],
                                        timetable['dlug_geo'],
                                        timetable['lineH'],
                                        timetable['brygadaH'],
                                        timetable['czas'],
                                        timetable['line']
                                        )

    timetable = timetable.drop(columns=['brygadaH', 'lineH'], axis=1)

    timetable.to_csv("earliness_all.csv")

    fd = timetable['earliness'].count()
    return fd/timetable.size
