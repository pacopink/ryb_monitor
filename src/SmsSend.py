#!/bin/env python
#coding: utf8
'''发送短信的API'''
import urllib
import urllib2
import json
import socket
socket.setdefaulttimeout(2)
from Logger import *

def send_msg(SMS_URL, target, msg):
    url = SMS_URL + "?phone={target}&msg={msg}".format(target=urllib.quote(target), msg=urllib.quote(msg))
    # url = SMS_URL+"?phone={target}&msg={msg}".format(target=urllib.quote(target), msg=msg)
    log_info("SMS_URL:[%s]", url)
    req = urllib2.Request(url)
    res = urllib2.urlopen(req)
    # TODO: HOW TO JUDGE THE RESULT
    code = res.getcode()
    content = res.read()
    #print content
    res.close()
    if code == 200:
        r = json.loads(content)

        if 'status' in r:
            return r['status'] == True
        else:
            return False
    else:
        return False
