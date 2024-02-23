import dis
import numpy as np
import pandas as pd
import getdata as gd
import os
import glob

REASONABLE_SPEED_INFINITY = 120
MAX_TIME_ELAPSED = 60.0
MAX_LATE_ALLOWED = 60.0*30.0


@np.vectorize
def calc_speed(dist, time) -> float:
    return dist/time * 3.6


def speed_for_line(line: str, save: bool = False) -> pd.DataFrame:
    """For all bus positions calculates its speed at the moment

    Args:
        line (str): line to calculate
        save (bool, optional): defines if save to .csv is done.
        Defaults to False.

    Returns:
        pd.DataFrame: returns dataframe with all moments and speeds.
    """
    path = os.getcwd()
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
            dist = calc_dist(lat, dlon, dlat)
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


def sle_line(line: str, limit: float = 50, max_t: float = 60) -> pd.DataFrame:
    """Filters those moments in bus position when speed was exceeded

    Args:
        line (str): line to track
        limit (float, optional):  Defaults to 50.
        max_t (float, optional): maximum time between two positions.
        that is considered to be straight line drive.
        Defaults to 60.

    Returns:
        pd.DataFrame: all moments with speed limit exceeded
    """
    try:
        file = f"./DATA/LIVE/LINES/SPEED/{line}.csv"
        res_df = pd.read_csv(file)
    except FileNotFoundError:
        res_df = speed_for_line(line, save=True)

    try:
        return res_df[(res_df['speed'] >= limit) &
                      (res_df['speed'] <= REASONABLE_SPEED_INFINITY) &
                      (res_df['dtime'] <= max_t)
                      ]
    except KeyError:
        return pd.DataFrame()


def sle_all() -> pd.DataFrame:
    """Computes sle_line() for all lines

    Returns:
        pd.DataFrame: All speedings combined
    """
    path = os.getcwd()
    lines = glob.glob(f"{path}/DATA/ROUTES/*")
    ret_list = []

    for line in lines:
        line = line.removeprefix(f"{path}/DATA/ROUTES/").removesuffix("/")
        print(line)

        ret_list.append(sle_line(line))

    return pd.concat(ret_list, ignore_index=True)


def speed_grid() -> pd.DataFrame:
    """Creates a grid with a point every 0.005 degree.
       For each point average speed around it is calculated.

    Returns:
        pd.DataFrame: dataframe with gridpoint coordinates and avg speed.
    """
    files = glob.glob(f"{os.getcwd()}/DATA/LIVE/LINES/SLE/*.csv")

    df = pd.concat([pd.read_csv(file) for file in files], ignore_index=True)
    res = pd.DataFrame({
                        'lat': (df['start_lat']+df['end_lat'])/2,
                        'lon': (df['start_lon']+df['end_lon'])/2,
                        'speed': df['speed']
                    }, dtype=float
                    )

    res = res.loc[(res['speed'] >= 3.0) &
                  (res['speed'] <= REASONABLE_SPEED_INFINITY)
                  ]

    @np.vectorize
    def round_my(lat):
        return np.floor(lat/0.005) * 0.005

    res['lat'] = round_my(res['lat'])
    res['lon'] = round_my(res['lon'])
    res = res.loc[res['lon'].between(20, 22)]
    res = res.loc[res['lat'].between(51, 53)]

    res = res.groupby(['lat', 'lon'])['speed'].mean().reset_index()
    res = res.loc[res['speed'] >= 5.0]

    res.to_csv(f"{os.getcwd()}/DATA/LIVE/speed_grid.csv")
    return res


@np.vectorize
def calc_dist(lat, dlon, dlat):
    """Calculates distance using haversine formula

    Args:
        lat (_type_): latitude
        dlon (_type_): difference between longitudes
        dlat (_type_): difference between latitudes

    Returns:
        _type_: 
    """
    lat, dlon, dlat = (np.radians(x) for x in (lat, dlon, dlat))
    a = np.sin(dlat/2)**2 + np.cos(lat) * np.cos(lat+dlat) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371000.0
    return c*r


@np.vectorize
def correct_hours(time_str):
    """Corects hour from timetable to be numpy-friendly (no 27:00:00)
    """
    hours, minutes, seconds = map(int, time_str.split(':'))
    if hours >= 24:
        hours -= 24
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@np.vectorize
def timediff(time1, time2) -> float:
    """Computes time difference between two times

    Args:
        time1
        time2

    Returns:
        float: time difference in seconds
    """
    hdiff = time1.hour - time2.hour
    mdiff = time1.minute - time2.minute
    sdiff = time1.second - time2.second
    return (hdiff if hdiff < 24 else hdiff-24) * 60 * 60 + mdiff * 60 + sdiff


@np.vectorize
def bus_earliness(
                  lat: float, lon: float,
                  line: np.int64, brigade: np.int64,
                  time
                ):
    """Finds a bus position that matches timetable event the most, then
       returns lateness in seconds.
    """
    found = all_positions.loc[
                              (all_positions['Lines'] == line) &
                              (all_positions['Brigade'] == brigade)
                            ]

    if found.size == 0:
        return np.NaN

    found['timediff'] = timediff(time, found['Time'])

    found = found.loc[np.abs(found['timediff']) <= MAX_LATE_ALLOWED]

    if found.size == 0:
        return np.NaN

    found['dist'] = calc_dist(
                              found['Lat'],
                              found['Lon']-lon,
                              found['Lat']-lat
                              )

    found = found[found['dist'] <= 100.0]
    if found.size == 0:
        return np.NaN

    found = found.sort_values(by='timediff', key=lambda x: np.abs(x))

    return found['timediff'].iloc[0]


