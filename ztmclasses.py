import datetime
import dis
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

    def __str__(self) -> str:
        """this does what you think it does

        Returns:
            _type_: _description_
        """
        return f"{self.latitude}N, {self.longitude}E"
    
class ZtmStop:
    stop_id : int
    order : str
    group_name : str
    position : Position

    def __init__(self, 
                 stop_id : int, 
                 order : str,
                 group_name : str,
                 street_id : str,
                 longitude : float, 
                 latitude : float,
                 direction : str
                 #nie wiem czy jest mi na coś ta data potrzebna 
                 ):
        self.position = Position(longitude, latitude)
        self.name = group_name
        self.id = stop_id
        self.order = order
        self.street = street_id
        self.direction = direction
    
    def __str__(self) -> str:
        return f"Przystanek: {self.name} {self.order}\n id przystanku: {self.id}\n pozycja {self.position}\n \
                ulica {self.street}, kierunek: {self.direction}"