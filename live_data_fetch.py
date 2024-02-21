import getdata as gd 
import time

def fetch(times, interval, dirpath="."):
    fail = 0
    for _ in range(times):
        try:
            gd.get_live(dirpath)
            print(f"SAVED {time.ctime()}")
        except:
            fail += 1
        time.sleep(interval)
        
    gd.organize_live()
    return fail/times