def earliness() -> float:
    """Computes earliness for every event in a timetable

    Returns:
        float: percent of matched timetable events to any bus.
    """
    pd.options.mode.chained_assignment = None

    path = os.curdir
    timetable = pd.read_csv(f"{path}/DATA/timetable_all.csv")
    allstops = pd.read_csv(f"{path}/DATA/allstops.csv")

    timetable['line'] = timetable['line'].astype(str)

    for frame in (timetable, allstops):
        frame['zespol'] = frame['zespol'].astype(str)
        frame['slupek'] = frame['slupek'].astype(str)

    timetable = timetable.merge(allstops, on=['zespol', 'slupek'])

    timetable = timetable.drop(
                               axis=1,
                               columns=['trasa',
                                        'id_ulicy',
                                        'kierunek_x',
                                        'obowiazuje_od',
                                        'kierunek_y']
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

    timetable['earliness'] = bus_earliness(
                                           timetable['szer_geo'],
                                           timetable['dlug_geo'],
                                           timetable['lineH'],
                                           timetable['brygadaH'],
                                           timetable['czas']
                                        )

    timetable = timetable.drop(columns=['brygadaH', 'lineH'], axis=1)

    timetable.to_csv(f"{os.getcwd()}/DATA/LIVE/earliness_all.csv")

    fd = timetable['earliness'].count()
    return fd/timetable.size


def earliness_by(cols: list[str]) -> pd.DataFrame:
    """Groups earliness by given key (for example computes
    avg earliness on stop.)

    Args:
        cols (list[str]): key to group

    Returns:
        pd.DataFrame:
    """
    df = pd.read_csv(f"{os.getcwd()}/DATA/LIVE/earliness_all.csv")
    df = df.dropna()
    df = df.groupby(cols)['earliness'].mean().reset_index()
    df['earliness'] /= 60.0
    df = df.sort_values(by='earliness', ascending=False)
    return df


def stop_line_prepare() -> dict:
    """Gets (complex, no) -> list of lines avaiable dictionary

    Returns:
        dict:
    """
    lines = pd.read_csv(f"{os.getcwd()}/DATA/timetable_all.csv")
    lines = lines.drop(axis=1,
                       labels=['trasa', 'czas', 'kierunek', 'brygada'])

    lines = lines.drop_duplicates()

    stop_lines = lines.groupby(['zespol', 'slupek']).agg(list).to_dict()
    return stop_lines['line']


def calc_intersect(a: tuple, b: tuple) -> int:
    """For two stops computes how many lines are on both of them

    Args:
        a (tuple): (a_id, a_no)
        b (tuple): (b_id, b_no)

    Returns:
        int: no of common lines
    """
    try:
        a_lines = stop_lines.get(a, [])
    except KeyError:
        a_lines = []
    try:
        b_lines = stop_lines.get(b, [])
    except KeyError:
        b_lines = []

    return len(set(a_lines).intersection(b_lines))


def distant_stops(k: int) -> list[dict]:
    """for every i in (1, k] finds pair of furthest stops that 
        have at least i stops in common

    Args:
        k (int):

    Returns:
        list[dict]: i-th dictionary stores data about the i-th pair
    """
    global stop_lines
    stop_lines = stop_line_prepare()
    allstops = pd.read_csv(f"{os.getcwd()}/DATA/allstops.csv")
    res_list = []
    allstops = allstops.drop(axis=1,
                             labels=['kierunek', 'obowiazuje_od', 'id_ulicy'])

    df1 = allstops.copy()
    df2 = allstops.copy()

    allstops = pd.merge(df1, df2, how='cross')

    allstops = allstops[allstops['zespol_x'] != allstops['zespol_y']]

    allstops = allstops.rename(columns={
        'zespol_x': 'a_zespol',
        'slupek_x': 'a_slupek',
        'szer_geo_x': 'a_szer_geo',
        'dlug_geo_x': 'a_dlug_geo',
        'nazwa_zespolu_x': 'a_nazwa_zespolu',
        'zespol_y': 'b_zespol',
        'slupek_y': 'b_slupek',
        'szer_geo_y': 'b_szer_geo',
        'dlug_geo_y': 'b_dlug_geo',
        'nazwa_zespolu_y': 'b_nazwa_zespolu'
    })

    allstops['distance'] = calc_dist(
                                allstops['a_szer_geo'],
                                allstops['a_dlug_geo']-allstops['b_dlug_geo'],
                                allstops['a_szer_geo']-allstops['b_szer_geo']
                                )
    intersects = []

    for i in range(len(allstops)):
        p = allstops.iloc[i]

        intersects.append(calc_intersect((p['a_zespol'], p['a_slupek']),
                                         (p['b_zespol'], p['b_slupek'])))

    allstops['intersect'] = intersects

    for i in range(1, k+1):
        allstops_c = allstops[allstops['intersect'] >= i]
        allstops_c = allstops_c.sort_values(by='distance', ascending=False)
        allstops_c = allstops_c.iloc[0]
        allstops_c['intersect'] = min(i, allstops_c['intersect'])
        res_list.append(allstops_c.to_dict())

    return res_list
