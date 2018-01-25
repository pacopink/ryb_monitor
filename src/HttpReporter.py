#!/bin/env python
#coding: utf8
'''负责通过HTTP POST上报状态'''

import httplib
import socket
import time
from Logger import *

socket.setdefaulttimeout(3)
URL="/indexer/report"
METHOD="POST"
HEADERS={"Content-Type":"application/json; charset=utf-8"}
def report(msg, host, port):
    conn = httplib.HTTPConnection(host, port)
    body = msg.toJson().encode("utf-8")
    def doPost():
        conn.request(method=METHOD, url=URL, body=body, headers=HEADERS)
        return conn.getresponse()
    res = doPost()
    if res.status==503:
        time.sleep(1)
        res = doPost()
        if res.status==503:
            time.sleep(1)
            res = doPost()
    if res.status==200:
        pass
        log_debug(res.read())
    else:
        log_error("get response [%d][%s] to request [http://%s:%d%s]  [%s] [%s]", res.status, res.read(), host, port, URL, METHOD, body)
    conn.close()

