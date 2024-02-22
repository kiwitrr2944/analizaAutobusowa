import folium
import analizedata as ad
import getdata as gd
import pandas as pd
import numpy as np
import glob
import csv
import os

colors = {
    '0': 'green',
    '1': 'blue',
    '2': 'yellow',
    '3': 'orange',
    '4': 'pink',
    '5': 'red',
    '6': 'purple',
    '7': 'brown',
    '8': 'black'
}

types = {
    "0": "przelotowy",
    "1": "stały",
    "2": "na żądanie",
    "3": "krańcowy",
    "4": "dla wysiadających",
    "5": "dla wsiadających",
    "6": "zajezdnia",
    "7": "techniczny",
    "8": "postojowy"
}


def plot_dot(complex, no, colour, m: folium.Map,
             lon, lat, r, w, text
             ) -> None:
    """Plot a point on a map with popup (complex, no, typ)

    Args:
        map (folium.Map): map to plot on.
    """

    folium.CircleMarker(
                    location=[lon, lat],
                    fill_color=colors[colour],
                    fill=True,
                    color=colors[colour],
                    popup=f"{complex} {no} {text}",
                    radius=r,
                    weight=w
                ).add_to(m)


def plot_line(slat, slon, elat, elon, speed, line, t, m: folium.Map) -> None:
    """Plot line on folium map matching parameters (locations)
        and with popup (speed, line, time)
    Args:
        m (folium.Map): map to plot on
    """
    folium.PolyLine(
                    locations=[(slat, slon),
                               (elat, elon)],
                    popup=f"Line = {line}\n \
                            Speed = {speed}\n \
                            Time = {t}\n",
                    color=colors[str(max(0, (int(speed//10) - 4)))]
                ).add_to(m)


def stop_location(complex: str, no: str) -> tuple[float, float, str, str]:
    """Find stop coordinates matching given (complex, no)

    Args:
        complex (str):
        no (str):

    Returns:
        tuple[float, float, str, str]: coordinates and parameters
    """
    found = allstops[(allstops['zespol'] == complex) &
                     (allstops['slupek'] == no)]
    try:
        return (found['szer_geo'].iloc[0],
                found['dlug_geo'].iloc[0],
                found['nazwa_zespolu'].iloc[0],
                found['slupek'].iloc[0]
                )
    except IndexError:
        print(f"NOT FOUND IN DATABASE: {complex}, {no})")
        return (0, 0, "", "")


def plot_routes(line: str) -> None:
    """Plot all stops on all routes of specific line

    Args:
        line (str): line to plot
    """
    global allstops
    try:
        allstops = pd.read_csv(f"{os.getcwd()}/DATA/allstops.csv")
    except FileNotFoundError:
        gd.get_all_stops()
        allstops = pd.read_csv(f"{os.getcwd()}/DATA/allstops.csv")

    allstops['zespol'] = allstops['zespol'].astype(str)
    allstops['slupek'] = allstops['slupek'].astype(str)
    path = os.getcwd()
    dirpath = f"{path}/DATA/ROUTES/{line}"

    routes = glob.glob(f"{dirpath}/*.csv")

    m = folium.Map(location=[52, 21])

    for route in routes:
        with open(route) as file:
            stops = csv.DictReader(file)
            for stop in stops:
                lon, lat, name, no = stop_location(str(stop['nr_zespolu']),
                                                   str(stop['nr_przystanku']))

                plot_dot(name, no, stop['typ'], m, lon, lat, 3, 5, stop['typ'])

    dirpath2 = f"{path}/DATA/MAPS/ROUTES"
    os.makedirs(dirpath2, exist_ok=True)

    m.save(f"{dirpath2}/{line}.html")


def plot_all_routes():
    path = os.getcwd()
    lines = glob.glob(f"{path}/DATA/ROUTES/*")

    for line in lines:
        plot_routes(line.removeprefix(f"{path}/DATA/ROUTES/"))


def draw_bus(line: str):
    """Draw all bus appearances of specific line on map.

    Args:
        line (str): line to plot
    """
    path = os.getcwd()

    m = folium.Map(location=[52, 21])

    df = ad.sle_line(line, 5)

    for x in df.iterrows():
        x = x[1]
        plot_line(
                  x['start_lat'],
                  x['start_lon'],
                  x['end_lat'],
                  x['end_lon'],
                  x['speed'],
                  x['line'],
                  x['time'],
                  m
                )

    os.makedirs(f"{path}/DATA/MAPS/LIVE", exist_ok=True)
    m.save(f"{path}/DATA/MAPS/LIVE/{line}.html")


def draw_all_buses():
    path = os.getcwd()
    lines = glob.glob(f"{path}/DATA/ROUTES/*")

    for line in lines:
        print(line)
        draw_bus(line.removeprefix(f"{path}/DATA/ROUTES/"))


def draw_all_speeding_buses() -> None:
    """Draw all speedings on a Warsaw map.
    """
    m = folium.Map(location=[52, 21])

    df = ad.sle_all()
    for x in df.iterrows():
        x = x[1]
        plot_line(
                  x['start_lat'],
                  x['start_lon'],
                  x['end_lat'],
                  x['end_lon'],
                  x['speed'],
                  x['line'],
                  x['time'],
                  m
                )

    m.save(f"{os.getcwd()}/DATA/MAPS/LIVE/all_lines.html")


def id_location_correlation():
    """Map showcasing correlation between first digit of complex id
        and its location
    """
    global allstops
    try:
        allstops = pd.read_csv(f"{os.getcwd()}/DATA/allstops.csv")
    except FileNotFoundError:
        gd.get_all_stops()
        allstops = pd.read_csv(f"{os.getcwd()}/DATA/allstops.csv")

    m = folium.Map(location=[52, 21])

    for x in allstops.iterrows():
        x = x[1]

        plot_dot(
            x['nazwa_zespolu'],
            x['slupek'],
            x['zespol'][0] if x['zespol'][0] != 'R' else '0',
            m,
            x['szer_geo'],
            x['dlug_geo'],
            3,
            4,
            f"id = {x['zespol'][0]}"
        )

    m.save(f"{os.getcwd()}/DATA/MAPS/id_loc_cor.html")


def draw_speed_grid():
    df = ad.speed_grid()
    m = folium.Map(location=[52, 21])
    print(df)
    for x in df.iterrows():
        x = x[1]
        plot_dot(
                "",
                "",
                str(min(8, max(0, (int(x['speed']//10) - 4)))),
                m,
                x['lat'],
                x['lon'],
                2,
                3,
                False
            )
    m.save(f"{os.getcwd()}/DATA/MAPS/speed_grid.html")


def draw_stop_earliness():
    df = ad.earliness_by(['nazwa_zespolu', 'slupek'])

    try:
        allstops = pd.read_csv(f"{os.getcwd()}/DATA/allstops.csv")
    except FileNotFoundError:
        gd.get_all_stops()
        allstops = pd.read_csv(f"{os.getcwd()}/DATA/allstops.csv")

    m = folium.Map(location=[52, 21])

    df = df.merge(allstops, on=['nazwa_zespolu', 'slupek'])

    df['earliness'] = np.around(df['earliness'], decimals=1)

    for x in df.iterrows():
        x = x[1]
        plot_dot(
                x['nazwa_zespolu'],
                x['slupek'],
                '1' if x['earliness'] <= 0 else '5',
                m,
                x['szer_geo'],
                x['dlug_geo'],
                np.abs(x['earliness'])/2,
                np.abs(x['earliness'])/2,
                f"avg lateness = {x['earliness']}min"
            )
    m.save("xd.html")


def plot_line_earliness(cnt):
    df = ad.earliness_by(['line'])

    df = df.head(cnt)

    a = df.plot(
                title=f"{cnt} most late lines",
                x='line',
                y='earliness',
                kind='bar',
                )

    a.get_figure().savefig(f"{os.getcwd()}/DATA/most_late.pdf")
