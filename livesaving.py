import getdata as gd 
import time

TIMES = 60*60*2

for i in range(TIMES):
    try:
        gd.live_test()
        print(f"SAVED {time.ctime()}")
    except:
        pass
    time.sleep(30)