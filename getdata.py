from asyncio.constants import DEBUG_STACK_DEPTH
from email.mime import base
from requests import get
from json import dumps
import typing
import pandas
from ztmclasses import ZtmRoute, ZtmStop

APIKEY = "916c4bfe-396c-4203-b87b-5a68889e9dd5"
dbtimetable_url = "https://api.um.warszawa.pl/api/action/dbtimetable_get/"
dbstore_url = "https://api.um.warszawa.pl/api/action/dbstore_get/"
routes_url = "https://api.um.warszawa.pl/api/action/public_transport_routes/"
dict_url = "https://api.um.warszawa.pl/api/action/public_transport_dictionary/"

stop_to_id = "https://api.um.warszawa.pl/api/action/dbtimetable_get/?id=b27f4c17-5c50-4a5b-89dd-236b282bc499"
lines_on_stop = "https://api.um.warszawa.pl/api/action/dbtimetable_get/?id=88cd555f-6f31-43ca-9de4-66c479ad5942"
dict_url = "https://api.um.warszawa.pl/api/action/public_transport_dictionary/?apikey=916c4bfe-396c-4203-b87b-5a68889e9dd5"

live = "https://api.um.warszawa.pl/api/action/busestrams_get/?resource_id="

base_params = {"apikey": APIKEY}

def json_print(text : str) -> None:
    """Wrapper for printing indented data for debugging

    Args:
        text (str): json-formatted text to print
    """
    text = dumps(text, sort_keys=True, indent=4)
    print(text)
    
def all_stops_url():
    """Gives url to data about all stops

    Returns:
        str: url
    """
    pms = base_params.copy()
    pms['id'] = "1c08a38c-ae09-46d2-8926-4f9d25cb0630"
    
    return get(dbstore_url, params=pms).json()

def lines_on_stop_url(stop, pos : str) -> dict:
    """Gives url to data about lines on stop. Stop can be 
    either name (conversion) or stop_id. 

    Args:
        stop (): stop_name or stop_id
        pos (str): number of "slupek"

    Returns:
        str: url
    """

    try:
        stopint = int(stop)
    except:
        stopint = get_stop_id(stop)

    pms = base_params.copy()
    pms['busstopId'] = str(stopint)
    pms['busstopNr'] = pos
    pms['id'] = "88cd555f-6f31-43ca-9de4-66c479ad5942"
    
    return get(dbtimetable_url, pms).json()

def stop_id_url(stop_name) -> dict:
    """Url for converter stop_name->stop_id
    !!!AMBIGOUS!!!

    Args:
        stop_name (str): stop_name to convert

    Returns:
        str: url
    """
    pms = base_params.copy()
    pms['name'] = stop_name
    pms['id'] = "b27f4c17-5c50-4a5b-89dd-236b282bc499"

    return get(dbtimetable_url, pms).json()

def gt_routes() -> dict:
    """Url for all routes of public transport

    Returns:
        str: url
    """
    
    return get(routes_url, params=base_params).json()


def live_data() -> dict:
    
    pms = base_params.copy()
    pms['type'] = '1'
    pms['resource_id'] = "%20f2e5503e927d-4ad3-9500-4ab9e55deb59"
    return get(live, params=pms).json()


def get_stop_id(stop_name : str) -> int:
    """Converts stop_name into stop_id
    !!!AMBIGOUS!!!

    Args:
        stop_name(str): stop_name to convert

    Returns:
        str: 4-digit code - id of the stop group with given name
    """
    response = stop_id_url(stop_name)
    return response['result'][0]['values'][0]['value']
    
def get_lines_from_stop(przystanek : str, slupek : str) -> list:
    """Lists all lines on given stop

    Args:
        stop (str): stop_name or stop_id
        pos (str): number of "slupek"
        
    Returns:
        list: all no. of lines departing in str format 
    """
    
    response = lines_on_stop_url(przystanek, slupek)
    linie = []
    data = response['result']
    for linia in data:
        linia = linia['values'][0]
        linie.append(linia['value'])
   
    print(linie)

    return linie  

def all_stops_data() -> list:
    """Data about all stops in format:

    Returns:
        list: list of ZtmStop objects
    """
    stops = all_stops_url()['result']
    ret = []
    for stop in stops:
        stop = stop['values']
        params = []
        for attr in stop:
            params.append(attr['value'])
        ret.append(ZtmStop(params))
        print(ret[-1])
        
    return ret
    
def get_routes():
    """Returns all routes as list of ZtmRoute objects

    Returns:
        str: TODO ta konwersja
    """
    response = gt_routes()
    routes = response['result']
    ret = []
    for line in routes:
        for route in routes[line]:
            a = ZtmRoute(line, route, routes[line][route])
            ret.append(a)
    return ret


def get_dictionary():
    with get(dict_url) as response:
        return response.json()
    
def live_test():
    url = "https://api.um.warszawa.pl/api/action/busestrams_get/?resource_id=%20f2e5503e927d-4ad3-9500-4ab9e55deb59&apikey=916c4bfe-396c-4203-b87b-5a68889e9dd5&type=1"
    
    with get(url) as response:
        response = response.json()['result']
        with open("test.csv", "r") as file:
            for data in response:
                pass