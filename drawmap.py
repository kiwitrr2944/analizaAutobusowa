import folium
import analizedata as ad
import glob
import pandas as pd
import csv
import os

BASIC_MAP = folium.Map(location=[52, 21])

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


def plotDot(stopname, slupek, typ, map, lon, lat):
    folium.CircleMarker(
                    location=[lon, lat],
                    fill_color=colors[typ],
                    fill=True,
                    color=colors[typ],
                    popup=f"{stopname} {slupek} typ={types[typ]}",
                    radius=3,
                    weight=5
                ).add_to(map)


def plot_line(slat, slon, elat, elon, speed, line, time, m):
    folium.PolyLine(
                    locations=[(slat, slon),
                               (elat, elon)],
                    popup=f"Line = {line}\n \
                            Speed = {speed}\n \
                            Time = {time}\n",
                    color=colors[str(max(0, (int(speed//10) - 4)))]
                ).add_to(m)


allstops = pd.read_csv(f"{os.getcwd()}/DATA/allstops.csv")
allstops['zespol'] = allstops['zespol'].astype(str)
allstops['slupek'] = allstops['slupek'].astype(int)


def stop_location(zespol, slupek):
    found = allstops[(allstops['zespol'] == zespol) &
                     (allstops['slupek'] == slupek)]
    try:
        return (found['szer_geo'].iloc[0],
                found['dlug_geo'].iloc[0],
                found['nazwa_zespolu'].iloc[0],
                found['slupek'].iloc[0]
                )
    except IndexError:
        print(f"NOT FOUND IN DATABASE: {zespol}, {slupek})")
        return (0, 0, 0, 0)


def plot_routes(line, path="."):
    dirpath = f"{path}/DATA/ROUTES/{line}"

    routes = glob.glob(f"{dirpath}/*.csv")

    m = folium.Map(location=[52, 21])
    for route in routes:
        with open(route) as file:
            stops = csv.DictReader(file)
            for stop in stops:
                lon, lat, name, pos = stop_location(str(stop['nr_zespolu']),
                                                    int(stop['nr_przystanku']))

                plotDot(name, pos, stop['typ'], m, lon, lat)

    dirpath2 = f"{path}/DATA/MAPS/ROUTES"
    os.makedirs(dirpath2, exist_ok=True)

    m.save(f"{dirpath2}/{line}.html")


def plot_all_routes(path="."):
    lines = glob.glob(f"{path}/DATA/ROUTES/*")

    for line in lines:
        plot_routes(line.removeprefix(f"{path}/DATA/ROUTES/"), path)


def draw_speeding_bus(line):
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


def draw_all_speeding_buses():
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

    m.save(f"{os.getcwd()}/DATA/MAPS/all_lines.html")


draw_all_speeding_buses()
