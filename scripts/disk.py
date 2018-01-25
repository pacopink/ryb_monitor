#!/usr/bin/env python
import psutil
concerned = ['/', '/home', '/tmp']
percent=0
def getPercent(path):
    try:
        return int(psutil.disk_usage(path).percent)
    except:
        return 0
print reduce(max, map(getPercent, concerned))
