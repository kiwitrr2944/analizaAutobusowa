from requests import get
from json import dumps

apikey = "916c4bfe-396c-4203-b87b-5a68889e9dd5"
stop_to_id = "https://api.um.warszawa.pl/api/action/dbtimetable_get/?id=b27f4c17-5c50-4a5b-89dd-236b282bc499"
allstops = "https://api.um.warszawa.pl/api/action/dbstore_get/?id=1c08a38c-ae09-46d2-8926-4f9d25cb0630"
lines_on_stop = "https://api.um.warszawa.pl/api/action/dbtimetable_get?id=88cd555f-6f31-43ca-9de4-66c479ad5942"


def json_print(text):
    """ 
        A function to print json indented
    """
    text = dumps(text, sort_keys=True, indent=4)
    print(text)

def all_stops_url():
    return f"{allstops}&apikey={apikey}"

def lines_on_stop_url(przystanek, slupek):
    if not przystanek.isdigit():
        przystanek = get_stop_id(przystanek)
    return f"{lines_on_stop}&busstopId={get_stop_id(przystanek)}&busstopNr={slupek}&apikey={apikey}"

def stop_id_url(nazwa):
    result = f"{stop_to_id}&name={nazwa}&apikey={apikey}"
    return result

def get_stop_id(przystanek):
    with get(stop_id_url(przystanek)) as response:
        return response.json()['result'][0]['values'][0]['value']
    
def get_lines_from_stop(przystanek, slupek):
    with get(lines_on_stop_url(przystanek, slupek)) as response:
        return response.json()
    
def all_stops_data():
    with get(all_stops_url()) as response:
        ret = response.json()['result']
        for x in ret:
            x = x['values']
        return ret
    
def find_stops_by_name(nazwa):
    ret = []
    lista = all_stops_data()
    for przystanek in lista:
        for atrybut in przystanek["values"]:
            if atrybut['key'] == "nazwa_zespolu" and atrybut['value'] == nazwa:
                ret.append(przystanek["values"])
                
    return ret