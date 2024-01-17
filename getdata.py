from requests import get
from json import dumps

apikey = "916c4bfe-396c-4203-b87b-5a68889e9dd5"
baseurl = "'https://api.um.warszawa.pl/api/action/"

def jsonPrint(text):
    text = dumps(text, sort_keys=True, indent=4)
    print(text)

def przystanki_url():
    return f"{base_url}"
