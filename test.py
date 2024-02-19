import getdata as gd
from ztmclasses import Position, ZtmStop

# stops = all_stops_data()

      
# linia = input("podaj linie: ")
# xd = get_routes()
# print(xd)

# print(gd.get_lines_from_stop("1242", "02"))
# all_stops_data()
gd.json_print(gd.request_timetable(input()))

# gd.get_live()
# gd.get_routes()
#stop_id_url("Marszałkowska")