from getdata import json_print, get_stop_id, get_lines_from_stop_name

przystanek, slupek = input().split(" ")
json_print(get_lines_from_stop_name(przystanek, slupek))
