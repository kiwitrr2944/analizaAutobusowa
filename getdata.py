from requests import get
from json import dumps

from ztmclasses import ZtmStop

apikey = "916c4bfe-396c-4203-b87b-5a68889e9dd5"
stop_to_id = "https://api.um.warszawa.pl/api/action/dbtimetable_get/?id=b27f4c17-5c50-4a5b-89dd-236b282bc499"
allstops = "https://api.um.warszawa.pl/api/action/dbstore_get/?id=1c08a38c-ae09-46d2-8926-4f9d25cb0630"
lines_on_stop = "https://api.um.warszawa.pl/api/action/dbtimetable_get?id=88cd555f-6f31-43ca-9de4-66c479ad5942"


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
    return f"{allstops}&apikey={apikey}"

def lines_on_stop_url(stop, pos):
    """Gives url to data about lines on stop. Stop can be 
    either name (conversion) or stop_id. 

    Args:
        stop (str): stop_name or stop_id
        pos (str): number of "slupek"

    Returns:
        str: url
    """

    try:
        stop = int(stop)
    except:
        stop = get_stop_id(stop)
    
    return f"{lines_on_stop}&busstopId={stop}&busstopNr={pos}&apikey={apikey}"

def stop_id_url(stop_name):
    """Url for converter stop_name->stop_id
    !!!AMBIGOUS!!!

    Args:
        stop_name (str): stop_name to convert

    Returns:
        str: url
    """
    return f"{stop_to_id}&name={stop_name}&apikey={apikey}"

def get_stop_id(stop_name : str) -> int:
    """Converts stop_name into stop_id
    !!!AMBIGOUS!!!

    Args:
        stop_name(str): stop_name to convert

    Returns:
        str: 4-digit code - id of the stop group with given name
    """
    with get(stop_id_url(stop_name)) as response:
        return int(response.json()['result'][0]['values'][0]['value'])
    
def get_lines_from_stop(przystanek : str, slupek : str) -> list:
    """Gives data about all lines on chosen stop

    Args:
        stop (str): stop_name or stop_id
        pos (str): number of "slupek"
        
    Returns:
        list: all no. of lines departing in str format 
    """
    
    with get(lines_on_stop_url(przystanek, slupek)) as response:
        linie = []
        data = response.json()['result']
        for linia in data:
            linia = linia['values'][0]
            linie.append(linia['value'])
    
        return linie  

def all_stops_data() -> list:
    """Data about all stops in format:

    Returns:
        list: list of ZtmStop instances
    """
    with get(all_stops_url()) as response:
        stops = response.json()['result']
        ret = []
        for stop in stops:
            stop = stop['values']
            params = []
            for attr in stop:
                params.append(attr['value'])
            ret.append(ZtmStop(params))
        return ret
    
def find_stops_by_name(nazwa):
    ret = []
    lista = all_stops_data()
    for przystanek in lista:
        for atrybut in przystanek["values"]:
            if atrybut['key'] == "nazwa_zespolu" and atrybut['value'] == nazwa:
                ret.append(przystanek["values"])
    return ret