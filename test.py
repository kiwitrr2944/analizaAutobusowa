from getdata import *
from ztmclasses import Position

pos = Position(0.0, 0.0)
pos2 = Position(52.22, 21.01)
print(pos.distance(pos2))

# przystanek, slupek = input().split(" ")
# print(get_lines_from_stop(przystanek, slupek))
# json_print(find_stops_by_name(przystanek))
# print(get_stop_id(przystanek))
# all_stops_data()