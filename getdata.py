from requests import get
from json import dumps
import typing
import pandas as pd
from ztmclasses import ZtmRoute, ZtmStop
import csv 
from datetime import datetime
import time

APIKEY : str = "916c4bfe-396c-4203-b87b-5a68889e9dd5"
MAXTIMEDIFF : float = 75.0
dbtimetable_url = "https://api.um.warszawa.pl/api/action/dbtimetable_get/"
dbstore_url = "https://api.um.warszawa.pl/api/action/dbstore_get/"
routes_url = "https://api.um.warszawa.pl/api/action/public_transport_routes/"
dict_url = "https://api.um.warszawa.pl/api/action/public_transport_dictionary/"
live_url = "https://api.um.warszawa.pl/api/action/busestrams_get/"

base_params = {"apikey": APIKEY}

def json_print(text : str) -> None:
    """Wrapper for printing indented data for debugging

    Args:
        text (str): json-formatted text to print
    """
    text = dumps(text, sort_keys=True, indent=4)
    print(text)
   
    
def request_all_stops():
    pms = base_params.copy()
    pms['id'] = "1c08a38c-ae09-46d2-8926-4f9d25cb0630"
    
    return get(dbstore_url, params=pms).json()['result']


def request_lines_stop(stop, pos : str):
    try:
        stopint = int(stop)
    except ValueError:
        stopint = get_stop_id(stop)

    pms = base_params.copy()
    pms['busstopId'] = str(stopint)
    pms['busstopNr'] = pos
    pms['id'] = "88cd555f-6f31-43ca-9de4-66c479ad5942"
    
    return get(dbtimetable_url, pms).json()['result']


def request_stop_id(stop_name) -> dict:
    pms = base_params.copy()
    pms['name'] = stop_name
    pms['id'] = "b27f4c17-5c50-4a5b-89dd-236b282bc499"

    return get(dbtimetable_url, pms).json()['result']


def request_routes():
    return get(routes_url, params=base_params).json()['result']


def request_live():
    pms = base_params.copy()
    pms['type'] = '1'
    pms['resource_id'] = "%20f2e5503e927d-4ad3-9500-4ab9e55deb59"
    
    return get(live_url, params=pms).json()['result']


def get_stop_id(stop_name : str) -> int:
    response = request_stop_id(stop_name)
    return response[0]['values'][0]['value']
    
    
def get_lines_from_stop(przystanek : str, slupek : str) -> list:
    response = request_lines_stop(przystanek, slupek)
    linie = []

    for linia in response:
        linia = linia['values'][0]
        linie.append(linia['value'])

    return linie  


def all_stops_data() -> list:
    stops = request_all_stops()
    ret = []
    header = []
    
    for attr in stops[0]['values']:
        header.append(attr['key'])
        
    filepath = "./DATA/allstops.csv"
        
    with open(filepath, 'w') as file:
        wr = csv.writer(file)
        wr.writerow(header)
        for stop in stops:
            stop = stop['values']
            params = []
            
            for attr in stop:    
                params.append(attr['value'])
            
            wr.writerow(params)
            ret.append(ZtmStop(params))

    return ret

    
def get_routes():
    response = request_routes()
    routes = response['result']
    ret = []
    json_print(routes)
    
    for line in routes:
        for route in routes[line]:
            a = ZtmRoute(line, route, routes[line][route])
            ret.append(a)
    
    return ret


def get_dictionary():
    with get(dict_url) as response:
        return response.json()
    
    
def get_live() -> bool:    
    pms = base_params.copy()
    pms['resource_id'] = '%20f2e5503e927d-4ad3-9500-4ab9e55deb59'
    pms['type'] = '1'
    
    time_now = datetime.now()

    response = request_live()
    header = []
    timeout = 1
        
    while response[0] == 'B':
        response = request_live()
        timeout = timeout * 1.5
        if timeout >= 30:
            raise TimeoutError
        time.sleep(timeout)

    for attr in response[0]:
        header.append(attr) 

    totalsec = 0
    cnt = 0
    goodcnt = 0
    filepath = f"./DATA/LIVE/{time_now.timetz()}"
    print(response[0])
    
    with open(filepath, "w") as file:
        wr = csv.writer(file)
        wr.writerow(header)
        
        for data in response:
            czas = datetime.fromisoformat(data['Time'])
            c = time_now - czas
            
            totalsec += c.total_seconds()
            cnt += 1
            
            if c.total_seconds() >= MAXTIMEDIFF:
                continue
            
            goodcnt += 1
            # print(c.total_seconds())
            
            lista = []
            
            for attr in header:
                lista.append(data[attr])
            wr.writerow(lista)
    
    print(goodcnt/cnt)
    return True