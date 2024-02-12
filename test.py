from getdata import *
from ztmclasses import Position, ZtmStop

# name = input()
# print(get_lines_from_stop(przystanek, slupek))
# json_print(find_stops_by_name(przystanek))
# print(get_stop_id(przystanek))
# stops = all_stops_data()
# for stop in stops:
    # if stop.name == name:
        # print(stop)
        # print(get_lines_from_stop(stop.id, stop.order))
        # print("----------------")
      
linia = input("podaj linie: ")
xd = get_routes()
json_print(xd)

#json_print(get_dictionary())