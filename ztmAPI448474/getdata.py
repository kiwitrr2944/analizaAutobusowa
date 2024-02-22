from requests import get
import pandas as pd
from datetime import datetime
from json import dumps
import csv
import os
import glob
import time
import genericpath

APIKEY = "916c4bfe-396c-4203-b87b-5a68889e9dd5"
MAXTIMEDIFF = 75.0
dbtimetable_url = "https://api.um.warszawa.pl/api/action/dbtimetable_get/"
dbstore_url = "https://api.um.warszawa.pl/api/action/dbstore_get/"
routes_url = "https://api.um.warszawa.pl/api/action/public_transport_routes/"
dict_url = "https://api.um.warszawa.pl/api/action/public_transport_dictionary/"
live_url = "https://api.um.warszawa.pl/api/action/busestrams_get/"

base_params = {"apikey": APIKEY}


def json_print(text: str) -> None:
    """Wrapper for printing indented data for debugging

    Args:
        text (str): json-formatted text to print
    """
    text = dumps(text, sort_keys=True, indent=4)
    print(text)


def request_all_stops() -> dict:
    """Request database with all stop info.

    Returns:
        dict: in ztm format
    """
    pms = base_params.copy()
    pms['id'] = "1c08a38c-ae09-46d2-8926-4f9d25cb0630"

    return get(dbstore_url, params=pms).json()['result']


def request_lines_from_stop(complex: str, no: str) -> dict:
    """Request lines from specific stop.

    Args:
        complex (str): complex name
        no (str): 'slupek'

    Returns:
        dict: in ztm format
    """
    try:
        int(complex)
    except ValueError:
        get_stop_id(complex)

    pms = base_params.copy()
    pms['id'] = "88cd555f-6f31-43ca-9de4-66c479ad5942"
    pms['busstopId'] = str(complex)
    pms['busstopNr'] = no

    return get(dbtimetable_url, pms).json()['result']


def request_stop_id(complex: str) -> dict:
    """Request id of a complex from its name.

    Args:
        complex(str): complex name.

    Returns:
        dict: dictionary with id.
    """
    pms = base_params.copy()
    pms['id'] = "b27f4c17-5c50-4a5b-89dd-236b282bc499"
    pms['name'] = complex

    return get(dbtimetable_url, pms).json()['result']


def request_routes() -> dict:
    """Request information about routes.

    Returns:
        dict: dictionary containing routes.
    """
    return get(routes_url, params=base_params).json()['result']


def request_timetable(complex: str, no: str, line: str) -> dict:
    """Request the timetable for a specific complex and line.

    Args:
        complex (str): id of the complex.
        no (str): 'slupek'.
        line (str): line id.

    Returns:
        dict: dictionary containing the timetable.
    """
    try:
        int(complex)
    except ValueError:
        get_stop_id(complex)

    pms = base_params.copy()
    pms['id'] = 'e923fa0e-d96c-43f9-ae6e-60518c9f3238'
    pms['busstopId'] = complex
    pms['busstopNr'] = no
    pms['line'] = line

    return get(dbtimetable_url, params=pms).json()['result']


def request_live() -> dict:
    """Request live data from API.

    Returns:
        dict: in ztm format
    """
    pms = base_params.copy()
    pms['resource_id'] = "%20f2e5503e927d-4ad3-9500-4ab9e55deb59"
    pms['type'] = '1'

    return get(live_url, params=pms).json()['result']


def request_dictionary() -> dict:
    """Download dictionary with ztm keywords.

    Returns:
        dict: _description_
    """
    with get(dict_url, params=base_params) as response:
        return response.json()['result']


def get_all_stops() -> bool:
    """Download and save in DATA/allstops.csv data about all stops.

    Returns:
        bool: True when save succedded.
    """
    stops = request_all_stops()
    header = []

    for attr in stops[0]['values']:
        header.append(attr['key'])

    dirpath = f"{os.getcwd()}/DATA/"
    os.makedirs(dirpath, exist_ok=True)

    filepath = dirpath + 'allstops.csv'

    with open(filepath, 'w') as file:
        wr = csv.writer(file)
        wr.writerow(header)
        for stop in stops:
            stop = stop['values']
            params = []

            for attr in stop:
                params.append(attr['value'])

            wr.writerow(params)

    return True


def get_lines_from_stop(complex: str, no: str) -> list[str]:
    """Get lines avaiable on stop

    Args:
        complex (str): complex id
        no (str): 'slupek'

    Returns:
        list[str]: list of lines
    """
    response = request_lines_from_stop(complex, no)
    lines = [line['values'][0]['value'] for line in response]

    return lines


