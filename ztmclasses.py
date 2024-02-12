from re import S
from geopy.distance import distance

class Position:
    def __init__(self, long : float, lat : float):
        """Creates a Position object

        Args:
            long (f): _description_
            lat (_type_): _description_
        """
        self.longitude = long
        self.latitude = lat
    
    def distance(self, other) -> float:
        """Returns distance between two positions in meters.
        
        Args:
            other (Position): point to measure to

        Returns:
            float: distance in meters
        """
        return distance((self.latitude, self.longitude), 
                              (other.latitude, other.longitude)).m

    def __repr__(self) -> str:
        """this does what you think it does

        Returns:
            _type_: _description_
        """
        return f"{self.latitude}N, {self.longitude}E"
  
  
class ZtmStop:
    id : str
    order : str
    name : str
    position : Position
    street : str
    direction : str

    def __init__(self, params : list):
        self.id = params[0]
        self.order = params[1]
        self.name = params[2]
        self.position = Position(params[5], params[4])
        self.street = params[3]
        self.direction = params[6] 
        
    def __repr__(self) -> str:
        return f"Przystanek: {self.name} {self.order}\nid przystanku: {self.id}\npozycja {self.position}\n\
ulica {self.street}, kierunek: {self.direction}"


class ZtmRouteStop:
    no : str 
    distance_from_origin : int
    stop : tuple
    status : int

    def __init__(self, args : list):
        self.no = args[0]
        self.stop = tuple(([args[1], args[2]]))
        self.distance_from_origin = args[3]
        self.status = args[4]
    
    def __repr__(self):
        return f"\n{self.no} {self.stop[0]} {self.stop[1]} {self.distance_from_origin}"


class ZtmRoute:
    line : str
    name : str
    stops : list
    
    def __init__(self, line : str, name : str, data : dict):
        self.line = line
        self.name = name
        self.stops = []
        
        for stop in data:
            args = [stop]
            for arg in data[stop]:
                args.append(data[stop][arg])
            
            self.stops.append(ZtmRouteStop(args))
            
        self.stops = sorted(self.stops, key=lambda x: int(x.no))
    
    def __repr__(self):
        return f"\n{self.line}, {self.name}, {self.stops}"
    