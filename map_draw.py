from genericpath import exists
from turtle import width
import folium
import analizedata as ad
import glob
import pandas as pd
import csv
import os
import getdata as gd


BASIC_MAP = folium.Map(location=[52, 21])

def plotDot(stopname, slupek, map, lon, lat, r=30):
    folium.CircleMarker(location=[lon, lat], 
                        radius=r//10, 
                        weight=5,
                        popup=f"{stopname}, {slupek}").add_to(map)



allstops = pd.read_csv(f"./DATA/allstops.csv")
allstops['zespol'] = allstops['zespol'].astype(str)
allstops['slupek'] = allstops['slupek'].astype(int)

def stop_location(zespol, slupek):
    found = allstops[(allstops['zespol'] == zespol) & (allstops['slupek'] == slupek)]
    try:
        return (found['szer_geo'].iloc[0], 
                found['dlug_geo'].iloc[0], 
                found['nazwa_zespolu'].iloc[0],
                found['slupek'].iloc[0])
    except:
        print(zespol, slupek)
        return (0, 0, 0, 0)


def plot_routes(line, path="."):
    dirpath = f"{path}/DATA/ROUTES/{line}"
    
    routes = glob.glob(f"{dirpath}/*.csv")
    
    m = folium.Map(location=[52, 21])
    for route in routes:
        with open(route) as file:
            stops = csv.DictReader(file)
            for stop in stops:
                lon, lat, name, pos = stop_location(str(stop['nr_zespolu']), int(stop['nr_przystanku']))
                plotDot(name, pos, m, lon, lat, 50)
    
    dirpath2 = f"{path}/DATA/MAPS/"
    os.makedirs(dirpath2, exist_ok=True)
    
    m.save(f"{dirpath2}/{line}.html")
      
      
def plot_all_lines(path="."):   
    lines = glob.glob(f"{path}/DATA/ROUTES/*")

    for line in lines:
        plot_routes(line.removeprefix(f"{path}/DATA/ROUTES/"), path)
    
# plot_routes(input("Podaj linie: "))
    
# plot_all_lines()

# print(ad.sle_line(input(), save=True))

colours = ['blue', 'yellow', 'orange', 'red']


def fun():
    m = folium.Map(location=[52, 21])
    line = input()
    df = ad.sle_line(line, save=True)
    cnt = 0
    for x in df.iterrows():
        x = x[1]
        color = int(x['speed'])//10
        color = min(3, color-5)

        folium.PolyLine(locations=[(x['start_lat'], x['start_lon']), 
                                   (x['end_lat'], x['end_lon'])],
                        popup=f"Speed = {x['speed']}",
                        color=colours[color]
                        ).add_to(m)
        
        # folium.Marker(location=(x['start_lat'], x['start_lon'])).add_to(m)     
        # folium.Marker(location=(x['end_lat'], x['end_lon'])).add_to(m)
    m.save("map.html")
    
fun()