def get_stop_id(complex: str) -> str:
    """Get complex id from name.

    Args:
        complex (str): complex name

    Returns:
        str: complex id
    """
    response = request_stop_id(complex)
    try:
        return response[0]['values'][0]['value']
    except IndexError:
        return "NO STOP EXISTS"


def get_routes() -> None:
    """Unwrap dictionary with all routes and save to /DATA/ROUTES/*.csv files.
    """
    response = request_routes()

    dirpath = f"{os.getcwd()}/DATA/ROUTES/"

    for line in response:
        dirpath2 = dirpath + line + '/'

        os.makedirs(dirpath2, exist_ok=True)

        for route in response[line]:
            filepath = dirpath2 + route + '.csv'

            route_list = response[line][route]
            header = []

            with open(filepath, 'w') as file:
                wr = csv.writer(file)

                for stop in route_list:
                    if len(header) == 0:
                        header = [i for i in route_list[stop]]
                        wr.writerow(header)
                    params = [route_list[stop][i] for i in header]
                    wr.writerow(params)

            df = pd.read_csv(filepath)
            df = df.sort_values(by=['odleglosc'])
            df.to_csv(filepath, index=False)


def get_timetable() -> None:
    """Get and parse all timetables one by one to save in
        /DATA/TIMETABLES/timetable.csv (slow and annoying)
    """
    dirpath = os.getcwd()
    if not genericpath.exists(f"{dirpath}/DATA/allstops.csv"):
        get_all_stops()

    with open(f"{dirpath}/DATA/allstops.csv") as file:
        rd = csv.DictReader(file)
        stops = [(row['zespol'], row['slupek']) for row in rd]

    filepath = f"{dirpath}/DATA/TIMETABLES/timetable.csv"

    with open(filepath, 'w') as file:
        wr = csv.writer(file)
        for stop in stops:
            lines = get_lines_from_stop(stop[0], stop[1])

            header = ['stop', 'no', 'line']

            for line in lines:
                print(stop[0], stop[1], line)
                response = request_timetable(stop[0], stop[1], line)

                for event in response:
                    event = event['values']

                    if len(header) == 3:
                        header = header + [param['key'] for param in event][2:]
                        wr.writerow(header)

                    row = [stop[0], stop[1], line] + [param['value']
                                                      for param in event][2:]
                    wr.writerow(row)


def get_live() -> bool:
    """Unwrap data about live bus positions in given moment and save to
        /DATA/LIVE/RAW/{moment}.csv

    Returns:
        bool: is operation successful
    """
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

    cnt = 0
    goodcnt = 0
    dirpath = f"{os.getcwd()}/DATA/LIVE/RAW"

    os.makedirs(dirpath, exist_ok=True)

    filepath = dirpath + str(time_now.timetz())

    with open(filepath, "w") as file:
        wr = csv.writer(file)
        wr.writerow(header)

        for data in response:
            czas = datetime.fromisoformat(data['Time'])
            c = time_now - czas

            cnt += 1

            if c.total_seconds() >= MAXTIMEDIFF:
                continue

            goodcnt += 1

            lista = []

            for attr in header:
                lista.append(data[attr])
            wr.writerow(lista)

    return True


def organize_live():
    """Divides raw live data into directories for lines."""
    dirpath = os.getcwd()

    files = glob.glob(f"{dirpath}/DATA/LIVE/RAW/*")
    df_list = [pd.read_csv(file, header=0) for file in files]

    df = pd.concat(df_list, ignore_index=True)
    df.sort_values(by=['VehicleNumber', 'Time'], axis=0, inplace=True)

    df.to_csv(f"{dirpath}/DATA/LIVE/positions_all.csv", index=False)

    lines = df['Lines'].unique().tolist()
    dirpath = f"{dirpath}/DATA/LIVE/LINES"
    os.makedirs(dirpath, exist_ok=True)

    for line in lines:
        filepath = f"{dirpath}/{line}.csv"
        df[df['Lines'] == line].to_csv(filepath, index=False)


def all_live() -> None:
    """Creates positions_all.csv file containing all live data gathered."""

    dirpath = os.getcwd()
    files = glob.glob(f"{dirpath}/DATA/LIVE/RAW/*")
    df_list = [pd.read_csv(file, header=0) for file in files]

    df = pd.concat(df_list, ignore_index=True)
    df.sort_values(by=['VehicleNumber', 'Time'], axis=0, inplace=True)

    df.to_csv(f"{dirpath}/DATA/LIVE/positions_all.csv", index=False)
