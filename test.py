# import getdata as gd
# import analizedata as ad
import mapdraw as md
from cProfile import Profile
from pstats import SortKey, Stats
# stops = all_stops_data()

# linia = input("podaj linie: ")
# xd = get_routes()
# print(xd)

# print(gd.get_lines_from_stop("1242", "02"))
# all_stops_data()
# gd.json_print(gd.request_timetable(input(), input(), input()))
# gd.get_timetable()
# gd.get_live()
# gd.get_routes()
# stop_id_url("Marszałkowska")
# gd.get_routes()

# with open('./DATA/ROUTES/738/TP-MET.csv') as file:
#     rd = csv.DictReader(file)
#     for x in rd:
#         print(x)
# gd.organize_live()
# gd.organize_live()

# print(sys.argv[1])

# gd.get_timetable2(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
# gd.organize_timetables()
with Profile() as profile:
    print(f"{md.draw_all_speeding_buses()}")
    (
        Stats(profile)
        .strip_dirs()
        .sort_stats(SortKey.TIME)
        .print_stats()
    )
